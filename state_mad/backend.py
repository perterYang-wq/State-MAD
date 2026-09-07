from typing import Protocol
from .cache import build_cache_key
from .schema import BackendOutput, GenerationRequest, GenerationResult, TokenUsage, digest

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
    def __init__(self): self.calls=0
    def generate(self,request):
        self.calls+=1
        answer="BRAVO" if request.condition in ("awareness","current-peer") else "ALPHA"
        return BackendOutput(f"ANSWER={answer}",TokenUsage(10,2,12))
