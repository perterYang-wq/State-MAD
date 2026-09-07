"""Frozen records and canonical serialization for direct categorical state."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Tuple

SCHEMA_VERSION = "state-mad-p0-v1"


def canonical_bytes(value: Any) -> bytes:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      default=lambda obj: asdict(obj) if hasattr(obj, "__dataclass_fields__") else list(obj)).encode()


def digest(value: Any) -> str:
    return "sha256:" + sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class AnswerPool:
    current: str
    stale: str
    static_wrong: str
    positions: Tuple[str, str, str]


@dataclass(frozen=True)
class ScenarioRecord:
    scenario_id: str; split: str; generator_seed: int; template_id: str
    counterbalance_group: int; fact_id: str; version_old_id: str; version_new_id: str
    v_old: str; v_new: str; v_wrong: str; answer_pool: AnswerPool
    agents: Tuple[str, str]; events: Tuple[str, ...]; target_visible_versions: Tuple[str, ...]
    pre_exposure_snapshot_id: str; decision_phase_id: str; final_vote_phase_id: str


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str; scenario_id: str; branch_id: str; parent_snapshot_hash: str | None
    event_ids: Tuple[str, ...]; message_ids: Tuple[str, ...]; visible_message_ids: Tuple[str, ...]
    current_version_id: str; phase_id: str

    @property
    def snapshot_hash(self) -> str: return digest(self)


@dataclass(frozen=True)
class EffectiveGenerationIdentity:
    system_input: str; user_input: str; model: str; model_revision: str
    tokenizer: str; tokenizer_revision: str; chat_template_revision: str
    decoding: Tuple[Tuple[str, Any], ...]; seed: int; max_new_tokens: int


@dataclass(frozen=True)
class GenerationRequest:
    request_id: str; identity: EffectiveGenerationIdentity; scenario_id: str
    experiment: str; phase: str; condition: str; pair_id: str; agent_id: str
    agent_role: str; snapshot_hash: str; parent_snapshot_hash: str | None; branch_id: str


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int; output_tokens: int; total_tokens: int

    def __post_init__(self):
        if min(self.input_tokens, self.output_tokens, self.total_tokens) < 0 or self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("token usage must be nonnegative and reconcile")


@dataclass(frozen=True)
class BackendOutput:
    raw_output: str; usage: TokenUsage


@dataclass(frozen=True)
class GenerationResult:
    raw_output: str; usage: TokenUsage; generated_usage: TokenUsage; cache_status: str
    cache_key: str; content_hash: str; origin_call_id: str


@dataclass(frozen=True)
class MessageRecord:
    message_id: str; content_hash: str; raw_content: str; author: str; recipient: str
    parent_message_ids: Tuple[str, ...]; fact_id: str; version_id: str
    generation_validity: str; decision_validity: str; phase_id: str; creation_source: str


@dataclass(frozen=True)
class CallRecord:
    call_id: str; run_id: str; scenario_id: str; experiment: str; condition: str
    pair_id: str; message_id: str; author: str; recipient: str; parent_message_ids: Tuple[str, ...]
    fact_id: str; version_id: str; generation_validity: str; decision_validity: str
    current_awareness_status: str; source_correction_status: str
    correction_visibility: str; prompt_hash: str; snapshot_hash: str
    model: str; model_revision: str; tokenizer_revision: str; seed: int
    config_hash: str; raw_output: str; parsed_output: str | None; answer_class: str
    input_tokens: int; output_tokens: int; total_tokens: int
    generated_input_tokens: int; generated_output_tokens: int; generated_total_tokens: int
    cache_status: str; eligibility: str; exclusion_reason: str | None; phase_id: str


@dataclass(frozen=True)
class LineageRecord:
    parent_message_id: str; child_message_id: str; relation: str
