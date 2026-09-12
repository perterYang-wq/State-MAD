"""Bounded E1 orchestration for model-free validation and later authorized use.

This module intentionally implements only awareness plus the four frozen E1
siblings.  It contains no relay, retransmission, correction, or mitigation.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .backend import CachedBackend, FakeBackend
from .cache import MessageCache
from .grading import grade_output
from .lineage import validate_e1_lineage
from .manifest import build_manifest, finalize_manifest
from .metrics import evaluate_e1
from .preflight import E1RunConfig, validate_e1_preflight
from .prompts import render_awareness_probe, render_decision, render_e1_peer_message
from .run_store import RunStore
from .scenarios import E1ScenarioSpec, build_balance_report, compile_e1_scenarios
from .schema import (CallRecord, EffectiveGenerationIdentity, GenerationRequest,
                     LineageRecord, MessageRecord, digest)
from .snapshots import fork_snapshot, make_pre_exposure_snapshot
from .validation import validate_e1_scenario_set


def _identity(prompt, config):
    return EffectiveGenerationIdentity(
        "State-MAD strict categorical response", prompt.text, config.models[0],
        config.model_revision, config.models[0], config.tokenizer_revision,
        "chat-template-v1", (("temperature", config.temperature), ("top_p", config.top_p)),
        config.seed, config.max_new_tokens)


def prepare_e1_run(config: E1RunConfig, backend):
    if config.mode == "scientific" and (isinstance(backend, FakeBackend) or not getattr(backend, "scientific_backend", False)):
        raise ValueError("Fake/non-production backend cannot run scientific E1")
    cache_root = Path(config.cache_root or ".state_mad/cache") / config.mode
    store_root = Path(config.run_store_root or ".state_mad/runs") / config.mode
    return CachedBackend(backend, MessageCache(cache_root)), RunStore(store_root).create(config.run_id)


def build_e1_peer_messages(scenario, token_counter=None):
    definitions = (
        ("current-peer", scenario.v_new, scenario.version_new_id, "current", "current", 1, 1),
        ("stale-peer", scenario.v_old, scenario.version_old_id, "current", "stale", 1, 0),
        ("static-wrong", scenario.v_wrong, f"{scenario.fact_id}:v_wrong", "never_current", "static_wrong", 0, 0),
    )
    messages={}; controls={}
    for condition,value,version,generation_validity,decision_validity,was_current,current_now in definitions:
        rendered=render_e1_peer_message(scenario,value,was_current,current_now)
        mid=f"{scenario.scenario_id}:{condition}:peer"
        messages[condition]=MessageRecord(mid,digest(rendered.text),rendered.text,"source","target",(),
            scenario.fact_id,version,generation_validity,decision_validity,"exposure","deterministic")
        controls[condition]={"template_id":rendered.template_id,"template_hash":rendered.template_hash,
            "content_hash":digest(rendered.text),"token_count":token_counter(rendered.text) if token_counter else None}
    counts=[x["token_count"] for x in controls.values()]
    return messages,{"renderings":controls,"token_counts_exact_match":None if token_counter is None else len(set(counts))==1}


def build_e1_peer_control_report(scenarios, token_counter, counting_source=None):
    """Check E1's structural and counterbalanced controls without generation."""
    conditions=("current-peer","stale-peer","static-wrong")
    flags={"current-peer":(1,1),"stale-peer":(1,0),"static-wrong":(0,0)}
    actual={condition:[] for condition in conditions}
    normalized={condition:[] for condition in conditions}
    decisions={condition:[] for condition in conditions}
    per_scenario={}
    for scenario in scenarios:
        peers,_=build_e1_peer_messages(scenario)
        parent=make_pre_exposure_snapshot(scenario)
        row={"actual_peer_token_counts":{},"status_normalized_token_counts":{},
             "full_decision_prompt_token_counts":{}}
        for condition in conditions:
            actual_count=token_counter(peers[condition].raw_content)
            normalized_text=render_e1_peer_message(scenario,scenario.v_new,*flags[condition]).text
            normalized_count=token_counter(normalized_text)
            branch=fork_snapshot(parent,condition,(peers[condition].message_id,))
            decision=render_decision(scenario,branch,condition,(peers[condition],))
            decision_count=token_counter(decision.text)
            row["actual_peer_token_counts"][condition]=actual_count
            row["status_normalized_token_counts"][condition]=normalized_count
            row["full_decision_prompt_token_counts"][condition]=decision_count
            actual[condition].append(actual_count); normalized[condition].append(normalized_count)
            decisions[condition].append(decision_count)
        per_scenario[scenario.scenario_id]=row
    sorted_actual={condition:sorted(actual[condition]) for condition in conditions}
    sorted_normalized={condition:sorted(normalized[condition]) for condition in conditions}
    sorted_decisions={condition:sorted(decisions[condition]) for condition in conditions}
    status_match=all(len(set(row["status_normalized_token_counts"].values()))==1
                     for row in per_scenario.values())
    actual_match=len({tuple(counts) for counts in sorted_actual.values()})==1
    decision_match=len({tuple(counts) for counts in sorted_decisions.values()})==1
    values=sorted({value for scenario in scenarios
                   for value in (scenario.v_old,scenario.v_new,scenario.v_wrong)})
    role_counts={value:{role:sum(getattr(scenario,role)==value for scenario in scenarios)
                        for role in ("v_old","v_new","v_wrong")} for value in values}
    expected=len(scenarios)//len(values) if values and len(scenarios)%len(values)==0 else None
    role_balance=len(scenarios)==40 and len(values)==4 and expected==10 and all(
        count==expected for counts in role_counts.values() for count in counts.values())
    return {"template_id":"peer-v2","counting_source":counting_source,
            "per_scenario":per_scenario,"condition_sorted_actual_peer_token_counts":sorted_actual,
            "condition_sorted_status_normalized_token_counts":sorted_normalized,
            "condition_sorted_full_decision_prompt_token_counts":sorted_decisions,
            "status_structure_exact_match":status_match,"actual_peer_multiset_match":actual_match,
            "actual_decision_prompt_multiset_match":decision_match,"role_counts":role_counts,
            "role_balance_pass":role_balance,
            "overall_pass":status_match and actual_match and decision_match and role_balance}
def run_e1(config: E1RunConfig, cached_backend, run_store, backend_probe=None, peer_token_counter=None):
    """Run exactly 40 scenarios × five logical Target calls."""
    if run_store is None: raise ValueError("E1 requires a run store for canonical artifacts")
    started_at=datetime.now(timezone.utc).isoformat()
    if config.mode=="scientific":
        backend=getattr(cached_backend,"backend",None)
        if isinstance(backend,FakeBackend) or not getattr(backend,"scientific_backend",False):
            raise ValueError("scientific E1 requires a production backend")
        if peer_token_counter is None: raise ValueError("scientific E1 requires actual peer tokenizer counts")
        expected_cache=Path(config.cache_root)/config.mode
        expected_run=Path(config.run_store_root)/config.mode/config.run_id
        if Path(getattr(getattr(cached_backend,"cache",None),"root",""))!=expected_cache:
            raise ValueError("scientific E1 cache root does not match explicit configuration")
        if run_store.run_dir!=expected_run:
            raise ValueError("scientific E1 run-store root does not match explicit configuration")
    scenarios=compile_e1_scenarios(E1ScenarioSpec(count=config.scenario_count,seed=config.seed))
    validation=validate_e1_scenario_set(scenarios.scenarios); balance=build_balance_report(scenarios.scenarios)
    probe=backend_probe or {"seed_supported":True,"model_available":True,"tokenizer_available":True,"backend":"fake"}
    preflight=validate_e1_preflight(config,scenarios.scenarios,probe)
    if not preflight["passed"]: raise RuntimeError("preflight failed: "+",".join(preflight["errors"]))
    peer_material={}
    for scenario in scenarios.scenarios:
        peers,control=build_e1_peer_messages(scenario,peer_token_counter)
        peer_material[scenario.scenario_id]=(peers,control)
    peer_control_report=None
    if peer_token_counter is not None:
        peer_control_report=build_e1_peer_control_report(
            scenarios.scenarios,peer_token_counter,probe.get("tokenizer") or probe.get("backend"))
    if config.mode=="scientific" and not peer_control_report["overall_pass"]:
        # Whole-set preflight: this executes before the first backend call.
        raise RuntimeError("NEEDS HUMAN DECISION: E1 peer-v2 controls do not match")
    calls=[]; messages=[]; edges=[]; rows=[]; probe_ids=[]; decision_ids={}; provenance=[]; peer_controls={}; current_origins=set(); topology={}
    for s in scenarios.scenarios:
        parent=make_pre_exposure_snapshot(s); frozen_parent=parent.snapshot_hash
        peers,control=peer_material[s.scenario_id]; peer_controls[s.scenario_id]=control
        messages.extend(peers.values())
        specs=[("awareness",render_awareness_probe(s,parent),fork_snapshot(parent,"awareness"),())]
        no_peer=fork_snapshot(parent,"no-peer")
        specs.append(("no-peer",render_decision(s,no_peer,"no-peer"),no_peer,()))
        for condition in config.conditions[1:]:
            peer=peers[condition]; branch=fork_snapshot(parent,condition,(peer.message_id,))
            specs.append((condition,render_decision(s,branch,condition,(peer,)),branch,(peer.message_id,)))
        topology[s.scenario_id]={"parent_snapshot_hash":frozen_parent,
            "branches":{condition:{"snapshot_hash":snapshot.snapshot_hash,
                "parent_snapshot_hash":snapshot.parent_snapshot_hash,"peer_message_ids":parent_messages}
                for condition,_,snapshot,parent_messages in specs}}
        for condition,prompt,snapshot,parent_messages in specs:
            if parent.snapshot_hash!=frozen_parent or snapshot.parent_snapshot_hash!=frozen_parent:
                raise RuntimeError("E1 sibling/parent invariant violated")
            call_id=f"{s.scenario_id}:{condition}:call"; message_id=f"{s.scenario_id}:{condition}:output"
            identity=_identity(prompt,config)
            request=GenerationRequest(call_id,identity,s.scenario_id,"E1",s.decision_phase_id,condition,
                s.scenario_id+":pair","target","target",snapshot.snapshot_hash,snapshot.parent_snapshot_hash,snapshot.branch_id)
            result=cached_backend.generate(request); grade=grade_output(result.raw_output,s.answer_pool)
            message=MessageRecord(message_id,result.content_hash,result.raw_output,"target","decision",parent_messages,
                s.fact_id,s.version_new_id,"not_applicable","decision_output",s.decision_phase_id,"model")
            messages.append(message)
            if condition=="awareness": probe_ids.append(message_id)
            else: decision_ids[(s.scenario_id,condition)]=message_id
            for parent_id in parent_messages: edges.append(LineageRecord(parent_id,message_id,"exposure"))
            call=CallRecord(call_id,config.run_id,s.scenario_id,"E1",condition,s.scenario_id+":pair",message_id,
                "target","decision",parent_messages,s.fact_id,s.version_new_id,"not_applicable","decision_output",
                "current" if condition=="awareness" and grade.answer_class=="CURRENT" else "derived_from_probe",
                "not_applicable","not_applicable",prompt.prompt_hash,snapshot.snapshot_hash,config.models[0],
                config.model_revision,config.tokenizer_revision,config.seed,digest(config),result.raw_output,
                grade.parsed_output,grade.answer_class,result.usage.input_tokens,result.usage.output_tokens,
                result.usage.total_tokens,result.generated_usage.input_tokens,result.generated_usage.output_tokens,
                result.generated_usage.total_tokens,result.cache_status,"eligible",None,s.decision_phase_id)
            calls.append(call); rows.append({**asdict(call)})
            if result.cache_status=="miss": current_origins.add(result.origin_call_id)
            origin_is_current=result.origin_call_id in current_origins
            provenance.append({"call_id":call_id,"effective_generation_identity_hash":digest(identity),
                "cache_key":result.cache_key,"cache_status":result.cache_status,"content_hash":result.content_hash,
                "origin_call_id":result.origin_call_id,"origin_run_id":config.run_id if origin_is_current else None,
                "origin_resolution":"current_run" if origin_is_current else "legacy_unresolved"})
            run_store.put_message(message); run_store.append_call(call)
        for peer in peers.values(): run_store.put_message(peer)
    for edge in edges: run_store.append_lineage(edge)
    per_scenario={sid:{arm:mid for (candidate,arm),mid in decision_ids.items() if candidate==sid} for sid in (s.scenario_id for s in scenarios.scenarios)}
    lineage_reports=[validate_e1_lineage(messages,edges,per_scenario[s.scenario_id],probe_ids) for s in scenarios.scenarios]
    lineage={"passed":all(x["passed"] for x in lineage_reports),"errors":tuple(e for x in lineage_reports for e in x["errors"]),
        "scenario_reports":lineage_reports}
    report=evaluate_e1(rows,[s.scenario_id for s in scenarios.scenarios])
    report["peer_controls"]=peer_controls
    report["peer_control_report"]=peer_control_report
    report["branch_topology"]=topology
    report["cache_summary"]={"hits":sum(c.cache_status=="hit" for c in calls),
        "misses":sum(c.cache_status=="miss" for c in calls)}
    scenarios_hash=run_store.write_once("scenarios.json",scenarios.scenarios)
    validation_hash=run_store.write_once("validation.json",validation)
    balance_hash=run_store.write_once("balance.json",balance)
    cache_provenance_hash=run_store.write_once("cache_provenance.json",provenance)
    report_hash=run_store.finalize(report)
    prompt_hashes={f"{c.scenario_id}:{c.condition}":c.prompt_hash for c in calls}
    artifacts={"scenario":scenarios.scenario_set_hash,"scenarios":scenarios_hash,"validation":validation_hash,
        "balance":balance_hash,"prompts":digest(prompt_hashes),"calls":digest(calls),"lineage":digest(edges),
        "report":report_hash,"cache_provenance":cache_provenance_hash}
    usage={"input_tokens":sum(c.generated_input_tokens for c in calls),"output_tokens":sum(c.generated_output_tokens for c in calls),
        "total_tokens":sum(c.generated_total_tokens for c in calls)}
    effective={"experiment":"E1","run_id":config.run_id,"mode":config.mode,"model_id":config.models[0],
        "model_revision":config.model_revision,"tokenizer_id":config.models[0],"tokenizer_revision":config.tokenizer_revision,
        "temperature":config.temperature,"top_p":config.top_p,"max_new_tokens":config.max_new_tokens,"seed":config.seed,
        "backend":probe.get("backend"),"runtime":dict(probe),"quantization":probe.get("quantization"),
        "batching":probe.get("batching"),"context":probe.get("context")}
    manifest=build_manifest(config,artifacts,preflight,("state-mad","e1",config.mode),started_at,effective=effective)
    manifest=finalize_manifest(manifest,datetime.now(timezone.utc).isoformat(),usage,
        {"hits":sum(c.cache_status=="hit" for c in calls),"misses":sum(c.cache_status=="miss" for c in calls)})
    run_store.write_once("manifest.json",manifest)
    return {"dry_run":config.mode=="dry-run","scientific_result":config.mode=="scientific",
        "scenario_set_hash":scenarios.scenario_set_hash,"scenarios":scenarios.scenarios,"validation":asdict(validation),
        "balance":balance,"preflight":preflight,"calls":calls,"messages":messages,"lineage":lineage,
        "report":report,"cache_provenance":provenance,"manifest":manifest}


def run_e1_dry(cached_backend, run_store, config=E1RunConfig(), peer_token_counter=None):
    return run_e1(config,cached_backend,run_store,
        {"seed_supported":True,"model_available":True,"tokenizer_available":True,"backend":"fake"},peer_token_counter)
