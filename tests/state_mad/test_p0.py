import json, tempfile, unittest
from dataclasses import replace
from pathlib import Path

from state_mad.backend import CachedBackend
from state_mad.cache import CacheIntegrityError, MessageCache, build_cache_key
from state_mad.e0 import run_e0_dry
from state_mad.grading import CLASSES, grade_output
from state_mad.manifest import build_manifest, finalize_manifest
from state_mad.preflight import E0RunConfig, validate_e0_preflight
from state_mad.prompts import render_awareness_probe, render_decision, render_peer_message
from state_mad.run_store import RunStore
from state_mad.scenarios import E0ScenarioSpec, compile_e0_scenarios
from state_mad.schema import BackendOutput, EffectiveGenerationIdentity, GenerationRequest, MessageRecord, TokenUsage, canonical_bytes, digest
from state_mad.snapshots import fork_snapshot, make_pre_exposure_snapshot
from state_mad.validation import ScenarioValidationError, validate_scenario_set

class ScriptedBackend:
    def __init__(self, scenarios): self.calls=0; self.scenarios={s.scenario_id:s for s in scenarios}
    def generate(self,req):
        self.calls+=1; s=self.scenarios[req.scenario_id]
        value=s.v_old if req.condition=="stale-peer" and int(s.scenario_id[-2:])<=4 else s.v_new
        return BackendOutput("ANSWER="+value,TokenUsage(11,2,13))

class P0Tests(unittest.TestCase):
    def setUp(self): self.ss=compile_e0_scenarios()
    def test_compiler_validator_counterbalance(self):
        other=compile_e0_scenarios(); self.assertEqual(self.ss.to_bytes(),other.to_bytes()); self.assertEqual(len(self.ss.scenarios),16)
        report=validate_scenario_set(self.ss.scenarios); self.assertTrue(report.passed); self.assertLessEqual(report.balance["max_delta"],1)
        with self.assertRaises(ValueError): compile_e0_scenarios(E0ScenarioSpec(count=15))
        bad=replace(self.ss.scenarios[0],v_new=self.ss.scenarios[0].v_old)
        with self.assertRaises(ScenarioValidationError): validate_scenario_set((bad,)+self.ss.scenarios[1:])
    def test_prompts_and_immutable_siblings(self):
        s=self.ss.scenarios[0]; parent=make_pre_exposure_snapshot(s); before=canonical_bytes(parent)
        probe=fork_snapshot(parent,"probe",("probe-output",)); decision=fork_snapshot(parent,"stale",("peer",))
        self.assertEqual(before,canonical_bytes(parent)); self.assertNotIn("probe-output",decision.message_ids)
        awareness=render_awareness_probe(s,parent)
        ordinary=render_decision(s,decision,"stale-peer",())
        self.assertEqual(parent.current_version_id,s.version_new_id)
        self.assertIn(f"Known current update: {s.v_new}",awareness.text)
        self.assertEqual(parent.visible_message_ids,())
        self.assertNotIn("Peer evidence",awareness.text)
        self.assertNotEqual(awareness.text,ordinary.text)
        a=render_peer_message(s,s.v_old,"x").text; b=render_peer_message(s,s.v_wrong,"x").text
        self.assertEqual(a.replace(s.v_old,"VALUE"),b.replace(s.v_wrong,"VALUE"))
        with self.assertRaises(ValueError):
            render_awareness_probe(s,replace(parent,current_version_id=s.version_old_id))
    def test_decision_response_contract_and_template_pairing(self):
        s=self.ss.scenarios[0]; parent=make_pre_exposure_snapshot(s)
        expected_awareness=(f"AWARENESS PROBE (isolated)\nKnown current update: {s.v_new}\n"
                            f"Current value of {s.fact_id}?\n"
                            "Output exactly one line and nothing else:\n"
                            f"ANSWER=<one of {'|'.join(s.answer_pool.positions)}>")
        awareness=render_awareness_probe(s,parent)
        schema=f"ANSWER=<one of {'|'.join(s.answer_pool.positions)}>"
        self.assertEqual(awareness.text,expected_awareness)
        self.assertEqual(awareness.template_id,"awareness-v3")
        self.assertIn(f"Known current update: {s.v_new}",awareness.text)
        self.assertNotIn("Peer evidence",awareness.text)
        self.assertEqual(awareness.text.count("ANSWER="),1)
        self.assertEqual(awareness.text.splitlines()[-2:],
                         ["Output exactly one line and nothing else:",schema])

        current_peer=MessageRecord("current-peer",digest("current"),
            render_peer_message(s,s.v_new,"created-after-update").text,"source","target",(),
            s.fact_id,s.version_new_id,"current","current","exposure","model")
        stale_peer=MessageRecord("stale-peer",digest("stale"),
            render_peer_message(s,s.v_old,"created-before-update").text,"source","target",(),
            s.fact_id,s.version_old_id,"current","stale","exposure","model")
        current=render_decision(s,fork_snapshot(parent,"current-peer",(current_peer.message_id,)),
                                "current-peer",(current_peer,))
        stale=render_decision(s,fork_snapshot(parent,"stale-peer",(stale_peer.message_id,)),
                              "stale-peer",(stale_peer,))
        expected_decision=lambda peer: (f"ORDINARY DECISION\nFact: {s.fact_id}\nKnown current update: {s.v_new}\n"
                                        f"Peer evidence:\n{peer}\nOutput exactly one line and nothing else:\n{schema}")
        self.assertEqual(current.text,expected_decision(current_peer.raw_content))
        self.assertEqual(stale.text,expected_decision(stale_peer.raw_content))
        for prompt in (current,stale):
            self.assertEqual(prompt.template_id,"decision-v2")
            self.assertIn("Output exactly one line and nothing else:\n"+schema,prompt.text)
            self.assertEqual(prompt.text.count("ANSWER="),1)
            self.assertEqual(prompt.text.splitlines()[-1],schema)
        self.assertEqual(current.template_hash,stale.template_hash)
        self.assertEqual(current.text.replace(current_peer.raw_content,"PEER_CONTENT"),
                         stale.text.replace(stale_peer.raw_content,"PEER_CONTENT"))
        peer=render_peer_message(s,s.v_old,"created-before-update")
        self.assertEqual(peer.template_id,"peer-v1")
        self.assertEqual(peer.text,f"PEER|fact={s.fact_id}|value={s.v_old}|confidence=high|history=created-before-update")
        self.assertNotEqual(awareness.text,current.text)

    def test_awareness_only_identity_change_and_frozen_behavior(self):
        s=self.ss.scenarios[0]; parent=make_pre_exposure_snapshot(s); config=E0RunConfig()
        awareness=render_awareness_probe(s,parent)
        old_awareness=(f"AWARENESS PROBE (isolated)\nKnown current update: {s.v_new}\n"
                       f"Current value of {s.fact_id}?\nANSWER=<one of {'|'.join(s.answer_pool.positions)}>")
        current_peer=MessageRecord("current-peer",digest("current"),
            render_peer_message(s,s.v_new,"created-after-update").text,"source","target",(),
            s.fact_id,s.version_new_id,"current","current","exposure","model")
        decision=render_decision(s,fork_snapshot(parent,"current-peer",(current_peer.message_id,)),
                                 "current-peer",(current_peer,))
        identity=lambda text: EffectiveGenerationIdentity(
            "State-MAD strict categorical response",text,config.models[0],config.model_revision,
            config.models[0],config.tokenizer_revision,"chat-template-v1",
            (("temperature",config.temperature),("top_p",config.top_p)),config.seed,config.max_new_tokens)
        self.assertNotEqual(build_cache_key(identity(old_awareness)),build_cache_key(identity(awareness.text)))
        expected_decision=(f"ORDINARY DECISION\nFact: {s.fact_id}\nKnown current update: {s.v_new}\n"
                           f"Peer evidence:\n{current_peer.raw_content}\nOutput exactly one line and nothing else:\n"
                           f"ANSWER=<one of {'|'.join(s.answer_pool.positions)}>")
        self.assertEqual(build_cache_key(identity(decision.text)),build_cache_key(identity(expected_decision)))
        self.assertEqual(config.max_new_tokens,32)
        self.assertEqual((config.seed,config.temperature,config.top_p),(7,0.0,1.0))
        self.assertEqual(CLASSES,("CURRENT","STALE","STATIC_WRONG","OTHER/INVALID"))
        self.assertEqual(grade_output(f"Current value of {s.fact_id}? ANSWER={s.v_new}",s.answer_pool).answer_class,
                         "OTHER/INVALID")
    def test_cache_identity_reuse_corruption_and_no_regeneration(self):
        with tempfile.TemporaryDirectory() as d:
            cache=MessageCache(d); backend=ScriptedBackend(self.ss.scenarios); wrapped=CachedBackend(backend,cache)
            ident=EffectiveGenerationIdentity("s","u","m","mr","t","tr","cr",(("temperature",0),),1,9)
            def req(tag): return GenerationRequest(tag,ident,"e0-01","E0","p",tag,tag,tag,"target","hash",None,tag)
            one=wrapped.generate(req("one")); two=wrapped.generate(req("two"))
            self.assertEqual(backend.calls,1); self.assertEqual(one.raw_output,two.raw_output); self.assertEqual(two.generated_usage.total_tokens,0)
            p=next(Path(d).glob("*.json")); p.write_text("{}")
            with self.assertRaises(CacheIntegrityError): wrapped.generate(req("three"))
            self.assertEqual(backend.calls,1)
    def test_grader_closed_classes(self):
        pool=self.ss.scenarios[0].answer_pool
        values=(pool.current,pool.stale,pool.static_wrong,"BOGUS")
        got={grade_output("ANSWER="+v,pool).answer_class for v in values}
        self.assertEqual(got,set(CLASSES)); self.assertEqual(grade_output("ANSWER="+pool.current+"\nANSWER="+pool.stale,pool).answer_class,"OTHER/INVALID")
    def test_run_store_keys_messages_by_message_identity(self):
        with tempfile.TemporaryDirectory() as d:
            store=RunStore(d).create("message-identity")
            raw="ANSWER=ALPHA"; content_hash=digest(raw)
            first=MessageRecord("message-1",content_hash,raw,"source","target",(),"fact-1","v1","current","current","exposure","model")
            second=replace(first,message_id="message-2",parent_message_ids=("parent",),phase_id="decision")

            store.put_message(first); store.put_message(second); store.put_message(first)

            records=[json.loads(path.read_bytes()) for path in (store.run_dir/"messages").glob("*.json")]
            self.assertEqual({record["message_id"] for record in records},{"message-1","message-2"})
            self.assertEqual({record["content_hash"] for record in records},{content_hash})
            with self.assertRaises(RuntimeError):
                store.put_message(replace(first,recipient="different-recipient"))
    def test_preflight_and_manifest(self):
        good={"seed_supported":True,"model_available":True,"tokenizer_available":True}
        self.assertTrue(validate_e0_preflight(E0RunConfig(),self.ss.scenarios,good)["passed"])
        for cfg in (replace(E0RunConfig(),agents=3),replace(E0RunConfig(),temperature=.1),replace(E0RunConfig(),experiment="E1"),replace(E0RunConfig(),conditions=("static-wrong",))):
            self.assertFalse(validate_e0_preflight(cfg,self.ss.scenarios,good)["passed"])
        pre=validate_e0_preflight(E0RunConfig(),self.ss.scenarios,good)
        arts={x:"sha256:x" for x in ("scenario","validation","prompts","calls","lineage")}
        man=build_manifest(E0RunConfig(),arts,pre,("dry",),"t",{"sha":"x","branch":"b","dirty":False})
        self.assertIn("manifest_hash",finalize_manifest(man,"u",{"total":0},{"hits":0}))
    def test_model_free_dry_run_lineage_tokens_and_gate(self):
        with tempfile.TemporaryDirectory() as d:
            backend=ScriptedBackend(self.ss.scenarios)
            store=RunStore(Path(d)/"runs").create("dry-16")
            result=run_e0_dry(CachedBackend(backend,MessageCache(Path(d)/"cache")),store)
            self.assertEqual(len(result["calls"]),48); self.assertEqual(backend.calls,48)
            self.assertLess(len({call.raw_output for call in result["calls"]}),len(result["calls"]))
            self.assertEqual(len(tuple((store.run_dir/"messages").glob("*.json"))),80)
            self.assertTrue(result["lineage"]["passed"]); self.assertFalse(result["scientific_result"])
            self.assertEqual(result["report"]["status"],"PASS_TARGET"); self.assertEqual(len(result["report"]["confirmed_regressions"]),4)
            probe_ids={m.message_id for m in result["messages"] if m.message_id.endswith(":awareness:output")}
            self.assertTrue(all(not (set(path)&probe_ids) for path in result["lineage"]["paths"].values()))
            self.assertTrue(all(c.total_tokens==c.input_tokens+c.output_tokens for c in result["calls"]))
            replay=run_e0_dry(CachedBackend(backend,MessageCache(Path(d)/"cache")))
            self.assertEqual(backend.calls,48); self.assertTrue(all(c.cache_status=="hit" and c.generated_total_tokens==0 for c in replay["calls"]))

if __name__=="__main__": unittest.main()
