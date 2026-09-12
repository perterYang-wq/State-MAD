"""Model-free, fail-closed E2 reconstruction and planning helpers.

E2 deliberately lives in a wrapper: frozen E1 evidence is read directly and
never regenerated, while downstream requests retain the ordinary cache
identity used by E0/E1.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .grading import grade_output
from .lineage import validate_e2_lineage
from .manifest import build_manifest, finalize_manifest
from .metrics import evaluate_e2_fscr, evaluate_e2_retransmission
from .preflight import validate_e2_preflight
from .prompts import render_awareness_probe, render_decision, render_e1_peer_message
from .backend import FakeBackend
from .schema import (AnswerPool, CallRecord, EffectiveGenerationIdentity,
                     GenerationRequest, LineageRecord, MessageRecord, ScenarioRecord, Snapshot,
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
    peer_message: MessageRecord


@dataclass(frozen=True)
class ResolvedE1ReplayPair:
    scenario: ScenarioRecord
    stale: E1ReplaySelection
    current: E1ReplaySelection
    awareness_call: CallRecord
    pair_id: str
    parent_snapshot_hash: str
    eligible_ids: tuple[str, ...]
    awareness_message: MessageRecord | None = None


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


def _load_e1_run(e1_run_dir: str | Path, expectation: E1RunExpectation):
    """Load and independently reconstruct the complete sealed 40-case E1 run."""
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
    pre_final={k:v for k,v in manifest.items() if k not in {"ended_at","usage","cache_stats","manifest_hash"}}
    if digest(pre_final)!=manifest.get("manifest_hash"):
        raise E2IntegrityError("MANIFEST_SELF_HASH")

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
    if len(scenarios)!=40 or len({s.scenario_id for s in scenarios})!=40:
        raise E2IntegrityError("E1_SCENARIO_COUNT")
    message_rows=[_load_json(path) for path in sorted((root/"messages").glob("*.json"))]
    messages=[_record(MessageRecord,row) for row in message_rows]
    by_message={m.message_id:m for m in messages}
    if len(by_message)!=len(messages): raise E2IntegrityError("DUPLICATE_MESSAGE_ID")
    pairs={}; eligible=[]
    for scenario in scenarios:
        scenario_id=scenario.scenario_id
        awareness = _one(calls, lambda x,sid=scenario_id: x.scenario_id == sid and x.condition == "awareness" and x.author == "target", "AWARENESS_SELECTOR")
        if awareness.parent_message_ids: raise E2IntegrityError("AWARENESS_CONTAMINATION",scenario_id)
        awareness_message=by_message.get(awareness.message_id)
        if awareness_message is None or awareness_message.raw_content!=awareness.raw_output or awareness_message.content_hash!=digest(awareness.raw_output):
            raise E2IntegrityError("AWARENESS_MESSAGE_INTEGRITY",scenario_id)
        awareness_grade=grade_output(awareness.raw_output,scenario.answer_pool)
        if (awareness.model,awareness.model_revision,awareness.tokenizer_revision,awareness.seed,awareness.phase_id)!=(expectation.model,expectation.model_revision,expectation.tokenizer_revision,expectation.seed,scenario.decision_phase_id):
            raise E2IntegrityError("AWARENESS_CONFIG_MISMATCH",scenario_id)
        if awareness.raw_output!=f"ANSWER={awareness_grade.parsed_output}" or awareness_grade.answer_class!=awareness.answer_class:
            raise E2IntegrityError("NONCANONICAL_AWARENESS",scenario_id)
        awareness_prov=_one(provenance,lambda x,cid=awareness.call_id:x.get("call_id")==cid,"CACHE_PROVENANCE_SELECTOR")
        if awareness_prov.get("content_hash")!=awareness_message.content_hash:
            raise E2IntegrityError("AWARENESS_PROVENANCE_MISMATCH",scenario_id)
        topology = report.get("branch_topology", {}).get(scenario_id, {})
        parent_hash = topology.get("parent_snapshot_hash")
        if not parent_hash: raise E2IntegrityError("MISSING_PARENT_TOPOLOGY",scenario_id)
        selections={}
        for condition in ("stale-peer", "current-peer"):
            call = _one(calls, lambda x,c=condition,sid=scenario_id: x.scenario_id == sid and x.condition == c and x.author == "target", "DUPLICATE_SELECTOR")
            if (call.run_id,call.experiment,call.pair_id,call.scenario_id)!=(expectation.run_id,"E1",scenario_id+":pair",scenario_id):
                raise E2IntegrityError("CALL_IDENTITY_MISMATCH",condition)
            if (call.model,call.model_revision,call.tokenizer_revision,call.seed,call.phase_id)!=(expectation.model,expectation.model_revision,expectation.tokenizer_revision,expectation.seed,scenario.decision_phase_id):
                raise E2IntegrityError("CALL_CONFIG_MISMATCH",condition)
            branch=topology.get("branches",{}).get(condition,{})
            if branch.get("snapshot_hash")!=call.snapshot_hash or branch.get("parent_snapshot_hash")!=parent_hash:
                raise E2IntegrityError("SNAPSHOT_MISMATCH",condition)
            message = by_message.get(call.message_id)
            if message is None: raise E2IntegrityError("MISSING_MESSAGE",call.message_id)
            if message.raw_content!=call.raw_output or (message.author,message.recipient,message.parent_message_ids)!=("target","decision",call.parent_message_ids):
                raise E2IntegrityError("MESSAGE_IDENTITY_MISMATCH",condition)
            if len(call.parent_message_ids)!=1: raise E2IntegrityError("E1_EXPOSURE_ANCESTRY",condition)
            peer = by_message.get(call.parent_message_ids[0])
            if peer is None: raise E2IntegrityError("MISSING_MESSAGE",call.parent_message_ids[0])
            expected_validity=("current","stale" if condition=="stale-peer" else "current")
            expected_value=scenario.v_old if condition=="stale-peer" else scenario.v_new
            expected_version=scenario.version_old_id if condition=="stale-peer" else scenario.version_new_id
            expected_text=render_e1_peer_message(scenario,expected_value,1,0 if condition=="stale-peer" else 1).text
            if (peer.message_id,peer.author,peer.recipient,peer.fact_id,peer.version_id,
                peer.generation_validity,peer.decision_validity,peer.phase_id,peer.creation_source,
                peer.raw_content,peer.content_hash)!=(call.parent_message_ids[0],"source","target",scenario.fact_id,
                expected_version,*expected_validity,"exposure","deterministic",expected_text,digest(expected_text)):
                raise E2IntegrityError("INVALID_E1_EXPOSURE",condition)
            if message.content_hash!=digest(call.raw_output) or message.content_hash!=digest(message.raw_content):
                raise E2IntegrityError("CONTENT_HASH_MISMATCH",condition)
            prov=_one(provenance,lambda x,cid=call.call_id:x.get("call_id")==cid,"CACHE_PROVENANCE_SELECTOR")
            if any((prov.get("content_hash")!=message.content_hash,not prov.get("cache_key"),not prov.get("origin_call_id"),prov.get("origin_resolution") not in {"current_run","external_verified"},prov.get("origin_run_id")!=expectation.run_id)):
                raise E2IntegrityError("CACHE_PROVENANCE_MISMATCH",condition)
            grade=grade_output(call.raw_output,scenario.answer_pool)
            if call.raw_output!=f"ANSWER={grade.parsed_output}" or grade.status!="valid" or grade.answer_class!=call.answer_class:
                raise E2IntegrityError("NONCANONICAL_ANSWER",condition)
            selections[condition] = E1ReplaySelection(condition,call,message,dict(prov),message.content_hash,parent_hash,peer)
        pair=ResolvedE1ReplayPair(scenario,selections["stale-peer"],selections["current-peer"],awareness,
                                  scenario_id+":pair",parent_hash,(),awareness_message)
        if awareness.answer_class=="CURRENT" and selections["stale-peer"].call.answer_class=="STALE" and selections["current-peer"].call.answer_class!="STALE":
            eligible.append(scenario_id)
        pairs[scenario_id]=pair
    recomputed=tuple(eligible)
    if recomputed!=expectation.eligible_ids or tuple(report.get("confirmed_treatment_only_stale_ids",()))!=recomputed:
        raise E2IntegrityError("ELIGIBLE_SET_MISMATCH")
    return {sid:replace(pair,eligible_ids=recomputed) for sid,pair in pairs.items()}, manifest, scenario_rows


def resolve_e1_replay_pairs(e1_run_dir: str | Path, expectation: E1RunExpectation):
    pairs,_,_=_load_e1_run(e1_run_dir,expectation)
    return tuple(pairs[sid] for sid in expectation.eligible_ids)


def resolve_e1_replay_pair(e1_run_dir: str | Path, expectation: E1RunExpectation,
                           scenario_id: str) -> ResolvedE1ReplayPair:
    """Resolve one member after validating and reconstructing the whole E1 run."""
    if scenario_id not in expectation.eligible_ids: raise E2IntegrityError("INELIGIBLE_SCENARIO",scenario_id)
    pairs,_,_=_load_e1_run(e1_run_dir,expectation)
    return pairs[scenario_id]


def reconstruct_e1_target_branch_snapshot(pair: ResolvedE1ReplayPair, arm: str) -> Snapshot:
    """Rebuild a selected, manifest-validated E1 Target branch exactly."""
    if arm not in {"stale","current"}: raise E2IntegrityError("INVALID_ARM",arm)
    selected=pair.stale if arm=="stale" else pair.current
    condition="stale-peer" if arm=="stale" else "current-peer"
    if selected.condition!=condition or selected.peer_message.message_id not in selected.call.parent_message_ids:
        raise E2IntegrityError("E1_BRANCH_PEER_ID",condition)
    parent=make_pre_exposure_snapshot(pair.scenario)
    if parent.snapshot_hash!=pair.parent_snapshot_hash or selected.parent_snapshot_hash!=parent.snapshot_hash:
        raise E2IntegrityError("E1_BRANCH_PARENT_HASH",condition)
    branch=fork_snapshot(parent,condition,(selected.peer_message.message_id,))
    if branch.snapshot_hash!=selected.call.snapshot_hash:
        raise E2IntegrityError("E1_BRANCH_SNAPSHOT_HASH",condition)
    return branch


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
        "not_applicable", "stale" if arm == "stale" else "current",
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
                                visible_messages):
    if condition not in {"source-final", "target-stale-final", "target-current-final", "relay-stale-final", "relay-current-final"}:
        raise E2IntegrityError("INVALID_FINAL_CONDITION")
    visible_messages=tuple(visible_messages)
    role = condition.split("-", 1)[0]
    expected=() if condition=="source-final" else tuple(snapshot.visible_message_ids)
    supplied=tuple(m.message_id for m in visible_messages)
    if supplied!=expected or (condition!="source-final" and len(supplied)!=1):
        raise E2IntegrityError("FINAL_VISIBLE_EVIDENCE_MISMATCH",condition)
    if any(m.author==role for m in visible_messages):
        raise E2IntegrityError("FINAL_SELF_OUTPUT_INJECTION",condition)
    prompt = render_decision(scenario, snapshot, condition, visible_messages)
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


def finalize_final_votes(final_votes, lineage_report):
    """Attach deterministic audit diagnostics after lineage evaluation."""
    finalized=[]
    for case in final_votes:
        votes=tuple(case["votes"]); by_role={v["author"]:dict(v) for v in votes}
        stale_ids=tuple(v["message_id"] for v in votes if v.get("answer_class")=="STALE")
        evidence=lineage_report.get("system_cases",{}).get(case["system_case_id"],{})
        exclusions=() if case.get("complete") else ("INCOMPLETE_FINAL_PHASE",)
        finalized.append({**case,"source":by_role.get("source"),"target":by_role.get("target"),
            "relay":by_role.get("relay"),"exclusion_reasons":exclusions,"stale_majority":len(stale_ids)>=2,
            "stale_majority_member_ids":stale_ids,"tier_b_evaluable":bool(evidence.get("tier_b_evaluable")),
            "tier_b_predicate":bool(evidence.get("tier_b_predicate")),
            "tier_b_evidence_ids":tuple(evidence.get("tier_b_evidence_ids",())),
            "tier_c_evaluable":bool(evidence.get("tier_c_evaluable")),
            "tier_c_predicate":bool(evidence.get("tier_c_predicate")),
            "tier_c_evidence_ids":tuple(evidence.get("tier_c_evidence_ids",()))})
    return tuple(finalized)


def _e2_call(request, result, scenario, config, condition, author, parent_ids):
    grade=grade_output(result.raw_output,scenario.answer_pool)
    message_id=request.request_id.removesuffix(":call")+":output"
    message=MessageRecord(message_id,result.content_hash,result.raw_output,author,"decision",tuple(parent_ids),
        scenario.fact_id,scenario.version_new_id,"not_applicable","decision_output",request.phase,"model")
    call=CallRecord(request.request_id,config.run_id,scenario.scenario_id,"E2",condition,request.pair_id,
        message_id,author,"decision",tuple(parent_ids),scenario.fact_id,scenario.version_new_id,"not_applicable",
        "decision_output","current" if condition=="relay-awareness" and grade.answer_class=="CURRENT" else
        "derived_from_probe" if condition=="relay-awareness" else "not_applicable",
        "not_applicable","not_applicable",digest(request.identity.user_input),request.snapshot_hash,config.models[0],
        config.model_revision,config.tokenizer_revision,config.seed,digest(config),result.raw_output,grade.parsed_output,
        grade.answer_class,result.usage.input_tokens,result.usage.output_tokens,result.usage.total_tokens,
        result.generated_usage.input_tokens,result.generated_usage.output_tokens,result.generated_usage.total_tokens,
        result.cache_status,"eligible",None,request.phase)
    provenance={"call_id":call.call_id,"effective_generation_identity_hash":digest(request.identity),
        "scenario_id":call.scenario_id,"condition":call.condition,
        "cache_key":result.cache_key,"cache_status":result.cache_status,"content_hash":result.content_hash,
        "origin_call_id":result.origin_call_id,"origin_run_id":None,"origin_resolution":"unavailable",
        "input_tokens":call.input_tokens,"output_tokens":call.output_tokens,"total_tokens":call.total_tokens,
        "generated_input_tokens":call.generated_input_tokens,"generated_output_tokens":call.generated_output_tokens,
        "generated_total_tokens":call.generated_total_tokens}
    return call,message,provenance


def validate_e2_runtime_binding(config, cached_backend, run_store):
    """Bind scientific configuration to injected objects without generating."""
    if config.mode!="scientific": return {"passed":True,"errors":(),"scientific":False}
    errors=[]; backend=getattr(cached_backend,"backend",None)
    if isinstance(backend,FakeBackend) or not getattr(backend,"scientific_backend",False):
        errors.append("ACTUAL_SCIENTIFIC_BACKEND")
    expected_cache=Path(config.cache_root or "")
    if Path(getattr(getattr(cached_backend,"cache",None),"root","")).resolve()!=expected_cache.resolve():
        errors.append("ACTUAL_CACHE_ROOT")
    expected_run=Path(config.run_store_root or "")/config.mode/config.run_id
    if Path(getattr(run_store,"run_dir","")).resolve()!=expected_run.resolve(): errors.append("ACTUAL_RUN_STORE")
    run_dir=getattr(run_store,"run_dir",None)
    if run_dir is None or not Path(run_dir).is_dir() or {p.name for p in Path(run_dir).iterdir()}!={"messages"} or any((Path(run_dir)/"messages").iterdir()):
        errors.append("RUN_STORE_NOT_NEW")
    if not (0<config.projected_total_tokens<=config.planning_ceiling): errors.append("SCIENTIFIC_TOKEN_PROJECTION")
    return {"passed":not errors,"errors":tuple(errors),"scientific":True}


def run_e2(config, e1_run_dir, expectation, cached_backend, run_store, backend_probe=None):
    """Execute the bounded E2 plan using only injected storage and generation."""
    started=datetime.now(timezone.utc).isoformat()
    if run_store is None or run_store.run_dir is None: raise E2IntegrityError("RUN_STORE_REQUIRED")
    runtime=validate_e2_runtime_binding(config,cached_backend,run_store)
    if not runtime["passed"]: raise E2IntegrityError("E2_RUNTIME_BINDING",",".join(runtime["errors"]))
    before={p:p.read_bytes() for p in Path(e1_run_dir).rglob("*") if p.is_file()}
    all_pairs,e1_manifest,scenario_rows=_load_e1_run(e1_run_dir,expectation)
    pairs=tuple(all_pairs[sid] for sid in expectation.eligible_ids)
    validated_tokenizer=e1_manifest.get("effective_generation",{}).get("tokenizer_revision")
    if config.tokenizer_revision!=validated_tokenizer:
        raise E2IntegrityError("E1_E2_TOKENIZER_REVISION")
    overlays=tuple(build_e2_overlay(p.scenario,p) for p in pairs)
    envelopes=[]; branch_plans=[]; final_snapshots=[]; relay_requests=[]; final_requests=[]
    for pair,overlay in zip(pairs,overlays):
        stale=make_e2_replay_envelope(pair,"stale",overlay,config.run_id)
        current=make_e2_replay_envelope(pair,"current",overlay,config.run_id); envelopes.extend((stale,current))
        branches=plan_relay_branches(pair.scenario,overlay,stale,current); branch_plans.append(branches)
        relay_requests.append(build_relay_awareness_request(pair.scenario,overlay,branches["awareness"],config,config.run_id))
        relay_requests.append(build_relay_decision_request(pair.scenario,overlay,branches["stale"],stale,"stale",config,config.run_id))
        relay_requests.append(build_relay_decision_request(pair.scenario,overlay,branches["current"],current,"current",config,config.run_id))
        source=make_pre_exposure_snapshot(pair.scenario)
        target_stale=reconstruct_e1_target_branch_snapshot(pair,"stale")
        target_current=reconstruct_e1_target_branch_snapshot(pair,"current")
        planned=plan_final_readout(pair.scenario,overlay,source,target_stale,target_current,branches["stale"],branches["current"])
        final_snapshots.append(planned)
        visible={"source-final":(),"target-stale-final":(pair.stale.peer_message,),
            "target-current-final":(pair.current.peer_message,),"relay-stale-final":(stale.message,),
            "relay-current-final":(current.message,)}
        for condition,snapshot in planned.items():
            final_requests.append(build_final_readout_request(pair.scenario,snapshot,condition,config,config.run_id,visible[condition]))
    planned_cases=[]
    for pair in pairs:
        for arm in ("stale","current"):
            planned_cases.append({"scenario_id":pair.scenario.scenario_id,"arm":arm,
                "source_call_id":f"{config.run_id}:{pair.scenario.scenario_id}:source-final:call",
                "final_vote_phase_id":pair.scenario.final_vote_phase_id,"communication_edges":(),"votes":(
                {"author":"source","condition":"source-final"},{"author":"target","condition":f"target-{arm}-final"},
                {"author":"relay","condition":f"relay-{arm}-final"})})
    preflight=validate_e2_preflight(config,overlays,pairs,backend_probe or {},planned_cases,branch_plans,
                                    [request for request,_ in final_requests],validated_tokenizer)
    if not preflight["passed"]: raise E2IntegrityError("E2_PREFLIGHT",",".join(preflight["errors"]))
    run_store.write_once("preflight.json",preflight)
    selected_evidence={p.scenario.scenario_id:{"awareness_call_id":p.awareness_call.call_id,
        "awareness_message_id":p.awareness_call.message_id,"awareness_content_hash":p.awareness_message.content_hash,
        "stale_call_id":p.stale.call.call_id,"stale_message_id":p.stale.message.message_id,
        "stale_content_hash":p.stale.content_hash,"stale_answer_class":p.stale.call.answer_class,
        "current_call_id":p.current.call.call_id,"current_message_id":p.current.message.message_id,
        "current_content_hash":p.current.content_hash,"current_answer_class":p.current.call.answer_class,
        "pair_id":p.pair_id,"parent_snapshot_hash":p.parent_snapshot_hash} for p in pairs}
    eligibility={"candidate_ids":expectation.eligible_ids,"candidate_n":len(expectation.eligible_ids),
        "eligible_ids":expectation.eligible_ids,"eligible_n":len(expectation.eligible_ids),
        "excluded_ids":(),"excluded_reasons":{},"selected_evidence":selected_evidence,"recomputed":True}
    run_store.write_once("eligibility.json",eligibility)
    run_store.write_once("e2_scenario_overlay.json",overlays)
    e1_message_inventory={row["message_id"]:digest(row) for row in
        (_load_json(path) for path in sorted((Path(e1_run_dir)/"messages").glob("*.json")))}
    effective=e1_manifest["effective_generation"]
    upstream={"e1_run_id":expectation.run_id,"manifest_hash":e1_manifest["manifest_hash"],
        "scenario_set_hash":expectation.scenario_set_hash,"scientific_sha":expectation.scientific_sha,
        "model_id":effective.get("model_id"),"model_revision":effective.get("model_revision"),
        "tokenizer_revision":effective.get("tokenizer_revision"),"seed":effective.get("seed"),
        "temperature":effective.get("temperature"),"top_p":effective.get("top_p"),
        "max_new_tokens":effective.get("max_new_tokens"),"artifact_hashes":{
        name:e1_manifest["artifact_hashes"].get(name) for name in ("scenarios","calls","cache_provenance","report")},
        "message_inventory_hash":digest(e1_message_inventory)}
    run_store.write_once("upstream_e1_provenance.json",upstream)
    replay_provenance=[dict(x.provenance) for x in envelopes]
    if len(replay_provenance)!=18 or len({x["e2_replay_message_id"] for x in replay_provenance})!=18:
        raise E2IntegrityError("REPLAY_PROVENANCE_CARDINALITY")
    run_store.write_once("upstream_replay_provenance.json",replay_provenance)
    topology={p.scenario.scenario_id:{"parent":branch_plans[i]["parent"],
        "branches":{k:branch_plans[i][k] for k in ("awareness","stale","current")}}
        for i,p in enumerate(pairs)}
    run_store.write_once("branch_topology.json",topology)
    calls=[]; messages=[]; cache_provenance=[]; relay_by={}; final_by={}
    for envelope in envelopes: messages.append(envelope.message); run_store.put_message(envelope.message)
    for (request,_prompt) in relay_requests:
        result=cached_backend.generate(request); pair=all_pairs[request.scenario_id]
        call,message,prov=_e2_call(request,result,pair.scenario,config,request.condition,"relay",
                                    tuple(request.identity.user_input and (request.branch_id,) if False else ()))
        # Decision ancestry is the exact visible replay; awareness has none.
        if request.condition.endswith("stale-replay") or request.condition.endswith("current-replay"):
            arm="stale" if "stale" in request.condition else "current"
            parent=(next(x.message.message_id for x in envelopes if x.provenance["e2_scenario_id"]==request.scenario_id and f":{arm}:replay" in x.message.message_id),)
            call=replace(call,parent_message_ids=parent); message=replace(message,parent_message_ids=parent)
        calls.append(call); messages.append(message); cache_provenance.append(prov); relay_by[(request.scenario_id,request.condition)]=call
        run_store.append_call(call); run_store.put_message(message)
    for request,_prompt in final_requests:
        result=cached_backend.generate(request); pair=all_pairs[request.scenario_id]
        snapshot=next(p[request.condition] for p,x in zip(final_snapshots,pairs) if x.scenario.scenario_id==request.scenario_id)
        call,message,prov=_e2_call(request,result,pair.scenario,config,request.condition,request.agent_id,snapshot.visible_message_ids)
        calls.append(call); messages.append(message); cache_provenance.append(prov); final_by[(request.scenario_id,request.condition)]=call
        run_store.append_call(call); run_store.put_message(message)
    final_votes=[]
    for pair in pairs:
        selected=[final_by[(pair.scenario.scenario_id,c)] for c in ("source-final","target-stale-final","target-current-final","relay-stale-final","relay-current-final")]
        final_votes.extend(assemble_final_votes(pair.scenario.scenario_id,pair.scenario.final_vote_phase_id,selected))
    # Join sealed E1 evidence solely in memory for mechanical cross-run lineage validation.
    validation_messages=list(messages); validation_calls=list(calls); edges=[]
    for pair,envelope_stale,envelope_current in zip(pairs,envelopes[::2],envelopes[1::2]):
        validation_messages.extend((pair.stale.peer_message,pair.current.peer_message,pair.awareness_message,pair.stale.message,pair.current.message))
        validation_calls.extend((pair.awareness_call,pair.stale.call,pair.current.call))
        sid=pair.scenario.scenario_id; rs=relay_by[(sid,"relay-stale-replay")]; rc=relay_by[(sid,"relay-current-replay")]
        ra=relay_by[(sid,"relay-awareness")]; rf=final_by[(sid,"relay-stale-final")]
        tsf=final_by[(sid,"target-stale-final")]; tcf=final_by[(sid,"target-current-final")]
        rcf=final_by[(sid,"relay-current-final")]
        specs=((pair.stale.peer_message.message_id,pair.stale.message.message_id,"source_stale_seed"),
            (pair.stale.peer_message.message_id,pair.stale.message.message_id,"source_to_target_exposure"),
            (pair.awareness_call.message_id,pair.stale.message.message_id,"target_awareness_sibling"),
            (pair.current.message.message_id,pair.stale.message.message_id,"target_paired_causal_adoption"),
            (pair.stale.message.message_id,envelope_stale.message.message_id,"e1_target_output_origin"),
            (pair.stale.message.message_id,envelope_stale.message.message_id,"exact_replay"),
            (envelope_stale.message.message_id,rs.message_id,"target_to_relay_exposure"),
            (ra.message_id,rs.message_id,"relay_awareness_sibling"),(rc.message_id,rs.message_id,"relay_matched_sibling"),
            (pair.stale.message.message_id,tsf.message_id,"final_vote_member"),
            (pair.current.message.message_id,tcf.message_id,"final_vote_member"),
            (rs.message_id,rf.message_id,"final_vote_member"),
            (rc.message_id,rcf.message_id,"final_vote_member"))
        edges.extend(LineageRecord(*x) for x in specs)
    preliminary=validate_e2_lineage(validation_messages,edges,replay_provenance,validation_calls,topology,final_votes)
    if not preliminary["passed"]: raise E2IntegrityError("E2_STRUCTURAL_LINEAGE",",".join(preliminary["errors"]))
    for pair in pairs:
        sid=pair.scenario.scenario_id; case_id=f"{sid}:e2-system:stale"
        rs=relay_by[(sid,"relay-stale-replay")]; ra=relay_by[(sid,"relay-awareness")]
        rf=final_by[(sid,"relay-stale-final")]; tf=final_by[(sid,"target-stale-final")]
        evidence=preliminary["system_cases"][case_id]
        if ra.answer_class=="CURRENT" and rs.answer_class=="STALE":
            edges.append(LineageRecord(rs.message_id,rf.message_id,"relay_stale_adoption"))
        if evidence["tier_b_predicate"]:
            edges.append(LineageRecord(pair.stale.message.message_id,tf.message_id,"tier_b_stale_majority_member"))
        if evidence["tier_c_predicate"]:
            edges.append(LineageRecord(rs.message_id,rf.message_id,"tier_c_complete_path"))
    lineage=validate_e2_lineage(validation_messages,edges,replay_provenance,validation_calls,topology,final_votes)
    if not lineage["passed"]: raise E2IntegrityError("E2_LINEAGE",",".join(lineage["errors"]))
    final_votes=finalize_final_votes(final_votes,lineage)
    lineage=validate_e2_lineage(validation_messages,edges,replay_provenance,validation_calls,topology,final_votes)
    if not lineage["passed"]: raise E2IntegrityError("E2_FINAL_VOTE_LINEAGE",",".join(lineage["errors"]))
    for edge in edges: run_store.append_lineage(edge)
    for vote in final_votes: run_store._append("final_votes.jsonl",vote)
    core_conditions={"relay-awareness","relay-stale-replay","relay-current-replay"}
    rows=[asdict(c) for c in calls if c.condition in core_conditions]
    integrity={sid:{"exact_replay":True,"infrastructure_failure":False} for sid in expectation.eligible_ids}
    retransmission=evaluate_e2_retransmission(rows,eligibility,{sid:{"same_parent":True} for sid in expectation.eligible_ids},integrity)
    fscr=evaluate_e2_fscr(final_votes,lineage)
    logical_usage={name:sum(getattr(c,name) for c in calls) for name in ("input_tokens","output_tokens","total_tokens")}
    generated_usage={name:sum(getattr(c,"generated_"+name) for c in calls) for name in ("input_tokens","output_tokens","total_tokens")}
    if logical_usage["total_tokens"]!=logical_usage["input_tokens"]+logical_usage["output_tokens"] or generated_usage["total_tokens"]!=generated_usage["input_tokens"]+generated_usage["output_tokens"]:
        raise E2IntegrityError("TOKEN_TOTAL_MISMATCH")
    cache_summary={"hits":sum(c.cache_status=="hit" for c in calls),"misses":sum(c.cache_status=="miss" for c in calls)}
    report={"retransmission":retransmission,"gate_4":retransmission["gate_4"],"fscr":fscr,
        "lineage":lineage,"exclusions":{"retransmission":retransmission["excluded"],
        "fscr":{name:value["excluded"] for name,value in fscr.items() if isinstance(value,dict) and "excluded" in value}},
        "logical_call_count":len(calls),"core_relay_call_count":len(rows),"cache_summary":cache_summary,
        "token_usage":{"logical":logical_usage,"generated":generated_usage}}
    run_store.write_once("cache_provenance.json",cache_provenance)
    report_hash=run_store.finalize(report)
    message_inventory={m.message_id:digest(m) for m in messages}
    artifacts={"scenario":expectation.scenario_set_hash,"validation":digest(lineage),"prompts":digest([r.identity.user_input for r,_ in relay_requests+final_requests]),
        "calls":digest(calls),"lineage":digest(edges),"preflight":digest(preflight),"eligibility":digest(eligibility),
        "e2_scenario_overlay":digest(overlays),"upstream_e1_provenance":digest(upstream),
        "upstream_replay_provenance":digest(replay_provenance),"branch_topology":digest(topology),
        "final_votes":digest(final_votes),"cache_provenance":digest(cache_provenance),"report":report_hash,
        "messages":digest(message_inventory)}
    after={p:p.read_bytes() for p in Path(e1_run_dir).rglob("*") if p.is_file()}
    if before!=after: raise E2IntegrityError("E1_MUTATED")
    manifest=build_manifest(config,artifacts,preflight,("state-mad","e2",config.mode),started,
        effective={"run_id":config.run_id,"model_id":config.models[0],"model_revision":config.model_revision,
        "tokenizer_revision":config.tokenizer_revision,"seed":config.seed,"temperature":config.temperature,
        "top_p":config.top_p,"max_new_tokens":config.max_new_tokens})
    usage={k:sum(getattr(c,"generated_"+k) for c in calls) for k in ("input_tokens","output_tokens","total_tokens")}
    manifest=finalize_manifest(manifest,datetime.now(timezone.utc).isoformat(),usage,
        {"hits":sum(c.cache_status=="hit" for c in calls),"misses":sum(c.cache_status=="miss" for c in calls)})
    run_store.write_once("manifest.json",manifest)
    return {"preflight":preflight,"calls":calls,"messages":messages,"lineage":lineage,
        "final_votes":final_votes,"report":report,"manifest":manifest,"artifacts":artifacts,
        "lineage_inputs":{"messages":tuple(validation_messages),"edges":tuple(edges),
            "replay_provenance":tuple(replay_provenance),"calls":tuple(validation_calls),"topology":topology}}
