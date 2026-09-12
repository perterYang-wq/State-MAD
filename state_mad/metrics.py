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


def evaluate_e2_retransmission(rows, eligibility=None, topology=None, integrity=None):
    """Pure conditional second-hop report; completed invalid answers are votes."""
    rows=tuple(rows); eligibility=eligibility or {}; topology=topology or {}; integrity=integrity or {}
    candidate_ids=tuple(eligibility.get("candidate_ids", sorted({r["scenario_id"] for r in rows})))
    e1_ids=tuple(eligibility.get("eligible_ids", candidate_ids)); by={sid:{} for sid in candidate_ids}
    for row in rows: by.setdefault(row["scenario_id"],{})[row["condition"]]=row
    aware=[]; completed=[]; included=[]; excluded={}
    for sid in candidate_ids:
        reasons=[]; arms=by.get(sid,{})
        if sid not in e1_ids: reasons.append("NOT_E1_ELIGIBLE")
        exact=integrity.get(sid,{}).get("exact_replay",arms.get("exact_replay",True))
        if not exact: reasons.append("INVALID_EXACT_REPLAY")
        awareness=arms.get("relay-awareness",arms.get("awareness",{}))
        if awareness.get("answer_class")=="CURRENT": aware.append(sid)
        else: reasons.append("RELAY_NOT_CURRENT_AWARE")
        stale=arms.get("relay-stale-replay",arms.get("stale",{})); current=arms.get("relay-current-replay",arms.get("current",{}))
        complete=all(x and x.get("answer_class") is not None and not x.get("infrastructure_failure",False) for x in (stale,current))
        if complete: completed.append(sid)
        else: reasons.append("INCOMPLETE_MATCHED_PAIR")
        parent=topology.get(sid,{}); same=parent.get("same_parent", stale.get("parent_snapshot_hash") is not None and stale.get("parent_snapshot_hash")==current.get("parent_snapshot_hash"))
        if not same: reasons.append("PARENT_MISMATCH")
        if integrity.get(sid,{}).get("infrastructure_failure",False): reasons.append("INFRASTRUCTURE_FAILURE")
        if reasons: excluded[sid]=tuple(dict.fromkeys(reasons))
        else: included.append(sid)
    treatment=sum(by[s].get("relay-stale-replay",by[s].get("stale",{})).get("answer_class")=="STALE" for s in included)
    control=sum(by[s].get("relay-current-replay",by[s].get("current",{})).get("answer_class")=="STALE" for s in included)
    n=len(included); tr=treatment/n if n else None; cr=control/n if n else None
    if n<8: gate="NOT ESTIMABLE AT PILOT SCALE"
    elif treatment>=2 and tr-cr>0: gate="SECOND-HOP-POSITIVE PILOT"
    elif n>=10 and treatment==0: gate="SECONDARY RETRANSMISSION UNSUPPORTED"
    else: gate="NO POSITIVE/UNSUPPORTED GATE CONCLUSION"
    return {"candidate_ids":candidate_ids,"candidate_n":len(candidate_ids),"e1_eligible_ids":e1_ids,
        "e1_eligible_n":len(e1_ids),"relay_aware_ids":tuple(aware),"relay_aware_n":len(aware),
        "completed_matched_pair_ids":tuple(completed),"completed_matched_pair_n":len(completed),
        "included_denominator_ids":tuple(included),"included_denominator_n":n,"excluded":excluded,
        "stale_treatment_count":treatment,"stale_treatment_rate":tr,
        "current_control_stale_count":control,"current_control_stale_rate":cr,
        "paired_difference":None if n==0 else tr-cr,"srr_cond":tr,"gate_4":gate,"interpretation":"conditional"}


def evaluate_e2_fscr(final_votes, lineage_report=None, system_eligibility=None):
    """Evaluate all three synchronized, diagnostic E2 FSCR tiers."""
    lineage_report=lineage_report or {}; system_eligibility=system_eligibility or {}
    complete=[]; excluded={}; ordinary=[]; exposure=[]; retransmission=[]
    tier_b=set(lineage_report.get("tier_b_system_case_ids",()))
    tier_c=set(lineage_report.get("tier_c_system_case_ids",()))
    for case in final_votes:
        cid=case["system_case_id"]; votes=tuple(case.get("votes",()))
        reasons=[]
        if not case.get("complete",False) or len(votes)!=3: reasons.append("INCOMPLETE_FINAL_PHASE")
        if len({v.get("author") for v in votes})!=3 or {v.get("author") for v in votes}!={"source","target","relay"}: reasons.append("INVALID_FINAL_ROLES")
        if any(v.get("phase_id")!=case.get("final_vote_phase_id") for v in votes): reasons.append("MIXED_FINAL_PHASE")
        if any(v.get("condition")=="source-stale-seed" or v.get("pre_update",False) for v in votes): reasons.append("PREUPDATE_SEED_VOTE")
        if case.get("communication_edges"): reasons.append("FINAL_READOUT_COMMUNICATION")
        if system_eligibility and not system_eligibility.get(cid,True): reasons.append("SYSTEM_INELIGIBLE")
        if reasons: excluded[cid]=tuple(dict.fromkeys(reasons)); continue
        complete.append(cid); stale={v.get("author") for v in votes if v.get("answer_class")=="STALE"}
        if len(stale)>=2:
            ordinary.append(cid)
            causal=set(case.get("causal_adopter_roles",()))
            if cid in tier_b or bool(stale & causal): exposure.append(cid)
            path=case.get("tier_c_complete_path",False) or cid in tier_c
            if path: retransmission.append(cid)
    n=len(complete)
    def metric(ids): return {"numerator_ids":tuple(ids),"numerator_n":len(ids),"denominator_ids":tuple(complete),"denominator_n":n,"rate":len(ids)/n if n else None}
    return {"ordinary_fscr":metric(ordinary),"exposure_induced_fscr":metric(exposure),
        "retransmission_supported_fscr":metric(retransmission),"excluded":excluded,
        "interpretation":"conditional/diagnostic","independent_retransmission_claim":False}
