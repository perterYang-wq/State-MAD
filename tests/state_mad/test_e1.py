import json
import inspect
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from state_mad.backend import CachedBackend
from state_mad.cache import MessageCache
from state_mad.e1 import (build_e1_peer_control_report,
                          build_e1_peer_messages, run_e1, run_e1_dry)
import state_mad.e0 as e0_module
from state_mad.grading import CLASSES, grade_output
from state_mad.lineage import validate_e1_lineage
from state_mad.metrics import E1_ARMS, evaluate_e1
from state_mad.preflight import E1RunConfig, validate_e1_preflight
from state_mad.prompts import (render_awareness_probe, render_decision,
                               render_e1_peer_message, render_peer_message)
from state_mad.run_store import RunStore
from state_mad.scenarios import E0ScenarioSpec, E1ScenarioSpec, compile_e0_scenarios, compile_e1_scenarios
from state_mad.schema import (BackendOutput, EffectiveGenerationIdentity,
                              GenerationRequest, TokenUsage, digest)
from state_mad.snapshots import make_pre_exposure_snapshot
from state_mad.validation import ScenarioValidationError, validate_e1_scenario_set


E0_HASH="sha256:9d8d2e6cf9f03d98cc81f4823ad36aae1f5dea3eaaa94c5f745b47e5a248ec50"
E0_SCIENTIFIC_HASH="sha256:8d6e36a6c82d3c79939b5a98c7af4937ff7274ab991695c4fa31ff1e58667e57"


class ScriptedE1Backend:
    def __init__(self, scenarios): self.calls=0; self.scenarios={s.scenario_id:s for s in scenarios}
    def generate(self, request):
        self.calls+=1; scenario=self.scenarios[request.scenario_id]; number=int(request.scenario_id[-2:])
        if request.condition=="stale-peer" and number<=8: value=scenario.v_old
        elif request.condition=="static-wrong": value=scenario.v_wrong
        else: value=scenario.v_new
        return BackendOutput("ANSWER="+value,TokenUsage(11,2,13))


class CountingBackend:
    def __init__(self): self.calls=0
    def generate(self, request):
        self.calls+=1
        return BackendOutput("ANSWER=ALPHA",TokenUsage(2,1,3))


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
        self.assertEqual(compile_e0_scenarios(E0ScenarioSpec(count=16,seed=7)).scenario_set_hash,E0_SCIENTIFIC_HASH)

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
        awareness=render_awareness_probe(scenario,snapshot)
        decision=render_decision(scenario,snapshot,"no-peer")
        peer=render_peer_message(scenario,scenario.v_old,"x")
        self.assertEqual((awareness.template_id,awareness.template_hash),("awareness-v3",digest("awareness-v3")))
        self.assertEqual((decision.template_id,decision.template_hash),("decision-v2",digest("decision-v2")))
        self.assertEqual(peer.text,f"PEER|fact={scenario.fact_id}|value={scenario.v_old}|confidence=high|history=x")
        self.assertEqual((peer.template_id,peer.template_hash),("peer-v1",digest("peer-v1")))
        self.assertEqual(awareness.prompt_hash,"sha256:1fa304a9a9eb2efb48a9047ecf6fc32feaaa0fdd917a5744311574e2772f3116")
        self.assertEqual(decision.prompt_hash,"sha256:c243875a36a89548ca9385a56b0881b89c31051a3c74897ef8d8da578c633aae")
        self.assertEqual(peer.prompt_hash,"sha256:47a5cbc8233f82e2a7513f1b836f1bc64efa2ea3fc886aadcad5599414a53a9c")
        self.assertIn("render_peer_message(s,value,history)",inspect.getsource(e0_module.run_e0))
        self.assertEqual(CLASSES,("CURRENT","STALE","STATIC_WRONG","OTHER/INVALID"))
        self.assertEqual(grade_output("ANSWER="+scenario.v_wrong,scenario.answer_pool).answer_class,"STATIC_WRONG")

    def test_peer_semantics_and_matching_surface(self):
        scenario=self.ss.scenarios[0]; peers,check=build_e1_peer_messages(scenario,lambda text: len(text.encode()))
        self.assertIn(f"|value={scenario.v_new}|",peers["current-peer"].raw_content)
        self.assertEqual(peers["current-peer"].version_id,scenario.version_new_id)
        self.assertIn(f"|value={scenario.v_old}|",peers["stale-peer"].raw_content)
        self.assertEqual(peers["stale-peer"].version_id,scenario.version_old_id)
        self.assertEqual((peers["stale-peer"].generation_validity,peers["stale-peer"].decision_validity),("current","stale"))
        self.assertIn("was_current=1|current_now=0",peers["stale-peer"].raw_content)
        self.assertEqual((peers["static-wrong"].generation_validity,peers["static-wrong"].decision_validity),("never_current","static_wrong"))
        self.assertEqual(peers["static-wrong"].version_id,scenario.fact_id+":v_wrong")
        self.assertIn(f"|value={scenario.v_wrong}|",peers["static-wrong"].raw_content)
        self.assertIn("was_current=0|current_now=0",peers["static-wrong"].raw_content)
        self.assertIn("was_current=1|current_now=1",peers["current-peer"].raw_content)
        self.assertTrue(all(x["template_id"]=="peer-v2" for x in check["renderings"].values()))
        self.assertTrue(all(isinstance(x["token_count"],int) for x in check["renderings"].values()))
        fields=[message.raw_content.split("|") for message in peers.values()]
        self.assertTrue(all([part.split("=")[0] for part in item]==
                            ["PEER","fact","value","confidence","was_current","current_now"] for item in fields))
        self.assertTrue(all(term not in message.raw_content for message in peers.values()
                            for term in ("current_after_update","correct_when_created_then_superseded","never_current")))

    def test_peer_v2_control_report_exact_and_counterbalanced(self):
        # A deterministic token fixture gives symbolic values unequal token
        # lengths while treating the matched binary status fields symmetrically.
        weights={"ALPHA":1,"BRAVO":2,"CHARLIE":3,"DELTA":4}
        counter=lambda text: (text.count("|")+text.count("\n")+
                              (0 if text.startswith("ORDINARY DECISION") else
                               sum(text.count(v)*n for v,n in weights.items())))
        report=build_e1_peer_control_report(self.ss.scenarios,counter,"synthetic-token-counter")
        self.assertEqual(report["template_id"],"peer-v2")
        self.assertTrue(report["status_structure_exact_match"])
        self.assertTrue(report["actual_peer_multiset_match"])
        self.assertTrue(report["actual_decision_prompt_multiset_match"])
        self.assertTrue(report["paired_full_prompt_token_balance_pass"])
        self.assertTrue(all(report["paired_full_prompt_pair_pass"].values()))
        self.assertTrue(all(total==0 for total in report["paired_full_prompt_delta_sums"].values()))
        self.assertTrue(report["role_balance_pass"]); self.assertTrue(report["overall_pass"])
        self.assertTrue(all(set(counts.values())=={10} for counts in report["role_counts"].values()))
        self.assertTrue(any(len(set(row["actual_peer_token_counts"].values()))>1
                            for row in report["per_scenario"].values()))

    def test_peer_v2_control_report_uses_paired_balance_not_marginal_multisets(self):
        def paired_counter(text):
            if not text.startswith("ORDINARY DECISION"):
                return 10
            scenario_number=int(text.split("fact=fact-e1-")[1][:2])
            pattern=(scenario_number-1)%3
            if "was_current=1|current_now=0" in text:
                return 100+(0,1,1)[pattern]
            if "was_current=0|current_now=0" in text:
                return 100+(0,0,2)[pattern]
            return 100+(0,0,2)[pattern]
        report=build_e1_peer_control_report(self.ss.scenarios,paired_counter)
        self.assertFalse(report["actual_decision_prompt_multiset_match"])
        self.assertTrue(report["paired_full_prompt_token_balance_pass"])
        self.assertTrue(report["overall_pass"])
        self.assertEqual(set(report["paired_full_prompt_deltas"]),{
            "current_vs_stale","current_vs_static_wrong","stale_vs_static_wrong"})
        for name,histogram in report["paired_full_prompt_delta_histograms"].items():
            self.assertTrue(all(histogram.get(delta,0)==histogram.get(-delta,0) for delta in histogram),name)
            self.assertEqual(report["paired_full_prompt_delta_sums"][name],0)
            self.assertTrue(report["paired_full_prompt_pair_pass"][name])

    def test_peer_v2_control_report_detects_each_hard_gate_failure(self):
        def asymmetric(text):
            return len(text)+(1 if "was_current=1|current_now=0" in text else 0)
        report=build_e1_peer_control_report(self.ss.scenarios,asymmetric)
        self.assertFalse(report["status_structure_exact_match"]); self.assertFalse(report["overall_pass"])
        def broken_actual(text):
            return len(text)+(1 if "fact=fact-e1-40|value=ALPHA" in text else 0)
        report=build_e1_peer_control_report(self.ss.scenarios,broken_actual)
        self.assertFalse(report["actual_peer_multiset_match"]); self.assertFalse(report["overall_pass"])
        def broken_prompt(text):
            return len(text)+(1 if text.startswith("ORDINARY DECISION") and
                                "fact-e1-40|value=ALPHA" in text else 0)
        report=build_e1_peer_control_report(self.ss.scenarios,broken_prompt)
        self.assertFalse(report["actual_decision_prompt_multiset_match"])
        self.assertFalse(report["paired_full_prompt_token_balance_pass"])
        self.assertTrue(any(total!=0 for total in report["paired_full_prompt_delta_sums"].values()))
        self.assertTrue(any(any(histogram.get(delta,0)!=histogram.get(-delta,0)
                                 for delta in histogram)
                            for histogram in report["paired_full_prompt_delta_histograms"].values()))
        self.assertFalse(report["overall_pass"])

        unbalanced=self.ss.scenarios[:-1]
        report=build_e1_peer_control_report(unbalanced,lambda text: 1)
        self.assertFalse(report["role_balance_pass"]); self.assertFalse(report["overall_pass"])

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
        with tempfile.TemporaryDirectory() as directory:
            backend=CountingBackend(); cached=CachedBackend(backend,MessageCache(directory))
            request=lambda request_id,experiment,ident: GenerationRequest(
                request_id,ident,"shared-scenario",experiment,"decision",experiment+":condition",
                experiment+":pair","target","target",experiment+":snapshot",None,experiment+":branch")
            first=cached.generate(request("e0-call","E0",identity))
            second=cached.generate(request("e1-call","E1",identity))
            changed=cached.generate(request("e1-changed","E1",replace(identity,user_input="different")))
            self.assertEqual((first.cache_status,second.cache_status,changed.cache_status),("miss","hit","miss"))
            self.assertEqual(backend.calls,2)
            self.assertEqual(second.generated_usage.total_tokens,0)

    def test_lineage_rejects_missing_decision_arm(self):
        report=validate_e1_lineage([],[],{"no-peer":"no-peer-output"},())
        self.assertFalse(report["passed"])
        self.assertIn("INCOMPLETE_DECISION_ARMS",report["errors"])

    def test_scientific_peer_mismatch_preflights_all_scenarios_before_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); config=E1RunConfig(mode="scientific",run_id="scientific-e1",
                cache_root=str(root/"cache"),run_store_root=str(root/"runs"),
                model_revision="model-revision",tokenizer_revision="tokenizer-revision")
            backend=CountingBackend(); backend.scientific_backend=True
            cached=CachedBackend(backend,MessageCache(root/"cache"/"scientific"))
            store=RunStore(root/"runs"/"scientific").create(config.run_id)
            def late_mismatch(text):
                return 6 if "fact-e1-40" in text and "was_current=0|current_now=0" in text else 5
            probe={"seed_supported":True,"model_available":True,"tokenizer_available":True,"backend":"language-model"}
            with self.assertRaisesRegex(RuntimeError,"NEEDS HUMAN DECISION"):
                run_e1(config,cached,store,probe,late_mismatch)
            self.assertEqual(backend.calls,0)

    def test_runtime_provenance_survives_manifest_persistence(self):
        runtime={"seed_supported":True,"model_available":True,"tokenizer_available":True,"backend":"scripted",
            "backend_version":"1.2.3","torch_version":"2.test","transformers_version":"4.test",
            "vllm_version":"0.test","gpu/runtime":{"gpu":"synthetic","runtime":"none"},
            "quantization":"none","batching":{"size":1},"context":{"max_sequence":4096}}
        with tempfile.TemporaryDirectory() as directory:
            backend=ScriptedE1Backend(self.ss.scenarios)
            store=RunStore(Path(directory)/"runs").create("runtime-provenance")
            result=run_e1(E1RunConfig(run_id="runtime-provenance"),
                CachedBackend(backend,MessageCache(Path(directory)/"cache")),store,runtime)
            persisted=json.loads((store.run_dir/"manifest.json").read_text())
            self.assertEqual(result["manifest"]["effective_generation"]["runtime"],runtime)
            self.assertEqual(persisted["effective_generation"]["runtime"],runtime)
            self.assertEqual(persisted["effective_generation"]["quantization"],"none")
            self.assertEqual(persisted["effective_generation"]["batching"],{"size":1})
            self.assertEqual(persisted["effective_generation"]["context"],{"max_sequence":4096})

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
