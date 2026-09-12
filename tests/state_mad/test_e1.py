import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from state_mad.backend import CachedBackend
from state_mad.cache import MessageCache, build_cache_key
from state_mad.e1 import build_e1_peer_messages, run_e1_dry
from state_mad.grading import CLASSES, grade_output
from state_mad.metrics import E1_ARMS, evaluate_e1
from state_mad.preflight import E1RunConfig, validate_e1_preflight
from state_mad.prompts import render_awareness_probe, render_decision, render_peer_message
from state_mad.run_store import RunStore
from state_mad.scenarios import E1ScenarioSpec, compile_e0_scenarios, compile_e1_scenarios
from state_mad.schema import (BackendOutput, EffectiveGenerationIdentity,
                              GenerationRequest, TokenUsage, canonical_bytes, digest)
from state_mad.snapshots import make_pre_exposure_snapshot
from state_mad.validation import ScenarioValidationError, validate_e1_scenario_set


E0_HASH="sha256:9d8d2e6cf9f03d98cc81f4823ad36aae1f5dea3eaaa94c5f745b47e5a248ec50"


class ScriptedE1Backend:
    def __init__(self, scenarios): self.calls=0; self.scenarios={s.scenario_id:s for s in scenarios}
    def generate(self, request):
        self.calls+=1; scenario=self.scenarios[request.scenario_id]; number=int(request.scenario_id[-2:])
        if request.condition=="stale-peer" and number<=8: value=scenario.v_old
        elif request.condition=="static-wrong": value=scenario.v_wrong
        else: value=scenario.v_new
        return BackendOutput("ANSWER="+value,TokenUsage(11,2,13))


def metric_rows(stale=0, current_stale=0, static_stale=0, count=40):
    rows=[]
    for index in range(count):
        sid=f"e1-{index+1:02d}"
        classes={"awareness":"CURRENT","no-peer":"CURRENT",
                 "current-peer":"STALE" if index<current_stale else "CURRENT",
                 "stale-peer":"STALE" if index<stale else "CURRENT",
                 "static-wrong":"STALE" if index<static_stale else "STATIC_WRONG"}
        for condition,answer_class in classes.items():
            rows.append({"call_id":sid+condition,"scenario_id":sid,"condition":condition,"answer_class":answer_class,
                "input_tokens":3,"output_tokens":1,"total_tokens":4,"generated_input_tokens":3,
                "generated_output_tokens":1,"generated_total_tokens":4})
    return rows


class E1Tests(unittest.TestCase):
    def setUp(self): self.ss=compile_e1_scenarios()

    def test_compiler_is_frozen_stable_and_balanced(self):
        again=compile_e1_scenarios()
        self.assertEqual(len(self.ss.scenarios),40); self.assertEqual(self.ss.to_bytes(),again.to_bytes())
        self.assertEqual([s.scenario_id for s in self.ss.scenarios],[f"e1-{i:02d}" for i in range(1,41)])
        self.assertEqual({s.split for s in self.ss.scenarios},{"pilot"})
        self.assertEqual({s.template_id for s in self.ss.scenarios},{"direct_state_categorical_v1"})
        report=validate_e1_scenario_set(self.ss.scenarios)
        self.assertTrue(report.passed); self.assertLessEqual(report.balance["max_delta"],1)
        self.assertEqual(compile_e0_scenarios().scenario_set_hash,E0_HASH)

    def test_compiler_and_validator_fail_closed(self):
        for count in (39,41):
            with self.assertRaises(ValueError): compile_e1_scenarios(E1ScenarioSpec(count=count))
        with self.assertRaises(ScenarioValidationError): validate_e1_scenario_set(self.ss.scenarios[:-1])
        with self.assertRaises(ScenarioValidationError): validate_e1_scenario_set(self.ss.scenarios+(replace(self.ss.scenarios[-1],scenario_id="e1-41"),))
        duplicate=(self.ss.scenarios[0],replace(self.ss.scenarios[1],scenario_id="e1-01"))+self.ss.scenarios[2:]
        with self.assertRaises(ScenarioValidationError): validate_e1_scenario_set(duplicate)
        for bad in (replace(self.ss.scenarios[0],v_wrong=self.ss.scenarios[0].v_old),
                    replace(self.ss.scenarios[0],version_new_id=self.ss.scenarios[0].version_old_id),
                    replace(self.ss.scenarios[0],target_visible_versions=()),
                    replace(self.ss.scenarios[0],decision_phase_id=self.ss.scenarios[0].final_vote_phase_id)):
            with self.assertRaises(ScenarioValidationError): validate_e1_scenario_set((bad,)+self.ss.scenarios[1:])

    def test_frozen_prompt_and_grader_contracts(self):
        scenario=self.ss.scenarios[0]; snapshot=make_pre_exposure_snapshot(scenario)
        self.assertEqual(render_awareness_probe(scenario,snapshot).template_id,"awareness-v3")
        self.assertEqual(render_decision(scenario,snapshot,"no-peer").template_id,"decision-v2")
        self.assertEqual(render_peer_message(scenario,scenario.v_old,"x").template_id,"peer-v1")
        self.assertEqual(CLASSES,("CURRENT","STALE","STATIC_WRONG","OTHER/INVALID"))
        self.assertEqual(grade_output("ANSWER="+scenario.v_wrong,scenario.answer_pool).answer_class,"STATIC_WRONG")

    def test_peer_semantics_and_matching_surface(self):
        scenario=self.ss.scenarios[0]; peers,check=build_e1_peer_messages(scenario,lambda text: len(text.encode()))
        self.assertEqual((peers["stale-peer"].generation_validity,peers["stale-peer"].decision_validity),("current","stale"))
        self.assertIn("correct_when_created_then_superseded",peers["stale-peer"].raw_content)
        self.assertEqual((peers["static-wrong"].generation_validity,peers["static-wrong"].decision_validity),("never_current","static_wrong"))
        self.assertEqual(peers["static-wrong"].version_id,scenario.fact_id+":v_wrong")
        self.assertIn("never_current",peers["static-wrong"].raw_content)
        self.assertTrue(all(x["template_id"]=="peer-v1" for x in check["renderings"].values()))
        self.assertTrue(all(isinstance(x["token_count"],int) for x in check["renderings"].values()))

    def test_preflight_is_e1_specific_and_fail_closed(self):
        probe={"seed_supported":True,"model_available":True,"tokenizer_available":True}
        self.assertTrue(validate_e1_preflight(E1RunConfig(),self.ss.scenarios,probe)["passed"])
        bad=(replace(E1RunConfig(),scenario_count=39),replace(E1RunConfig(),agents=3),
             replace(E1RunConfig(),conditions=("no-peer",)),replace(E1RunConfig(),main_rounds=2),
             replace(E1RunConfig(),experiment="E0"),replace(E1RunConfig(),temperature=.1))
        self.assertTrue(all(not validate_e1_preflight(config,self.ss.scenarios,probe)["passed"] for config in bad))

    def test_metrics_gates_denominators_and_tokens(self):
        report=evaluate_e1(metric_rows(stale=8),[f"e1-{i:02d}" for i in range(1,41)])
        self.assertEqual(report["awareness_numerator"],40); self.assertEqual(report["treatment_only_count"],8)
        self.assertEqual(report["sar"],{"no-peer":0.0,"current-peer":0.0,"stale-peer":.2,"static-wrong":0.0})
        self.assertEqual(report["current_state_accuracy"],{"no-peer":1.0,"current-peer":1.0,"stale-peer":.8,"static-wrong":0.0})
        self.assertAlmostEqual(report["csae"],.2); self.assertAlmostEqual(report["stale_vs_no_peer"],.2)
        self.assertAlmostEqual(report["stale_vs_static_wrong"],.2); self.assertEqual(report["gate_2"],"POSITIVE PILOT TARGET MET")
        self.assertEqual(report["gate_3"],"NO GATE-3 NEGATIVE FLAG")
        self.assertEqual(report["tokens"]["total"]["total_tokens"],800)
        self.assertEqual(report["tokens"]["by_scenario"]["e1-01"]["total_tokens"],20)
        self.assertEqual(report["tokens"]["by_condition"]["awareness"]["total_tokens"],160)
        unsupported=evaluate_e1(metric_rows(stale=1),[f"e1-{i:02d}" for i in range(1,41)])
        self.assertEqual(unsupported["gate_2"],"CAUSAL PROPAGATION UNSUPPORTED AT PILOT SCOPE")
        unresolved=evaluate_e1(metric_rows(stale=3),[f"e1-{i:02d}" for i in range(1,41)])
        self.assertEqual(unresolved["gate_2"],"NEEDS HUMAN DECISION")
        negative=evaluate_e1(metric_rows(stale=40,static_stale=40),[f"e1-{i:02d}" for i in range(1,41)])
        self.assertEqual(negative["paired_stale_static_wrong_concordance"],1)
        self.assertEqual(negative["gate_3"],"STALE-SPECIFICITY NOT SUPPORTED")
        invalid=metric_rows(); invalid[1]["answer_class"]="OTHER/INVALID"
        self.assertEqual(sum(evaluate_e1(invalid,[f"e1-{i:02d}" for i in range(1,41)])["class_distributions"]["no-peer"].values()),40)

    def test_cache_identity_cross_experiment_reuse(self):
        identity=EffectiveGenerationIdentity("s","u","m","r","t","tr","c",(("temperature",0),),7,9)
        self.assertEqual(build_cache_key(identity),build_cache_key(identity))
        self.assertNotEqual(build_cache_key(identity),build_cache_key(replace(identity,user_input="different")))

    def test_full_model_free_run_artifacts_lineage_cache_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            backend=ScriptedE1Backend(self.ss.scenarios); cache=MessageCache(Path(directory)/"cache")
            store=RunStore(Path(directory)/"runs").create("e1-dry")
            result=run_e1_dry(CachedBackend(backend,cache),store,peer_token_counter=lambda text: len(text.split("|")))
            self.assertEqual((len(result["scenarios"]),len(result["calls"]),backend.calls),(40,200,200))
            self.assertTrue(result["lineage"]["passed"]); self.assertEqual(result["report"]["gate_2"],"POSITIVE PILOT TARGET MET")
            for item in result["report"]["branch_topology"].values():
                self.assertEqual(set(item["branches"]),{"awareness","no-peer",*E1_ARMS[1:]})
                self.assertTrue(all(branch["parent_snapshot_hash"]==item["parent_snapshot_hash"] for branch in item["branches"].values()))
                self.assertEqual(item["branches"]["awareness"]["peer_message_ids"],())
                self.assertEqual(item["branches"]["no-peer"]["peer_message_ids"],())
                self.assertTrue(all(len(item["branches"][arm]["peer_message_ids"])==1 for arm in E1_ARMS[1:]))
            self.assertEqual(len(result["cache_provenance"]),200)
            required={"scenarios.json","validation.json","balance.json","calls.jsonl","lineage.jsonl","report.json","cache_provenance.json","manifest.json","messages"}
            self.assertEqual(required,{path.name for path in store.run_dir.iterdir()})
            for name,key in (("scenarios.json","scenarios"),("validation.json","validation"),("balance.json","balance"),
                             ("report.json","report"),("cache_provenance.json","cache_provenance")):
                self.assertEqual(digest(json.loads((store.run_dir/name).read_text())),result["manifest"]["artifact_hashes"][key])
            self.assertEqual(result["manifest"]["usage"],{"input_tokens":2200,"output_tokens":400,"total_tokens":2600})
            self.assertEqual(result["manifest"]["cache_stats"],{"hits":0,"misses":200})
            with self.assertRaises(FileExistsError): RunStore(Path(directory)/"runs").create("e1-dry")
            replay_store=RunStore(Path(directory)/"runs").create("e1-replay")
            replay=run_e1_dry(CachedBackend(backend,cache),replay_store,replace(E1RunConfig(),run_id="e1-replay"))
            self.assertEqual(backend.calls,200); self.assertTrue(all(call.generated_total_tokens==0 for call in replay["calls"]))
            self.assertTrue(all(item["origin_run_id"] is None and item["origin_resolution"]=="legacy_unresolved" for item in replay["cache_provenance"]))
            self.assertEqual(replay["manifest"]["usage"],{"input_tokens":0,"output_tokens":0,"total_tokens":0})


if __name__=="__main__": unittest.main()
