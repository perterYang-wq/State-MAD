# State-MAD Experiment Plan — Stage-03 Review

Status: FINAL REVIEW
Stage: 03-Experiment-Plan-Review
Authority: `RESEARCH_CONTRACT.md` > frozen human revisions > `02_EXPERIMENT_PLAN_DRAFT.md` > reference papers

## 1. Review Verdict

**Verdict: PASS WITH MINOR NOTES — READY FOR REPOSITORY AUDIT**

The blocking issue from the earlier review is resolved: `RESEARCH_CONTRACT.md` now exists as a formal frozen contract, and `02_EXPERIMENT_PLAN_DRAFT.md` exists as the Stage-02 plan. The draft is fundamentally aligned with the Research Contract and preserves the intended narrow scope: phenomenon/controlled measurement is primary; mitigation is secondary; the first phase remains one open 7B/8B model, at most three Agents, at most two main debate rounds, 16 sanity scenarios, 40 pilot scenarios, deterministic grading, cached trajectories, and a 0.8M-token planning ceiling.

Stage 03 does **not** redesign the project. It makes the minimum causal, metric, replay, statistical, and implementation-boundary corrections required before Repository Audit.

## 2. Source and Authority Check

The review used the following project artifacts as authoritative inputs:

- `RESEARCH_CONTRACT.md` — formal frozen contract and highest authority.
- `02_EXPERIMENT_PLAN_DRAFT.md` — Stage-02 draft to be reviewed and superseded.
- `01_ARS_NOVELTY_REVIEW.md` — archived risk/novelty analysis, subordinate to the Research Contract.
- MAD-M² — engineering baseline and erroneous-memory comparison.
- StateMem — evolving-state/supersession and controlled state-tracking reference.
- Post-Removal Logical Residue — persistence/contagion comparison.
- Wrong but Useful — fixed-message caching and downstream replay reference.
- When Identity Skews Debate — identity/conformity confound reference.
- Hear Both Sides — message-retention reference; not added as a baseline.

The frozen Research Contract explicitly defines propagation as a causal stale-adoption effect in a current-aware target and RQ3 as correction-visible residue. It also forbids presenting version/provenance/supersession primitives as method novelty.

## 3. Parts of Stage 02 Preserved

The following Stage-02 components are preserved because they are causally appropriate and consistent with the Research Contract:

1. Behavioral current-awareness gate.
2. Immutable target and relay snapshots.
3. Awareness-probe output never writes back into treatment history.
4. Same-snapshot branching.
5. Four E1 arms: no-peer / current-peer / stale-peer / static-wrong.
6. Current-peer as the primary E1 matched control.
7. Closed-pool deterministic grading with CURRENT / STALE / STATIC_WRONG / OTHER.
8. Once-correct stale seed generated/cached before supersession.
9. Deterministic state identity and supersession.
10. E1 → E2 → E3 cache inheritance.
11. E3 A/B/C correction conditions and clean matched reference.
12. Four E4 methods only: Vanilla MAD / MAD-M² / State-MAD / sham.
13. Historical raw-message preservation rather than physical stale-message deletion.
14. Immutable message cache and downstream-only replay.
15. Structured lineage logging.
16. Explicit pilot STOP / GO gates.
17. 16-scenario E0 and 40-scenario pilot.
18. Hard 0.8M-token planning ceiling.
19. Falsification and claim shrinkage as valid outcomes.

## 4. Required Revisions Applied

### Revision 1 — SRR is conditional, not population-level

Stage 02 used `SRR` over cases in which the primary target had already adopted stale state. The metric is renamed and frozen as:

**Conditional Secondary Retransmission Rate (`SRR_cond`)**

\[
SRR_{cond}
=
P(R\rightarrow v_{old}\mid T\text{ is an eligible causal primary stale adopter and retransmits its cached stale output})
\]

An eligible **causal primary stale adopter** is operationalized by a paired treatment-only transition:

- T is current-aware before exposure;
- stale-peer branch outputs `v_old`;
- matched current-peer branch does **not** output `v_old`;
- both branches originate from the same target snapshot.

This prevents the phrase “causal stale adopter” from meaning merely “stale happened after treatment.”

E2 now estimates a conditional downstream effect among naturally observed primary adopters. It is **not** an unconditional probability that arbitrary stale exposure propagates two hops in the population.

### Revision 2 — E2 matched replay tightened

For every eligible primary adopter, Relay treatment and control use the **same relay snapshot**.

Treatment:

- exact cached Target output from the stale-peer branch.

Control:

- exact cached Target output from the matched current-peer branch.

Required invariants:

- Relay independently passes its own current-awareness probe before exposure;
- same relay snapshot;
- same prompt template;
- same message position/order;
- same source/identity label;
- same decoding configuration;
- no upstream regeneration.

Because exact LLM outputs can otherwise introduce style/length confounds, the controlled benchmark must use a strict structured response skeleton for E1 Target messages used in E2. E2 causal matched replay is eligible only when both cached Target outputs satisfy the same canonical output skeleton, differing in the factual/answer value rather than free-form reasoning style. A format mismatch is logged and excluded from the E2 matched causal denominator; it is never manually rewritten.

If this makes E2 too sparse, the correct Stage-03 outcome is `NOT ESTIMABLE AT PILOT SCALE`, not data expansion.

### Revision 3 — False stale consensus is three-tiered

The previous two-level FSCR definition is replaced by three explicitly different outcomes:

**A. Ordinary Stale Consensus**

Final post-update majority equals `v_old`, regardless of why.

**B. Exposure-Induced False Stale Consensus**

Final post-update majority equals `v_old`, and at least one current-aware Agent in that majority exhibits the E1 paired treatment-only causal stale transition.

**C. Retransmission-Supported False Stale Consensus**

A complete mechanically reconstructed lineage exists:

`Source stale seed → current-aware Target → paired causal stale adoption → exact cached Target stale retransmission → current-aware Relay → Relay stale adoption → final majority = v_old`.

Only C can support wording that secondary retransmission **contributes to** a stale majority. Even C is a path-supported conditional analysis, not a population-level mediation effect.

If C is sparse in the pilot, it remains diagnostic and cannot become a headline claim.

### Revision 4 — Final voting phase corrected

Every vote used for an FSCR numerator must come from the **same designated post-update decision phase**.

The pre-update once-correct `m_old` is an exposure message only. It can never be counted as Source's final vote.

The run schema therefore requires a `decision_phase_id` / `final_vote_phase_id`, and FSCR is valid only when all three votes share that phase and occur after the authoritative update.

### Revision 5 — Value/surface counterbalancing added

Random answer-option position alone does not control lexical/value preference. The scenario compiler must now counterbalance the value pool over semantic roles.

For a three-value pool such as `Amber / Cobalt / Silver`, each surface value must appear as CURRENT, STALE, and STATIC_WRONG across scenarios as evenly as integer counts permit. For the 40-scenario pilot, role counts per surface value should differ by at most 1 within the relevant template strata. Answer option positions are counterbalanced independently.

The scenario schema records `counterbalance_group`, `surface_value`, and `semantic_role` so the balance can be validated before model calls.

### Revision 6 — stale-peer and static-wrong message style matched

Stale and static-wrong peer messages must use the same deterministic message skeleton, source label, confidence style, syntax, answer format, and approximately identical token footprint. Only factual value and the underlying symbolic temporal history differ.

Free-form long stale reasoning cannot be compared to a short templated static-wrong statement.

The preferred first-phase design is a strict structured claim/answer skeleton so the comparison isolates temporal status rather than prose style.

### Revision 7 — E4 renamed and oracle boundary made explicit

The Stage-02 `State-MAD minimal mitigation` is formally named:

**Controlled Supersession-Aware Mitigation**

This name is preferred to “Oracle State-MAD” because it describes the experimental role without implying that oracle detection is the contribution. The frozen plan must nevertheless state the assumption explicitly:

> The mitigation assumes that state identity and supersession labels are available from the controlled benchmark. It evaluates the value of explicit state-validity awareness, not the ability to infer stale state from unrestricted natural language.

Therefore E4 is not evidence for a deployable stale-state detector, semantic parser, or general memory architecture.

### Revision 8 — awareness probe vs no-peer call audited

The Stage-02 description left the exact prompt relationship ambiguous. Reusing the no-peer decision as the eligibility probe would make the no-peer stale rate mechanically zero among eligible cases and would condition the no-peer outcome on itself.

The frozen design therefore requires:

- `awareness_probe_prompt != no_peer_decision_prompt`;
- same pre-exposure snapshot;
- same state evidence;
- same decoding configuration;
- different task wording/purpose.

The awareness probe is an access/knowledge check (“which value is the latest authoritative state accessible to you?”). The no-peer branch remains the ordinary decision question used by all E1 arms.

This extra call is necessary for causal validity of the no-peer secondary contrast. Probe output never writes back to any treatment/control history.

If Repository Audit finds that the actual implementation uses byte-identical prompts after all, those calls must be deduplicated and the no-peer contrast must be treated as selected/degenerate rather than independently measured.

### Revision 9 — pilot gates separated from inferential statistics

All thresholds such as 0.05, 0.10, 2 cases, 5 cases, 8 cases, and 10 cases are operational **Pilot Go / No-Go Gates** only.

They are not p-value thresholds, statistical significance criteria, or guarantees of power.

Formal 100–300-scenario inference is offline over cached paired outcomes, using:

- paired scenario bootstrap confidence intervals;
- McNemar's test for paired binary outcomes when its assumptions and counts are appropriate;
- exact paired sign/binomial or paired permutation tests when discordant counts are small or the statistic is not a simple binary pair.

No statistical analysis may trigger new LLM calls.

### Revision 10 — E0 scope re-frozen

E0 remains 16 scenarios and tests only:

1. the model can use `v_new`;
2. the current-awareness gate is usable;
3. stale-peer exposure can produce non-zero regression.

E0 does not test full consensus, long propagation, complex recovery, or the full mitigation matrix.

If no stale regression is observed, **STOP before Pilot**.

### Revision 11 — E3 correction-visible denominator tightened

CVRR numerator requires all of:

- `target_prior_stale_adopter == true`;
- `source_corrected == true`;
- source no longer treats `v_old` as current;
- `correction_delivered == true`;
- `correction_accessible_at_decision == true`;
- target post-correction decision equals `v_old`.

CVRR denominator contains only eligible prior stale adopters satisfying all visible-correction checks.

The clean reference remains:

`never-stale-adopted + same correction + same visibility + same decision prompt`.

Re-infection is executed only for naturally occurring C-condition residual cases. No infected target may be manufactured.

### Revision 12 — E4 sham control tightened

Sham metadata must match, as closely as tokenizer permits:

- number of fields;
- field positions;
- formatting;
- source messages;
- prompt-block token footprint.

Sham field names and values are opaque and may not include temporal-validity semantics such as `current`, `stale`, `superseded`, `active`, `latest`, `valid`, or `invalid`.

Any token mismatch must be recorded; the implementation should target exact tokenizer-count matching or the smallest achievable mismatch without changing source content.

### Revision 13 — Cache/replay contract expanded

`GENERATE ONCE` is frozen for:

- symbolic scenario;
- answer mapping;
- once-correct old source message;
- current-peer message;
- static-wrong peer message;
- target snapshot;
- relay snapshot;
- E1 branch outputs;
- source correction message;
- E2 eligible Target stale/current matched outputs;
- E3 residual message if naturally produced;
- E4 Round-1 pool.

Changing visibility, order, identity label, metadata rendering, mask, or correction visibility never authorizes upstream regeneration. Only the downstream Agent whose input actually changes may be rerun.

### Revision 14 — Logging/lineage contract expanded

The frozen structured record must include at least:

- scenario_id
- fact_id
- version_id
- message_id
- author
- parent_message_ids
- recipient
- generation-time validity
- decision-time validity
- current-aware status
- source correction status
- correction visible/accessibility status
- prompt hash
- snapshot hash
- model
- revision
- seed
- config
- raw output
- parsed output
- token usage
- cache hit

Additional mechanical fields are allowed when they support the frozen design, including `pair_id`, `condition`, `decision_phase_id`, `eligibility_flags`, and `exclusion_reason`.

Every adoption, retransmission, consensus, residue, and re-infection claim must be reconstructable from these records without researcher text interpretation.

## 5. Statistical / Causal Interpretation Review

### E1

E1 is the primary causal experiment. Because each arm forks from the same pre-exposure snapshot and the primary contrast is stale-peer vs current-peer, CSAE is a paired treatment contrast among targets that independently passed the awareness gate.

The static-wrong and no-peer contrasts remain secondary diagnostics.

### E2

E2 conditions on an E1 post-treatment outcome. Therefore `SRR_cond` is **not** a population average second-hop propagation rate.

Within the selected primary-adopter subset, Relay exposure can still be tested with a matched same-snapshot stale-output vs current-output replay. The causal scope is downstream and conditional on that selected subset.

### Consensus

Ordinary consensus is descriptive. Exposure-induced consensus adds a verified causal-adoption member. Retransmission-supported consensus adds a verified two-hop path. These path classifications do not by themselves estimate a population-level mediation effect of retransmission on consensus.

### E3

CVRR is a conditional persistence rate among prior stale adopters with verified visible correction. It does not estimate the prevalence of residue among all Agents or all scenarios.

### E4

Mitigation comparisons are paired within a frozen Round-1 pool. The primary mechanism test is State-MAD vs sham under matched input footprint; Vanilla and MAD-M² are additional frozen baselines.

## 6. Reviewer-Style Final Attack

### Reviewer A — MAD-M²

**Objection:** “stale is just another wrong message.”

**Is the frozen experiment sufficient?**  
Conditionally yes. E1 explicitly separates once-correct-then-superseded stale from never-correct static wrong, verifies the target already has current state, uses a matched current-peer control, and E4 includes MAD-M².

**Remaining vulnerability:**  
At decision time both stale and static-wrong values are wrong. If E1 finds no stale-specific behavioral difference and MAD-M² handles both equally well, the novelty must shrink to a temporal problem formulation rather than a distinct behavioral mechanism.

**Defensible wording:**  
“Once-correct but later-superseded messages constitute a temporally defined failure class; in our controlled current-aware setting, stale peer exposure produces the measured paired adoption/recovery behavior.”

**NOT allowed:**  
“Stale information is inherently more harmful than erroneous information,” or “MAD-M² cannot address stale information,” unless the direct experiments support those statements.

**Severity after revision:** High but non-fatal.

### Reviewer B — StateMem

**Objection:** “you are using oracle supersession labels and merely replicating StateMem across Agents.”

**Is the frozen experiment sufficient?**  
Yes for the intended phenomenon claim, not for a method-novelty claim. The frozen unit is communication-mediated Agent/message/version transition, not centralized state tracking, and E2/E3 require secondary carriers and correction-visible persistence.

**Remaining vulnerability:**  
The controlled benchmark supplies the state identity and supersession relation. Thus the mitigation says nothing about automatic stale-state detection in unrestricted language.

**Defensible wording:**  
“We use benchmark-provided supersession labels to isolate whether explicit state-validity awareness changes communication-mediated stale adoption and recovery.”

**NOT allowed:**  
“We introduce a new state memory architecture,” “we solve stale-state detection,” “we automatically infer supersession in natural language,” or “we are the first to track evolving state across Agents.”

**Severity after revision:** High but non-fatal.

### Reviewer C — Post-Removal Logical Residue

**Objection:** “secondary residue is already post-removal contagion.”

**Is the frozen experiment sufficient?**  
Yes to distinguish the planned claim, because RQ3 requires legitimate factual supersession, source correction, correction delivery, correction accessibility at target decision time, and a clean matched reference. Source removal alone is not evidence.

**Remaining vulnerability:**  
The broad persistence/contagion pattern is not new. The contribution must remain the narrower correction-visible stale-state mechanism.

**Defensible wording:**  
“After a legitimate state update and visible correction from the original source, previously induced secondary stale copies can remain behaviorally active under the evaluated controlled setting.”

**NOT allowed:**  
“We are the first to discover post-source residue or contagion in MAD.”

**Severity after revision:** High but non-fatal.

### Reviewer D — Causal inference

**Objection:** “your second-hop and consensus analysis conditions on post-treatment outcomes and overclaims causality.”

**Is the frozen experiment sufficient?**  
Yes after the Stage-03 correction. `SRR_cond` explicitly conditions on observed paired primary adopters; Relay treatment/control is matched from the same relay snapshot. Consensus is split into descriptive/path-supported tiers.

**Remaining vulnerability:**  
The selected primary-adopter subgroup is post-treatment. The study cannot estimate an unconditional two-hop population ATE or a causal mediation effect from retransmission to final consensus without a different design, which is outside the frozen scope.

**Defensible wording:**  
“Among observed paired primary stale adopters, their cached stale retransmissions can induce downstream stale adoption relative to matched cached current-branch outputs.”  
“Retransmission-supported stale consensus was observed along mechanically verified paths.”

**NOT allowed:**  
“Stale exposure has an unconditional two-hop propagation probability of SRR_cond,” or “secondary retransmission causally increases the population false-consensus rate.”

**Severity after revision:** Non-fatal.

No reviewer objection is Fatal under the frozen claim boundaries.

## 7. Remaining Risks / Minor Notes

1. Strict E2 output-skeleton matching may reduce eligible cases. This is acceptable; report `NOT ESTIMABLE AT PILOT SCALE` rather than relaxing the match after seeing outcomes.
2. Repository Audit must verify whether the MAD-M² codebase can support immutable snapshot/branch semantics without accidental history mutation. This is an implementation audit question, not a reason to redesign the experiment now.
3. MAD-M² adapter details must reuse the official code path as far as possible; exact variant/configuration is to be mapped during Repository Audit, not invented in Stage 03.
4. The final 100–300-scenario inferential analysis must use the pre-declared paired units and must not convert pilot gates into p-value criteria.

## 8. Final Decision

`RESEARCH_CONTRACT.md` exists and is authoritative. The required causal, conditional-denominator, consensus, counterbalancing, oracle-boundary, replay, statistical, and logging corrections have been incorporated into the frozen plan.

The project may now proceed only to:

`04-Repository-Audit → Implementation Map → Codex implementation`

It may **not** skip Repository Audit and begin patching the repository.

**PASS WITH MINOR NOTES — READY FOR REPOSITORY AUDIT**
