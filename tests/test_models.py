import importlib
import inspect
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock


def load_models_without_runtime_dependencies():
    torch = types.ModuleType("torch")
    torch.bfloat16 = object()
    vllm = types.ModuleType("vllm")
    vllm.LLM = Mock
    vllm.SamplingParams = Mock()

    config_utils = types.ModuleType("src.config_utils")
    config_utils.LLMConfig = object
    model_utils = types.ModuleType("src.model_utils")
    model_utils.TokenUsageTracker = Mock
    utils = types.ModuleType("src.utils")
    utils.extract_answers = Mock()
    utils.extract_answers_with_box = Mock()

    modules = {
        "torch": torch,
        "vllm": vllm,
        "src.config_utils": config_utils,
        "src.model_utils": model_utils,
        "src.utils": utils,
    }
    previous = {name: sys.modules.get(name) for name in modules}
    sys.modules.update(modules)
    sys.modules.pop("src.models", None)
    try:
        return importlib.import_module("src.models")
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class LanguageModelSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = load_models_without_runtime_dependencies()

    def make_model(self):
        model = self.models.LanguageModel.__new__(self.models.LanguageModel)
        tokenizer = Mock(eos_token_id=2)
        tokenizer.apply_chat_template.return_value = ["rendered"]
        model.llm = Mock()
        model.llm.get_tokenizer.return_value = tokenizer
        model.llm.generate.return_value = []
        model.llm_config = SimpleNamespace(model="fake-model")
        model.system_msg = None
        model.token_usage_tracker = Mock()
        model.extract_fn = None
        return model

    def test_optional_seed_is_forwarded_without_changing_legacy_calls(self):
        model = self.make_model()

        model(["prompt"], answer_process=False, seed=1234)
        seeded = self.models.SamplingParams.call_args.kwargs
        self.assertEqual(seeded["seed"], 1234)

        self.models.SamplingParams.reset_mock()
        model(["prompt"], answer_process=False)
        legacy = self.models.SamplingParams.call_args.kwargs
        self.assertNotIn("seed", legacy)
        self.assertEqual(legacy["temperature"], 1)
        self.assertEqual(legacy["top_p"], 1)
        self.assertEqual(legacy["max_tokens"], 24064)
        self.assertTrue(legacy["logprobs"])

    def test_seed_support_is_model_free_detectable_for_preflight(self):
        from state_mad.preflight import E0RunConfig, validate_e0_preflight
        from state_mad.scenarios import compile_e0_scenarios

        parameters = inspect.signature(self.models.LanguageModel.__call__).parameters
        seed_supported = "seed" in parameters
        self.assertTrue(seed_supported)
        self.assertIsNone(parameters["seed"].default)
        probe = {
            "seed_supported": seed_supported,
            "model_available": True,
            "tokenizer_available": True,
            "backend": "fake",
        }
        report = validate_e0_preflight(
            E0RunConfig(), compile_e0_scenarios().scenarios, probe
        )
        self.assertTrue(report["passed"])
        self.assertTrue(report["resolved"]["seed_supported"])


if __name__ == "__main__":
    unittest.main()
