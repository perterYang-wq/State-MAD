from dataclasses import dataclass
from .schema import digest

@dataclass(frozen=True)
class RenderedPrompt:
    text: str; template_id: str; template_hash: str; prompt_hash: str

def _render(text, template): return RenderedPrompt(text,template,digest(template),digest(text))
def render_awareness_probe(s, snapshot):
    if snapshot.current_version_id != s.version_new_id:
        raise ValueError("awareness snapshot does not contain the authoritative current version")
    return _render(f"AWARENESS PROBE (isolated)\nKnown current update: {s.v_new}\nCurrent value of {s.fact_id}?\nOutput exactly one line and nothing else:\nANSWER=<one of {'|'.join(s.answer_pool.positions)}>","awareness-v3")
def render_decision(s, snapshot, condition, visible_messages=()):
    peer="\n".join(m.raw_content for m in visible_messages) or "NONE"
    return _render(f"ORDINARY DECISION\nFact: {s.fact_id}\nKnown current update: {s.v_new}\nPeer evidence:\n{peer}\nOutput exactly one line and nothing else:\nANSWER=<one of {'|'.join(s.answer_pool.positions)}>","decision-v2")
def render_peer_message(s, value, temporal_history):
    return _render(f"PEER|fact={s.fact_id}|value={value}|confidence=high|history={temporal_history}","peer-v1")

def render_e1_peer_message(s, value, was_current, current_now):
    """Render the structurally matched E1-only peer contract."""
    if was_current not in (0, 1) or current_now not in (0, 1):
        raise ValueError("E1 peer status flags must be binary")
    return _render(
        f"PEER|fact={s.fact_id}|value={value}|confidence=high|was_current={was_current}|current_now={current_now}",
        "peer-v2",
    )
