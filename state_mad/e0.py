"""Strictly bounded E0 orchestration; no legacy MAD core dependency."""
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from .backend import CachedBackend, FakeBackend
from .cache import MessageCache
from .manifest import build_manifest, finalize_manifest
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
from .run_store import RunStore

def _identity(prompt,config):
    return EffectiveGenerationIdentity("State-MAD strict categorical response",prompt.text,config.models[0],config.model_revision,config.models[0],config.tokenizer_revision,"chat-template-v1",(("temperature",config.temperature),("top_p",config.top_p)),config.seed,config.max_new_tokens)

def prepare_e0_run(config:E0RunConfig, backend):
    """Create non-overwriting, mode-separated cache and artifact namespaces."""
    if config.mode=="scientific" and (isinstance(backend,FakeBackend) or not getattr(backend,"scientific_backend",False)):
        raise ValueError("Fake/non-production backend cannot run scientific E0")
    cache_root=Path(config.cache_root or ".state_mad/cache")/config.mode
    store_root=Path(config.run_store_root or ".state_mad/runs")/config.mode
    store=RunStore(store_root).create(config.run_id)
    return CachedBackend(backend,MessageCache(cache_root)),store

def run_e0(config:E0RunConfig,cached_backend,run_store=None,backend_probe=None):
    started_at=datetime.now(timezone.utc).isoformat()
    if config.mode=="scientific":
        backend=getattr(cached_backend,"backend",None)
        if isinstance(backend,FakeBackend) or not getattr(backend,"scientific_backend",False):
            raise ValueError("scientific E0 requires LanguageModelBackend")
        expected_cache=Path(config.cache_root)/config.mode
        expected_run=Path(config.run_store_root)/config.mode/config.run_id
        if Path(getattr(getattr(cached_backend,"cache",None),"root",""))!=expected_cache:
            raise ValueError("scientific E0 cache root does not match explicit configuration")
        if run_store is None or run_store.run_dir!=expected_run:
            raise ValueError("scientific E0 run-store root does not match explicit configuration")
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
            call=CallRecord(rid,config.run_id,s.scenario_id,"E0",cond,s.scenario_id+":pair",mid,"target","decision",parent_messages,s.fact_id,s.version_new_id,"not_applicable","decision_output",aware,"not_applicable","not_applicable",prompt.prompt_hash,snapshot.snapshot_hash,config.models[0],config.model_revision,config.tokenizer_revision,config.seed,digest(config),result.raw_output,grade.parsed_output,grade.answer_class,result.usage.input_tokens,result.usage.output_tokens,result.usage.total_tokens,result.generated_usage.input_tokens,result.generated_usage.output_tokens,result.generated_usage.total_tokens,result.cache_status,"eligible",None,s.decision_phase_id)
            calls.append(call); metric_rows.append({"scenario_id":s.scenario_id,"condition":cond,"answer_class":grade.answer_class})
            if run_store: run_store.put_message(msg); run_store.append_call(call)
        if run_store:
            for pm in peer_messages.values(): run_store.put_message(pm)
    for e in edges:
        if run_store: run_store.append_lineage(e)
    lineage=validate_e0_lineage(messages,edges,decision_ids,probe_ids)
    report=evaluate_e0(metric_rows,[s.scenario_id for s in ss.scenarios])
    prompt_hashes={c.condition+":"+c.scenario_id:c.prompt_hash for c in calls}
    artifacts={"scenario":ss.scenario_set_hash,"validation":digest(validation),"prompts":digest(prompt_hashes),"calls":digest(calls),"lineage":digest(edges)}
    usage={"input_tokens":sum(c.generated_input_tokens for c in calls),"output_tokens":sum(c.generated_output_tokens for c in calls),"total_tokens":sum(c.generated_total_tokens for c in calls)}
    manifest=build_manifest(config,artifacts,preflight,("state-mad","e0",config.mode),started_at,effective={"model_id":config.models[0],"model_revision":config.model_revision,"tokenizer_id":config.models[0],"tokenizer_revision":config.tokenizer_revision,"temperature":config.temperature,"top_p":config.top_p,"max_new_tokens":config.max_new_tokens,"seed":config.seed,"backend":preflight["resolved"].get("backend"),"cache_root":config.cache_root,"run_store_root":config.run_store_root,"run_id":config.run_id})
    manifest=finalize_manifest(manifest,datetime.now(timezone.utc).isoformat(),usage,{"hits":sum(c.cache_status=="hit" for c in calls),"misses":sum(c.cache_status=="miss" for c in calls)})
    if run_store: run_store.write_once("manifest.json",manifest)
    return {"dry_run":config.mode=="dry-run","scientific_result":config.mode=="scientific","scenario_set_hash":ss.scenario_set_hash,"validation":asdict(validation),"preflight":preflight,"calls":calls,"messages":messages,"lineage":lineage,"report":report,"manifest":manifest}

def run_e0_dry(cached_backend,run_store=None,config=E0RunConfig()):
    return run_e0(config,cached_backend,run_store,{"seed_supported":True,"model_available":True,"tokenizer_available":True,"backend":"fake"})
