from collections import defaultdict

E2_RELATIONS=frozenset(("source_stale_seed","source_to_target_exposure","target_awareness_sibling",
    "target_paired_causal_adoption","e1_target_output_origin","exact_replay","target_to_relay_exposure",
    "relay_awareness_sibling","relay_matched_sibling","relay_stale_adoption","final_vote_member",
    "tier_b_stale_majority_member","tier_c_complete_path"))

def _field(value,name,default=None):
    return value.get(name,default) if isinstance(value,dict) else getattr(value,name,default)

def validate_e0_lineage(messages, edges, decision_message_ids, probe_message_ids):
    by_id={m.message_id:m for m in messages}; parents=defaultdict(list)
    errors=[]
    for e in edges:
        if e.parent_message_id not in by_id or e.child_message_id not in by_id: errors.append("MISSING_MESSAGE")
        parents[e.child_message_id].append(e.parent_message_id)
    def ancestors(mid):
        seen=set(); stack=list(parents[mid])
        while stack:
            x=stack.pop()
            if x in seen: continue
            seen.add(x); stack.extend(parents[x])
        return seen
    for mid in decision_message_ids:
        if ancestors(mid)&set(probe_message_ids): errors.append(f"PROBE_CONTAMINATION:{mid}")
    for m in messages:
        if m.decision_validity=="stale" and m.generation_validity!="current": errors.append(f"NOT_ONCE_CORRECT:{m.message_id}")
    return {"passed":not errors,"errors":tuple(errors),"paths":{m:tuple(sorted(ancestors(m))) for m in decision_message_ids}}

def validate_e1_lineage(messages, edges, decisions, probe_message_ids):
    """Validate only E1's four decision arms and isolated awareness sibling."""
    by_id={m.message_id:m for m in messages}; parents=defaultdict(list); errors=[]
    for e in edges:
        if e.parent_message_id not in by_id or e.child_message_id not in by_id: errors.append("MISSING_MESSAGE")
        parents[e.child_message_id].append(e.parent_message_id)
    def ancestors(mid):
        seen=set(); stack=list(parents[mid])
        while stack:
            item=stack.pop()
            if item in seen: continue
            seen.add(item); stack.extend(parents[item])
        return seen
    expected={"no-peer":0,"current-peer":1,"stale-peer":1,"static-wrong":1}
    if set(decisions)!=set(expected): errors.append("INCOMPLETE_DECISION_ARMS")
    for condition,mid in decisions.items():
        if condition not in expected:
            continue
        if mid not in by_id: errors.append(f"MISSING_DECISION_MESSAGE:{mid}")
        found=ancestors(mid); peer=[by_id[x] for x in found if x in by_id and by_id[x].phase_id=="exposure"]
        if len(peer)!=expected[condition]: errors.append(f"PEER_ANCESTRY:{condition}:{mid}")
        if found & set(probe_message_ids): errors.append(f"AWARENESS_CONTAMINATION:{mid}")
        if condition=="current-peer" and peer and (peer[0].generation_validity,peer[0].decision_validity)!=("current","current"):
            errors.append(f"MALFORMED_CURRENT:{mid}")
        if condition=="stale-peer" and peer and (peer[0].generation_validity,peer[0].decision_validity)!=("current","stale"):
            errors.append(f"MALFORMED_STALE:{mid}")
        if condition=="static-wrong" and peer and (peer[0].generation_validity,peer[0].decision_validity)!=("never_current","static_wrong"):
            errors.append(f"MALFORMED_STATIC_WRONG:{mid}")
    return {"passed":not errors,"errors":tuple(errors),"paths":{m:tuple(sorted(ancestors(m))) for m in decisions.values()}}


def validate_e2_lineage(messages, edges, replay_provenance, calls, topology, final_votes):
    """Pure validator for exact two-hop E2 lineage and final-readout isolation."""
    messages=tuple(messages); edges=tuple(edges); replay_provenance=tuple(replay_provenance)
    calls=tuple(calls); final_votes=tuple(final_votes)
    by_id={_field(m,"message_id"):m for m in messages}; errors=[]; parents=defaultdict(list)
    if len(by_id)!=len(messages): errors.append("DUPLICATE_MESSAGE_ID")
    for edge in edges:
        parent=_field(edge,"parent_message_id"); child=_field(edge,"child_message_id"); relation=_field(edge,"relation")
        if relation not in E2_RELATIONS: errors.append(f"INVALID_RELATION:{relation}")
        if parent not in by_id or child not in by_id: errors.append("MISSING_MESSAGE")
        else:
            parents[child].append(parent)
            if _field(by_id[parent],"fact_id")!=_field(by_id[child],"fact_id"): errors.append("CROSS_SCENARIO_LINK")
    state={}
    def visit(node):
        if state.get(node)==1: errors.append("CYCLE"); return
        if state.get(node)==2: return
        state[node]=1
        for parent in parents[node]: visit(parent)
        state[node]=2
    for node in by_id: visit(node)
    def ancestors(mid):
        seen=set(); stack=list(parents[mid])
        while stack:
            item=stack.pop()
            if item in seen: continue
            seen.add(item); stack.extend(parents[item])
        return seen
    probe_ids={_field(c,"message_id") for c in calls if _field(c,"condition") in {"awareness","relay-awareness"}}
    for call in calls:
        condition=_field(call,"condition",""); mid=_field(call,"message_id")
        if condition in {"relay-stale-replay","relay-current-replay"} and mid in by_id and ancestors(mid)&probe_ids:
            errors.append(f"AWARENESS_CONTAMINATION:{mid}")
    provenance={_field(p,"e2_replay_message_id"):p for p in replay_provenance}
    if len(provenance)!=len(replay_provenance): errors.append("DUPLICATE_REPLAY_PROVENANCE")
    for mid,row in provenance.items():
        message=by_id.get(mid)
        if (message is None or _field(row,"relation")!="exact_replay" or
            _field(row,"content_hash")!=_field(message,"content_hash") or
            _field(message,"raw_content") is None): errors.append(f"INVALID_REPLAY_PROVENANCE:{mid}")
        origin=by_id.get(_field(row,"e1_message_id"))
        if origin is not None and (_field(origin,"raw_content")!=_field(message,"raw_content") or
                                   _field(origin,"content_hash")!=_field(message,"content_hash")):
            errors.append(f"CHANGED_REPLAY_CONTENT:{mid}")
        arm="stale" if _field(row,"e1_condition")=="stale-peer" else "current" if _field(row,"e1_condition")=="current-peer" else None
        if arm is None or f":{arm}:replay" not in mid: errors.append(f"SWAPPED_REPLAY_ARM:{mid}")
    for sid, plan in topology.items():
        parent=_field(plan,"parent",plan); parent_hash=_field(parent,"snapshot_hash",_field(plan,"parent_snapshot_hash"))
        branches=_field(plan,"branches",plan)
        for name in ("awareness","stale","current"):
            branch=_field(branches,name)
            if branch is None or _field(branch,"parent_snapshot_hash")!=parent_hash: errors.append(f"WRONG_RELAY_PARENT:{sid}:{name}")
        awareness=_field(branches,"awareness")
        if awareness is not None and (_field(awareness,"message_ids",()) or _field(awareness,"visible_message_ids",())):
            errors.append(f"AWARENESS_CONTAMINATION:{sid}")
    tier_b=[]; tier_c=[]
    final_ids={v.get("message_id") for case in final_votes for v in case.get("votes",())}
    for case in final_votes:
        cid=case.get("system_case_id"); votes=tuple(case.get("votes",()))
        if case.get("communication_edges"): errors.append(f"FINAL_READOUT_COMMUNICATION:{cid}")
        if len(votes)!=3 or len({v.get("author") for v in votes})!=3: errors.append(f"INCOMPLETE_FINAL_VOTES:{cid}")
        if any(v.get("phase_id")!=case.get("final_vote_phase_id") for v in votes): errors.append(f"MIXED_FINAL_PHASE:{cid}")
        if any(v.get("condition")=="source-stale-seed" or v.get("pre_update",False) for v in votes): errors.append(f"PREUPDATE_SEED_VOTE:{cid}")
        for vote in votes:
            message=by_id.get(vote.get("message_id"))
            if message and set(_field(message,"parent_message_ids",())) & final_ids:
                errors.append(f"FINAL_READOUT_COMMUNICATION:{cid}")
        relations={_field(e,"relation") for e in edges if _field(e,"child_message_id") in {v.get("message_id") for v in votes}}
        if "tier_b_stale_majority_member" in relations: tier_b.append(cid)
        if "tier_c_complete_path" in relations: tier_c.append(cid)
    # Relation-specific claims must be backed by the complete ordered vocabulary.
    present={_field(e,"relation") for e in edges}
    if "tier_c_complete_path" in present:
        required=E2_RELATIONS-{"tier_b_stale_majority_member"}
        if not required<=present: errors.append("INCOMPLETE_TIER_C_PATH")
    return {"passed":not errors,"errors":tuple(errors),
        "paths":{mid:tuple(sorted(ancestors(mid))) for mid in by_id},
        "tier_b_system_case_ids":tuple(tier_b),"tier_c_system_case_ids":tuple(tier_c)}
