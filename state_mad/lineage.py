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
    call_keys=[(_field(c,"scenario_id"),_field(c,"condition")) for c in calls]
    if len(call_keys)!=len(set(call_keys)): errors.append("DUPLICATE_CALL_CONDITION")
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
    actual_parents={mid:tuple(_field(message,"parent_message_ids",())) for mid,message in by_id.items()}
    def actual_ancestors(mid):
        seen=set(); stack=list(actual_parents.get(mid,()))
        while stack:
            item=stack.pop()
            if item in seen: continue
            seen.add(item); stack.extend(actual_parents.get(item,()))
        return seen
    for call in calls:
        condition=_field(call,"condition",""); mid=_field(call,"message_id")
        if condition in {"relay-stale-replay","relay-current-replay"} and mid in by_id and actual_ancestors(mid)&probe_ids:
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
    system_cases={}
    final_ids={v.get("message_id") for case in final_votes for v in case.get("votes",())}
    final_final_edges=[e for e in edges if _field(e,"parent_message_id") in final_ids and _field(e,"child_message_id") in final_ids]
    for edge in final_final_edges:
        errors.append(f"FINAL_TO_FINAL_EDGE:{_field(edge,'parent_message_id')}:{_field(edge,'child_message_id')}")
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
        sid=case.get("scenario_id"); case_errors=[]
        scenario_calls=[c for c in calls if _field(c,"scenario_id")==sid]
        roots={_field(c,"message_id") for c in scenario_calls}|{v.get("message_id") for v in votes}
        scenario_mids=set(roots)
        for root in tuple(roots):
            if root in by_id: scenario_mids.update(ancestors(root))
        scenario_edges=[e for e in edges if _field(e,"parent_message_id") in scenario_mids and _field(e,"child_message_id") in scenario_mids]
        relations={_field(e,"relation") for e in scenario_edges}
        by_condition={_field(c,"condition"):c for c in scenario_calls}
        stale_majority=sum(v.get("answer_class")=="STALE" for v in votes)>=2
        paired=(by_condition.get("stale-peer") is not None and by_condition.get("current-peer") is not None and
            _field(by_condition["stale-peer"],"answer_class")=="STALE" and
            _field(by_condition["current-peer"],"answer_class")!="STALE" and
            _field(by_condition.get("awareness"),"answer_class")=="CURRENT")
        edge_set={(_field(e,"parent_message_id"),_field(e,"child_message_id"),_field(e,"relation")) for e in scenario_edges}
        stale_call=by_condition.get("stale-peer"); current_call=by_condition.get("current-peer"); awareness_call=by_condition.get("awareness")
        target_final=next((v for v in votes if v.get("author")=="target"),{})
        relay_final=next((v for v in votes if v.get("author")=="relay"),{})
        target_branch=stale_call if case.get("arm")=="stale" else current_call
        b_expected={( _field(awareness_call,"message_id"),_field(stale_call,"message_id"),"target_awareness_sibling"),
            (_field(current_call,"message_id"),_field(stale_call,"message_id"),"target_paired_causal_adoption"),
            (_field(target_branch,"message_id"),target_final.get("message_id"),"final_vote_member")}
        complete_case=not case.get("communication_edges") and len(votes)==3 and all(v.get("phase_id")==case.get("final_vote_phase_id") for v in votes)
        b_evaluable=paired and b_expected<=edge_set and complete_case
        target_stale=any(v.get("author")=="target" and v.get("answer_class")=="STALE" for v in votes)
        b_predicate=b_evaluable and case.get("arm")=="stale" and stale_majority and target_stale
        replay=[p for p in replay_provenance if _field(p,"e2_scenario_id")==sid and _field(p,"e1_condition")=="stale-peer"]
        replay_mid=_field(replay[0],"e2_replay_message_id") if len(replay)==1 else None
        replay_ok=(len(replay)==1 and replay_mid in scenario_mids and
            _field(replay[0],"e1_message_id")==_field(stale_call,"message_id"))
        relay_ok=(_field(by_condition.get("relay-awareness"),"answer_class")=="CURRENT" and
            by_condition.get("relay-stale-replay") is not None and by_condition.get("relay-current-replay") is not None)
        stale_peer=(_field(stale_call,"parent_message_ids",()) or (None,))[0]
        rs=by_condition.get("relay-stale-replay"); rc=by_condition.get("relay-current-replay"); ra=by_condition.get("relay-awareness")
        relay_branch=rs if case.get("arm")=="stale" else rc
        seed_message=by_id.get(stale_peer); replay_message=by_id.get(replay_mid)
        semantics_ok=(seed_message is not None and _field(seed_message,"generation_validity")=="current" and
            _field(seed_message,"decision_validity")=="stale" and replay_message is not None and
            _field(replay_message,"generation_validity")=="not_applicable" and _field(replay_message,"decision_validity")=="stale")
        relay_plan=topology.get(sid,{}); relay_parent=_field(relay_plan,"parent",relay_plan)
        relay_branches=_field(relay_plan,"branches",relay_plan); relay_parent_hash=_field(relay_parent,"snapshot_hash",_field(relay_plan,"parent_snapshot_hash"))
        relay_topology_ok=all(_field(_field(relay_branches,name),"parent_snapshot_hash")==relay_parent_hash for name in ("awareness","stale","current"))
        c_expected={(stale_peer,_field(stale_call,"message_id"),"source_stale_seed"),
            (stale_peer,_field(stale_call,"message_id"),"source_to_target_exposure"),*b_expected,
            (_field(stale_call,"message_id"),replay_mid,"e1_target_output_origin"),
            (_field(stale_call,"message_id"),replay_mid,"exact_replay"),
            (replay_mid,_field(rs,"message_id"),"target_to_relay_exposure"),
            (_field(ra,"message_id"),_field(rs,"message_id"),"relay_awareness_sibling"),
            (_field(rc,"message_id"),_field(rs,"message_id"),"relay_matched_sibling"),
            (_field(relay_branch,"message_id"),relay_final.get("message_id"),"final_vote_member")}
        c_evaluable=b_evaluable and relay_ok and replay_ok and semantics_ok and relay_topology_ok and c_expected<=edge_set
        relay_stale=_field(by_condition.get("relay-stale-replay"),"answer_class")=="STALE"
        c_predicate=c_evaluable and case.get("arm")=="stale" and relay_stale and stale_majority
        if not b_evaluable: case_errors.append("TIER_B_NOT_EVALUABLE")
        if not c_evaluable: case_errors.append("TIER_C_NOT_EVALUABLE")
        evidence_ids=tuple(sorted({_field(e,"parent_message_id") for e in scenario_edges}|{_field(e,"child_message_id") for e in scenario_edges}))
        system_cases[cid]={"tier_b_evaluable":b_evaluable,"tier_b_predicate":b_predicate,
            "tier_b_evidence_ids":evidence_ids if b_evaluable else (),"tier_c_evaluable":c_evaluable,
            "tier_c_predicate":c_predicate,"tier_c_evidence_ids":evidence_ids if c_evaluable else (),
            "errors":tuple(case_errors)}
    calls_by_message={_field(c,"message_id"):c for c in calls}
    votes_by_message={v.get("message_id"):(case,v) for case in final_votes for v in case.get("votes",())}
    for edge in edges:
        relation=_field(edge,"relation"); parent=_field(edge,"parent_message_id"); child=_field(edge,"child_message_id")
        if relation=="relay_stale_adoption":
            relay_call=calls_by_message.get(parent); case_vote=votes_by_message.get(child)
            sid=_field(relay_call,"scenario_id"); awareness=next((c for c in calls if _field(c,"scenario_id")==sid and _field(c,"condition")=="relay-awareness"),None)
            if (_field(relay_call,"condition")!="relay-stale-replay" or _field(relay_call,"answer_class")!="STALE" or
                _field(awareness,"answer_class")!="CURRENT" or not case_vote or case_vote[1].get("author")!="relay"):
                errors.append(f"FALSE_RELAY_STALE_ADOPTION:{parent}:{child}")
        elif relation=="tier_b_stale_majority_member":
            case_vote=votes_by_message.get(child)
            if not case_vote or case_vote[1].get("answer_class")!="STALE" or not system_cases.get(case_vote[0].get("system_case_id"),{}).get("tier_b_predicate"):
                errors.append(f"FALSE_TIER_B_CLAIM:{parent}:{child}")
        elif relation=="tier_c_complete_path":
            case_vote=votes_by_message.get(child)
            if not case_vote or not system_cases.get(case_vote[0].get("system_case_id"),{}).get("tier_c_predicate"):
                errors.append(f"FALSE_TIER_C_CLAIM:{parent}:{child}")
    return {"passed":not errors,"errors":tuple(errors),
        "paths":{mid:tuple(sorted(ancestors(mid))) for mid in by_id},
        "system_cases":system_cases,"final_final_edge_count":len(final_final_edges)}
