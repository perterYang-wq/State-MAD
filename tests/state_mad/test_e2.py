"""Model-free E2 contract tests.  No tokenizer, model, GPU, or network exists here."""
from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from state_mad.e2 import (E1RunExpectation, E2IntegrityError, E2_ELIGIBLE_IDS,
    FROZEN_E1_SCENARIO_HASH, assemble_final_votes, build_e2_overlay,
    build_final_readout_request, build_relay_awareness_request,
    build_relay_decision_request, make_e2_replay_envelope, plan_final_readout,
    plan_relay_branches, resolve_e1_replay_pair)
from state_mad.lineage import validate_e2_lineage
from state_mad.metrics import evaluate_e2_fscr, evaluate_e2_retransmission
from state_mad.backend import CachedBackend
from state_mad.cache import MessageCache
from state_mad.preflight import E2RunConfig, validate_e2_preflight
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
    s=next(x for x in compile_e1_scenarios().scenarios if x.scenario_id=="e1-04")
    calls=[call(s,"awareness",s.v_new,"awareness-output"),
           call(s,"stale-peer",s.v_old,"stale-output",parent=(s.scenario_id+":stale-peer:peer",)),
           call(s,"current-peer",s.v_new,"current-output",parent=(s.scenario_id+":current-peer:peer",))]
    messages=[]; provenance=[]
    root=tmp_path/"e1"; (root/"messages").mkdir(parents=True)
    for condition,value,validity in (("stale-peer",s.v_old,"stale"),("current-peer",s.v_new,"current")):
        raw=f"PEER|fact={s.fact_id}|value={value}"
        peer=MessageRecord(f"{s.scenario_id}:{condition}:peer",digest(raw),raw,"source","target",(),s.fact_id,
            s.version_old_id if validity=="stale" else s.version_new_id,"current",validity,"exposure","deterministic")
        (root/"messages"/(peer.message_id+".json")).write_text(json.dumps(asdict(peer)))
    for c in calls:
        m=MessageRecord(c.message_id,digest(c.raw_output),c.raw_output,"target","decision",c.parent_message_ids,s.fact_id,
            s.version_new_id,"not_applicable","decision_output",s.decision_phase_id,"model")
        messages.append(m); (root/"messages"/(m.message_id+".json")).write_text(json.dumps(asdict(m)))
        provenance.append({"call_id":c.call_id,"cache_key":"key-"+c.condition,"content_hash":m.content_hash,
            "origin_call_id":c.call_id,"origin_run_id":c.run_id,"origin_resolution":"current_run","cache_status":"miss"})
    scenarios=[asdict(s)]; call_rows=[asdict(c) for c in calls]
    report={"confirmed_treatment_only_stale_ids":list(E2_ELIGIBLE_IDS),"branch_topology":{s.scenario_id:{
        "parent_snapshot_hash":"e1-parent","branches":{name:{"snapshot_hash":"snapshot-"+name,
        "parent_snapshot_hash":"e1-parent"} for name in ("awareness","stale-peer","current-peer")}}}}
    for name,value in (("scenarios.json",scenarios),("cache_provenance.json",provenance),("report.json",report)):
        (root/name).write_text(json.dumps(value))
    (root/"calls.jsonl").write_text("".join(json.dumps(x)+"\n" for x in call_rows))
    manifest={"repository":{"sha":"b002fe3d3dce8fe5d94b83f946dde2e494e09d4e"},
        "artifact_hashes":{"scenario":FROZEN_E1_SCENARIO_HASH,"scenarios":digest(scenarios),"calls":digest(call_rows),
        "cache_provenance":digest(provenance),"report":digest(report)},"effective_generation":{
        "run_id":"e1-qwen25-7b-seed7-pilot-20260912-v1","model_id":"Qwen/Qwen2.5-7B-Instruct",
        "model_revision":"a09a35458c702b33eeacc393d103063234e8bc28","tokenizer_revision":TOKENIZER_REVISION,
        "seed":7,"temperature":0.0,"top_p":1.0,"max_new_tokens":32},"ended_at":"now","manifest_hash":"sealed",
        "usage":{},"cache_stats":{}}
    (root/"manifest.json").write_text(json.dumps(manifest))
    return root,s


def resolve(fixture):
    root,_=fixture
    return resolve_e1_replay_pair(root,E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION),"e1-04")


def test_read_only_resolver_exact_replay_and_provenance(e1_dir):
    before={p:p.read_bytes() for p in e1_dir[0].rglob("*") if p.is_file()}
    pair=resolve(e1_dir)
    assert pair.stale.call.raw_output==pair.stale.message.raw_content
    assert pair.current.call.raw_output==pair.current.message.raw_content
    assert pair.stale.content_hash==digest("ANSWER="+e1_dir[1].v_old)
    assert pair.stale.cache_provenance["origin_call_id"]==pair.stale.call.call_id
    assert pair.eligible_ids==E2_ELIGIBLE_IDS
    assert before=={p:p.read_bytes() for p in e1_dir[0].rglob("*") if p.is_file()}


@pytest.mark.parametrize("field,value,code",[("run_id","wrong","RUN_ID"),("scientific_sha","bad","SCIENTIFIC_SHA"),
    ("scenario_set_hash","bad","SCENARIO_SET_HASH")])
def test_resolver_rejects_wrong_frozen_reference(e1_dir,field,value,code):
    expectation=replace(E1RunExpectation(tokenizer_revision=TOKENIZER_REVISION),**{field:value})
    with pytest.raises(E2IntegrityError,match=code): resolve_e1_replay_pair(e1_dir[0],expectation,"e1-04")


def test_resolver_rejects_corruption_duplicate_and_noncanonical(e1_dir):
    root,_=e1_dir; calls=(root/"calls.jsonl").read_text()
    (root/"calls.jsonl").write_text(calls+calls.splitlines()[1]+"\n")
    with pytest.raises(E2IntegrityError): resolve(e1_dir)


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
    plan=plan_final_readout(s,overlay,source,fork_snapshot(target,"stale"),fork_snapshot(target,"current"),relay["stale"],relay["current"])
    assert len(plan)==5 and all(x.phase_id==s.final_vote_phase_id for x in plan.values())
    assert all(not set(x.message_ids)-set({stale.message.message_id,current.message.message_id}) for x in plan.values())
    config=E2RunConfig(tokenizer_revision=TOKENIZER_REVISION)
    requests=[build_final_readout_request(s,snapshot,condition,config,"e2-test")[0] for condition,snapshot in plan.items()]
    assert len({r.request_id for r in requests})==5
    cases=assemble_final_votes(s.scenario_id,s.final_vote_phase_id,final_calls(s,s.final_vote_phase_id))
    assert len(cases)==2 and cases[0]["source_call_id"]==cases[1]["source_call_id"]
    assert all(not case["communication_edges"] for case in cases)


def relay_rows(ids, treatment="STALE", control="CURRENT"):
    rows=[]
    for sid in ids:
        for condition,klass in (("relay-awareness","CURRENT"),("relay-stale-replay",treatment),("relay-current-replay",control)):
            rows.append({"scenario_id":sid,"condition":condition,"answer_class":klass,
                         "parent_snapshot_hash":"p","infrastructure_failure":False})
    return rows


def test_srr_cond_other_invalid_and_gate_boundaries():
    ids=E2_ELIGIBLE_IDS
    rows=relay_rows(ids,"OTHER/INVALID"); report=evaluate_e2_retransmission(rows,{"candidate_ids":ids,"eligible_ids":ids})
    assert report["included_denominator_n"]==9 and report["srr_cond"]==0
    assert report["gate_4"]=="NO POSITIVE/UNSUPPORTED GATE CONCLUSION"
    rows=relay_rows(ids); rows[2]["answer_class"]="STALE"; rows[5]["answer_class"]="STALE"
    report=evaluate_e2_retransmission(rows,{"candidate_ids":ids,"eligible_ids":ids})
    assert report["stale_treatment_count"]==9 and report["current_control_stale_count"]==2
    assert report["gate_4"]=="SECOND-HOP-POSITIVE PILOT"
    short=ids[:7]; assert evaluate_e2_retransmission(relay_rows(short),{"candidate_ids":short,"eligible_ids":short})["gate_4"]=="NOT ESTIMABLE AT PILOT SCALE"
    ten=tuple(f"x{i}" for i in range(10)); assert evaluate_e2_retransmission(relay_rows(ten,"CURRENT"),{"candidate_ids":ten,"eligible_ids":ten})["gate_4"]=="SECONDARY RETRANSMISSION UNSUPPORTED"


def test_three_fscr_tiers_other_invalid_and_incomplete(e1_dir):
    s=e1_dir[1]; cases=list(assemble_final_votes(s.scenario_id,s.final_vote_phase_id,final_calls(s,s.final_vote_phase_id)))
    cases[0]={**cases[0],"causal_adopter_roles":("target",),"tier_c_complete_path":True}
    report=evaluate_e2_fscr(cases)
    assert report["ordinary_fscr"]["numerator_n"]==1
    assert report["exposure_induced_fscr"]["numerator_n"]==1
    assert report["retransmission_supported_fscr"]["numerator_n"]==1
    cases[1]={**cases[1],"complete":False}; assert evaluate_e2_fscr(cases)["ordinary_fscr"]["denominator_n"]==1
    other=[dict(v,answer_class="OTHER/INVALID") if v["author"]=="source" else v for v in cases[0]["votes"]]
    assert evaluate_e2_fscr([{**cases[0],"votes":tuple(other)}])["ordinary_fscr"]["denominator_n"]==1


def test_preflight_call_bound_and_no_backend_execution(e1_dir):
    pair=resolve(e1_dir); pairs=tuple(replace(pair,scenario=replace(pair.scenario,scenario_id=sid)) for sid in E2_ELIGIBLE_IDS)
    overlays=[]
    for sid in E2_ELIGIBLE_IDS:
        overlay=replace(build_e2_overlay(pair.scenario,pair),scenario_id=sid,overlay_digest="")
        overlays.append(replace(overlay,overlay_digest=digest({k:v for k,v in asdict(overlay).items() if k!="overlay_digest"})))
    overlays=tuple(overlays)
    specs=[]
    for sid in E2_ELIGIBLE_IDS:
        fake=final_calls(replace(pair.scenario,scenario_id=sid),pair.scenario.final_vote_phase_id)
        specs.extend(assemble_final_votes(sid,pair.scenario.final_vote_phase_id,fake))
    probe={"backend":"not-executed","seed_supported":False,"model_available":False,"tokenizer_available":False}
    report=validate_e2_preflight(E2RunConfig(tokenizer_revision=TOKENIZER_REVISION),overlays,pairs,probe,specs)
    assert report["passed"] and report["logical_calls"]==72 and not report["model_checks_executed"]


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
