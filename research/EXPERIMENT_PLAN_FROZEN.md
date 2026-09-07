# State-MAD Experiment Plan — Frozen

Status: FROZEN AFTER STAGE-03 REVIEW
Stage: 03-Experiment-Plan-Review
Supersedes: `02_EXPERIMENT_PLAN_DRAFT.md`
Authority: `RESEARCH_CONTRACT.md` remains higher authority if any conflict is discovered.

This is the only valid experiment plan for Repository Audit and subsequent implementation planning.

# 1 Experimental Principles

## 1.1 Primary scientific target

The first phase studies a failure mechanism, not a new memory architecture:

`current state acquired → stale peer exposure → causal stale adoption → conditional secondary retransmission → possible stale consensus`

and recovery:

`source corrected → correction delivered/visible → residual stale belief? → possible retransmission/re-infection?`

A value that is wrong because the target never received the update is not State-MAD propagation.

## 1.2 Frozen contribution hierarchy

Primary:

- causal stale adoption;
- conditional secondary retransmission;
- false stale consensus characterization;
- correction-visible residual stale belief;
- possible re-infection;
- controlled measurement.

Secondary:

- minimal controlled supersession-aware mitigation.

Not claimed as novel:

- fact/state identity;
- version;
- provenance;
- supersession;
- active/stale/conflicting status;
- state-aware retrieval itself.

## 1.3 First-phase resource envelope

- Model: one open 7B/8B checkpoint; Stage-02 default `Qwen2.5-7B-Instruct` unless Repository Audit finds an availability/compatibility blocker requiring human decision.
- Homogeneous Agents.
- Agents: at most 3.
- Main debate rounds: at most 2.
- Decoding: deterministic first phase (`temperature=0`, fixed config/seed where applicable).
- Sanity: 16 scenarios.
- Pilot: 40 scenarios.
- Deterministic grading; no LLM-as-a-Judge.
- Hard planning ceiling: 0.8M total tokens for sanity + pilot.

Exceeding any frozen resource bound requires `STOP + 需要人工决策`.

## 1.4 Current-awareness gate and immutable branching

For each Target/Relay, create an immutable pre-exposure snapshot after `v_new` is available.

Awareness verification and experimental branches fork from that snapshot. Awareness-probe output must never be written back into branch history.

To keep the no-peer outcome from being selected on itself:

- `awareness_probe_prompt != no_peer_decision_prompt`.

The awareness probe checks whether the Agent can behaviorally access the current authoritative state. The no-peer branch uses the same ordinary decision question used by the peer-exposure branches.

If implementation inspection later reveals byte-identical awareness/no-peer prompts, identical cache keys must be reused, and the no-peer contrast must be flagged as selected/degenerate rather than independently measured.

## 1.5 Closed-pool deterministic grading

Each scenario has a symbolic answer pool mapping to:

- `CURRENT`
- `STALE`
- `STATIC_WRONG`
- `OTHER/INVALID`

The model emits a strict structured answer. Grading is mechanical; raw output is preserved.

## 1.6 Historical preservation

A superseded factual state loses authority as current, but historical raw messages remain preserved for audit. State-MAD does not equate `stale = harmful = delete whole message`.

# 2 Frozen Operational Definitions

Let fact/state identity `f` have:

\[
v_{old}\xrightarrow{\text{superseded by}}v_{new}.
\]

## 2.1 Erroneous memory

Wrong at creation:

\[
m(f,t_0)\neq G(f,t_0).
\]

## 2.2 Stale / superseded memory

Correct at creation, invalid after authoritative update:

\[
m(f,t_0)=G(f,t_0),\quad G(f,t_1)\neq G(f,t_0),\ t_1>t_0.
\]

It is stale when later treated as current.

## 2.3 Current-aware Agent

An Agent is `current_aware=true` only if an independent awareness probe from the pre-exposure snapshot outputs `v_new` before the experimental exposure.

Merely placing `v_new` somewhere in the prompt is insufficient.

## 2.4 Stale peer exposure

A peer message is stale exposure only if:

1. it states `v_old`;
2. it was generated while `v_old` was current, or is a frozen controlled rendering of that once-correct state;
3. an authoritative update later makes `v_new` current;
4. the message is presented after supersession as if relevant to the current decision.

## 2.5 Causal stale adoption

The primary causal operationalization is a paired contrast in a current-aware target from the same snapshot:

\[
CSAE = SAR_{stale-peer}-SAR_{current-peer}.
\]

At the scenario level, an **eligible causal primary stale adopter** for E2 is a paired treatment-only transition:

- stale-peer output = `v_old`;
- matched current-peer output != `v_old`;
- Target was independently current-aware before either exposure.

## 2.6 Conditional secondary retransmission

A Target that satisfies the paired causal-adopter definition becomes an observed secondary carrier when its exact cached stale-branch output is exposed to an independently current-aware Relay.

Relay adoption of `v_old` under this exposure is a second-hop stale adoption.

The corresponding metric is conditional on the observed primary-adopter subset and is not a population propagation rate.

## 2.7 False stale consensus tiers

All votes must be from the same post-update `final_vote_phase_id`.

`m_old` is exposure evidence only and cannot be counted as a final vote.

### A. Ordinary Stale Consensus

Final post-update majority among three Agent decisions equals `v_old`.

### B. Exposure-Induced False Stale Consensus

Ordinary stale consensus plus at least one majority member is a current-aware paired causal stale adopter.

### C. Retransmission-Supported False Stale Consensus

A complete lineage exists:

`Source stale seed → current-aware Target → paired causal stale adoption → exact cached Target stale output → current-aware Relay → Relay stale adoption → post-update majority = v_old`.

Only C can support the limited claim that a verified second-hop retransmission path participates in a false stale majority.

## 2.8 Correction-visible residue

RQ3 evidence requires all:

- `target_prior_stale_adopter=true`;
- Source has obtained `v_new`;
- Source no longer treats `v_old` as current;
- `source_corrected=true` is behaviorally verified;
- correction is delivered;
- correction is accessible to Target at decision time;
- measurement occurs afterward.

Target output `v_old` after these checks is a correction-visible residual stale outcome.

## 2.9 Re-infection

A Source that was verified corrected to `v_new` later outputs `v_old` after exposure to an exact cached residual stale message from a secondary Agent, relative to a matched same-corrected-snapshot control without that residual message.

# 3 Metrics

## 3.1 SAR — Stale Adoption Rate

For arm `a`:

\[
SAR_a = \frac{\#\{\text{current-aware eligible targets with post-exposure output }v_{old}\}}{\#\{\text{current-aware eligible targets with completed arm }a\}}.
\]

Eligibility:

- awareness probe = `v_new`;
- experimental call completed.

Exclusion:

- infrastructure failure only.

Invalid model format is `OTHER/INVALID`, not denominator deletion.

## 3.2 CSAE — Causal Stale Adoption Effect

Primary:

\[
CSAE= SAR_{stale-peer}-SAR_{current-peer}.
\]

Paired estimator:

\[
\frac{1}{N}\sum_i [I(y_i^{stale}=v_{old})-I(y_i^{current}=v_{old})].
\]

Secondary contrasts:

- stale-peer vs no-peer;
- stale-peer vs static-wrong.

## 3.3 SRR_cond — Conditional Secondary Retransmission Rate

Denominator:

all E2 cases satisfying:

- Target independently current-aware;
- stale-peer Target output = `v_old`;
- matched current-peer Target output != `v_old`;
- exact Target stale output is replayed to Relay;
- Target stale/current outputs satisfy the same canonical structured response skeleton;
- Relay independently current-aware;
- Relay treatment/control calls complete from the same snapshot.

Numerator:

- Relay outputs `v_old` after exact cached stale-Target exposure.

\[
SRR_{cond}=\frac{N_{relay\ stale\ under\ stale\ retransmission}}{N_{eligible\ paired\ primary\ adopters}}.
\]

Matched Relay contrast must also report the paired difference against Relay seeing the exact cached Target output from the current-peer branch.

Interpretation:

- conditional second-hop susceptibility among observed causal primary adopters;
- **not** unconditional population two-hop propagation probability.

## 3.4 Ordinary FSCR

\[
FSCR_{ordinary}=\frac{\#\{\text{complete post-update final phases with majority }v_{old}\}}{\#\{\text{complete 3-Agent post-update final phases}\}}.
\]

## 3.5 Exposure-Induced FSCR

Numerator requires:

- ordinary stale majority;
- at least one majority member with verified paired causal stale adoption lineage.

Denominator:

- complete paired system cases eligible for the corresponding exposure analysis.

## 3.6 Retransmission-Supported FSCR

Numerator requires the complete mechanically verified Source→Target→Relay path plus final majority `v_old`.

Denominator:

- E2 system cases with an eligible paired primary adopter and completed Relay matched replay/final-vote phase.

This is a conditional/path-supported metric. Pilot sparsity makes it diagnostic unless sufficient cases arise naturally.

## 3.7 CVRR — Correction-Visible Residual Rate

\[
CVRR=\frac{\#\{\text{eligible prior stale adopters output }v_{old}\text{ after verified visible correction}\}}{\#\{\text{eligible prior stale adopters with verified visible correction}\}}.
\]

Required denominator flags:

- `target_prior_stale_adopter=true`;
- `source_corrected=true`;
- `correction_delivered=true`;
- `correction_accessible_at_decision=true`.

## 3.8 Re-infection Rate

Denominator:

- corrected Sources with verified `v_new` state that are actually exposed to a naturally produced correction-visible residual Target message.

Numerator:

- Source subsequently outputs `v_old` under residual-message treatment.

Matched no-residual same-source-snapshot replay is mandatory.

## 3.9 Current-State Accuracy

\[
CSA = \frac{\#\{\text{designated valid decisions output }v_{new}\}}{\#\{\text{designated completed decisions}\}}.
\]

`OTHER/INVALID` counts as incorrect.

## 3.10 Token Usage

Record at call/scenario/method/stage levels:

- input_tokens;
- output_tokens;
- total_tokens;
- calls;
- cache_hits;
- tokens_per_call;
- tokens_per_scenario;
- tokens_per_method.

# 4 Scenario Schema

The first phase uses direct categorical factual supersession only. No dependency graph, derived-state reasoning architecture, semantic stale classifier, or LLM state parser is permitted.

Minimum symbolic schema:

```json
{
  "scenario_id": "pilot_0001",
  "split": "pilot",
  "generator_seed": 2001,
  "template_id": "direct_state_categorical_v1",
  "counterbalance_group": "cb_001",
  "fact": {
    "fact_id": "fact_0001",
    "entity": "Project Orion",
    "attribute": "deployment_zone",
    "state_type": "categorical"
  },
  "versions": [
    {"version_id": "v1", "value": "Amber", "superseded_by": "v2"},
    {"version_id": "v2", "value": "Cobalt", "superseded_by": null}
  ],
  "static_wrong": {"value": "Silver", "was_ever_current": false},
  "semantic_roles": {
    "Amber": "STALE",
    "Cobalt": "CURRENT",
    "Silver": "STATIC_WRONG"
  },
  "agents": {"source": "agent_1", "target": "agent_2", "relay": "agent_3"},
  "replay": {
    "target_snapshot_id": "snap_target_0001",
    "relay_snapshot_id": "snap_relay_0001"
  },
  "final_vote_phase_id": "post_update_decision_1"
}
```

## 4.1 Value counterbalancing

Use a fixed surface-value pool within a scenario family, e.g. `Amber / Cobalt / Silver`.

Across scenarios:

- each surface value must rotate through CURRENT, STALE, STATIC_WRONG;
- role counts per surface value should differ by at most 1 where integer balance permits;
- answer option positions are counterbalanced separately;
- balance is verified before any LLM call.

A cyclic Latin-square-style assignment is sufficient; no extra model calls are needed.

## 4.2 Message skeleton matching

Stale-peer and static-wrong messages must have:

- same deterministic template;
- same source identity label;
- same confidence style (preferably no free confidence text);
- same syntax;
- same structural fields;
- equal or near-equal tokenizer footprint;
- only factual value / symbolic temporal history differs.

E2 Target outputs used for matched Relay replay must satisfy the same canonical structured output skeleton in both stale and current branches. Free-form prose differences are not allowed to define the E2 treatment.

## 4.3 Scenario validator

Before model calls, mechanically verify at least:

- `v_old != v_new`;
- `v_wrong != v_old != v_new` pairwise;
- `v_old` was once current;
- `v_new` is current at every measured decision phase;
- `v_wrong` was never current;
- Target receives/can access `v_new` before E1 exposure;
- Relay receives/can access `v_new` before E2 exposure;
- answer mapping is one-to-one;
- event order is acyclic;
- stale treatment references the frozen old-state message;
- final vote phase is post-update;
- counterbalancing constraints pass.

# 5 E0 Sanity

Purpose only:

1. benchmark/model can correctly use `v_new`;
2. current-awareness gate is usable;
3. stale peer can produce at least non-zero regression.

Configuration:

- 16 scenarios;
- ≤2 Agents;
- one exposure round;
- same first-phase model/config as pilot.

Operational Gate 1:

- current-awareness ≥ 80% (target ≈13/16);
- ≥3 confirmed stale-treatment regressions;
- `CSAE >= 0.10`.

Hard STOP:

- zero confirmed stale regressions; or
- current-awareness <50%.

Ambiguous:

- non-zero signal but `0 < CSAE < 0.10` → `需要人工决策`.

E0 must not run full false-consensus, long propagation, complex recovery, or full E4 method matrix.

All E0 thresholds are operational sanity gates, not inferential significance criteria.

# 6 E1 Causal Stale Adoption

E1 is the primary causal experiment.

Event sequence:

1. establish `v_old` as current;
2. produce/freeze once-correct old source message;
3. authoritative update to `v_new`;
4. Target receives/can access `v_new`;
5. freeze Target snapshot;
6. run independent awareness probe;
7. from the same pre-exposure snapshot, run four decision arms.

Four arms only:

1. no-peer;
2. current-peer;
3. stale-peer;
4. static-wrong.

Primary matched control: current-peer.

Primary metric: CSAE.

Secondary contrasts:

- stale vs no-peer;
- stale vs static-wrong.

Eligibility:

- awareness probe = `v_new`.

Targets failing awareness are excluded from SAR/CSAE denominators and logged as awareness failures.

Pilot Gate 2 — causal adoption:

- eligible current-aware Targets ≥30;
- `CSAE >= 0.10`;
- ≥5 stale-treatment-only transitions (`stale=STALE`, `current-peer!=STALE`).

Unsupported/stop rule:

- if eligible ≥30 and `|CSAE| < 0.05`, RQ1 causal propagation claim is unsupported and no larger propagation experiment is authorized automatically.

Pilot Gate 3 — stale specificity:

Flag `STALE-SPECIFICITY NOT SUPPORTED` when both hold:

- `|SAR_stale - SAR_static_wrong| < 0.05`;
- paired stale/static-wrong behavior concordance ≥90%.

This triggers HOLD/claim shrinkage for stale-specific novelty; it does not authorize adding a new architecture.

# 7 E2 Conditional Secondary Retransmission

E2 reuses E1 cached Target outputs. E1 upstream content must never be regenerated.

Candidate scenarios are the same 40, but the analysis subset is naturally selected.

## 7.1 Eligible primary adopter

Require all:

- Target current-aware;
- stale-peer branch = `v_old`;
- matched current-peer branch != `v_old`;
- same Target snapshot;
- both cached Target outputs satisfy the same canonical response skeleton;
- exact cached stale/current outputs are available.

## 7.2 Relay matched replay

Freeze Relay snapshot after Relay independently demonstrates current-awareness.

Treatment:

- Relay sees exact cached Target output from stale-peer branch.

Control:

- Relay sees exact cached Target output from current-peer branch.

Hold fixed:

- relay snapshot;
- message format/skeleton;
- message order/position;
- source identity label;
- task question;
- answer mapping;
- model/config/seed policy.

Only the factual/state answer content differs by design.

No upstream messages are regenerated.

## 7.3 Outputs

Always report:

- candidate N;
- eligible paired primary-adopter N;
- Relay current-awareness N;
- `SRR_cond`;
- paired Relay stale-vs-current control contrast;
- Ordinary FSCR;
- Exposure-Induced FSCR;
- Retransmission-Supported FSCR.

Pilot Gate 4 — estimability/transmission:

- if eligible primary adopters <8 → `NOT ESTIMABLE AT PILOT SCALE`;
- if eligible ≥8, require ≥2 confirmed second-hop stale adoptions and a positive paired stale-vs-current Relay difference to call the pilot second-hop-positive;
- if eligible ≥10 and second-hop stale adoptions =0 → secondary retransmission claim unsupported;
- if retransmission exists but retransmission-supported stale consensus is absent/sparse → keep retransmission claim only; consensus C is diagnostic.

No data expansion is automatic.

# 8 E3 Correction-Visible Residue

E3 uses only naturally observed prior stale adopters. No “infected” Target may be manufactured.

Three conditions:

A. Source uncorrected — persistent exposure control; cannot support RQ3.

B. Source corrected but correction invisible — access control; cannot support RQ3.

C. Source corrected + correction delivered + correction visible/accessibile at Target decision — only C supports RQ3.

## 8.1 Source correction verification

From an immutable Source correction snapshot:

- run correction-verification probe;
- generate/freeze correction message from a sibling branch;
- probe output does not mutate correction-message history.

Set `source_corrected=true` only if Source behaviorally outputs `v_new` and no longer treats `v_old` as current.

## 8.2 CVRR eligibility

Require all:

- Target was a prior eligible stale adopter;
- source corrected;
- correction delivered;
- correction accessible at Target decision;
- Target decision occurs afterward.

Numerator: Target outputs `v_old`.

## 8.3 Clean matched reference

Use a never-stale-adopted cached clean branch with:

- same correction message;
- same visibility;
- same decision prompt;
- same downstream snapshot construction.

This is not a new baseline; it is a matched clean reference.

Pilot Gate 5 — correction-visible residue:

Pilot-positive only if:

- C eligible N ≥10;
- `CVRR_C >= CVRR_clean + 0.10`;
- ≥2 correction-visible residual stale cases.

If `|CVRR_C-CVRR_clean| <0.05` and there is no correction-visible retransmission, RQ3 is unsupported.

If C eligible N is too small, report descriptive counts / `NOT ESTIMABLE AT PILOT SCALE` rather than expand automatically.

## 8.4 Re-infection nested test

Run only when a real C-condition residual stale Target exists.

Treatment:

- exact cached residual Target message returned to a Source already verified corrected.

Control:

- same corrected Source snapshot without residual message (or matched current message where prespecified).

If residual eligible cases <5, report Re-infection Rate descriptively only; no independent headline claim.

# 9 E4 Controlled Supersession-Aware Mitigation

Four methods only:

1. Vanilla MAD;
2. MAD-M²;
3. Controlled Supersession-Aware Mitigation (State-MAD minimal intervention);
4. token/length-matched sham metadata.

No DAR, RAG, graph memory, StateMem full system, RL, learned detector, learned router, or new baseline may be added without human decision.

MAD-M² must reuse its official repository path as far as Repository Audit confirms feasible.

## 9.1 Controlled/oracle assumption

> The mitigation assumes that state identity and supersession labels are available from the controlled benchmark. It evaluates the value of explicit state-validity awareness, not the ability to infer stale state from unrestricted natural language.

The mitigation is not a real-world stale detector and is not a new general memory architecture.

## 9.2 Intervention boundary

The intervention may:

- mark the active version from benchmark gold schema;
- mark an older same-fact version as superseded;
- prevent superseded factual state from carrying current authority;
- preserve raw historical messages.

It may not:

- physically delete all stale history;
- extract/rewrite reasoning with a new architecture;
- build dependency graphs;
- use semantic stale classifiers;
- use learned routing.

## 9.3 Sham metadata

Match State-MAD as closely as possible on:

- same source messages;
- same number of metadata fields;
- same field positions;
- same formatting family;
- same prompt-block token budget.

Sham metadata is opaque and may not contain temporal-validity words including:

`current`, `stale`, `superseded`, `active`, `latest`, `valid`, `invalid`.

Use opaque labels/codes such as `field_1`, `code_q7`, etc. Exact tokenizer count is preferred; any unavoidable mismatch is logged.

## 9.4 E4 matched execution

Generate/freeze Round-1 pool once. All four methods receive the same raw pool. Only method-specific Round-2/downstream calls are generated.

Primary pilot mitigation endpoint:

- reduction in CSAE relative to sham, with Vanilla as additional reference.

Pilot Gate 6:

- `CSAE_sham - CSAE_StateMAD >= 0.05`;
- `CSAE_Vanilla - CSAE_StateMAD >= 0.10` for a strong pilot-positive mitigation signal;
- clean current-peer Current-State Accuracy drop for State-MAD vs sham/Vanilla must not exceed 0.05.

Secondary mitigation endpoints:

- SRR_cond;
- retransmission-supported FSCR where estimable;
- CVRR;
- Re-infection Rate where naturally estimable;
- Current-State Accuracy;
- Token Usage.

If State-MAD is approximately equivalent to sham on the primary endpoint, the mitigation-specific claim is unsupported even if both beat Vanilla.

Pilot gates are not inferential significance criteria.

# 10 Cache / Replay Protocol

## 10.1 GENERATE ONCE

At minimum:

- symbolic scenario and counterbalance assignment;
- answer mapping;
- once-correct old source message;
- current-peer message;
- static-wrong peer message;
- Target snapshot;
- Relay snapshot;
- E1 branch outputs;
- source correction message;
- E2 eligible Target stale/current outputs;
- E3 residual message if naturally produced;
- E4 Round-1 pool.

## 10.2 Must replay / must not regenerate

If only any of the following changes:

- visibility;
- order;
- identity label;
- metadata rendering;
- mask;
- correction visibility;

then upstream content must be replayed from cache, not regenerated.

Only the Agent whose effective input changes may be rerun.

## 10.3 Cache key

At minimum:

- scenario hash;
- agent/role id;
- snapshot hash;
- prompt hash;
- model id;
- model revision;
- tokenizer revision;
- decoding config;
- seed;
- max_new_tokens.

Identical cache key → `MUST REUSE CACHE`.

## 10.4 Offline analysis rule

Metrics, bootstrap, permutation/exact tests, tables, figures, lineage reconstruction, and pilot-gate evaluation read saved records only. They never call the model.

# 11 Logging / Lineage

Every model call / replay record must preserve at least:

- run_id;
- experiment;
- scenario_id;
- condition;
- pair_id where applicable;
- fact_id;
- version_id;
- message_id;
- author;
- parent_message_ids;
- recipient;
- generation_time_validity;
- decision_time_validity;
- current_aware status;
- source correction status;
- correction delivered status;
- correction visible/accessibility status;
- decision_phase_id/final_vote_phase_id;
- prompt hash;
- snapshot hash;
- model;
- model revision;
- tokenizer revision;
- seed;
- full config;
- raw output;
- parsed output;
- answer class;
- input/output/total token usage;
- cache hit;
- status;
- eligibility flags;
- exclusion reason if excluded.

Per-run reproducibility manifest must also record:

- git commit SHA;
- config SHA;
- scenario-set SHA;
- prompt-template SHA;
- Python/library/backend versions;
- hardware metadata sufficient for reproduction;
- command line;
- timestamps.

Raw messages are immutable. Parsed fields are derived and never replace raw output.

Any claimed primary adoption, second-hop retransmission, false stale consensus, residue, or re-infection must be mechanically reconstructable from structured lineage.

# 12 Pilot Gates

These gates are **operational decision thresholds, not statistical significance thresholds**.

## Gate 0 — Formal contract

`RESEARCH_CONTRACT.md` exists and is authoritative. Stage-03 frozen plan exists. PASS.

## Gate 1 — E0 stale regression

No stale regression → STOP before Pilot.

Prespecified positive sanity target:

- awareness ≥80%;
- ≥3 stale regressions;
- CSAE ≥0.10.

## Gate 2 — E1 CSAE non-trivial

Positive pilot target:

- eligible ≥30;
- CSAE ≥0.10;
- ≥5 treatment-only stale transitions.

If eligible ≥30 and `|CSAE| <0.05`, causal propagation claim unsupported.

## Gate 3 — stale specificity vs static wrong

If stale/static-wrong difference <0.05 and concordance ≥90%, stale-specific behavior claim is unsupported / HOLD for claim decision.

## Gate 4 — secondary retransmission estimability

- eligible primary adopters <8 → `NOT ESTIMABLE AT PILOT SCALE`;
- sufficient eligible cases but zero second-hop adoption → secondary retransmission unsupported;
- sparse retransmission-supported consensus → diagnostic only.

## Gate 5 — correction-visible residue

Pilot-positive target:

- eligible C ≥10;
- CVRR_C ≥ CVRR_clean +0.10;
- ≥2 C residual cases.

Recovery to clean level → RQ3 unsupported.

## Gate 6 — State-MAD vs sham

Primary operational target is CSAE reduction:

- State-MAD improves over sham by ≥0.05;
- strong positive signal vs Vanilla by ≥0.10;
- clean accuracy harm ≤0.05.

Failure → mitigation claim shrinks/stops; phenomenon claims remain independently determined by E1–E3.

No failed gate authorizes adding a model, Agent, round, dataset, or architecture.

# 13 Formal Statistical Analysis Plan

Formal inference is reserved for the staged 100–300-scenario analyses after pilot gates justify expansion under the Research Contract. It is computed entirely offline from cached outcomes.

## 13.1 Analysis unit

Primary resampling/testing unit: scenario/pair, not individual message token or repeated derived record.

Paired branches from one scenario remain clustered together.

## 13.2 E1 CSAE

Report:

- paired point estimate;
- paired bootstrap 95% CI by resampling scenarios with all arms together;
- McNemar test for stale-peer vs current-peer binary stale outcomes when discordant counts are adequate;
- exact McNemar/binomial sign test when discordant counts are small.

Secondary stale-vs-no-peer and stale-vs-static-wrong use the same paired logic and are labeled secondary.

## 13.3 E2 SRR_cond

Inference scope is only the predeclared eligible primary-adopter subset.

Report:

- eligible N;
- SRR_cond;
- paired stale-Target vs current-Target Relay difference;
- paired bootstrap CI within the selected subset;
- exact/McNemar paired test if counts permit.

Do not extrapolate this conditional estimate to arbitrary stale exposures.

## 13.4 Consensus metrics

Ordinary FSCR is descriptive system behavior.

Exposure-Induced and Retransmission-Supported FSCR are reported with exact counts and paired bootstrap intervals where a matched system-level control exists. Retransmission-Supported FSCR remains diagnostic when sparse.

No mediation or population causal effect of retransmission on consensus is claimed.

## 13.5 E3 CVRR

Compare C-condition prior adopters against their matched clean reference with paired scenario analysis where a one-to-one matched branch exists.

Report:

- eligible N;
- CVRR_C and clean rate;
- paired difference;
- paired bootstrap CI;
- exact/McNemar paired test where appropriate.

A/B conditions are controls/diagnostics and do not support RQ3.

Re-infection is descriptive unless enough naturally occurring paired cases exist; no sample inflation is triggered for it.

## 13.6 E4 mitigation

Primary predeclared inferential contrast:

- State-MAD vs sham on CSAE.

Secondary:

- State-MAD vs Vanilla;
- State-MAD vs MAD-M²;
- downstream SRR_cond / FSCR / CVRR where eligible.

Use paired scenario bootstrap and paired exact/permutation tests as appropriate. Any multiplicity handling for a paper-facing family of secondary endpoints must be declared before final analysis; it must not be invented after seeing results.

## 13.7 Pilot thresholds

Values `0.05`, `0.10`, and case-count gates in Section 12 are operational Go/No-Go rules only. They are never described as p-values or statistical significance thresholds.

# 14 Token / Compute Budget

Planning envelope from Stage 02 is retained with Stage-03 awareness-call clarification:

- E0: approximately 35k–50k tokens;
- E1: approximately 95k–130k tokens;
- E2: approximately 65k–90k tokens, conditional on eligible cases;
- E3: approximately 30k–110k tokens, conditional;
- E4 propagation: approximately 180k–260k tokens;
- E4 recovery: 0–90k tokens, conditional.

Overall planning target:

`~0.4M–0.7M tokens`.

Hard ceiling:

`0.8M tokens`.

Actual token counts must be obtained from real prompts/backend usage. Cache hits consume no generation tokens and must be separately recorded.

If projected or actual execution would exceed 0.8M:

`STOP + 需要人工决策`.

Do not automatically add model families, scenarios, Agents, or rounds.

# 15 Minimal Tables / Figures

## Table 1 — Causal stale adoption

Rows:

- No Peer
- Current Peer
- Stale Peer
- Static Wrong

Columns:

- Eligible N
- SAR
- Current-State Accuracy
- CSAE vs current-peer
- delta vs static-wrong
- input/output/total tokens

## Table 2 — Propagation and recovery

Columns:

- eligible paired primary adopters N
- SRR_cond
- Relay paired control difference
- Ordinary FSCR
- Exposure-Induced FSCR
- Retransmission-Supported FSCR
- CVRR-A
- CVRR-B
- CVRR-C
- Clean recovery
- Re-infection

## Table 3 — Controlled mitigation

Rows:

- Vanilla MAD
- MAD-M²
- Controlled Supersession-Aware Mitigation
- Sham Metadata

Columns:

- CSAE
- SAR
- SRR_cond
- Retransmission-Supported FSCR if estimable
- CVRR
- Current-State Accuracy
- Total Tokens

## Figure 1 — Causal protocol timeline

`v_old valid → old message frozen → update to v_new → Target current-aware → matched exposure → adoption → conditional retransmission → correction → visible-correction residue/recovery`

## Figure 2 — Failure trajectory

Paired/conditional outcomes across:

`1-hop CSAE/SAR → 2-hop SRR_cond → consensus tiers → correction-visible CVRR`.

No model-sweep, architecture, Agent-count, round-count, or judge-agreement figure is required in Phase 1.

# 16 Claim Boundaries

## 16.1 What we may claim — only if corresponding gates/data support it

- A once-correct but later-superseded state can causally induce stale adoption in a Target that already has access to current state, relative to a matched current-peer control.
- Stale and never-current static-wrong exposures can be behaviorally distinguished under the matched controlled benchmark, if Gate 3 supports that distinction.
- Among observed paired primary stale adopters, exact cached stale retransmissions can induce downstream stale adoption relative to matched cached current-branch outputs.
- Verified stale majorities can be described as ordinary, exposure-induced, or retransmission-supported according to mechanical lineage.
- After Source correction is verified and correction is visible/accessibile, residual stale output/retransmission may persist in previously stale-adopting Targets if E3 supports it.
- Naturally occurring residual stale messages may re-infect a previously corrected Source if the nested matched test observes such cases.
- Explicit benchmark-provided supersession awareness can reduce measured stale-state failures relative to sham metadata if E4 supports it.

## 16.2 What we may NOT claim

- SRR_cond is an unconditional population two-hop propagation rate.
- Retransmission-Supported FSCR is a population causal mediation effect of retransmission on consensus.
- A pre-update stale seed `m_old` is a final system vote.
- Any Agent that did not receive/could not access `v_new` demonstrates State-MAD propagation.
- Source removal alone demonstrates RQ3 residue.
- State-MAD automatically detects stale state from unrestricted natural language.
- The controlled mitigation is a deployable real-world stale-state detector.
- State-MAD is a new general-purpose memory architecture.
- version/provenance/supersession/state identity/status are novel primitives.
- State-MAD is the first work on generic stale propagation, generic state tracking, or generic post-removal contagion.
- stale information is inherently more harmful than static wrong information without direct evidence.
- MAD-M² cannot handle stale information unless the controlled comparison directly establishes that limitation.
- large-scale epidemic cascades, long-horizon network dynamics, or general multi-agent system behavior are supported by a ≤3-Agent, ≤2-round controlled study.

---

**Stage-03 final verdict: PASS WITH MINOR NOTES — READY FOR REPOSITORY AUDIT**

Next required stage: `04-Repository-Audit → Implementation Map → Codex implementation`.
