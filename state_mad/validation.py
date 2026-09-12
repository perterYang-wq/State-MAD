from dataclasses import dataclass
from .scenarios import build_balance_report

class ScenarioValidationError(ValueError): pass
@dataclass(frozen=True)
class ValidationReport:
    passed: bool; errors: tuple[str,...]; balance: dict

def validate_scenario_set(scenarios, phase="E0"):
    errors=[]
    if phase=="E0" and len(scenarios)!=16: errors.append("E0_COUNT")
    ids=set()
    for s in scenarios:
        if s.scenario_id in ids: errors.append("DUPLICATE_SCENARIO_ID")
        ids.add(s.scenario_id)
        if len({s.v_old,s.v_new,s.v_wrong})!=3: errors.append(f"NON_DISTINCT:{s.scenario_id}")
        if s.version_new_id not in s.target_visible_versions: errors.append(f"TARGET_NOT_CURRENT:{s.scenario_id}")
        if s.answer_pool.positions and set(s.answer_pool.positions)!={s.v_old,s.v_new,s.v_wrong}: errors.append(f"NON_BIJECTIVE_POOL:{s.scenario_id}")
        required=("old_created","authoritative_update","target_current","exposure","decision")
        if s.events!=required: errors.append(f"INVALID_EVENT_ORDER:{s.scenario_id}")
        if s.decision_phase_id==s.final_vote_phase_id: errors.append(f"PHASE_COLLISION:{s.scenario_id}")
    balance=build_balance_report(scenarios)
    if not balance["passed"]: errors.append("COUNTERBALANCE")
    report=ValidationReport(not errors,tuple(errors),balance)
    if errors: raise ScenarioValidationError(";".join(errors))
    return report

def validate_e1_scenario_set(scenarios):
    errors=[]
    if len(scenarios)!=40: errors.append("E1_COUNT")
    ids=set()
    for s in scenarios:
        if s.scenario_id in ids: errors.append("DUPLICATE_SCENARIO_ID")
        ids.add(s.scenario_id)
        if len({s.v_old,s.v_new,s.v_wrong})!=3: errors.append(f"NON_DISTINCT:{s.scenario_id}")
        wrong_version=f"{s.fact_id}:v_wrong"
        if len({s.version_old_id,s.version_new_id,wrong_version})!=3: errors.append(f"VERSION_COLLISION:{s.scenario_id}")
        if s.version_new_id not in s.target_visible_versions: errors.append(f"TARGET_NOT_CURRENT:{s.scenario_id}")
        if set(s.answer_pool.positions)!={s.v_old,s.v_new,s.v_wrong} or len(s.answer_pool.positions)!=3:
            errors.append(f"INVALID_ANSWER_POOL:{s.scenario_id}")
        if (s.answer_pool.current,s.answer_pool.stale,s.answer_pool.static_wrong)!=(s.v_new,s.v_old,s.v_wrong):
            errors.append(f"INVALID_ROLE_MAPPING:{s.scenario_id}")
        if s.events!=("old_created","authoritative_update","target_current","exposure","decision"):
            errors.append(f"INVALID_EVENT_ORDER:{s.scenario_id}")
        if s.decision_phase_id==s.final_vote_phase_id or not s.decision_phase_id.endswith(":decision"):
            errors.append(f"INVALID_PHASE:{s.scenario_id}")
        if s.split!="pilot" or s.template_id!="direct_state_categorical_v1": errors.append(f"INVALID_E1_METADATA:{s.scenario_id}")
    expected={f"e1-{i:02d}" for i in range(1,41)}
    if ids!=expected: errors.append("INVALID_E1_IDS")
    balance=build_balance_report(scenarios)
    if not balance["passed"]: errors.append("COUNTERBALANCE")
    report=ValidationReport(not errors,tuple(errors),balance)
    if errors: raise ScenarioValidationError(";".join(errors))
    return report
