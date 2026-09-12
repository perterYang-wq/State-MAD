from dataclasses import dataclass

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
