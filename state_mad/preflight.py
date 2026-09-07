from dataclasses import dataclass

@dataclass(frozen=True)
class E0RunConfig:
    scenario_count:int=16; agents:int=2; exposure_rounds:int=1; temperature:float=0.0
    models:tuple[str,...]=("Qwen/Qwen2.5-7B-Instruct",); model_revision:str="resolved-revision"
    tokenizer_revision:str="resolved-tokenizer-revision"; seed:int=7; max_new_tokens:int=32
    experiment:str="E0"; conditions:tuple[str,...]=("awareness","current-peer","stale-peer")
    method:str="state-mad-p0"; main_rounds:int=1

def validate_e0_preflight(config, scenarios, backend_probe):
    errors=[]
    checks=((config.scenario_count==16 and len(scenarios)==16,"SCENARIO_COUNT"),(config.agents<=2,"AGENTS"),(config.exposure_rounds==1,"EXPOSURE_ROUNDS"),(config.temperature==0,"TEMPERATURE"),(len(config.models)==1 and "7B" in config.models[0],"MODEL"),(config.main_rounds<=2,"ROUNDS"),(config.experiment=="E0","EXPERIMENT"),(config.method=="state-mad-p0","METHOD"),(set(config.conditions)<={"awareness","current-peer","stale-peer"},"CONDITIONS"),(bool(config.model_revision) and bool(config.tokenizer_revision),"REVISIONS"))
    errors += [name for ok,name in checks if not ok]
    for field in ("seed_supported","model_available","tokenizer_available"):
        if not backend_probe.get(field,False): errors.append(field.upper())
    return {"passed":not errors,"errors":tuple(errors),"resolved":dict(backend_probe)}
