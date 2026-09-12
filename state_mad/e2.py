"""Model-free, fail-closed E2 reconstruction and planning helpers.

E2 deliberately lives in a wrapper: frozen E1 evidence is read directly and
never regenerated, while downstream requests retain the ordinary cache
identity used by E0/E1.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .grading import grade_output
from .prompts import render_awareness_probe, render_decision
from .schema import (AnswerPool, CallRecord, EffectiveGenerationIdentity,
                     GenerationRequest, MessageRecord, ScenarioRecord, Snapshot,
                     digest)
from .snapshots import fork_snapshot, make_pre_exposure_snapshot

FROZEN_E1_RUN_ID = "e1-qwen25-7b-seed7-pilot-20260912-v1"
FROZEN_E1_SHA = "b002fe3d3dce8fe5d94b83f946dde2e494e09d4e"
FROZEN_E1_SCENARIO_HASH = "sha256:83c4034bc163b66285fb3085047507c773b14be9c1556e8165bbd9dd2d6df7c9"
FROZEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"
FROZEN_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
E2_ELIGIBLE_IDS = ("e1-04", "e1-10", "e1-16", "e1-18", "e1-22",
                   "e1-28", "e1-30", "e1-34", "e1-40")
FINAL_VOTE_MODE = "synchronized-role-specific-noncommunicative-v1"


class E2IntegrityError(ValueError):
    """A stable fail-closed E2 integrity error."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(code + (f":{detail}" if detail else ""))


@dataclass(frozen=True)
class E1RunExpectation:
    run_id: str = FROZEN_E1_RUN_ID
    scientific_sha: str = FROZEN_E1_SHA
    scenario_set_hash: str = FROZEN_E1_SCENARIO_HASH
    model: str = FROZEN_MODEL
    model_revision: str = FROZEN_MODEL_REVISION
    tokenizer_revision: str = ""
    seed: int = 7
    temperature: float = 0.0
    top_p: float = 1.0
    max_new_tokens: int = 32
    eligible_ids: tuple[str, ...] = E2_ELIGIBLE_IDS


@dataclass(frozen=True)
class E1ReplaySelection:
    condition: str
    call: CallRecord
    message: MessageRecord
    cache_provenance: Mapping[str, Any]
    content_hash: str
    parent_snapshot_hash: str


@dataclass(frozen=True)
class ResolvedE1ReplayPair:
    scenario: ScenarioRecord
    stale: E1ReplaySelection
    current: E1ReplaySelection
    awareness_call: CallRecord
    pair_id: str
    parent_snapshot_hash: str
    eligible_ids: tuple[str, ...]


@dataclass(frozen=True)
class E2ScenarioOverlay:
    scenario_id: str
    e1_scenario_set_hash: str
    e1_scenario_digest: str
    source_agent_id: str
    target_agent_id: str
    relay_agent_id: str
    relay_current_version_id: str
    relay_current_evidence_event_ids: tuple[str, ...]
    relay_parent_snapshot_id: str
    relay_parent_snapshot_hash: str
    final_vote_phase_id: str
    overlay_schema: str = "e2-overlay-v1"
    overlay_digest: str = ""


@dataclass(frozen=True)
class E2ReplayEnvelope:
    message: MessageRecord
    provenance: Mapping[str, Any]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise E2IntegrityError("CORRUPT_ARTIFACT", str(path)) from exc


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise E2IntegrityError("CORRUPT_ARTIFACT", str(path)) from exc


def _record(cls, row: Mapping[str, Any]):
    try:
        if cls is ScenarioRecord:
            row = dict(row); row["answer_pool"] = AnswerPool(**row["answer_pool"])
            for key in ("agents", "events", "target_visible_versions"):
                row[key] = tuple(row[key])
        elif cls in (CallRecord, MessageRecord):
            row = dict(row); row["parent_message_ids"] = tuple(row["parent_message_ids"])
        return cls(**row)
    except (KeyError, TypeError, ValueError) as exc:
        raise E2IntegrityError("CORRUPT_RECORD", cls.__name__) from exc


def _one(rows: Iterable[Any], predicate, code: str):
    found = [row for row in rows if predicate(row)]
    if len(found) != 1:
        raise E2IntegrityError(code, str(len(found)))
    return found[0]


def _artifact(manifest: Mapping[str, Any], name: str, value: Any) -> None:
    expected = manifest.get("artifact_hashes", {}).get(name)
    if not expected or digest(value) != expected:
        raise E2IntegrityError("ARTIFACT_HASH_MISMATCH", name)


def resolve_e1_replay_pair(e1_run_dir: str | Path, expectation: E1RunExpectation,
                           scenario_id: str) -> ResolvedE1ReplayPair:
    """Resolve one exact E1 pair without a backend, cache fallback, or writes."""
    root = Path(e1_run_dir)
    manifest = _load_json(root / "manifest.json")
    effective = manifest.get("effective_generation", {})
    checks = {
        "RUN_ID": effective.get("run_id") == expectation.run_id,
        "SCIENTIFIC_SHA": manifest.get("repository", {}).get("sha") == expectation.scientific_sha,
        "SCENARIO_SET_HASH": manifest.get("artifact_hashes", {}).get("scenario") == expectation.scenario_set_hash,
        "MODEL": effective.get("model_id") == expectation.model,
        "MODEL_REVISION": effective.get("model_revision") == expectation.model_revision,
        "TOKENIZER_REVISION": bool(expectation.tokenizer_revision) and effective.get("tokenizer_revision") == expectation.tokenizer_revision,
        "SEED": effective.get("seed") == expectation.seed,
        "TEMPERATURE": effective.get("temperature") == expectation.temperature,
        "TOP_P": effective.get("top_p") == expectation.top_p,
        "MAX_NEW_TOKENS": effective.get("max_new_tokens") == expectation.max_new_tokens,
        "FINALIZED": all(k in manifest for k in ("ended_at", "manifest_hash", "usage", "cache_stats")),
    }
    for code, ok in checks.items():
        if not ok: raise E2IntegrityError(code)
    if scenario_id not in expectation.eligible_ids:
        raise E2IntegrityError("INELIGIBLE_SCENARIO", scenario_id)

    scenario_rows = _load_json(root / "scenarios.json")
    call_rows = _load_jsonl(root / "calls.jsonl")
    provenance = _load_json(root / "cache_provenance.json")
    report = _load_json(root / "report.json")
    _artifact(manifest, "scenarios", scenario_rows)
    _artifact(manifest, "calls", call_rows)
    _artifact(manifest, "cache_provenance", provenance)
    _artifact(manifest, "report", report)
    scenarios = [_record(ScenarioRecord, row) for row in scenario_rows]
    calls = [_record(CallRecord, row) for row in call_rows]
    scenario = _one(scenarios, lambda x: x.scenario_id == scenario_id, "SCENARIO_SELECTOR")

    recomputed = tuple(report.get("confirmed_treatment_only_stale_ids", ()))
    if recomputed != expectation.eligible_ids:
        raise E2IntegrityError("ELIGIBLE_SET_MISMATCH")
    awareness = _one(calls, lambda x: x.scenario_id == scenario_id and x.condition == "awareness" and x.author == "target", "AWARENESS_SELECTOR")
    if awareness.answer_class != "CURRENT": raise E2IntegrityError("AWARENESS_NOT_CURRENT")
    if awareness.parent_message_ids: raise E2IntegrityError("AWARENESS_CONTAMINATION")
    topology = report.get("branch_topology", {}).get(scenario_id, {})
    parent_hash = topology.get("parent_snapshot_hash")
    if not parent_hash: raise E2IntegrityError("MISSING_PARENT_TOPOLOGY")

    selections = {}
    for condition in ("stale-peer", "current-peer"):
        call = _one(calls, lambda x, c=condition: x.scenario_id == scenario_id and x.condition == c and x.author == "target", "DUPLICATE_SELECTOR")
        if (call.run_id, call.experiment, call.pair_id, call.scenario_id) != (expectation.run_id, "E1", scenario_id + ":pair", scenario_id):
            raise E2IntegrityError("CALL_IDENTITY_MISMATCH", condition)
        if (call.model, call.model_revision, call.tokenizer_revision, call.seed, call.phase_id) != (
                expectation.model, expectation.model_revision, expectation.tokenizer_revision,
                expectation.seed, scenario.decision_phase_id):
            raise E2IntegrityError("CALL_CONFIG_MISMATCH", condition)
        branch = topology.get("branches", {}).get(condition, {})
        if branch.get("snapshot_hash") != call.snapshot_hash or branch.get("parent_snapshot_hash") != parent_hash:
            raise E2IntegrityError("SNAPSHOT_MISMATCH", condition)
        message_row = _load_json(root / "messages" / f"{call.message_id}.json")
        message = _record(MessageRecord, message_row)
        if message.message_id != call.message_id or message.raw_content != call.raw_output:
            raise E2IntegrityError("RAW_OUTPUT_MISMATCH", condition)
        if (message.author, message.recipient, message.parent_message_ids) != ("target", "decision", call.parent_message_ids):
            raise E2IntegrityError("MESSAGE_IDENTITY_MISMATCH", condition)
        if len(call.parent_message_ids) != 1:
            raise E2IntegrityError("E1_EXPOSURE_ANCESTRY", condition)
        peer = _record(MessageRecord, _load_json(root / "messages" / f"{call.parent_message_ids[0]}.json"))
        expected_validity = ("current", "stale" if condition == "stale-peer" else "current")
        if (peer.message_id, peer.author, peer.recipient, peer.fact_id,
            peer.generation_validity, peer.decision_validity) != (
                call.parent_message_ids[0], "source", "target", scenario.fact_id, *expected_validity):
            raise E2IntegrityError("INVALID_E1_EXPOSURE", condition)
        if message.content_hash != digest(call.raw_output) or message.content_hash != digest(message.raw_content):
            raise E2IntegrityError("CONTENT_HASH_MISMATCH", condition)
        prov = _one(provenance, lambda x: x.get("call_id") == call.call_id, "CACHE_PROVENANCE_SELECTOR")
        if any((prov.get("content_hash") != message.content_hash,
                not prov.get("cache_key"), not prov.get("origin_call_id"),
                prov.get("origin_resolution") not in {"current_run", "external_verified"},
                prov.get("origin_run_id") != expectation.run_id)):
            raise E2IntegrityError("CACHE_PROVENANCE_MISMATCH", condition)
        grade = grade_output(call.raw_output, scenario.answer_pool)
        if call.raw_output != f"ANSWER={grade.parsed_output}" or grade.status != "valid" or grade.answer_class != call.answer_class:
            raise E2IntegrityError("NONCANONICAL_ANSWER", condition)
        selections[condition] = E1ReplaySelection(condition, call, message, dict(prov), message.content_hash, parent_hash)
    if selections["stale-peer"].call.answer_class != "STALE" or selections["current-peer"].call.answer_class == "STALE":
        raise E2IntegrityError("NOT_PAIRED_CAUSAL_ADOPTION")
    return ResolvedE1ReplayPair(scenario, selections["stale-peer"], selections["current-peer"],
                                awareness, scenario_id + ":pair", parent_hash, recomputed)


def build_e2_overlay(scenario: ScenarioRecord, pair: ResolvedE1ReplayPair,
                     e1_scenario_set_hash: str = FROZEN_E1_SCENARIO_HASH) -> E2ScenarioOverlay:
    if scenario != pair.scenario or e1_scenario_set_hash != FROZEN_E1_SCENARIO_HASH:
        raise E2IntegrityError("OVERLAY_E1_BINDING")
    parent0 = make_pre_exposure_snapshot(scenario)
    parent = replace(parent0, snapshot_id=f"{scenario.scenario_id}:relay:parent", branch_id="relay-parent")
    if parent.current_version_id != scenario.version_new_id or not parent.event_ids:
        raise E2IntegrityError("RELAY_CURRENT_UNAVAILABLE")
    values = dict(scenario_id=scenario.scenario_id, e1_scenario_set_hash=e1_scenario_set_hash,
        e1_scenario_digest=digest(scenario), source_agent_id="source", target_agent_id="target",
        relay_agent_id="relay", relay_current_version_id=scenario.version_new_id,
        relay_current_evidence_event_ids=tuple(parent.event_ids), relay_parent_snapshot_id=parent.snapshot_id,
        relay_parent_snapshot_hash=parent.snapshot_hash, final_vote_phase_id=scenario.final_vote_phase_id,
        overlay_schema="e2-overlay-v1")
    return E2ScenarioOverlay(**values, overlay_digest=digest(values))


def make_e2_replay_envelope(pair: ResolvedE1ReplayPair, arm: str,
                            overlay: E2ScenarioOverlay, e2_run_id: str) -> E2ReplayEnvelope:
    if arm not in {"stale", "current"}: raise E2IntegrityError("INVALID_ARM", arm)
    selected = pair.stale if arm == "stale" else pair.current
    if pair.scenario.scenario_id != overlay.scenario_id: raise E2IntegrityError("CROSS_SCENARIO_REPLAY")
    mid = f"{e2_run_id}:{overlay.scenario_id}:target-relay:{arm}:replay"
    message = MessageRecord(mid, selected.content_hash, selected.call.raw_output, overlay.target_agent_id,
        overlay.relay_agent_id, (), pair.scenario.fact_id,
        pair.scenario.version_old_id if arm == "stale" else pair.scenario.version_new_id,
        "current" if arm == "stale" else "not_applicable", "stale" if arm == "stale" else "current",
        pair.scenario.decision_phase_id, "e2_exact_e1_target_replay")
    provenance = {"e2_replay_message_id":mid, "relation":"exact_replay",
        "creation_source":message.creation_source, "e1_run_id":selected.call.run_id,
        "e1_call_id":selected.call.call_id, "e1_message_id":selected.message.message_id,
        "e1_condition":selected.condition, "e1_pair_id":selected.call.pair_id,
        "e1_snapshot_hash":selected.call.snapshot_hash, "e1_parent_snapshot_hash":selected.parent_snapshot_hash,
        "content_hash":selected.content_hash, "cache_key":selected.cache_provenance["cache_key"],
        "origin_call_id":selected.cache_provenance["origin_call_id"],
        "origin_run_id":selected.cache_provenance["origin_run_id"],
        "origin_resolution":selected.cache_provenance["origin_resolution"], "e2_scenario_id":overlay.scenario_id,
        "target_agent_id":overlay.target_agent_id, "relay_agent_id":overlay.relay_agent_id}
    return E2ReplayEnvelope(message, provenance)


def _relay_parent(scenario: ScenarioRecord, overlay: E2ScenarioOverlay) -> Snapshot:
    parent = replace(make_pre_exposure_snapshot(scenario), snapshot_id=overlay.relay_parent_snapshot_id,
                     branch_id="relay-parent")
    if parent.snapshot_hash != overlay.relay_parent_snapshot_hash: raise E2IntegrityError("OVERLAY_PARENT_HASH")
    return parent


def plan_relay_branches(scenario: ScenarioRecord, overlay: E2ScenarioOverlay,
                        stale: E2ReplayEnvelope, current: E2ReplayEnvelope) -> Mapping[str, Snapshot]:
    parent = _relay_parent(scenario, overlay); frozen = digest(parent)
    branches = {"awareness":fork_snapshot(parent, "relay-awareness"),
        "stale":fork_snapshot(parent, "relay-stale-replay", (stale.message.message_id,)),
        "current":fork_snapshot(parent, "relay-current-replay", (current.message.message_id,))}
    if digest(parent) != frozen or any(x.parent_snapshot_hash != parent.snapshot_hash for x in branches.values()):
        raise E2IntegrityError("RELAY_PARENT_MUTATION")
    if branches["awareness"].message_ids or set(branches["stale"].message_ids) & set(branches["current"].message_ids):
        raise E2IntegrityError("BRANCH_CONTAMINATION")
    return {"parent":parent, **branches}


def _identity(prompt, config) -> EffectiveGenerationIdentity:
    return EffectiveGenerationIdentity("State-MAD strict categorical response", prompt.text, config.models[0],
        config.model_revision, config.models[0], config.tokenizer_revision, "chat-template-v1",
        (("temperature", config.temperature), ("top_p", config.top_p)), config.seed, config.max_new_tokens)


def build_relay_awareness_request(scenario, overlay, branch, config, e2_run_id):
    prompt = render_awareness_probe(scenario, branch)
    request = GenerationRequest(f"{e2_run_id}:{scenario.scenario_id}:relay:awareness:call", _identity(prompt, config),
        scenario.scenario_id, "E2", scenario.decision_phase_id, "relay-awareness",
        f"{scenario.scenario_id}:e2-relay-pair", "relay", "relay", branch.snapshot_hash,
        branch.parent_snapshot_hash, branch.branch_id)
    return request, prompt


def build_relay_decision_request(scenario, overlay, branch, envelope, arm, config, e2_run_id):
    condition = f"relay-{arm}-replay"
    prompt = render_decision(scenario, branch, condition, (envelope.message,))
    request = GenerationRequest(f"{e2_run_id}:{scenario.scenario_id}:relay:{arm}-replay:call", _identity(prompt, config),
        scenario.scenario_id, "E2", scenario.decision_phase_id, condition,
        f"{scenario.scenario_id}:e2-relay-pair", "relay", "relay", branch.snapshot_hash,
        branch.parent_snapshot_hash, branch.branch_id)
    return request, prompt


def plan_final_readout(scenario: ScenarioRecord, overlay: E2ScenarioOverlay,
                       source_parent: Snapshot, target_stale: Snapshot, target_current: Snapshot,
                       relay_stale: Snapshot, relay_current: Snapshot) -> Mapping[str, Snapshot]:
    parents = {"source-final":source_parent, "target-stale-final":target_stale,
        "target-current-final":target_current, "relay-stale-final":relay_stale, "relay-current-final":relay_current}
    planned = {}
    for condition, parent in parents.items():
        before = digest(parent)
        planned[condition] = replace(fork_snapshot(parent, condition), phase_id=overlay.final_vote_phase_id,
                                     message_ids=parent.message_ids, visible_message_ids=parent.visible_message_ids)
        if digest(parent) != before: raise E2IntegrityError("FINAL_PARENT_MUTATION")
    if source_parent.message_ids or source_parent.visible_message_ids or source_parent.current_version_id != scenario.version_new_id:
        raise E2IntegrityError("SOURCE_FINAL_NOT_CURRENT_NO_PEER")
    return planned


def build_final_readout_request(scenario, snapshot, condition, config, e2_run_id,
                                visible_messages=()):
    if condition not in {"source-final", "target-stale-final", "target-current-final", "relay-stale-final", "relay-current-final"}:
        raise E2IntegrityError("INVALID_FINAL_CONDITION")
    prompt = render_decision(scenario, snapshot, condition, tuple(visible_messages))
    role = condition.split("-", 1)[0]
    request = GenerationRequest(f"{e2_run_id}:{scenario.scenario_id}:{condition}:call", _identity(prompt, config),
        scenario.scenario_id, "E2", scenario.final_vote_phase_id, condition,
        f"{scenario.scenario_id}:e2-final", role, role, snapshot.snapshot_hash,
        snapshot.parent_snapshot_hash, snapshot.branch_id)
    return request, prompt


def assemble_final_votes(scenario_id: str, final_vote_phase_id: str,
                         calls: Iterable[CallRecord | Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = [asdict(x) if hasattr(x, "__dataclass_fields__") else dict(x) for x in calls]
    by = {row.get("condition"):row for row in rows}
    required = ("source-final", "target-stale-final", "target-current-final", "relay-stale-final", "relay-current-final")
    if len(rows) != 5 or any(sum(r.get("condition") == c for r in rows) != 1 for c in required):
        raise E2IntegrityError("FINAL_CALL_SET")
    if any(r.get("scenario_id") != scenario_id or r.get("phase_id") != final_vote_phase_id for r in rows):
        raise E2IntegrityError("MIXED_FINAL_PHASE")
    if any(r.get("condition") == "source-stale-seed" for r in rows): raise E2IntegrityError("PREUPDATE_SEED_VOTE")
    source = by["source-final"]
    if (source.get("author") != "source" or source.get("parent_message_ids") or
            source.get("source_correction_status") not in {None, "not_applicable"}):
        raise E2IntegrityError("SOURCE_FINAL_SEMANTICS")
    final_message_ids={row.get("message_id") for row in rows}
    if any(set(row.get("parent_message_ids",())) & final_message_ids for row in rows):
        raise E2IntegrityError("FINAL_READOUT_COMMUNICATION")
    result=[]
    for arm in ("stale", "current"):
        chosen = [source, by[f"target-{arm}-final"], by[f"relay-{arm}-final"]]
        result.append({"system_case_id":f"{scenario_id}:e2-system:{arm}", "scenario_id":scenario_id,
            "arm":arm, "final_vote_phase_id":final_vote_phase_id, "votes":tuple({k:r.get(k) for k in
            ("call_id","message_id","author","answer_class","phase_id","cache_status","condition")} for r in chosen),
            "source_call_id":source.get("call_id"), "complete":all(r.get("answer_class") is not None and
            not r.get("infrastructure_failure", False) for r in chosen), "communication_edges":()})
    return tuple(result)
