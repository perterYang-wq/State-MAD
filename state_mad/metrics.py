def summarize_tokens(records):
    return {"calls":len(records),"hits":sum(r.cache_status=="hit" for r in records),"generated_input_tokens":sum(r.generated_input_tokens for r in records),"generated_output_tokens":sum(r.generated_output_tokens for r in records),"generated_total_tokens":sum(r.generated_total_tokens for r in records)}
def evaluate_e0(rows, scenario_ids):
    by={sid:{} for sid in scenario_ids}
    for r in rows: by.setdefault(r["scenario_id"],{})[r["condition"]]=r
    aware=[sid for sid,x in by.items() if x.get("awareness",{}).get("answer_class")=="CURRENT"]
    eligible=[sid for sid in aware if "current-peer" in by[sid] and "stale-peer" in by[sid]]
    regressions=[sid for sid in eligible if by[sid]["current-peer"]["answer_class"]!="STALE" and by[sid]["stale-peer"]["answer_class"]=="STALE"]
    cur_stale=sum(by[s]["current-peer"]["answer_class"]=="STALE" for s in eligible); stale_stale=sum(by[s]["stale-peer"]["answer_class"]=="STALE" for s in eligible)
    awareness=len(aware)/len(scenario_ids) if scenario_ids else 0; csae=(stale_stale-cur_stale)/len(eligible) if eligible else None
    status="INCOMPLETE"; reason="missing eligible pairs"
    if awareness<.5: status,reason="STOP","awareness below 50%"
    elif not regressions: status,reason="STOP","zero confirmed stale regressions"
    elif csae is not None and 0<csae<.1: status,reason="HUMAN_DECISION","ambiguous CSAE"
    elif awareness>=.8 and len(regressions)>=3 and csae is not None and csae>=.1: status,reason="PASS_TARGET","Gate 1 targets met"
    return {"status":status,"reason":reason,"awareness_rate":awareness,"eligible":eligible,"confirmed_regressions":regressions,"csae":csae,"sar":{"current-peer":cur_stale/len(eligible) if eligible else None,"stale-peer":stale_stale/len(eligible) if eligible else None}}
