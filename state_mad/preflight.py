from dataclasses import asdict, dataclass
from pathlib import Path

from .schema import digest

PRODUCTION_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
_REVISION_PLACEHOLDERS = {"resolved-revision", "resolved-tokenizer-revision"}

@dataclass(frozen=True)
class E0RunConfig:
    scenario_count:int=16; agents:int=2; exposure_rounds:int=1; temperature:float=0.0
    top_p:float=1.0; models:tuple[str,...]=(PRODUCTION_MODEL_ID,); model_revision:str="resolved-revision"
    tokenizer_revision:str="resolved-tokenizer-revision"; seed:int=7; max_new_tokens:int=32
    experiment:str="E0"; conditions:tuple[str,...]=("awareness","current-peer","stale-peer")
    method:str="state-mad-p0"; main_rounds:int=1
    mode:str="dry-run"; run_id:str="dry-run"; cache_root:str|None=None; run_store_root:str|None=None

@dataclass(frozen=True)
class E1RunConfig:
    scenario_count:int=40; agents:int=2; exposure_rounds:int=1; temperature:float=0.0
    top_p:float=1.0; models:tuple[str,...]=(PRODUCTION_MODEL_ID,); model_revision:str="resolved-revision"
    tokenizer_revision:str="resolved-tokenizer-revision"; seed:int=7; max_new_tokens:int=32
    experiment:str="E1"; conditions:tuple[str,...]=('no-peer','current-peer','stale-peer','static-wrong')
    method:str="state-mad-e1"; main_rounds:int=1; mode:str="dry-run"; run_id:str="dry-run"
    cache_root:str|None=None; run_store_root:str|None=None

def _resolved_revision(value):
    return bool(value and value.strip() and value not in _REVISION_PLACEHOLDERS)

def validate_e0_preflight(config, scenarios, backend_probe):
    errors=[]
    scientific=config.mode=="scientific"
    checks=((config.scenario_count==16 and len(scenarios)==16,"SCENARIO_COUNT"),(config.agents<=2,"AGENTS"),(config.exposure_rounds==1,"EXPOSURE_ROUNDS"),(config.temperature==0,"TEMPERATURE"),(config.top_p==1.0,"TOP_P"),(len(config.models)==1 and config.models[0]==PRODUCTION_MODEL_ID,"MODEL"),(config.main_rounds<=2,"ROUNDS"),(config.experiment=="E0","EXPERIMENT"),(config.method=="state-mad-p0","METHOD"),(set(config.conditions)<={"awareness","current-peer","stale-peer"},"CONDITIONS"),(config.mode in {"dry-run","scientific"},"MODE"))
    if scientific:
        checks += ((_resolved_revision(config.model_revision) and _resolved_revision(config.tokenizer_revision),"REVISIONS"),(bool(config.run_id and config.run_id!="dry-run"),"RUN_ID"),(bool(config.cache_root),"CACHE_ROOT"),(bool(config.run_store_root),"RUN_STORE_ROOT"),(backend_probe.get("backend")=="language-model","SCIENTIFIC_BACKEND"))
    errors += [name for ok,name in checks if not ok]
    for field in ("seed_supported","model_available","tokenizer_available"):
        if not backend_probe.get(field,False): errors.append(field.upper())
    return {"passed":not errors,"errors":tuple(errors),"resolved":dict(backend_probe)}

def validate_e1_preflight(config, scenarios, backend_probe):
    errors=[]; scientific=config.mode=="scientific"
    expected=('no-peer','current-peer','stale-peer','static-wrong')
    checks=((config.scenario_count==40 and len(scenarios)==40,"SCENARIO_COUNT"),(config.agents==2,"AGENTS"),
        (config.exposure_rounds==1,"EXPOSURE_ROUNDS"),(config.main_rounds==1,"ROUNDS"),
        (config.temperature==0,"TEMPERATURE"),(config.top_p==1.0,"TOP_P"),
        (len(config.models)==1 and config.models[0]==PRODUCTION_MODEL_ID,"MODEL"),(config.experiment=="E1","EXPERIMENT"),
        (config.method=="state-mad-e1","METHOD"),(config.conditions==expected,"CONDITIONS"),
        (config.mode in {"dry-run","scientific"},"MODE"),(isinstance(config.seed,int),"SEED"),
        (isinstance(config.max_new_tokens,int) and config.max_new_tokens>0,"MAX_NEW_TOKENS"))
    if scientific:
        checks += ((_resolved_revision(config.model_revision) and _resolved_revision(config.tokenizer_revision),"REVISIONS"),
            (bool(config.run_id and config.run_id!="dry-run"),"RUN_ID"),(bool(config.cache_root),"CACHE_ROOT"),
            (bool(config.run_store_root),"RUN_STORE_ROOT"),(backend_probe.get("backend")=="language-model","SCIENTIFIC_BACKEND"))
    errors.extend(name for ok,name in checks if not ok)
    for field in ("seed_supported","model_available","tokenizer_available"):
        if not backend_probe.get(field,False): errors.append(field.upper())
    return {"passed":not errors,"errors":tuple(errors),"resolved":dict(backend_probe)}


E2_ELIGIBLE_IDS=("e1-04","e1-10","e1-16","e1-18","e1-22","e1-28","e1-30","e1-34","e1-40")
E2_MODEL_REVISION="a09a35458c702b33eeacc393d103063234e8bc28"
E2_SCENARIO_HASH="sha256:83c4034bc163b66285fb3085047507c773b14be9c1556e8165bbd9dd2d6df7c9"
E2_E1_SHA="b002fe3d3dce8fe5d94b83f946dde2e494e09d4e"
E2_E1_RUN="e1-qwen25-7b-seed7-pilot-20260912-v1"
E2_FINAL_MODE="synchronized-role-specific-noncommunicative-v1"

@dataclass(frozen=True)
class E2RunConfig:
    scenario_count:int=9; agents:int=3; communication_hops:int=2
    temperature:float=0.0; top_p:float=1.0; models:tuple[str,...]=(PRODUCTION_MODEL_ID,)
    model_revision:str=E2_MODEL_REVISION; tokenizer_revision:str=""
    seed:int=7; max_new_tokens:int=32; experiment:str="E2"; method:str="state-mad-e2"
    mode:str="dry-run"; run_id:str="dry-run"; cache_root:str|None=None; run_store_root:str|None=None
    eligible_ids:tuple[str,...]=E2_ELIGIBLE_IDS; e1_run_id:str=E2_E1_RUN
    e1_scientific_sha:str=E2_E1_SHA; e1_scenario_set_hash:str=E2_SCENARIO_HASH
    final_vote_mode:str=E2_FINAL_MODE; logical_call_maximum:int=72; planning_ceiling:int=800000
    projected_total_tokens:int=0


def _get(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def validate_e2_preflight(config, overlays, replay_pairs, backend_probe,
                          final_vote_spec, branch_plans, final_call_plans):
    """Validate the entire E2 plan without touching a tokenizer or backend."""
    errors=[]; overlays=tuple(overlays); replay_pairs=tuple(replay_pairs); branch_plans=tuple(branch_plans)
    final_call_plans=tuple(final_call_plans)
    checks=((config.scenario_count==9 and len(overlays)==len(replay_pairs)==9,"SCENARIO_COUNT"),
        (config.agents==3,"AGENTS"),(config.communication_hops==2,"COMMUNICATION_HOPS"),
        (config.temperature==0,"TEMPERATURE"),(config.top_p==1,"TOP_P"),
        (config.models==(PRODUCTION_MODEL_ID,),"MODEL"),(config.model_revision==E2_MODEL_REVISION,"MODEL_REVISION"),
        (bool(config.tokenizer_revision),"TOKENIZER_REVISION"),(config.seed==7,"SEED"),
        (config.max_new_tokens==32,"MAX_NEW_TOKENS"),(config.experiment=="E2","EXPERIMENT"),
        (config.method=="state-mad-e2","METHOD"),(config.mode in {"dry-run","scientific"},"MODE"),
        (config.eligible_ids==E2_ELIGIBLE_IDS,"ELIGIBLE_IDS"),(config.e1_run_id==E2_E1_RUN,"E1_RUN"),
        (config.e1_scientific_sha==E2_E1_SHA,"E1_SHA"),(config.e1_scenario_set_hash==E2_SCENARIO_HASH,"E1_SCENARIO_HASH"),
        (config.final_vote_mode==E2_FINAL_MODE,"FINAL_VOTE_MODE"),(config.logical_call_maximum==72,"CALL_MAXIMUM"),
        (0<=config.projected_total_tokens<=config.planning_ceiling==800000,"TOKEN_CEILING"))
    errors.extend(name for ok,name in checks if not ok)
    ids=tuple(_get(x,"scenario_id") for x in overlays)
    if ids!=config.eligible_ids or len(set(ids))!=9: errors.append("OVERLAY_IDS")
    pair_ids=tuple(_get(_get(x,"scenario"),"scenario_id") for x in replay_pairs)
    if pair_ids!=config.eligible_ids or len(set(pair_ids))!=9: errors.append("REPLAY_PAIR_IDS")
    for overlay in overlays:
        raw=asdict(overlay) if hasattr(overlay,"__dataclass_fields__") else dict(overlay)
        claimed=raw.pop("overlay_digest",None)
        if (_get(overlay,"e1_scenario_set_hash")!=E2_SCENARIO_HASH or
            _get(overlay,"relay_current_version_id") is None or
            not _get(overlay,"relay_current_evidence_event_ids") or
            claimed!=digest(raw)): errors.append("INVALID_OVERLAY")
    for pair in replay_pairs:
        stale=_get(pair,"stale"); current=_get(pair,"current")
        stale_call=_get(stale,"call"); current_call=_get(current,"call")
        stale_message=_get(stale,"message"); current_message=_get(current,"message")
        if (_get(stale,"condition")!="stale-peer" or
            _get(current,"condition")!="current-peer" or
            _get(pair,"parent_snapshot_hash") is None): errors.append("INVALID_REPLAY_PAIR")
        for selected,selected_call,selected_message in ((stale,stale_call,stale_message),(current,current_call,current_message)):
            raw=_get(selected_call,"raw_output")
            if (raw is None or raw!=_get(selected_message,"raw_content") or digest(raw)!=_get(selected,"content_hash") or
                _get(selected,"content_hash")!=_get(selected_message,"content_hash")): errors.append("EXACT_REPLAY_INTEGRITY")
    for plan in branch_plans:
        parent=_get(plan,"parent"); siblings=tuple(_get(plan,x) for x in ("awareness","stale","current"))
        if any(x is None or _get(x,"parent_snapshot_hash")!=_get(parent,"snapshot_hash") for x in siblings): errors.append("RELAY_SIBLING_TOPOLOGY")
        if siblings and (_get(siblings[0],"message_ids",()) or set(_get(siblings[1],"message_ids",())) & set(_get(siblings[2],"message_ids",()))): errors.append("AWARENESS_CONTAMINATION")
        if any(len(_get(x,"message_ids",()))!=1 for x in siblings[1:]): errors.append("RELAY_REPLAY_VISIBILITY")
        stale_ids=_get(siblings[1],"message_ids",()) if siblings[1] is not None else ()
        current_ids=_get(siblings[2],"message_ids",()) if siblings[2] is not None else ()
        if len(stale_ids)!=1 or len(current_ids)!=1 or ":stale:replay" not in stale_ids[0] or ":current:replay" not in current_ids[0]: errors.append("RELAY_REPLAY_ARM_MAPPING")
    plan_ids=tuple(_get(_get(p,"parent",p),"scenario_id") for p in branch_plans)
    if len(branch_plans)!=9 or len(set(plan_ids))!=9 or set(plan_ids)!=set(config.eligible_ids): errors.append("BRANCH_PLAN_COUNT")
    if len(final_call_plans)!=45: errors.append("FINAL_CALL_PLAN_COUNT")
    expected_conditions={"source-final","target-stale-final","target-current-final","relay-stale-final","relay-current-final"}
    overlays_by_id={_get(x,"scenario_id"):x for x in overlays}
    for sid in config.eligible_ids:
        plans=[p for p in final_call_plans if _get(p,"scenario_id")==sid]
        if len(plans)!=5 or {_get(p,"condition") for p in plans}!=expected_conditions: errors.append("FINAL_CALL_PLAN_SET"); continue
        if any(_get(p,"phase")!=_get(overlays_by_id[sid],"final_vote_phase_id") for p in plans): errors.append("FINAL_CALL_PHASE")
        mapping={_get(p,"condition"):_get(p,"branch_id","") for p in plans}
        if ("stale" not in mapping["target-stale-final"] or "current" not in mapping["target-current-final"] or
            "stale" not in mapping["relay-stale-final"] or "current" not in mapping["relay-current-final"]): errors.append("FINAL_BRANCH_MAPPING")
    specs=tuple(final_vote_spec)
    if len(specs)!=18: errors.append("SYSTEM_CASE_COUNT")
    by_scenario={sid:[x for x in specs if _get(x,"scenario_id")==sid] for sid in config.eligible_ids}
    for sid, cases in by_scenario.items():
        if len(cases)!=2 or {_get(x,"arm") for x in cases}!={"stale","current"}: errors.append("MATCHED_SYSTEM_CASES"); continue
        if len({_get(x,"source_call_id") for x in cases})!=1: errors.append("SOURCE_NOT_SHARED")
        if any(_get(x,"communication_edges",()) for x in cases): errors.append("FINAL_COMMUNICATION")
        phases={_get(x,"final_vote_phase_id") for x in cases}
        if len(phases)!=1 or None in phases: errors.append("FINAL_PHASE")
        for case in cases:
            votes=_get(case,"votes",())
            if len(votes)!=3 or {_get(v,"author") for v in votes}!={"source","target","relay"}: errors.append("FINAL_ROLES")
            if any(_get(v,"condition")=="source-stale-seed" for v in votes): errors.append("PREUPDATE_SEED_VOTE")
            expected={"source-final",f"target-{_get(case,'arm')}-final",f"relay-{_get(case,'arm')}-final"}
            if {_get(v,"condition") for v in votes}!=expected: errors.append("FINAL_BRANCH_MAPPING")
    if config.logical_call_maximum < 8*len(config.eligible_ids): errors.append("RESOURCE_CALL_BOUND")
    if config.cache_root and config.run_store_root:
        cache=Path(config.cache_root).resolve(); store=Path(config.run_store_root).resolve()
        if cache==store or cache in store.parents or store in cache.parents: errors.append("CACHE_RUN_STORE_COLLISION")
        destination=store/config.run_id
        if destination.exists(): errors.append("RUN_STORE_EXISTS")
    if config.mode=="scientific":
        if not config.run_id or config.run_id=="dry-run": errors.append("RUN_ID")
        if not config.cache_root: errors.append("CACHE_ROOT")
        if not config.run_store_root: errors.append("RUN_STORE_ROOT")
        if backend_probe.get("backend")!="language-model": errors.append("SCIENTIFIC_BACKEND")
        for field in ("seed_supported","model_available","tokenizer_available"):
            if not backend_probe.get(field,False): errors.append(field.upper())
    return {"passed":not errors,"errors":tuple(errors),"resolved":dict(backend_probe),
            "logical_calls":8*len(config.eligible_ids),"model_checks_executed":False}
