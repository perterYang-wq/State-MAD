from __future__ import annotations
from dataclasses import dataclass
from .schema import AnswerPool, ScenarioRecord, canonical_bytes, digest

DEFAULT_VALUES = ("ALPHA", "BRAVO", "CHARLIE", "DELTA")

@dataclass(frozen=True)
class E0ScenarioSpec:
    count: int = 16; template_id: str = "direct-categorical-v1"
    value_pool: tuple[str, ...] = DEFAULT_VALUES; seed: int = 20260907

@dataclass(frozen=True)
class ScenarioSet:
    scenarios: tuple[ScenarioRecord, ...]; scenario_set_hash: str

    def to_bytes(self): return canonical_bytes(self.scenarios)

def compile_e0_scenarios(spec: E0ScenarioSpec = E0ScenarioSpec()) -> ScenarioSet:
    if spec.count != 16: raise ValueError("E0 requires exactly 16 scenarios")
    if len(spec.value_pool) < 3: raise ValueError("at least three values required")
    out=[]; n=len(spec.value_pool)
    for i in range(spec.count):
        roles=tuple(spec.value_pool[(i+j)%n] for j in range(3))
        # Independent cycle: option position does not follow the value-role cycle.
        position_shift=i%3
        positions=tuple(roles[(j+position_shift)%3] for j in range(3))
        sid=f"e0-{i+1:02d}"; fact=f"fact-{i+1:02d}"
        out.append(ScenarioRecord(sid,"e0",spec.seed,spec.template_id,i%12,fact,
            fact+":v1",fact+":v2",roles[0],roles[1],roles[2],AnswerPool(roles[1],roles[0],roles[2],positions),
            ("source","target"),("old_created","authoritative_update","target_current","exposure","decision"),
            (fact+":v2",),sid+":pre",sid+":decision",sid+":final"))
    scenarios=tuple(out)
    return ScenarioSet(scenarios,digest(scenarios))

def build_balance_report(scenarios):
    values=sorted({v for s in scenarios for v in (s.v_old,s.v_new,s.v_wrong)})
    role_counts={v:{r:sum(getattr(s,r)==v for s in scenarios) for r in ("v_old","v_new","v_wrong")} for v in values}
    position_counts={r:[sum(getattr(s,r)==s.answer_pool.positions[p] for s in scenarios) for p in range(3)] for r in ("v_old","v_new","v_wrong")}
    deltas=[max(c.values())-min(c.values()) for c in role_counts.values()]+[max(c)-min(c) for c in position_counts.values()]
    return {"role_counts":role_counts,"position_counts":position_counts,"max_delta":max(deltas),"passed":max(deltas)<=1}
