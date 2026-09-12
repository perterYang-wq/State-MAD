"""Model-free E2 contract tests.  No tokenizer, model, GPU, or network exists here."""
from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from state_mad.e2 import (E1RunExpectation, E2IntegrityError, E2_ELIGIBLE_IDS,
    FROZEN_E1_SCENARIO_HASH, assemble_final_votes, build_e2_overlay,
    build_final_readout_request, build_relay_awareness_request,
    build_relay_decision_request, make_e2_replay_envelope, plan_final_readout,
    plan_relay_branches, resolve_e1_replay_pair, resolve_e1_replay_pairs, run_e2)
from state_mad.lineage import validate_e2_lineage
from state_mad.metrics import evaluate_e2_fscr, evaluate_e2_retransmission
from state_mad.backend import CachedBackend
from state_mad.cache import MessageCache
from state_mad.preflight import E2RunConfig, validate_e2_preflight
from state_mad.run_store import RunStore
from state_mad.scenarios import compile_e1_scenarios
from state_mad.schema import BackendOutput, CallRecord, MessageRecord, TokenUsage, digest
from state_mad.snapshots import fork_snapshot, make_pre_exposure_snapshot


TOKENIZER_REVISION="fixture-tokenizer-revision"


def call(s, condition, answer, message_id, *, author="target", phase=None, parent=()):
    klass={s.v_new:"CURRENT",s.v_old:"STALE",s.v_wrong:"STATIC_WRONG"}.get(answer,"OTHER/INVALID")
    return CallRecord(f"{s.scenario_id}:{condition}:call","e1-qwen25-7b-seed7-pilot-20260912-v1",
        s.scenario_id,"E1",condition,s.scenario_id+":pair",message_id,author,"decision",tuple(parent),
        s.fact_id,s.version_new_id,"not_applicable","decision_output","current" if condition=="awareness" else "derived_from_probe",
        "not_applicable","not_applicable",digest(condition),"snapshot-"+condition,"Qwen/Qwen2.5-7B-Instruct",
        "a09a35458c702b33eeacc393d103063234e8bc28",TOKENIZER_REVISION,7,"config",
        "ANSWER="+answer,answer,klass,1,1,2,1,1,2,"miss","eligible",None,phase or s.decision_phase_id)


@pytest.fixture
def e1_dir(tmp_path):
    scenarios_all=compile_e1_scenarios().scenarios
    s=next(x for x in scenarios_all if x.scenario_id=="e1-04")
    calls=[]
    messages=[]; provenance=[]
    root=tmp_path/"e1"; (root/"messages").mkdir(parents=True)
    for scenario in scenarios_all:
        calls.extend((call(scenario,"awareness",scenario.v_new,scenario.scenario_id+":awareness-output"),
            call(scenario,"stale-peer",scenario.v_old if scenario.scenario_id in E2_ELIGIBLE_IDS else scenario.v_new,
                 scenario.scenario_id+":stale-output",parent=(scenario.scenario_id+":stale-peer:peer",)),
            call(scenario,"current-peer",scenario.v_new,scenario.scenario_id+":current-output",parent=(scenario.scenario_id+":current-peer:peer",))))
        for condition,value,validity in (("stale-peer",scenario.v_old,"stale"),("current-peer",scenario.v_new,"current")):
            raw=f"PEER|fact={scenario.fact_id}|value={value}"
            peer=MessageRecord(f"{scenario.scenario_id}:{condition}:peer",digest(raw),raw,"source","target",(),scenario.fact_id,
                scenario.version_old_id if validity=="stale" else scenario.version_new_id,"current",validity,"exposure","deterministic")
            (root/"messages"/(peer.message_id+".json")).write_text(json.dumps(asdict(peer)))
    for c in calls:
        scenario=next(x for x in scenarios_all if x.scenario_id==c.scenario_id)
        m=MessageRecord(c.message_id,digest(c.raw_output),c.raw_output,"target","decision",c.parent_message_ids,scenario.fact_id,
            scenario.version_new_id,"not_applicable","decision_output",scenario.decision_phase_id,"model")
        messages.append(m); (root/"messages"/(m.message_id+".json")).write_text(json.dumps(asdict(m)))
        provenance.append({"call_id":c.call_id,"cache_key":"key-"+c.condition,"content_hash":m.content_hash,
            "origin_call_id":c.call_id,"origin_run_id":c.run_id,"origin_resolution":"current_run","cache_status":"miss"})
    scenarios=[asdict(x) for x in scenarios_all]; call_rows=[asdict(c) for c in calls]
    report={"confirmed_treatment_only_stale_ids":list(E2_ELIGIBLE_IDS),"branch_topology":{x.scenario_id:{
        "parent_snapshot_hash":"e1-parent-"+x.scenario_id,"branches":{name:{"snapshot_hash":"snapshot-"+name,
        "parent_snapshot_hash":"e1-parent-"+x.scenario_id} for name in ("awareness","stale-peer","current-peer")}} for x in scenarios_all}}
    for name,value in (("scenarios.json",scenarios),("cache_provenance.json",provenance),("report.json",report)):
        (root/name).write_text(json.dumps(value))
    (root/"calls.jsonl").write_text("".join(json.dumps(x)+"\n" for x in call_rows))
    manifest={"schema":"state-mad-manifest-v1","repository":{"sha":"b002fe3d3dce8fe5d94b83f946dde2e494e09d4e"},
        "artifact_hashes":{"scenario":FROZEN_E1_SCENARIO_HASH,"scenarios":digest(scenarios),"calls":digest(call_rows),
        "cache_provenance":digest(provenance),"report":digest(report)},"effective_generation":{
        "run_id":"e1-qwen25-7b-seed7-pilot-20260912-v1","model_id":"Qwen/Qwen2.5-7B-Instruct",
        "model_revision":"a09a35458c702b33eeacc393d103063234e8bc28","tokenizer_revision":TOKENIZER_REVISION,
        "seed":7,"temperature":0.0,"top_p":1.0,"max_new_tokens":32},"config_hash":"config","preflight":{"passed":True},
        "command":["e1"],"started_at":"then","python":"fixture","platform":"fixture"}
    manifest={**manifest,"ended_at":"now","usage":{},"cache_stats":{},"manifest_hash":digest(manifest)}
    (root/"manifest.json").write_text(json.dumps(manifest))
    return root,s


def resolve(fixture):
    root,_=fixture
    return resolve_e1_replay_pair(root,E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION),"e1-04")


def reseal(root):
    manifest=json.loads((root/"manifest.json").read_text())
    calls=[json.loads(x) for x in (root/"calls.jsonl").read_text().splitlines()]
    manifest["artifact_hashes"]["calls"]=digest(calls)
    manifest["artifact_hashes"]["report"]=digest(json.loads((root/"report.json").read_text()))
    pre={k:v for k,v in manifest.items() if k not in {"ended_at","usage","cache_stats","manifest_hash"}}
    manifest["manifest_hash"]=digest(pre); (root/"manifest.json").write_text(json.dumps(manifest))


def test_read_only_resolver_exact_replay_and_provenance(e1_dir):
    before={p:p.read_bytes() for p in e1_dir[0].rglob("*") if p.is_file()}
    pair=resolve(e1_dir)
    assert pair.stale.call.raw_output==pair.stale.message.raw_content
    assert pair.current.call.raw_output==pair.current.message.raw_content
    assert pair.stale.content_hash==digest("ANSWER="+e1_dir[1].v_old)
    assert pair.stale.cache_provenance["origin_call_id"]==pair.stale.call.call_id
    assert pair.eligible_ids==E2_ELIGIBLE_IDS
    assert before=={p:p.read_bytes() for p in e1_dir[0].rglob("*") if p.is_file()}


def test_whole_run_recomputation_reads_all_forty(e1_dir):
    pairs=resolve_e1_replay_pairs(e1_dir[0],E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION))
    assert tuple(p.scenario.scenario_id for p in pairs)==E2_ELIGIBLE_IDS
    assert all(p.eligible_ids==E2_ELIGIBLE_IDS for p in pairs)


@pytest.mark.parametrize("field,value,code",[("run_id","wrong","RUN_ID"),("scientific_sha","bad","SCIENTIFIC_SHA"),
    ("scenario_set_hash","bad","SCENARIO_SET_HASH")])
def test_resolver_rejects_wrong_frozen_reference(e1_dir,field,value,code):
    expectation=replace(E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION),**{field:value})
    with pytest.raises(E2IntegrityError,match=code): resolve_e1_replay_pair(e1_dir[0],expectation,"e1-04")


def test_resolver_rejects_corruption_duplicate_and_noncanonical(e1_dir):
    root,_=e1_dir; calls=(root/"calls.jsonl").read_text()
    (root/"calls.jsonl").write_text(calls+calls.splitlines()[1]+"\n")
    with pytest.raises(E2IntegrityError): resolve(e1_dir)


def test_manifest_self_hash_and_independent_eligibility_fail_closed(e1_dir):
    root,s=e1_dir; manifest=json.loads((root/"manifest.json").read_text()); manifest["manifest_hash"]="bad"
    (root/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(E2IntegrityError,match="MANIFEST_SELF_HASH"): resolve(e1_dir)
    # Restore the fixture, then make actual E1 evidence contradict its still-nine report.
    pre={k:v for k,v in manifest.items() if k not in {"ended_at","usage","cache_stats","manifest_hash"}}
    manifest["manifest_hash"]=digest(pre); (root/"manifest.json").write_text(json.dumps(manifest))
    calls=[json.loads(x) for x in (root/"calls.jsonl").read_text().splitlines()]
    row=next(x for x in calls if x["scenario_id"]=="e1-04" and x["condition"]=="stale-peer")
    row.update(raw_output="ANSWER="+s.v_new,parsed_output=s.v_new,answer_class="CURRENT")
    (root/"calls.jsonl").write_text("".join(json.dumps(x)+"\n" for x in calls))
    message_path=root/"messages"/(row["message_id"]+".json"); message=json.loads(message_path.read_text())
    message.update(raw_content=row["raw_output"],content_hash=digest(row["raw_output"])); message_path.write_text(json.dumps(message))
    provenance=json.loads((root/"cache_provenance.json").read_text()); next(x for x in provenance if x["call_id"]==row["call_id"])["content_hash"]=message["content_hash"]
    (root/"cache_provenance.json").write_text(json.dumps(provenance))
    manifest=json.loads((root/"manifest.json").read_text()); manifest["artifact_hashes"].update(calls=digest(calls),cache_provenance=digest(provenance))
    pre={k:v for k,v in manifest.items() if k not in {"ended_at","usage","cache_stats","manifest_hash"}}; manifest["manifest_hash"]=digest(pre)
    (root/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(E2IntegrityError,match="ELIGIBLE_SET_MISMATCH"): resolve(e1_dir)


def test_overlay_relay_siblings_exact_insertion_and_parent_immutability(e1_dir):
    pair=resolve(e1_dir); overlay=build_e2_overlay(pair.scenario,pair); frozen=digest(overlay)
    assert overlay.overlay_schema=="e2-overlay-v1" and overlay.relay_current_version_id==pair.scenario.version_new_id
    stale=make_e2_replay_envelope(pair,"stale",overlay,"e2-test")
    current=make_e2_replay_envelope(pair,"current",overlay,"e2-test")
    assert stale.message.raw_content==pair.stale.call.raw_output
    assert current.message.raw_content==pair.current.call.raw_output
    branches=plan_relay_branches(pair.scenario,overlay,stale,current); parent_hash=branches["parent"].snapshot_hash
    assert digest(overlay)==frozen
    assert all(branches[x].parent_snapshot_hash==parent_hash for x in ("awareness","stale","current"))
    assert not branches["awareness"].message_ids
    config=E2RunConfig(tokenizer_revision=TOKENIZER_REVISION)
    awareness,_=build_relay_awareness_request(pair.scenario,overlay,branches["awareness"],config,"e2-test")
    stale_request,stale_prompt=build_relay_decision_request(pair.scenario,overlay,branches["stale"],stale,"stale",config,"e2-test")
    assert awareness.identity.user_input not in stale_prompt.text
    assert pair.stale.call.raw_output in stale_prompt.text
    # Metadata does not enter effective generation identity.
    assert stale_request.identity==replace(stale_request,condition="metadata-only").identity


@pytest.mark.parametrize("arm,decision_validity",[("stale","stale"),("current","current")])
def test_target_replay_is_post_update_decision_not_once_correct_seed(e1_dir,arm,decision_validity):
    pair=resolve(e1_dir); envelope=make_e2_replay_envelope(pair,arm,build_e2_overlay(pair.scenario,pair),"e2-test")
    assert envelope.message.generation_validity=="not_applicable"
    assert envelope.message.decision_validity==decision_validity
    assert pair.stale.peer_message.generation_validity=="current"


def final_calls(s, phase):
    values={"source-final":s.v_new,"target-stale-final":s.v_old,"target-current-final":s.v_new,
            "relay-stale-final":s.v_old,"relay-current-final":s.v_new}
    return [replace(call(s,c,v,c+":output",author=c.split("-")[0],phase=phase),run_id="e2-test",experiment="E2")
            for c,v in values.items()]


def test_final_readout_is_five_noncommunicative_calls_and_shared_source(e1_dir):
    pair=resolve(e1_dir); s=pair.scenario; overlay=build_e2_overlay(s,pair)
    source=make_pre_exposure_snapshot(s); target=make_pre_exposure_snapshot(s)
    stale=make_e2_replay_envelope(pair,"stale",overlay,"e2-test"); current=make_e2_replay_envelope(pair,"current",overlay,"e2-test")
    relay=plan_relay_branches(s,overlay,stale,current)
    plan=plan_final_readout(s,overlay,source,fork_snapshot(target,"stale",(pair.stale.peer_message.message_id,)),
        fork_snapshot(target,"current",(pair.current.peer_message.message_id,)),relay["stale"],relay["current"])
    assert len(plan)==5 and all(x.phase_id==s.final_vote_phase_id for x in plan.values())
    historical={stale.message.message_id,current.message.message_id,pair.stale.peer_message.message_id,pair.current.peer_message.message_id}
    assert all(not set(x.message_ids)-historical for x in plan.values())
    config=E2RunConfig(tokenizer_revision=TOKENIZER_REVISION)
    visible={"source-final":(),"target-stale-final":(pair.stale.peer_message,),
        "target-current-final":(pair.current.peer_message,),"relay-stale-final":(stale.message,),
        "relay-current-final":(current.message,)}
    built=[build_final_readout_request(s,snapshot,condition,config,"e2-test",visible[condition]) for condition,snapshot in plan.items()]
    requests=[x[0] for x in built]; prompts={r.condition:p.text for r,p in built}
    assert len({r.request_id for r in requests})==5
    assert "Peer evidence:\nNONE" in prompts["source-final"]
    assert pair.stale.peer_message.raw_content in prompts["target-stale-final"]
    assert pair.current.peer_message.raw_content in prompts["target-current-final"]
    assert stale.message.raw_content in prompts["relay-stale-final"] and current.message.raw_content in prompts["relay-current-final"]
    assert stale.message.generation_validity==current.message.generation_validity=="not_applicable"
    cases=assemble_final_votes(s.scenario_id,s.final_vote_phase_id,final_calls(s,s.final_vote_phase_id))
    assert len(cases)==2 and cases[0]["source_call_id"]==cases[1]["source_call_id"]
    assert all(not case["communication_edges"] for case in cases)
    with pytest.raises(E2IntegrityError,match="FINAL_VISIBLE_EVIDENCE_MISMATCH"):
        build_final_readout_request(s,plan["target-stale-final"],"target-stale-final",config,"e2-test",())


def relay_rows(ids, treatment="STALE", control="CURRENT"):
    rows=[]
    for sid in ids:
        for condition,klass in (("relay-awareness","CURRENT"),("relay-stale-replay",treatment),("relay-current-replay",control)):
            rows.append({"scenario_id":sid,"condition":condition,"answer_class":klass,
                         "parent_snapshot_hash":"p","infrastructure_failure":False})
    return rows


def test_srr_cond_other_invalid_and_gate_boundaries():
    ids=E2_ELIGIBLE_IDS
    integrity={sid:{"exact_replay":True} for sid in ids}
    rows=relay_rows(ids,"OTHER/INVALID"); report=evaluate_e2_retransmission(rows,{"candidate_ids":ids,"eligible_ids":ids},integrity=integrity)
    assert report["included_denominator_n"]==9 and report["srr_cond"]==0
    assert report["gate_4"]=="NO POSITIVE/UNSUPPORTED GATE CONCLUSION"
    rows=relay_rows(ids); rows[2]["answer_class"]="STALE"; rows[5]["answer_class"]="STALE"
    report=evaluate_e2_retransmission(rows,{"candidate_ids":ids,"eligible_ids":ids},integrity=integrity)
    assert report["stale_treatment_count"]==9 and report["current_control_stale_count"]==2
    assert report["gate_4"]=="SECOND-HOP-POSITIVE PILOT"
    short=ids[:7]; assert evaluate_e2_retransmission(relay_rows(short),{"candidate_ids":short,"eligible_ids":short},integrity={x:{"exact_replay":True} for x in short})["gate_4"]=="NOT ESTIMABLE AT PILOT SCALE"
    ten=tuple(f"x{i}" for i in range(10)); assert evaluate_e2_retransmission(relay_rows(ten,"CURRENT"),{"candidate_ids":ten,"eligible_ids":ten},integrity={x:{"exact_replay":True} for x in ten})["gate_4"]=="SECONDARY RETRANSMISSION UNSUPPORTED"
    missing=evaluate_e2_retransmission(relay_rows(ids),{"candidate_ids":ids,"eligible_ids":ids})
    assert missing["included_denominator_n"]==0
    with pytest.raises(ValueError,match="DUPLICATE_RELAY_ROW"):
        evaluate_e2_retransmission(relay_rows(ids)+[relay_rows(ids)[1]],{"candidate_ids":ids,"eligible_ids":ids},integrity=integrity)


@pytest.mark.parametrize("mutation,reason",[("missing-control","INCOMPLETE_MATCHED_PAIR"),
    ("infrastructure","INCOMPLETE_MATCHED_PAIR"),("missing-eligibility","NOT_E1_ELIGIBLE"),
    ("missing-replay","INVALID_EXACT_REPLAY")])
def test_retransmission_claim_inputs_fail_closed(mutation,reason):
    sid="e1-04"; rows=relay_rows((sid,)); eligibility={"candidate_ids":(sid,),"eligible_ids":(sid,)}
    integrity={sid:{"exact_replay":True}}
    if mutation=="missing-control": rows=[r for r in rows if r["condition"]!="relay-current-replay"]
    elif mutation=="infrastructure": rows[1]["infrastructure_failure"]=True
    elif mutation=="missing-eligibility": eligibility={"candidate_ids":(sid,)}
    else: integrity={}
    report=evaluate_e2_retransmission(rows,eligibility,integrity=integrity)
    assert report["included_denominator_n"]==0 and reason in report["excluded"][sid]


def test_three_fscr_tiers_other_invalid_and_incomplete(e1_dir):
    s=e1_dir[1]; cases=list(assemble_final_votes(s.scenario_id,s.final_vote_phase_id,final_calls(s,s.final_vote_phase_id)))
    verified={"system_cases":{cases[0]["system_case_id"]:{"tier_b_evaluable":True,"tier_b_predicate":True,
        "tier_c_evaluable":True,"tier_c_predicate":True,"errors":()},cases[1]["system_case_id"]:{
        "tier_b_evaluable":False,"tier_b_predicate":False,"tier_c_evaluable":False,"tier_c_predicate":False,"errors":("NO_PATH",)}}}
    report=evaluate_e2_fscr(cases,verified)
    assert report["ordinary_fscr"]["numerator_n"]==1
    assert report["exposure_induced_fscr"]["numerator_n"]==1
    assert report["retransmission_supported_fscr"]["numerator_n"]==1
    assert report["ordinary_fscr"]["denominator_n"]==2 and report["exposure_induced_fscr"]["denominator_n"]==1
    cases[1]={**cases[1],"complete":False}; assert evaluate_e2_fscr(cases,verified)["ordinary_fscr"]["denominator_n"]==1
    other=[dict(v,answer_class="OTHER/INVALID") if v["author"]=="source" else v for v in cases[0]["votes"]]
    assert evaluate_e2_fscr([{**cases[0],"votes":tuple(other)}],verified)["ordinary_fscr"]["denominator_n"]==1
    promoted={**cases[0],"tier_c_complete_path":True,"causal_adopter_roles":("target",)}
    blank=evaluate_e2_fscr([promoted],{"system_cases":{}})
    assert blank["exposure_induced_fscr"]["numerator_n"]==blank["retransmission_supported_fscr"]["numerator_n"]==0


def test_preflight_call_bound_and_no_backend_execution(e1_dir):
    pairs=resolve_e1_replay_pairs(e1_dir[0],E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION))
    overlays=tuple(build_e2_overlay(p.scenario,p) for p in pairs); branches=[]; final_plans=[]; specs=[]
    config=E2RunConfig(tokenizer_revision=TOKENIZER_REVISION)
    for pair,overlay in zip(pairs,overlays):
        stale=make_e2_replay_envelope(pair,"stale",overlay,"e2-test"); current=make_e2_replay_envelope(pair,"current",overlay,"e2-test")
        branch=plan_relay_branches(pair.scenario,overlay,stale,current); branches.append(branch)
        source=make_pre_exposure_snapshot(pair.scenario)
        planned=plan_final_readout(pair.scenario,overlay,source,
            fork_snapshot(source,"target-stale",(pair.stale.peer_message.message_id,)),
            fork_snapshot(source,"target-current",(pair.current.peer_message.message_id,)),branch["stale"],branch["current"])
        visible={"source-final":(),"target-stale-final":(pair.stale.peer_message,),"target-current-final":(pair.current.peer_message,),
            "relay-stale-final":(stale.message,),"relay-current-final":(current.message,)}
        final_plans.extend(build_final_readout_request(pair.scenario,snap,c,config,"e2-test",visible[c])[0] for c,snap in planned.items())
        specs.extend(assemble_final_votes(pair.scenario.scenario_id,pair.scenario.final_vote_phase_id,final_calls(pair.scenario,pair.scenario.final_vote_phase_id)))
    probe={"backend":"not-executed","seed_supported":False,"model_available":False,"tokenizer_available":False}
    report=validate_e2_preflight(config,overlays,pairs,probe,specs,branches,final_plans)
    assert report["passed"] and report["logical_calls"]==72 and not report["model_checks_executed"]
    assert not validate_e2_preflight(config,overlays,pairs,probe,specs,(),final_plans)["passed"]
    assert not validate_e2_preflight(config,overlays,pairs,probe,specs,branches[:-1],final_plans)["passed"]
    assert not validate_e2_preflight(config,overlays,pairs,probe,specs,branches,final_plans[:-1])["passed"]
    wrong=[replace(final_plans[0],phase="wrong"),*final_plans[1:]]
    assert not validate_e2_preflight(config,overlays,pairs,probe,specs,branches,wrong)["passed"]


def test_lineage_rejects_cycle_cross_fact_and_final_communication(e1_dir):
    s=e1_dir[1]
    a=MessageRecord("a",digest("a"),"a","source","target",(),s.fact_id,s.version_old_id,"current","stale","x","seed")
    b=replace(a,message_id="b",fact_id="other",parent_message_ids=("a",))
    edges=[{"parent_message_id":"a","child_message_id":"b","relation":"source_to_target_exposure"},
           {"parent_message_id":"b","child_message_id":"a","relation":"target_to_relay_exposure"}]
    report=validate_e2_lineage([a,b],edges,[],[],{},[])
    assert not report["passed"] and "CYCLE" in report["errors"] and "CROSS_SCENARIO_LINK" in report["errors"]


def test_e1_regression_surface_unchanged():
    scenarios=compile_e1_scenarios()
    assert len(scenarios.scenarios)==40


def test_downstream_identical_identity_reuses_cache(tmp_path, e1_dir):
    pair=resolve(e1_dir); overlay=build_e2_overlay(pair.scenario,pair)
    envelope=make_e2_replay_envelope(pair,"stale",overlay,"e2-test")
    branch=plan_relay_branches(pair.scenario,overlay,envelope,
        make_e2_replay_envelope(pair,"current",overlay,"e2-test"))["stale"]
    config=E2RunConfig(tokenizer_revision=TOKENIZER_REVISION)
    request,_=build_relay_decision_request(pair.scenario,overlay,branch,envelope,"stale",config,"e2-test")
    class TrapCounter:
        def __init__(self): self.calls=0
        def generate(self, request):
            self.calls+=1; return BackendOutput("ANSWER="+pair.scenario.v_old,TokenUsage(2,1,3))
    backend=TrapCounter(); cached=CachedBackend(backend,MessageCache(tmp_path/"cache"))
    first=cached.generate(request); second=cached.generate(replace(request,request_id="metadata-only"))
    assert (first.cache_status,second.cache_status,backend.calls)==("miss","hit",1)
    assert second.generated_usage.total_tokens==0 and first.cache_key==second.cache_key


def test_model_free_e2_orchestrator_closes_artifacts(tmp_path, e1_dir):
    scenarios={s.scenario_id:s for s in compile_e1_scenarios().scenarios}
    class Scripted:
        def generate(self,request):
            s=scenarios[request.scenario_id]
            stale=request.condition in {"relay-stale-replay","target-stale-final","relay-stale-final"}
            return BackendOutput("ANSWER="+(s.v_old if stale else s.v_new),TokenUsage(2,1,3))
    before={p:p.read_bytes() for p in e1_dir[0].rglob("*") if p.is_file()}
    config=E2RunConfig(tokenizer_revision=TOKENIZER_REVISION,run_id="e2-model-free")
    store=RunStore(tmp_path/"runs").create(config.run_id)
    result=run_e2(config,e1_dir[0],E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION),
        CachedBackend(Scripted(),MessageCache(tmp_path/"cache")),store,{})
    required={"preflight.json","eligibility.json","e2_scenario_overlay.json","upstream_e1_provenance.json",
        "upstream_replay_provenance.json","calls.jsonl","messages","lineage.jsonl","branch_topology.json",
        "final_votes.jsonl","cache_provenance.json","report.json","manifest.json"}
    assert {p.name for p in store.run_dir.iterdir()}==required
    bound={"preflight","eligibility","e2_scenario_overlay","upstream_e1_provenance","upstream_replay_provenance",
        "calls","messages","lineage","branch_topology","final_votes","cache_provenance","report"}
    assert bound <= set(result["manifest"]["artifact_hashes"])
    assert result["manifest"]["artifact_hashes"]["messages"]==result["artifacts"]["messages"]
    assert before=={p:p.read_bytes() for p in e1_dir[0].rglob("*") if p.is_file()}
    stale_case="e1-04:e2-system:stale"
    assert result["lineage"]["system_cases"][stale_case]["tier_c_predicate"]
    inputs=result["lineage_inputs"]
    missing=[e for e in inputs["edges"] if not (e.relation=="exact_replay" and "e1-04" in e.parent_message_id)]
    broken=validate_e2_lineage(inputs["messages"],missing,inputs["replay_provenance"],inputs["calls"],inputs["topology"],result["final_votes"])
    assert not broken["system_cases"][stale_case]["tier_c_evaluable"]
    # A relation from another scenario cannot complete e1-04's path.
    foreign=next(e for e in inputs["edges"] if e.relation=="exact_replay" and "e1-10" in e.parent_message_id)
    mixed=missing+[foreign]
    cross=validate_e2_lineage(inputs["messages"],mixed,inputs["replay_provenance"],inputs["calls"],inputs["topology"],result["final_votes"])
    assert not cross["system_cases"][stale_case]["tier_c_evaluable"]


def test_failed_preflight_never_finalizes_manifest(tmp_path,e1_dir):
    store=RunStore(tmp_path/"bad-runs").create("bad-e2")
    bad=replace(E2RunConfig(tokenizer_revision=TOKENIZER_REVISION,run_id="bad-e2"),communication_hops=3)
    class Never:
        def generate(self,request): raise AssertionError("preflight must precede generation")
    with pytest.raises(E2IntegrityError,match="E2_PREFLIGHT"):
        run_e2(bad,e1_dir[0],E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION),
            CachedBackend(Never(),MessageCache(tmp_path/"bad-cache")),store,{})
    assert not (store.run_dir/"manifest.json").exists()
