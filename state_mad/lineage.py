from collections import defaultdict

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
    for condition,mid in decisions.items():
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
