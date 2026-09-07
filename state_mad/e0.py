"""Strictly bounded E0 orchestration; no legacy MAD core dependency."""
from dataclasses import asdict
from .grading import grade_output
from .lineage import validate_e0_lineage
from .metrics import evaluate_e0
from .preflight import E0RunConfig, validate_e0_preflight
from .prompts import render_awareness_probe, render_decision, render_peer_message
from .scenarios import E0ScenarioSpec, compile_e0_scenarios
from .schema import (CallRecord, EffectiveGenerationIdentity, GenerationRequest,
                     LineageRecord, MessageRecord, digest)
from .snapshots import fork_snapshot, make_pre_exposure_snapshot
from .validation import validate_scenario_set

def _identity(prompt,config):
    return EffectiveGenerationIdentity("State-MAD strict categorical response",prompt.text,config.models[0],config.model_revision,config.models[0],config.tokenizer_revision,"chat-template-v1",(("temperature",config.temperature),),config.seed,config.max_new_tokens)

def run_e0(config:E0RunConfig,cached_backend,run_store=None,backend_probe=None):
    ss=compile_e0_scenarios(E0ScenarioSpec(count=config.scenario_count,seed=config.seed)); validation=validate_scenario_set(ss.scenarios)
    preflight=validate_e0_preflight(config,ss.scenarios,backend_probe or {"seed_supported":True,"model_available":True,"tokenizer_available":True})
    if not preflight["passed"]: raise RuntimeError("preflight failed: "+",".join(preflight["errors"]))
    calls=[]; messages=[]; edges=[]; metric_rows=[]; probe_ids=[]; decision_ids=[]
    for s in ss.scenarios:
        parent=make_pre_exposure_snapshot(s); parent_hash=parent.snapshot_hash
        peer_data=(("current-peer",s.v_new,s.version_new_id,"current","current_after_update"),("stale-peer",s.v_old,s.version_old_id,"stale","correct_when_created_then_superseded"))
        peer_messages={}
        for cond,value,version,validity,history in peer_data:
            raw=render_peer_message(s,value,history).text; mid=f"{s.scenario_id}:{cond}:peer"
            peer_messages[cond]=MessageRecord(mid,digest(raw),raw,"source","target",(),s.fact_id,version,"current",validity,"exposure","deterministic")
            messages.append(peer_messages[cond])
        specs=[("awareness",render_awareness_probe(s,parent),fork_snapshot(parent,"probe"),()),]
        for cond,_,_,_,_ in peer_data:
            pm=peer_messages[cond]; branch=fork_snapshot(parent,cond,(pm.message_id,)); specs.append((cond,render_decision(s,branch,cond,(pm,)),branch,(pm.message_id,)))
        for cond,prompt,snapshot,parent_messages in specs:
            if parent.snapshot_hash!=parent_hash: raise RuntimeError("parent snapshot mutated")
            rid=f"{s.scenario_id}:{cond}:call"; mid=f"{s.scenario_id}:{cond}:output"
            req=GenerationRequest(rid,_identity(prompt,config),s.scenario_id,"E0",s.decision_phase_id,cond,s.scenario_id+":pair","target","target",snapshot.snapshot_hash,snapshot.parent_snapshot_hash,snapshot.branch_id)
            result=cached_backend.generate(req); grade=grade_output(result.raw_output,s.answer_pool)
            msg=MessageRecord(mid,result.content_hash,result.raw_output,"target","decision",parent_messages,s.fact_id,s.version_new_id,"not_applicable","decision_output",s.decision_phase_id,"model")
            messages.append(msg); decision_ids.append(mid) if cond!="awareness" else probe_ids.append(mid)
            for p in parent_messages: edges.append(LineageRecord(p,mid,"exposure"))
            aware="current" if cond=="awareness" and grade.answer_class=="CURRENT" else "derived_from_probe"
            call=CallRecord(rid,"dry-run",s.scenario_id,"E0",cond,s.scenario_id+":pair",mid,"target","decision",parent_messages,s.fact_id,s.version_new_id,"not_applicable","decision_output",aware,"not_applicable","not_applicable",prompt.prompt_hash,snapshot.snapshot_hash,config.models[0],config.model_revision,config.tokenizer_revision,config.seed,digest(config),result.raw_output,grade.parsed_output,grade.answer_class,result.usage.input_tokens,result.usage.output_tokens,result.usage.total_tokens,result.generated_usage.input_tokens,result.generated_usage.output_tokens,result.generated_usage.total_tokens,result.cache_status,"eligible",None,s.decision_phase_id)
            calls.append(call); metric_rows.append({"scenario_id":s.scenario_id,"condition":cond,"answer_class":grade.answer_class})
            if run_store: run_store.put_message(msg); run_store.append_call(call)
        if run_store:
            for pm in peer_messages.values(): run_store.put_message(pm)
    for e in edges:
        if run_store: run_store.append_lineage(e)
    lineage=validate_e0_lineage(messages,edges,decision_ids,probe_ids)
    report=evaluate_e0(metric_rows,[s.scenario_id for s in ss.scenarios])
    return {"dry_run":True,"scientific_result":False,"scenario_set_hash":ss.scenario_set_hash,"validation":asdict(validation),"preflight":preflight,"calls":calls,"messages":messages,"lineage":lineage,"report":report}

def run_e0_dry(cached_backend,run_store=None,config=E0RunConfig()):
    return run_e0(config,cached_backend,run_store,{"seed_supported":True,"model_available":True,"tokenizer_available":True,"backend":"fake"})
