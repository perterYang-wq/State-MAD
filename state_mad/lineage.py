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
