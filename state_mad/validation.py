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
