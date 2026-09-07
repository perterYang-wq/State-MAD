import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from state_mad.backend import FakeBackend, LanguageModelBackend
from state_mad.cache import build_cache_key
from state_mad.e0 import _identity, prepare_e0_run, run_e0
from state_mad.preflight import E0RunConfig, PRODUCTION_MODEL_ID, validate_e0_preflight
from state_mad.prompts import render_awareness_probe
from state_mad.scenarios import compile_e0_scenarios
from state_mad.schema import GenerationRequest
from state_mad.snapshots import make_pre_exposure_snapshot
from tests.test_models import load_models_without_runtime_dependencies


class ConfigFixture:
    def __init__(self, general, model):
        self.__dict__.update(model)


class ProductionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.scenarios = compile_e0_scenarios().scenarios

    def scientific_config(self, root):
        return E0RunConfig(mode="scientific", run_id="scientific-001",
            cache_root=str(Path(root)/"cache"), run_store_root=str(Path(root)/"runs"),
            model_revision="0123456789abcdef", tokenizer_revision="fedcba9876543210")

    def test_backend_to_language_model_to_sampling_params(self):
        models = load_models_without_runtime_dependencies()
        config = replace(E0RunConfig(), model_revision="0123456789abcdef",
                         tokenizer_revision="fedcba9876543210")
        backend = LanguageModelBackend(config, models.LanguageModel, ConfigFixture)
        tokenizer = Mock(eos_token_id=2)
        tokenizer.apply_chat_template.return_value = ["rendered prompt"]
        backend.model.llm.get_tokenizer.return_value = tokenizer
        generated = SimpleNamespace(prompt_token_ids=[1, 2, 3], outputs=[SimpleNamespace(
            text="ANSWER=BRAVO", token_ids=[4, 5], logprobs=[])])
        backend.model.llm.generate.return_value = [generated]
        scenario = self.scenarios[0]
        prompt = render_awareness_probe(scenario, make_pre_exposure_snapshot(scenario))
        identity = _identity(prompt, config)
        request = GenerationRequest("call", identity, scenario.scenario_id, "E0", "phase",
            "awareness", "pair", "target", "target", "snapshot", None, "probe")

        output = backend.generate(request)

        self.assertEqual(tokenizer.apply_chat_template.call_args.args[0][0][-1]["content"], prompt.text)
        self.assertEqual(output.raw_output, "ANSWER=BRAVO")
        params = models.SamplingParams.call_args.kwargs
        self.assertEqual(params["seed"], config.seed)
        self.assertEqual(params["temperature"], 0)
        self.assertEqual(params["top_p"], 1.0)
        self.assertEqual(params["max_tokens"], 32)

    def test_top_p_and_max_tokens_are_effective_cache_identity(self):
        scenario = self.scenarios[0]
        prompt = render_awareness_probe(scenario, make_pre_exposure_snapshot(scenario))
        base = _identity(prompt, E0RunConfig())
        changed_top_p = replace(base, decoding=(("temperature", 0.0), ("top_p", .9)))
        changed_max = replace(base, max_new_tokens=33)
        self.assertNotEqual(build_cache_key(base), build_cache_key(changed_top_p))
        self.assertNotEqual(build_cache_key(base), build_cache_key(changed_max))

    def test_scientific_preflight_exact_identity_and_revisions(self):
        good_probe = {"seed_supported":True, "model_available":True,
                      "tokenizer_available":True, "backend":"language-model"}
        with tempfile.TemporaryDirectory() as root:
            good = self.scientific_config(root)
            self.assertTrue(validate_e0_preflight(good, self.scenarios, good_probe)["passed"])
            for bad in (replace(good, models=("other/7B",)),
                        replace(good, model_revision="resolved-revision"),
                        replace(good, tokenizer_revision="resolved-tokenizer-revision")):
                self.assertFalse(validate_e0_preflight(bad, self.scenarios, good_probe)["passed"])

    def test_scientific_rejects_fake_and_namespaces_are_non_overwriting(self):
        with tempfile.TemporaryDirectory() as root:
            scientific = self.scientific_config(root)
            with self.assertRaises(ValueError):
                prepare_e0_run(scientific, FakeBackend())
            dry = replace(E0RunConfig(), cache_root=str(Path(root)/"cache"),
                          run_store_root=str(Path(root)/"runs"))
            _, dry_store = prepare_e0_run(dry, FakeBackend())
            self.assertIn("dry-run", dry_store.run_dir.parts)
            production = Mock(scientific_backend=True)
            _, scientific_store = prepare_e0_run(scientific, production)
            self.assertIn("scientific", scientific_store.run_dir.parts)
            self.assertNotEqual(dry_store.run_dir, scientific_store.run_dir)
            with self.assertRaises(FileExistsError):
                prepare_e0_run(scientific, production)
            from state_mad.backend import CachedBackend
            from state_mad.cache import MessageCache
            with self.assertRaises(ValueError):
                run_e0(scientific, CachedBackend(FakeBackend(), MessageCache(Path(root)/"rogue")),
                       backend_probe={"seed_supported":True, "model_available":True,
                                      "tokenizer_available":True, "backend":"language-model"})

    def test_scientific_manifest_has_resolved_effective_settings(self):
        class ModelFreeProduction:
            scientific_backend = True
            def generate(self, request):
                from state_mad.schema import BackendOutput, TokenUsage
                return BackendOutput("ANSWER=INVALID-"+request.request_id, TokenUsage(3, 2, 5))

        with tempfile.TemporaryDirectory() as root:
            config = self.scientific_config(root)
            cached, store = prepare_e0_run(config, ModelFreeProduction())
            probe = {"seed_supported":True, "model_available":True,
                     "tokenizer_available":True, "backend":"language-model"}
            result = run_e0(config, cached, store, probe)
            effective = result["manifest"]["effective_generation"]
            self.assertEqual(effective["model_id"], PRODUCTION_MODEL_ID)
            self.assertEqual(effective["model_revision"], config.model_revision)
            self.assertEqual(effective["tokenizer_revision"], config.tokenizer_revision)
            self.assertEqual(effective["temperature"], 0)
            self.assertEqual(effective["top_p"], 1.0)
            self.assertEqual(effective["max_new_tokens"], 32)
            self.assertEqual(effective["seed"], 7)
            self.assertEqual(effective["run_id"], config.run_id)
            self.assertTrue(all(call.run_id == config.run_id for call in result["calls"]))
            self.assertTrue((store.run_dir/"manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
