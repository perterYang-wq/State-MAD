from typing import Protocol
from .cache import build_cache_key
from .schema import BackendOutput, GenerationRequest, GenerationResult, TokenUsage, digest
from .preflight import E0RunConfig, PRODUCTION_MODEL_ID

class GenerationBackend(Protocol):
    def generate(self, request: GenerationRequest) -> BackendOutput: ...

class CachedBackend:
    def __init__(self, backend, cache): self.backend=backend; self.cache=cache
    def generate(self, request):
        key=build_cache_key(request.identity); status,payload=self.cache.lookup(key)
        if status=="HIT":
            usage=TokenUsage(**payload["usage"])
            return GenerationResult(payload["raw_output"],usage,TokenUsage(0,0,0),"hit",key,payload["content_hash"],payload["origin_call_id"])
        output=self.backend.generate(request); origin=request.request_id; content_hash=digest(output.raw_output)
        payload={"cache_key":key,"raw_output":output.raw_output,"usage":{"input_tokens":output.usage.input_tokens,"output_tokens":output.usage.output_tokens,"total_tokens":output.usage.total_tokens},"content_hash":content_hash,"origin_call_id":origin}
        self.cache.commit_miss(key,payload)
        return GenerationResult(output.raw_output,output.usage,output.usage,"miss",key,content_hash,origin)

class FakeBackend:
    scientific_backend = False
    def __init__(self): self.calls=0
    def generate(self,request):
        self.calls+=1
        answer="BRAVO" if request.condition in ("awareness","current-peer") else "ALPHA"
        return BackendOutput(f"ANSWER={answer}",TokenUsage(10,2,12))

class LanguageModelBackend:
    """Thin, explicit State-MAD adapter around MAD-M²'s LanguageModel."""
    scientific_backend = True

    def __init__(self, config:E0RunConfig, language_model_cls=None, llm_config_cls=None):
        if config.models != (PRODUCTION_MODEL_ID,) or config.temperature != 0 or config.top_p != 1.0:
            raise ValueError("production E0 requires its exact frozen model and decoding settings")
        if language_model_cls is None or llm_config_cls is None:
            from src.config_utils import LLMConfig
            from src.models import LanguageModel
            language_model_cls = language_model_cls or LanguageModel
            llm_config_cls = llm_config_cls or LLMConfig
        # Never read configs.yaml: every effective generation setting is explicit.
        llm_config=llm_config_cls({}, {"model":PRODUCTION_MODEL_ID,"model_path":None,
            "temperature":0,"top_p":1.0,"max_tokens":config.max_new_tokens})
        llm_config.model=PRODUCTION_MODEL_ID; llm_config.model_path=None
        llm_config.temperature=0; llm_config.top_p=1.0
        llm_config.max_tokens=config.max_new_tokens
        self.config=config
        self.model=language_model_cls(llm_config, system_msg="State-MAD strict categorical response")

    def generate(self, request:GenerationRequest)->BackendOutput:
        expected=(("temperature",0.0),("top_p",1.0))
        i=request.identity
        if (i.model!=PRODUCTION_MODEL_ID or i.model_revision!=self.config.model_revision or
            i.tokenizer_revision!=self.config.tokenizer_revision or i.decoding!=expected or
            i.max_new_tokens!=self.config.max_new_tokens):
            raise ValueError("request identity differs from effective production configuration")
        result=self.model([i.user_input],answer_process=False,seed=i.seed)
        raw=result["results"][0]
        input_tokens=result["cur_batch_input_tokens"]; output_tokens=result["cur_batch_output_tokens"]
        return BackendOutput(raw,TokenUsage(input_tokens,output_tokens,input_tokens+output_tokens))
