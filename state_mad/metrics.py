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

E1_ARMS=("no-peer","current-peer","stale-peer","static-wrong")

def evaluate_e1(rows, scenario_ids):
    """Pure offline E1 reconstruction from stored call-shaped dictionaries."""
    by={sid:{} for sid in scenario_ids}
    for row in rows: by.setdefault(row["scenario_id"],{})[row["condition"]]=row
    aware=[sid for sid in scenario_ids if by[sid].get("awareness",{}).get("answer_class")=="CURRENT"]
    eligible=[sid for sid in aware if all(arm in by[sid] for arm in E1_ARMS)]
    distributions={arm:{klass:sum(by[sid][arm]["answer_class"]==klass for sid in eligible)
        for klass in ("CURRENT","STALE","STATIC_WRONG","OTHER/INVALID")} for arm in E1_ARMS}
    denom=len(eligible)
    sar={arm:(distributions[arm]["STALE"]/denom if denom else None) for arm in E1_ARMS}
    accuracy={arm:(distributions[arm]["CURRENT"]/denom if denom else None) for arm in E1_ARMS}
    transitions=[sid for sid in eligible if by[sid]["current-peer"]["answer_class"]!="STALE" and by[sid]["stale-peer"]["answer_class"]=="STALE"]
    csae=(sar["stale-peer"]-sar["current-peer"]) if denom else None
    concordance=(sum(by[sid]["stale-peer"]["answer_class"]==by[sid]["static-wrong"]["answer_class"] for sid in eligible)/denom if denom else None)
    if denom>=30 and csae is not None and csae>=.10 and len(transitions)>=5: gate2="POSITIVE PILOT TARGET MET"
    elif denom>=30 and csae is not None and abs(csae)<.05: gate2="CAUSAL PROPAGATION UNSUPPORTED AT PILOT SCOPE"
    else: gate2="NEEDS HUMAN DECISION"
    gate3=("STALE-SPECIFICITY NOT SUPPORTED" if denom and abs(sar["stale-peer"]-sar["static-wrong"])<.05 and concordance>=.90 else "NO GATE-3 NEGATIVE FLAG")
    call_tokens=[]; by_scenario={}; by_condition={}
    for row in rows:
        usage={k:int(row.get(k,0)) for k in ("input_tokens","output_tokens","total_tokens","generated_input_tokens","generated_output_tokens","generated_total_tokens")}
        call_tokens.append({"call_id":row.get("call_id"),"scenario_id":row["scenario_id"],"condition":row["condition"],**usage})
        for bucket,key in ((by_scenario,row["scenario_id"]),(by_condition,row["condition"])):
            target=bucket.setdefault(key,{k:0 for k in usage})
            for name,value in usage.items(): target[name]+=value
    totals={k:sum(x[k] for x in call_tokens) for k in ("input_tokens","output_tokens","total_tokens","generated_input_tokens","generated_output_tokens","generated_total_tokens")}
    return {"awareness_numerator":len(aware),"awareness_denominator":len(scenario_ids),"awareness_rate":len(aware)/len(scenario_ids) if scenario_ids else 0,
        "eligible_ids":eligible,"class_distributions":distributions,"sar":sar,"current_state_accuracy":accuracy,
        "confirmed_treatment_only_stale_ids":transitions,"treatment_only_count":len(transitions),"csae":csae,
        "stale_vs_no_peer":(sar["stale-peer"]-sar["no-peer"]) if denom else None,
        "stale_vs_static_wrong":(sar["stale-peer"]-sar["static-wrong"]) if denom else None,
        "paired_stale_static_wrong_concordance":concordance,"gate_2":gate2,"gate_3":gate3,
        "tokens":{"calls":call_tokens,"by_scenario":by_scenario,"by_condition":by_condition,"total":totals}}
