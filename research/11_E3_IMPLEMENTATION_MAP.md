# State-MAD E3 Implementation Map

**Status:** PLANNING ARTIFACT — NO IMPLEMENTATION OR E3 SCIENTIFIC EXECUTION AUTHORIZED

**Stage:** E3-Specific Implementation Map

**Scientific base:** `main @ c057117dc7b60bb1bec4d7ab6f4d7890eadd3155`

**Planning parent:** `audit/e3-repository-delta @ 283bb4855ff30df43cc1eaf108f39eb46d48f3b4`

**Authority:**

`RESEARCH_CONTRACT.md`
→ `EXPERIMENT_PLAN_FROZEN.md`
→ `IMPLEMENTATION_REQUIREMENTS.md`
→ `03_EXPERIMENT_PLAN_REVIEW.md`
→ `04_REPOSITORY_AUDIT.md` / `05_IMPLEMENTATION_MAP.md`
→ completed E1/E2 frozen evidence
→ `10_E3_REPOSITORY_DELTA_AUDIT.md`
→ this map

This file refines only the implementation path for frozen E3 / RQ3. It does
not change RQ3, authorize code changes, authorize tokenizer/model/GPU access,
authorize scientific generation, enlarge the sample, or authorize E4.

## 0. Planning Result and Frozen Boundary

### 0.1 Planning result

The repository can support the frozen E3 correction-visible residue and nested
re-infection design with a narrow wrapper plus bounded extensions. No audited
requirement forces a MAD-M² core change, a scenario-schema migration, a prompt
rewrite, a new model, a new Agent, a new round, or a new baseline.

The minimum candidate implementation delta is:

- **NEW** `state_mad/e3.py`;
- **EXTEND** `state_mad/preflight.py`;
- **EXTEND** `state_mad/lineage.py`;
- **EXTEND** `state_mad/metrics.py`; and
- **NEW** `tests/state_mad/test_e3.py`.

Everything else is REUSE or WRAP unless implementation proves a frozen
requirement cannot otherwise be satisfied. Such proof is a STOP trigger, not
a license to expand scope.

### 0.2 Frozen scientific subset

The E3 pilot candidate set is exactly the nine naturally observed E1 paired
causal stale adopters:

`e1-04`, `e1-10`, `e1-16`, `e1-18`, `e1-22`, `e1-28`, `e1-30`,
`e1-34`, `e1-40`.

E2 does not enlarge or redefine this set. E3 eligibility comes from E1 frozen
evidence through the existing whole-run fail-closed E1 resolver.

### 0.3 Pilot estimability boundary

The frozen Gate 5 requires C-condition eligible N `>= 10`. The current natural
candidate pool is at most 9. Therefore the current E3 pilot can never receive a
positive Gate-5 label without changing frozen scale.

The required scale label for the current pilot is:

`NOT ESTIMABLE AT PILOT SCALE`

E3 may still report descriptive C eligibility, `CVRR_C`, matched clean CVRR,
paired contrast, residual IDs/counts, correction-visible retransmission, and
nested re-infection outcomes if later authorized and naturally observed.

No implementation may add scenarios, seeds, models, Agents, rounds, or
synthetic infected cases to cross the Gate-5 threshold.

## A. Frozen E3 Conditions and Evidence Semantics

### A.1 Condition flags

The E3 implementation must encode correction state mechanically rather than
infer it from condition names or prose.

The frozen condition semantics are:

| Condition | `source_corrected` | `correction_delivered` | `correction_accessible_at_decision` | RQ3 headline eligible? |
| --- | --- | --- | --- | --- |
| A — source uncorrected | `false` | `false` | `false` | No |
| B — corrected, invisible | `true` | `true` | `false` | No |
| C — corrected, visible | `true` | `true` | `true` | Yes, subject to all other eligibility checks |
| Clean-C matched reference | `true` | `true` | `true` | Control only |

B is frozen as **delivered but inaccessible at decision time**. The exact same
valid correction message is present in branch history but absent from
model-visible evidence. This makes B an access/visibility control and makes
A/B model-visible input identical when all other held-fixed inputs are equal.

A contains no correction message in history. C and Clean-C contain the same
exact correction message in history and expose it at decision time.

### A.2 Source-corrected status

`source_corrected=true` is set only when the isolated Source correction probe
is mechanically canonical and grades `CURRENT` / `v_new`.

The Source correction message is a separate sibling output. It must also be
canonical and grade `CURRENT` before it can qualify as a valid correction
message for B/C/Clean-C. A non-current or noncanonical correction-message
output is preserved as evidence but is never edited into compliance.

A Source probe failure is a scientific eligibility failure for B/C/Clean-C,
not an infrastructure failure and not a reason to regenerate.

### A.3 Measurement ordering

The E3 overlay must prove this ordering for B/C/Clean-C:

`authoritative update → verified Source correction → frozen correction message → correction delivery → Target post-correction decision`

For C/Clean-C, accessibility is additionally true at the Target decision.
For B, the correction is in history but inaccessible. A remains on the
uncorrected branch at the same designated E3 Target decision phase.

## B. Read-Only Upstream E1 Resolution

### B.1 Reuse existing resolver

`state_mad/e3.py` must import and reuse from `state_mad/e2.py`:

- `E1RunExpectation`;
- `resolve_e1_replay_pairs`; and
- `reconstruct_e1_target_branch_snapshot`.

No second E1 resolver is permitted.

The E3 wrapper must require the recomputed eligible set to equal the exact nine
frozen IDs. It must preserve the E2 resolver's manifest, content, grade,
provenance, snapshot, and whole-run integrity checks.

### B.2 Upstream evidence roles

For each scenario:

- the E1 `stale-peer` branch is the prior-infected Target history;
- the E1 `current-peer` branch is the matched clean Target history;
- the exact E1 Source stale-peer message remains the prior stale exposure;
- the exact E1 Target stale/current outputs remain evidence of prior adoption
  and clean behavior, respectively.

E3 must not infer prior infection from E2 final votes, restrict the candidate
set to the six E2 second-hop-positive cases, or regenerate any E1/E2 call.

### B.3 Upstream immutability

Before E3 orchestration, record byte content for the frozen upstream E1 run
files used by the resolver. After E3 completion, require byte-for-byte equality.
Missing cache entries must never trigger upstream regeneration.

E2 scientific artifacts may be opened read-only only if needed for provenance
cross-checking; they are not required to define E3 eligibility.

## C. E3 Scenario Overlay and Phase IDs

### C.1 Ownership

`state_mad/e3.py` owns an immutable `E3ScenarioOverlay` per candidate scenario.
The frozen E1 `ScenarioRecord` and scenario-set hash remain unchanged.

### C.2 Required overlay fields

Each overlay must contain at least:

```text
scenario_id
frozen_e1_run_id
frozen_e1_scientific_sha
frozen_e1_scenario_set_hash
e1_scenario_digest
source_agent_id="source"
target_agent_id="target"
prior_stale_condition="stale-peer"
clean_reference_condition="current-peer"
source_correction_parent_snapshot_id
source_correction_parent_snapshot_hash
source_correction_phase_id
post_correction_target_phase_id
reinfection_phase_id
prior_stale_branch_snapshot_hash
clean_branch_snapshot_hash
overlay_schema="e3-overlay-v1"
overlay_digest
```

Freeze deterministic phase IDs as:

- Source correction: `<scenario_id>:e3-source-correction`;
- Target residue measurement: `<scenario_id>:e3-post-correction`;
- nested re-infection: `<scenario_id>:e3-reinfection`.

The overlay must also carry deterministic event-order metadata sufficient to
prove that the Target residue phase follows Source correction for B/C/Clean-C
and that re-infection follows any naturally produced C residual message.

### C.3 Agent/resource scope

E3 uses only two logical Agents, Source and Target. No Relay is required.
The total project bound remains at most three Agents and at most two main
communication hops/rounds. E3 must not introduce an additional Agent to make
residual propagation easier to observe.

## D. Source Correction Parent and Isolated Siblings

### D.1 Source correction parent

Create one immutable Source correction parent per scenario through an E3-only
wrapper over the existing `Snapshot` dataclass. Do not change
`state_mad/snapshots.py` unless later implementation proves this impossible,
which is a STOP trigger.

The Source correction parent must:

- bind the same scenario/fact;
- have `current_version_id == version_new_id`;
- be post-authoritative-update;
- contain no correction-probe output;
- contain no Target residual output; and
- have one captured parent hash reused by all Source-correction siblings.

### D.2 Sibling topology

Freeze this topology:

```text
immutable Source correction parent
├── source-correction-awareness
└── source-correction-message
```

The awareness output must never be appended to the correction-message sibling
or any Target A/B/C/Clean-C history.

### D.3 Prompt reuse

Use existing prompt renderers unchanged:

- `render_awareness_probe` / `awareness-v3` for Source correction verification;
- `render_decision` / `decision-v2` for the Source correction message.

No new model-visible correction-verification wording is authorized by this
map. If these renderers are shown during implementation to be incapable of the
frozen semantics, STOP for human review instead of silently changing prompts.

### D.4 Deterministic call IDs

Freeze logical conditions and IDs:

- condition `source-correction-awareness`;
  call `<e3_run_id>:<scenario_id>:source:correction-awareness:call`;
- condition `source-correction-message`;
  call `<e3_run_id>:<scenario_id>:source:correction-message:call`.

Generated output message IDs replace `:call` with `:output`.

## E. Exact Source Correction Replay

### E.1 One correction message, reused everywhere

A valid canonical CURRENT `source-correction-message` output is generated or
cache-resolved once. `state_mad/e3.py` then creates one exact Source→Target
correction replay envelope:

`<e3_run_id>:<scenario_id>:source-target:correction:replay`

Its `raw_content` must equal the exact Source correction-message raw output.
No strip, normalization, rewrite, summary, prefix, or hand edit is allowed.

Freeze:

- author = `source`;
- recipient = `target`;
- creation source = `e3_exact_source_correction_replay`;
- relation = `correction_exact_replay`;
- represented version = `version_new_id`;
- decision validity = `current`.

### E.2 Replay provenance

Persist a sealed `correction_replay_provenance.json` row containing at least:

```text
scenario_id
e3_replay_message_id
source_correction_call_id
source_correction_message_id
content_hash
cache_key
origin_call_id
source_parent_snapshot_hash
source_correction_probe_call_id
source_corrected
correction_message_valid
relation="correction_exact_replay"
```

If the correction output is noncanonical or not CURRENT, no valid correction
replay envelope is created for headline C evidence.

## F. Target A/B/C and Clean-C Branch Construction

### F.1 Base histories

Use `reconstruct_e1_target_branch_snapshot` unchanged to recover:

- prior-infected base = E1 stale branch;
- clean base = E1 current branch.

The E3 wrapper may construct new immutable post-E1 snapshots, but it may not
mutate or rewrite the frozen E1 snapshot evidence.

### F.2 Visibility wrapper

Implement an E3-only immutable helper that can add a message to history without
necessarily adding it to `visible_message_ids`.

Required branch semantics:

```text
prior-infected E1 stale history
├── A: no correction in history; stale prior peer visible
├── B: exact correction in history but hidden; stale prior peer visible
└── C: exact correction in history and visible; stale prior peer + correction visible

matched clean E1 current history
└── Clean-C: exact correction in history and visible; current prior peer + correction visible
```

Visible-message order is frozen chronologically:

1. prior E1 peer evidence;
2. later Source correction replay, when visible.

The Target's prior E1 generated answer is eligibility evidence, not an extra
model-visible peer message unless a later human decision explicitly changes
that design.

### F.3 Model-visible equality requirements

A and B must produce byte-identical model-visible prompts and identical
`EffectiveGenerationIdentity` when the correction is hidden in B. Their
logical condition labels, snapshot hashes, and evidence metadata must not alter
the cache key.

C and Clean-C use the same prompt template, same correction raw text, same
correction position, same task, same model/config/seed policy, and same phase.
Their intended model-visible difference is the frozen prior history:
prior stale peer versus matched current peer.

### F.4 Frozen Target conditions and IDs

Use these condition strings:

- `target-a-uncorrected`;
- `target-b-corrected-invisible`;
- `target-c-corrected-visible`;
- `target-clean-c-visible`.

Calls:

`<e3_run_id>:<scenario_id>:target:<condition>:call`

Generated output messages replace `:call` with `:output`.

All four conditions use the designated E3 post-correction Target phase ID for
matched timing, while the evidence table records that A's Source branch is
uncorrected.

## G. E3 Correction Evidence Sidecar

### G.1 Rationale

Do not migrate the generic `CallRecord` merely to add E3-only correction flags.
The existing record lacks separate fields for correction delivery and
accessibility. The minimum implementation is a sealed E3 sidecar joined
mechanically to calls/messages.

### G.2 Artifact

Write once:

`e3_correction_evidence.json`

One row per E3 Target A/B/C/Clean-C logical decision must contain at least:

```text
scenario_id
condition
call_id
message_id
pair_id
prior_e1_condition
prior_e1_call_id
prior_e1_message_id
prior_e1_peer_message_id
prior_e1_answer_class
target_prior_stale_adopter
clean_reference
source_correction_probe_call_id
source_correction_message_call_id
correction_replay_message_id
source_corrected
correction_message_valid
correction_delivered
correction_accessible_at_decision
measurement_after_correction
parent_snapshot_hash
snapshot_hash
visible_message_ids
history_message_ids
eligibility
exclusion_reasons
evidence_digest
```

The sidecar is authoritative for E3 correction-state eligibility only when it
is manifest-sealed and agrees with calls, messages, snapshots, and lineage.
Condition names alone are never sufficient evidence.

## H. Cache Contract and Required Cross-Stage Reuse

### H.1 Cache identity

Reuse `EffectiveGenerationIdentity`, `build_cache_key`, `MessageCache`, and
`CachedBackend` unchanged. Experiment name, run ID, condition, logical Agent
role, snapshot hash, and E3 sidecar metadata must not be added to the cache key
unless already model-visible through the existing identity contract.

### H.2 Mandatory A/B alias

When A and B have identical rendered prompts and generation settings:

`cache_key(A) == cache_key(B)`

and the second logical call must reuse the exact cached output. A condition
namespace must never force a second physical generation.

### H.3 Mandatory cross-stage identity reuse

If an E3 logical call has the same complete effective generation identity as a
frozen prior scientific call, the shared scientific cache must reuse it.

In particular, implementation must test for natural aliasing of:

- Source correction awareness with an existing awareness-v3 identity;
- Source correction message / no-peer ordinary decision with an existing
  identical decision-v2 identity;
- Target A/B with the frozen E1 stale-peer decision identity when all rendered
  input and generation parameters are identical; and
- re-infection no-residual control with the Source correction-message identity
  when they are identical.

These aliases are integrity requirements, not assumptions about whether a
particular deployment cache still contains every prior key. A missing
operational cache entry may generate the downstream logical call once; it may
never regenerate frozen upstream E1 evidence through an upstream resolver.

## I. CVRR and Clean Reference Metric Contract

### I.1 Pure offline evaluator

Extend `state_mad/metrics.py` with a pure function conceptually equivalent to:

```text
evaluate_e3_residue(
    target_calls,
    correction_evidence,
    lineage_report,
    candidate_ids,
) -> dict
```

It performs no file I/O, tokenizer call, backend call, or generation.

### I.2 C eligibility

A scenario enters the raw C CVRR denominator only if all are true:

- scenario is one of the exact nine frozen prior stale adopters;
- `target_prior_stale_adopter=true`;
- Source correction probe is canonical CURRENT;
- `source_corrected=true`;
- correction message is canonical CURRENT;
- `correction_delivered=true`;
- `correction_accessible_at_decision=true`;
- `measurement_after_correction=true`;
- C Target call completed;
- no infrastructure failure; and
- lineage/evidence joins pass.

A completed `OTHER/INVALID` remains in the denominator and is non-STALE.

CVRR numerator: C Target answer class = `STALE`.

### I.3 Clean-C matched reference

For every C-eligible scenario, the matched clean call must use the E1 current
branch plus the exact same correction replay and downstream construction.

Report separately:

- raw C denominator/numerator/rate (`CVRR_C`);
- clean complete denominator/numerator/rate (`CVRR_clean`);
- complete paired C/Clean-C IDs;
- paired stale indicators;
- paired difference `mean[I(C=STALE)-I(Clean-C=STALE)]`; and
- all exclusion reasons.

Gate-5 comparison uses only complete matched C/Clean-C pairs, while raw C CVRR
is also reported independently.

### I.4 Gate 5 at the current pilot

Because candidate N is fixed at 9, the current implementation must never emit
`POSITIVE PILOT` for Gate 5.

Freeze current-scale output:

`gate_5 = "NOT ESTIMABLE AT PILOT SCALE"`

The report may additionally expose descriptive diagnostic booleans such as
whether `CVRR_C - CVRR_clean >= 0.10` and whether at least two residual cases
occurred, but those booleans cannot override the N gate.

No negative population-level RQ3 conclusion is promoted automatically at this
structurally sub-threshold pilot scale.

## J. Correction-Visible Residual Retransmission

A C Target output graded STALE after all C eligibility checks is a
correction-visible residual stale outcome.

It becomes a correction-visible **retransmission** only when that exact residual
output is actually wrapped and delivered downstream as the nested Target→Source
residual replay described below. A merely stale C decision is residual belief,
not automatically a retransmission event.

The report must keep these counts distinct:

- correction-visible residual C cases;
- residual replay envelopes actually constructed/delivered; and
- Source re-infection outcomes after those deliveries.

## K. Nested Re-Infection Design

### K.1 Eligibility selector

After the base residue phase, mechanically select only C cases satisfying all
C eligibility checks and grading `STALE`.

If there are zero such cases, plan zero re-infection calls.

No artificial residual message may be created to make this set non-empty.

### K.2 Exact residual replay

For each naturally eligible residual case, create one exact Target→Source replay
envelope:

`<e3_run_id>:<scenario_id>:target-source:residual:replay`

Freeze:

- raw text = exact C Target `raw_output`;
- content hash = exact C Target output hash;
- author = `target`;
- recipient = `source`;
- creation source = `e3_exact_residual_replay`;
- relation = `residual_exact_replay`;
- represented version = `version_old_id` after mechanical STALE grading.

Persist `residual_replay_provenance.json` with the complete C-call/message
origin, content hash, cache origin, scenario, and Source/Target IDs.

### K.3 Re-infection control mode

Freeze the allowed control choice to:

`same-corrected-source-no-residual`

Do not use a matched-current peer message in the current pilot.

Treatment/control topology:

```text
same verified-corrected Source parent
├── source-reinfection-control       # no residual peer message
└── source-reinfection-treatment     # exact residual Target message only
```

Both branches use the same Source parent, same current state, same task,
same phase, same model/config/seed policy. The only intended model-visible
difference is the exact residual Target message.

### K.4 Call IDs

Use:

- `<e3_run_id>:<scenario_id>:source:reinfection-control:call`;
- `<e3_run_id>:<scenario_id>:source:reinfection-treatment:call`.

Both calls use the E3 re-infection phase ID.

If the no-residual control renders the same effective input as the earlier
Source correction-message call, it must use the same cache key and exact cached
output.

### K.5 Re-infection metric

Extend `metrics.py` with pure offline evaluation reporting:

- naturally residual candidate IDs/N;
- complete matched re-infection IDs/N;
- treatment STALE count/rate;
- control STALE count/rate;
- paired difference;
- treatment-only re-infection IDs where treatment is STALE and control is not;
- frozen Re-infection Rate = treatment STALE count / eligible matched N;
- exclusions/reasons; and
- interpretation field.

A matched control is mandatory for causal wording. A Source already STALE in
the no-residual control must not be described as newly re-infected by the
residual message.

If naturally eligible residual cases are fewer than 5, the report must mark
re-infection as **descriptive only** with no independent headline claim.

## L. E3 Lineage Contract

### L.1 Extension

Extend `state_mad/lineage.py` with E3-only relation vocabulary and a pure
`validate_e3_lineage(...)` validator. Existing E0/E1/E2 validators remain
unchanged.

Freeze the new relation names:

- `source_correction_awareness_sibling`;
- `source_correction_message_sibling`;
- `source_correction_verified`;
- `correction_exact_replay`;
- `correction_to_target_history`;
- `correction_to_target_visible`;
- `prior_stale_adopter_origin`;
- `clean_reference_origin`;
- `target_correction_visible_residual`;
- `clean_reference_pair`;
- `residual_exact_replay`;
- `target_to_source_residual_exposure`;
- `reinfection_matched_sibling`; and
- `source_reinfection`.

### L.2 Validator requirements

The validator must fail closed on at least:

- missing/duplicate message or call IDs;
- cross-scenario edges;
- cycles;
- Source correction probe contamination of correction-message or Target paths;
- a Source marked corrected without canonical CURRENT probe evidence;
- correction replay whose raw text/hash differs from Source correction output;
- B with correction present in model-visible parent IDs/prompt;
- B lacking the correction in sealed history when `correction_delivered=true`;
- C lacking correction delivery or visible correction ancestry;
- C counted without post-correction ordering;
- wrong E1 prior-stale origin;
- clean branch not bound to the matched E1 current branch;
- residual replay not originating from a naturally eligible C STALE output;
- hand-created/synthetic residual messages;
- re-infection treatment/control with different Source parent hashes;
- correction probe output in re-infection history;
- a re-infection claim without matched control; or
- sidecar/call/message/snapshot disagreement.

Every CVRR, residual retransmission, and re-infection claim must be mechanically
reconstructable from sealed records.

## M. E3 Preflight Contract

### M.1 Configuration

Extend `state_mad/preflight.py` with `E3RunConfig` and E3-only validators.
Do not weaken or modify the meaning of E0/E1/E2 validation.

Freeze the E3 configuration constraints:

| Field | Required value / bound |
| --- | --- |
| `experiment` | `E3` |
| `method` | `state-mad-e3` |
| `mode` | `dry-run` or later `scientific` |
| models | exactly `Qwen/Qwen2.5-7B-Instruct` |
| model revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| tokenizer revision | explicit and equal to frozen E1/E2 scientific revision when scientific execution is later authorized |
| seed | `7` |
| temperature | `0.0` |
| top-p | `1.0` |
| max new tokens | `32` |
| candidate IDs | exact frozen nine-ID tuple |
| logical Agents | `2` |
| max communication hops | `2` |
| base logical-call maximum | `54` |
| nested re-infection calls | `2 * residual_n` |
| total logical-call maximum | `72` |
| planning ceiling | `800000` tokens |
| re-infection control mode | `same-corrected-source-no-residual` |
| Gate-5 pilot-positive estimable | `false` at current frozen nine-case scale |

### M.2 Whole-set model-free preflight

Before any future model call, validate:

- exact upstream E1 identity and nine-case set;
- overlay uniqueness and digests;
- source correction parent topology;
- correction sibling isolation;
- A/B/C/Clean-C condition flag matrix;
- exact correction replay construction;
- prior-stale and clean matched base histories;
- B history-present/visibility-hidden semantics;
- A/B rendered prompt and effective-identity equality;
- C/Clean-C correction-text equality and ordering;
- sidecar schema/join integrity;
- run-store nonexistence/write-once safety;
- scientific cache/run-store separation;
- resource bounds; and
- maximum call projection.

This model-free preflight must not instantiate a tokenizer or language model.

### M.3 Nested re-infection preflight

After base C outputs exist, run a second pure nested selector/preflight before
any re-infection generation. It must require:

- every selected residual is a naturally produced, eligible C STALE output;
- exact residual replay provenance;
- same corrected Source parent for treatment/control;
- no probe contamination;
- no synthetic residual;
- `residual_n <= 9`;
- nested calls exactly `2 * residual_n`; and
- total logical calls `<= 72`.

If `residual_n == 0`, nested preflight succeeds with zero planned re-infection
calls.

## N. Token and Call Projection

### N.1 Logical-call envelope

Base maximum per scenario:

1. Source correction awareness;
2. Source correction message;
3. Target A;
4. Target B;
5. Target C;
6. Target Clean-C.

For nine scenarios: `54` logical calls maximum before re-infection.

Nested re-infection adds exactly two logical calls per naturally eligible C
residual case. With at most nine residual cases, total E3 logical calls are
bounded by `72`.

### N.2 Physical generation expectations

Physical generations may be lower because effective-input cache reuse is
mandatory. In particular, A/B must alias, and identical cross-stage identities
must reuse existing cached outputs when present.

No scientific claim may depend on a particular hit/miss count. The manifest
must record actual logical and generated token usage separately.

### N.3 Future tokenizer-only gate

This map does not authorize tokenizer access.

Before any E3 scientific generation, a separately authorized tokenizer-only
preflight must:

- project exact base-call prompt tokens for the frozen nine cases;
- reserve output tokens using max-new-tokens;
- conservatively reserve the worst-case nested re-infection envelope within the
  72-call maximum; and
- remain below the frozen `800000` planning ceiling.

If residual cases are later observed, exact tokenizer accounting for the actual
nested prompts must be recomputed before nested scientific calls. No token
projection may silently trigger model loading.

## O. Run Artifacts and Manifest Binding

### O.1 Required E3 write-once artifacts

The future E3 run directory should contain at least:

```text
calls.jsonl
lineage.jsonl
manifest.json
report.json
messages/
e3_scenario_overlay.json
e3_correction_evidence.json
correction_replay_provenance.json
residual_replay_provenance.json
branch_topology.json
eligibility.json
cache_provenance.json
```

`residual_replay_provenance.json` may be an empty sealed array when no natural
C residual exists.

### O.2 Manifest

Reuse `build_manifest` / `finalize_manifest` and bind hashes for every E3
evidence artifact, including overlay, correction evidence, both replay
provenance tables, topology, eligibility, calls, lineage, report, messages,
and preflight.

The manifest must retain exact repository SHA, branch/dirty state, model and
tokenizer revisions, seed, decoding, runtime, token usage, cache statistics,
and frozen E1 upstream references.

## P. Implementation Order

If a later human authorization permits E3 implementation, implement only in
this order:

1. E3 immutable overlay and read-only E1 reuse;
2. Source correction parent/sibling planning;
3. exact correction replay envelope and sidecar;
4. Target A/B/C/Clean-C visibility wrapper and request planning;
5. pure CVRR/clean metric;
6. E3 lineage validator;
7. E3 model-free preflight;
8. natural residual selector and exact residual replay;
9. nested re-infection planning/metric;
10. run persistence/manifest assembly;
11. model-free tests only.

Do not implement E4 or any scale expansion as part of E3.

## Q. Required Model-Free Tests

`tests/state_mad/test_e3.py` must cover at least:

1. exact nine-ID E1 resolution and zero upstream mutation;
2. E2 second-hop-positive set is not substituted for E3 eligibility;
3. stale/current E1 branch reconstruction remains exact;
4. Source correction parent remains immutable across siblings;
5. Source correction awareness output never contaminates correction-message or Target histories;
6. Source corrected flag requires canonical CURRENT probe;
7. invalid/non-current correction message cannot create valid C correction evidence;
8. correction replay preserves exact raw text/content hash;
9. A has no correction in history;
10. B has correction in history but not visibility;
11. C has the same correction in history and visibility;
12. Clean-C uses the same correction raw text and position as C;
13. A/B rendered prompts are byte-identical;
14. A/B effective identities and cache keys are identical;
15. condition/run/snapshot metadata alone cannot split the cache key;
16. identical prior scientific effective identity reuses the normal shared cache;
17. infected C and Clean-C use matched task/config/phase construction;
18. CVRR denominator rejects missing Source correction;
19. CVRR denominator rejects missing valid correction message;
20. CVRR denominator rejects missing delivery;
21. CVRR denominator rejects missing accessibility;
22. CVRR denominator rejects pre-correction measurement;
23. completed OTHER/INVALID remains in the denominator as non-STALE;
24. Gate 5 cannot become positive with C eligible N < 10;
25. clean matched contrast uses only complete paired C/Clean-C cases;
26. zero natural residual cases plan zero re-infection calls;
27. only naturally eligible C STALE output can become a residual replay;
28. residual replay exact raw text/content hash cannot be edited;
29. treatment/control re-infection branches share one corrected Source parent;
30. re-infection control mode is exactly no-residual;
31. identical no-residual control identity reuses Source correction-message cache when applicable;
32. re-infection metric reports treatment/control rates, paired difference, and treatment-only IDs;
33. fewer than five residual cases forces descriptive-only re-infection interpretation;
34. E3 lineage rejects invisible-as-visible correction;
35. E3 lineage rejects wrong E1 origin, cross-scenario edge, cycle, synthetic residual, and wrong Source parent;
36. E3 metric and lineage recomputation use zero model/tokenizer/backend calls;
37. preflight rejects >3 Agents, >2 hops, extra model/seed/scenario, wrong revision, wrong control mode, unsafe roots, or >72 logical calls;
38. upstream E1 bytes are unchanged after full dry-run orchestration; and
39. existing E0/E1/E2 tests remain unchanged and pass.

No test may call a tokenizer merely to validate canonical `ANSWER=<value>`
structure.

## R. File-Level Delta Freeze

| Path | Action | E3 responsibility | Constraint |
| --- | --- | --- | --- |
| `state_mad/e3.py` | **NEW** | E3 overlay, read-only E1 reuse, Source correction siblings, correction replay, A/B/C/Clean-C branches, sidecar, residual replay, nested re-infection, run assembly | Isolated wrapper only |
| `state_mad/preflight.py` | **EXTEND** | `E3RunConfig`, whole-set E3 checks, nested residual preflight | Do not weaken E0/E1/E2 validators |
| `state_mad/lineage.py` | **EXTEND** | E3 relation set and `validate_e3_lineage` | Preserve existing E0/E1/E2 semantics |
| `state_mad/metrics.py` | **EXTEND** | CVRR, Clean-C contrast, Gate 5, Re-infection Rate | Pure offline only |
| `tests/state_mad/test_e3.py` | **NEW** | Model-free contract tests | No tokenizer/model/GPU/network requirement |
| `state_mad/e2.py` | **REUSE** | E1 resolver and E1 branch reconstruction | No weakening or duplication |
| `state_mad/schema.py` | **REUSE** | Generic records unchanged | Missing E3 flags live in sealed sidecar |
| `state_mad/snapshots.py` | **REUSE** | Base immutable record/helpers | E3 wrapper handles hidden visibility |
| `state_mad/prompts.py` | **REUSE** | awareness-v3 / decision-v2 | No prompt change without human review |
| `state_mad/cache.py` | **REUSE** | shared scientific cache | Preserve effective-input identity |
| `state_mad/backend.py` | **REUSE** | downstream generation only | No upstream E1 generation path |
| `state_mad/grading.py` | **REUSE** | deterministic classes | No LLM judge |
| `state_mad/run_store.py` | **REUSE** | write-once persistence | No storage redesign |
| `state_mad/manifest.py` | **REUSE/WRAP** | seal E3 artifacts | Hash every new evidence table |
| `state_mad/scenarios.py` | **REUSE unchanged** | frozen E1 scenarios | No new scenario family |
| `state_mad/validation.py` | **REUSE unchanged** | frozen E1 scenario validation | No E3 rewrite of scenario hash |
| `state_mad/e1.py` | **REUSE read-only** | frozen upstream evidence | Never rerun/modify for E3 |
| `src/**` | **REUSE unchanged** | MAD-M² core | Any proposed edit is STOP |

The implementation authorization, if later granted, should be restricted to
exactly the five NEW/EXTEND files above. Any sixth source/test file requires a
specific explanation and human review before modification.

## S. STOP / Human-Decision Triggers

STOP and request `需要人工决策` if any of the following occurs:

- the nine frozen E1 prior stale adopters cannot be reproduced exactly;
- any E1/E2 upstream evidence would need regeneration, normalization, editing,
  or substitution;
- a proposal conditions E3 only on the six E2 second-hop-positive cases;
- B cannot be encoded as delivered-but-inaccessible without making hidden
  correction metadata model-visible;
- A/B identical model-visible inputs receive different effective cache keys;
- Source correction probe and correction-message branches cannot remain
  siblings of one immutable parent;
- a valid C condition cannot prove Source correction, valid correction content,
  delivery, accessibility, and post-correction measurement separately;
- the Clean-C reference cannot reuse the matched E1 current branch and exact
  same correction replay;
- a residual message would need to be synthetic, researcher-authored,
  normalized, summarized, or otherwise altered;
- re-infection treatment/control cannot share the same verified-corrected
  Source parent;
- implementing E3 appears to require changing `awareness-v3`, `decision-v2`,
  the generic schema, `snapshots.py`, or MAD-M² `src/**` rather than a bounded
  wrapper;
- total E3 logical calls would exceed 72;
- current pilot scale would be enlarged merely to make Gate 5 estimable;
- >3 Agents, >2 main rounds/hops, an extra model, seed, baseline, scenario
  family, RL, fine-tuning, learned detector/router, semantic parser, graph
  memory, or LLM-as-a-Judge is proposed; or
- tokenizer/model/GPU/scientific generation is requested before the later
  explicit gates.

No stop trigger may be automatically repaired by expanding research scope.

## T. Implementation Acceptance Gate

A future E3 implementation can be considered **implementation-complete but not
scientifically authorized** only when all are true:

- only the approved file-level delta is changed;
- all E3 model-free tests pass;
- all existing E0/E1/E2 tests pass unchanged;
- exact nine-case upstream resolution passes against real frozen E1 artifacts;
- E1 upstream bytes remain unchanged;
- A/B cache-identity assertion passes;
- C/Clean-C exact correction matching passes;
- CVRR/Gate-5 offline logic returns `NOT ESTIMABLE AT PILOT SCALE` for the
  frozen nine-case maximum;
- zero-residual dry-run produces zero nested re-infection calls;
- synthetic/wrong-origin residual tests fail closed;
- maximum call projection is `<=72`;
- `git diff` contains no MAD-M² core or frozen research-artifact changes; and
- no tokenizer/model/GPU call was required for implementation acceptance.

Only after this gate and separate human authorization may tokenizer-only budget
preflight be considered. Scientific E3 execution requires another explicit
human authorization after that preflight.

## U. Planning Verdict

**IMPLEMENTATION-READY WITH FROZEN PILOT-SCALE ESTIMABILITY LIMIT**

The E3 implementation path is now sufficiently specified to hand to Codex as a
bounded implementation task without reopening RQ3. The required mechanism is:

`natural E1 stale adopter → Source correction verified → exact correction frozen → A/B/C visibility control → correction-visible Target residual measurement → optional exact residual replay → same-parent Source re-infection test`

The implementation must preserve the principal scientific limitation:
current natural candidate N is 9, so the frozen Gate-5 positive threshold of
10 cannot be reached in this pilot. This is a result-design boundary, not a
software defect.

This map authorizes no code change and no scientific execution. The next gate
is explicit human authorization for the bounded E3 implementation delta only.
