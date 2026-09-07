# State-MAD Implementation Requirements

Status: FROZEN REQUIREMENTS AFTER STAGE-03 REVIEW
Purpose: Requirements only. This document does not prescribe repository patches.
Authority: `RESEARCH_CONTRACT.md` and `EXPERIMENT_PLAN_FROZEN.md`.

# 1 Repository Constraints

1. Reuse the official MAD-M² repository as the engineering base.
2. Do not reimplement the overall MAD framework.
3. Reuse the official MAD-M² baseline path as far as the Repository Audit confirms feasible.
4. Do not modify the repository before `04-Repository-Audit` and an explicit Implementation Map are completed.
5. Repository Audit must map existing files/functions/config paths before Codex writes code.
6. If repository structure prevents a frozen requirement from being implemented without changing the research scope, mark `需要人工决策`; do not invent a new architecture.

# 2 Required Capabilities

The implementation must provide the following capabilities, either by reusing existing repository components or by adding the minimum supporting code after Repository Audit.

## 2.1 Symbolic scenario compiler

Must:

- create direct categorical state-update scenarios;
- assign deterministic `fact_id` / `version_id`;
- encode `v_old → v_new` supersession;
- define a never-current `v_wrong`;
- freeze answer mapping;
- create event order;
- emit scenario records without LLM semantic parsing.

## 2.2 Scenario validator

Must mechanically reject invalid scenarios before model calls.

Checks include:

- pairwise distinct current/stale/static-wrong values;
- old value was once current;
- static-wrong was never current;
- new value is authoritative at all measured decisions;
- Target/Relay have current state available before exposure;
- answer mapping is one-to-one;
- event order is acyclic;
- stale message references the correct old version;
- final-vote phase is post-update;
- value counterbalancing passes.

## 2.3 Value counterbalancing

Must rotate surface values across:

- CURRENT;
- STALE;
- STATIC_WRONG.

Across the scenario set, each surface value must occupy these roles as evenly as integer counts permit. Answer-option position is independently counterbalanced.

The compiler/validator must output a balance report before any model call.

## 2.4 Immutable snapshots

Must support:

- immutable Target pre-exposure snapshot;
- immutable Relay pre-exposure snapshot;
- immutable Source correction snapshot;
- branch/fork semantics that do not mutate the parent snapshot.

Awareness-probe output must never be appended to treatment/control history.

## 2.5 Branch/replay runner

Must support:

- sibling matched branches from one snapshot;
- downstream replay using cached upstream messages;
- same-snapshot paired treatment/control calls;
- E1 → E2 → E3 cache inheritance;
- E4 frozen Round-1 pool reused across all methods.

## 2.6 Immutable message cache

Must:

- persist raw message bytes/text and parsed fields;
- return the exact cached message for replay;
- forbid silent regeneration under an identical cache key;
- distinguish cache miss, cache hit, and forced-invalid states.

## 2.7 Deterministic grader

Must parse the strict answer format and map to:

- CURRENT;
- STALE;
- STATIC_WRONG;
- OTHER/INVALID.

No LLM judge is allowed.

## 2.8 Lineage tracker

Must reconstruct:

- Source stale seed;
- Target exposure;
- paired Target causal stale adoption;
- Target retransmission;
- Relay exposure/adoption;
- final-vote phase;
- Source correction;
- correction delivery/accessibility;
- residual Target output;
- optional re-infection.

## 2.9 Metric engine

Must compute all frozen metrics mechanically from structured records:

- SAR;
- CSAE;
- SRR_cond;
- Ordinary FSCR;
- Exposure-Induced FSCR;
- Retransmission-Supported FSCR;
- CVRR;
- Re-infection Rate;
- Current-State Accuracy;
- Token Usage.

Repeated metric computation must not call the model.

## 2.10 Baseline adapters

Only:

- Vanilla MAD;
- MAD-M²;
- Controlled Supersession-Aware Mitigation;
- Sham Metadata.

No fifth method/baseline is permitted in Phase 1 without human decision.

## 2.11 Reproducibility manifest

Must capture repository, model, prompt, scenario, config, backend, seed, token, and runtime provenance sufficient to rerun a cached experiment.

# 3 Required Experimental Conditions

Only the following first-phase experimental conditions are authorized.

## 3.1 E1 peer-exposure conditions

- `no-peer`
- `current-peer`
- `stale-peer`
- `static-wrong`

Primary matched control: `current-peer`.

## 3.2 Correction conditions

- source uncorrected;
- source corrected + correction invisible;
- source corrected + correction visible/accessibile.

Only the last condition supports RQ3.

## 3.3 E4 methods

- Vanilla MAD;
- MAD-M²;
- Controlled Supersession-Aware Mitigation;
- Sham Metadata.

## 3.4 Message structure constraints

Stale-peer vs static-wrong messages must use the same deterministic skeleton and source-label format.

E2 Target stale/current outputs must satisfy the same canonical structured response skeleton before they are eligible for matched Relay replay.

No researcher may hand-edit an LLM output to force skeleton equivalence.

# 4 Forbidden Implementation Expansion

Phase 1 must not add:

- reinforcement learning;
- fine-tuning;
- learned stale detector;
- semantic stale classifier;
- learned router;
- dependency graph;
- general-purpose memory architecture;
- StateMem clone;
- general natural-language state parser;
- LLM-as-a-Judge;
- extra Agent beyond 3;
- extra main debate round beyond 2;
- new baseline;
- DAR baseline;
- RAG baseline;
- graph memory;
- large dataset expansion;
- model sweep;
- physical deletion of all stale raw messages;
- reasoning extraction/rewrite architecture.

Any requirement that appears to need one of these must be escalated as `需要人工决策` rather than implemented.

# 5 Cache Contract

## 5.1 Calls/content that may generate once

The first valid cache miss may generate and freeze:

- source once-correct old-state output/message;
- current-peer output/message;
- static-wrong peer output/message if the frozen renderer uses a model call; otherwise render deterministically;
- Target E1 branch outputs;
- Relay downstream outputs;
- Source correction message;
- Target post-correction E3 outputs;
- Source re-infection test output when eligible;
- E4 Round-1 outputs;
- E4 method-specific downstream/Round-2 outputs.

The symbolic scenario, answer mapping, metadata blocks, and deterministic message skeletons should be generated by code, not by an LLM.

## 5.2 Calls/content that must replay

Must replay exact cached upstream content when only any of the following changes:

- message visibility;
- message order;
- source identity label;
- metadata rendering;
- mask state;
- correction visibility;
- method-specific downstream rendering over the same frozen Round-1 pool.

E2 must replay:

- exact cached Target stale-branch output for treatment;
- exact cached Target current-peer-branch output for control.

E3 re-infection must replay the naturally produced exact residual Target message.

## 5.3 Identical cache keys must reuse

Cache key must include at least:

- scenario_hash;
- experiment/phase;
- condition;
- agent_id/role;
- snapshot_hash;
- prompt_hash;
- visible_message_ids or their content hashes;
- model_id;
- model_revision;
- tokenizer_revision;
- temperature/top_p/decoding config;
- seed;
- max_new_tokens.

If the effective generation input and all generation parameters are identical, the key must be identical and the cached output must be reused.

Silent regeneration under the same key is an experimental integrity failure.

## 5.4 Awareness vs no-peer call rule

Frozen design uses different prompts:

- awareness probe = current-state access/knowledge verification;
- no-peer = ordinary decision question.

Therefore they are separate cache keys.

If Repository Audit finds the implementation actually constructs identical prompts/configuration/snapshot, they must share one cache key/call. In that case the no-peer branch cannot be interpreted as an independent secondary outcome among awareness-selected cases.

# 6 Metric Contract

All metric computation is mechanical.

## 6.1 SAR

Numerator:

- current-aware eligible Target outputs STALE in a specified E1 arm.

Denominator:

- current-aware Targets with completed calls in that arm.

Eligibility:

- independent awareness probe outputs CURRENT.

Exclusions:

- infrastructure failure only.

`OTHER/INVALID` remains in denominator and is not stale numerator.

## 6.2 CSAE

Numerator/statistic:

- sum over paired scenarios of `I(stale-peer=STALE)-I(current-peer=STALE)`.

Denominator:

- eligible scenarios with both primary paired arms completed from same snapshot.

Exclusions:

- awareness failure;
- infrastructure failure in either paired arm.

## 6.3 SRR_cond

Numerator:

- Relay outputs STALE under exact cached stale-Target exposure.

Denominator:

- paired E1 causal primary adopters whose stale/current Target outputs satisfy the canonical output skeleton, whose exact messages are replayable, and whose Relay independently passes awareness and completes matched replay.

Primary-adopter eligibility:

- Target awareness = CURRENT;
- Target stale branch = STALE;
- Target current-peer branch != STALE.

Exclusions:

- Target did not meet paired causal-adopter rule;
- stale/current message skeleton mismatch;
- Relay awareness failure;
- missing/infrastructure-failed matched Relay call.

Interpretation field in output must label the metric `conditional`, not `population`.

## 6.4 Ordinary FSCR

Numerator:

- final post-update 3-Agent majority = STALE.

Denominator:

- complete 3-Agent final-vote phases.

Eligibility:

- all votes share the same post-update `final_vote_phase_id`.

Exclusion:

- incomplete final phase.

Pre-update `m_old` can never be a vote.

## 6.5 Exposure-Induced FSCR

Numerator:

- Ordinary FSCR case plus at least one stale-majority member has paired causal stale-adoption lineage.

Denominator:

- complete system cases for which causal-adoption lineage is evaluable.

## 6.6 Retransmission-Supported FSCR

Numerator requires all:

- Source stale seed;
- Target current-aware;
- Target paired causal stale adoption;
- exact cached Target stale retransmission;
- Relay current-aware;
- Relay stale adoption;
- final post-update majority = STALE.

Denominator:

- E2 complete system cases with an eligible primary adopter and completed matched Relay/final-vote phase.

Output must label pilot sparse results `diagnostic` when appropriate.

## 6.7 CVRR

Numerator:

- prior eligible stale Target outputs STALE after verified visible correction.

Denominator requires:

- target_prior_stale_adopter=true;
- source_corrected=true;
- source no longer treats old value as current;
- correction_delivered=true;
- correction_accessible_at_decision=true;
- post-correction Target decision completed.

Exclusions:

- any missing condition above;
- infrastructure failure.

Conditions A/B are never included in headline CVRR_C denominator.

## 6.8 Re-infection Rate

Numerator:

- verified corrected Source outputs STALE after exposure to exact cached naturally produced residual Target message.

Denominator:

- corrected Sources with a real C-condition residual Target message and completed matched re-infection treatment/control.

No artificial infected message is allowed.

## 6.9 Current-State Accuracy

Numerator:

- designated decision = CURRENT.

Denominator:

- designated completed decisions in the relevant condition.

`OTHER/INVALID` is incorrect.

## 6.10 Token Usage

For every call and aggregation:

- input_tokens;
- output_tokens;
- total_tokens;
- cache_hit;
- stage/scenario/method summaries.

# 7 Logging Contract

Every call/replay record must include at least:

- run_id
- experiment
- scenario_id
- condition
- pair_id
- fact_id
- version_id
- message_id
- author
- parent_message_ids
- recipient
- generation_time_validity
- decision_time_validity
- current_aware
- source_corrected
- correction_delivered
- correction_accessible_at_decision
- decision_phase_id
- final_vote_phase_id where applicable
- prompt_hash
- snapshot_hash
- model
- model_revision
- tokenizer_revision
- seed
- config
- system/user prompt or immutable prompt reference
- visible_message_ids/content hashes
- raw_output
- parsed_output
- answer_class
- token usage
- cache_hit
- status
- eligibility_flags
- exclusion_reason

Lineage records must be sufficient for metric computation without human semantic labeling.

Raw outputs are append-only/immutable.

# 8 Reproducibility Contract

Every valid run must save:

- git commit SHA;
- repository branch/dirty-state indicator;
- config file/hash;
- scenario set/hash;
- prompt templates/hash;
- model identifier and exact revision if available;
- tokenizer identifier/revision;
- decoding parameters;
- seeds;
- Python version;
- relevant package/backend versions;
- GPU/backend/quantization/batching/context configuration;
- command line;
- start/end timestamps;
- token usage;
- raw trajectories;
- cache manifest and hit/miss statistics.

Offline analysis must be reproducible from saved scenario + call + lineage records without model access.

Pilot statistical thresholds are operational gates only. Formal paired bootstrap/McNemar/exact/permutation analysis must use saved outcomes and make no LLM calls.

# 9 Sanity Gate

Codex implementation/execution order is constrained to:

`minimal dry run → E0 only → evaluate Gate 1`.

Before E0 PASS, Codex must not implement/run full Pilot automation as an end-to-end experiment campaign.

Minimum dry run validates:

- scenario compiler/validator;
- counterbalancing report;
- deterministic message skeleton;
- snapshot non-mutation;
- cache reuse;
- deterministic grading;
- lineage reconstruction;
- token logging.

E0 uses 16 scenarios and tests only:

1. use of `v_new`;
2. awareness-gate viability;
3. non-zero stale regression.

If E0 has zero confirmed stale regressions:

`STOP`.

Do not rescue E0 by:

- adding a model;
- adding scenarios beyond the frozen sanity range;
- adding Agents;
- adding rounds;
- adding a new prompt architecture;
- adding RL/fine-tuning;
- adding a new baseline.

Any such proposal is `需要人工决策`.

---

Next stage after this requirements document: Repository Audit and Implementation Map. No repository patch is authorized by this file alone.
