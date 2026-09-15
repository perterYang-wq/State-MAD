# State-MAD E3 Repository Delta Audit

Status: **AUDIT ONLY — NO IMPLEMENTATION OR E3 SCIENTIFIC EXECUTION AUTHORIZED**

Stage: E3-specific Repository Delta Audit

Audit base: `main @ c057117dc7b60bb1bec4d7ab6f4d7890eadd3155`

## 1. Audit Scope and Authority

This document is a read-only repository audit for the frozen E3 / RQ3 design.
It does not modify experiment code, reopen RQ3, authorize an E3 Implementation
Map, authorize implementation, authorize tokenizer/model/GPU access, or
authorize E3 scientific generation.

Authority is applied in this order:

1. `research/RESEARCH_CONTRACT.md`;
2. `research/EXPERIMENT_PLAN_FROZEN.md`;
3. `research/IMPLEMENTATION_REQUIREMENTS.md`;
4. `research/03_EXPERIMENT_PLAN_REVIEW.md`;
5. `research/04_REPOSITORY_AUDIT.md` and the approved general Implementation Map;
6. the completed E1/E2 implementation and frozen result artifacts; and
7. this E3-specific delta audit.

The narrow audit question is:

> Can the repository at the stated base support the frozen correction-visible
> residue and nested re-infection design with a minimal E3 wrapper/extension,
> and what exact capability gaps must be resolved before any E3 implementation?

The answer is **yes, with bounded gaps**, but the frozen current pilot has a
hard estimability limitation described in Section 3.

## 2. Frozen E3 / RQ3 Scientific Contract

RQ3 remains unchanged:

> 当原始 stale source Agent 已经获得 current-state correction，且该 correction
> 已经对先前暴露的 Agents 可见之后，系统中是否仍存在 residual stale belief、
> secondary stale retransmission，或对已纠正 Agent 的 re-infection？

A correction-visible residue measurement is valid only after all of the
following are true:

- Source has obtained `v_new`;
- Source no longer treats `v_old` as current;
- Source correction is behaviorally verified;
- correction is delivered to the Target;
- correction is accessible/visible to the Target at decision time; and
- the residual measurement occurs afterward.

Only then can a Target output of `v_old`, treatment of `v_old` as current, or
retransmission of `v_old` count as RQ3 evidence. Correction-invisible
persistence is a control outcome, not RQ3 evidence.

The frozen E3 conditions are:

- **A — Source uncorrected:** persistent-exposure control; cannot support RQ3.
- **B — Source corrected, correction invisible:** access control; cannot support RQ3.
- **C — Source corrected + correction delivered + correction visible/accessibile:** the only headline RQ3 condition.

E3 may use only naturally observed prior stale adopters. It may not manufacture
an infected Target or an artificial residual stale message.

The clean matched reference is not a new baseline. It is a never-stale-adopted
cached branch with the same correction message, same visibility, same decision
prompt, and same downstream snapshot construction.

Re-infection is nested and is run only when a real C-condition residual Target
message exists. Treatment replays that exact residual message to an already
verified-corrected Source; the matched control uses the same corrected Source
snapshot without the residual message, or the prespecified matched-current
message if the later E3 Implementation Map freezes that option.

## 3. Frozen Upstream Evidence and Pilot Estimability

### 3.1 Natural prior stale-adopter set

The frozen E1 pilot contains exactly nine paired treatment-only causal stale
adopters:

`e1-04`, `e1-10`, `e1-16`, `e1-18`, `e1-22`, `e1-28`, `e1-30`,
`e1-34`, `e1-40`.

In E1, stale-peer produced nine STALE outcomes and current-peer produced zero
STALE outcomes. Therefore the current frozen 40-scenario pilot supplies at
most **9 naturally observed eligible prior stale Targets** for E3.

E2 does not enlarge this set. E2 conditions on those same nine primary
adopters and is downstream RQ1 evidence. Its six second-hop-positive cases do
not replace the frozen E3 prior-stale-adopter definition.

### 3.2 Gate-5 consequence

The frozen E3 Pilot Gate 5 requires all of:

- C-condition eligible N `>= 10`;
- `CVRR_C >= CVRR_clean + 0.10`; and
- at least two correction-visible residual stale cases.

Because the natural upstream E1 adopter pool has maximum N = 9, the current
40-scenario pilot **cannot satisfy the N >= 10 pilot-positive gate**, even if
every E3 correction/visibility check later succeeds.

Therefore, without changing any frozen design:

> **E3 GATE-5 POSITIVE STATUS IS NOT ESTIMABLE AT THE CURRENT PILOT SCALE.**

A later authorized E3 pilot may still produce scientifically useful bounded
**descriptive** evidence: C eligible N, CVRR_C, clean-reference CVRR, residual
case IDs/counts, correction-visible retransmission evidence, and any naturally
eligible re-infection outcomes. But it must not be promoted to the frozen
Gate-5 positive headline at N < 10.

No automatic data expansion is permitted. Adding scenarios, seeds, models,
Agents, or rounds merely to cross the Gate-5 threshold is **需要人工决策** and is
outside this audit.

### 3.3 Re-infection estimability

Re-infection eligibility is determined only after C-condition execution. If
fewer than five naturally occurring C residual cases exist, the frozen plan
requires descriptive Re-infection Rate only, with no independent headline
claim. No synthetic residual message may be introduced to increase N.

## 4. Current Repository Capability Map

| E3 operation | Classification | Current capability / bounded gap |
| --- | --- | --- |
| Resolve natural prior stale adopters | **REUSE** | `state_mad.e2.resolve_e1_replay_pairs` already validates the complete frozen E1 run and reconstructs the exact nine eligible paired adopters without regeneration. |
| Reconstruct infected and clean Target histories | **REUSE/WRAP** | `reconstruct_e1_target_branch_snapshot(pair, "stale"|"current")` reconstructs the stale-adopted branch and matched current/clean branch. E3 must append only new post-correction state through an isolated wrapper. |
| Immutable Source correction parent | **WRAP** | `Snapshot` is sufficient, but no Source-correction constructor exists. E3 needs a deterministic wrapper/overlay rather than editing E1 scenario bytes. |
| Source correction-verification sibling | **REUSE/WRAP** | `awareness-v3` is role-neutral and can behaviorally test `v_new`; E3 must isolate its output from the correction-message sibling. Exact use must be frozen by the E3 Implementation Map. |
| Source correction-message sibling | **REUSE/WRAP** | Existing `decision-v2`, grading, cache, and MessageRecord can generate/freeze one canonical Source correction output. No current repository evidence forces a new prompt. |
| Conditions A/B/C | **WRAP** | Snapshot fields distinguish stored/history message IDs from model-visible message IDs, but current `fork_snapshot` makes every addition visible. E3 needs a thin visibility constructor for hidden vs visible correction. |
| Exact correction-message reuse | **REUSE** | `MessageRecord.raw_content`, `CachedBackend`, and MessageCache preserve exact text. B/C must refer to the same frozen correction message rather than regenerating it. |
| Clean matched reference | **REUSE/WRAP** | The E1 matched current branch is a natural never-stale-adopted reference for each of the nine cases; E3 applies the same correction and downstream construction. |
| Deterministic grading | **REUSE** | `grade_output` already maps exact categorical outputs to CURRENT / STALE / STATIC_WRONG / OTHER/INVALID. |
| CVRR | **EXTEND** | `metrics.py` has E0/E1/E2 metrics but no CVRR implementation. |
| Re-infection Rate | **EXTEND** | `metrics.py` has no re-infection metric or eligibility/exclusion logic. |
| Correction/re-infection lineage | **EXTEND** | `lineage.py` validates E0/E1/E2 only and has no Source-correction, correction-delivery/accessibility, residual, or re-infection relations. |
| E3 preflight | **EXTEND** | `preflight.py` has E0/E1/E2 config/validators only. E3 needs a whole-plan fail-closed validator and exact call/token projection. |
| E3 orchestration | **NEW** | No `state_mad/e3.py` exists. A narrow E3 wrapper should own the E3 overlay, source-correction siblings, A/B/C branches, clean reference, residual replay, nested re-infection, and artifact assembly. |
| Call-level correction flags | **WRAP preferred** | `CallRecord` has `source_correction_status` and one `correction_visibility` field, but lacks separate `correction_delivered` and `correction_accessible_at_decision` fields required by the frozen logging contract. Prefer a sealed E3 evidence sidecar keyed to calls/messages instead of breaking prior schemas. |
| Run persistence | **REUSE** | `RunStore` already supports append-only calls/lineage/messages and write-once JSON evidence. |
| Manifest/provenance | **REUSE/WRAP** | Generic manifest hashing works; the E3 wrapper must seal all new correction-evidence, topology, eligibility, residual, and re-infection artifacts. |
| Cache/backend | **REUSE** | Existing effective-generation identity gives exact replay/hit behavior and refuses duplicate cache commits. |
| Scenario compiler / E1 scenario hash | **REUSE unchanged** | No new scenarios are needed for the current pilot. E3 should overlay new correction events/roles rather than mutate the frozen E1 scenario set. |
| MAD-M² core `src/**` | **REUSE unchanged** | Static inspection finds no E3 requirement that forces a core modification. |

## 5. Read-Only E1 / E2 Inheritance Audit

### 5.1 E1 is the authoritative E3 upstream infection source

E3 should not infer infection from E2 final votes or regenerate an E1 call.
The existing E2 read-only resolver already performs the needed whole-run
authentication:

- manifest identity and finalization;
- scientific repository SHA;
- scenario-set hash;
- model/tokenizer/decoding identity;
- exact awareness and stale/current call selection;
- CallRecord/MessageRecord/content-hash agreement;
- cache-provenance agreement;
- canonical structured output check; and
- recomputation of the exact nine E1 causal-adopter IDs.

This is sufficient as the E3 upstream selector. E3 should import/reuse it
rather than write a second permissive resolver.

### 5.2 E1 bytes remain read-only

The E2 orchestrator already demonstrates a fail-closed pattern: snapshot the
upstream E1 files before reconstruction and verify that their bytes are
unchanged afterward. E3 should preserve the same property. No E1/E2 call may
be regenerated merely because a scientific cache entry is absent.

### 5.3 E2 artifacts are not required to define E3 eligibility

E2 is useful implementation precedent for overlays, exact replay, sibling
isolation, provenance tables, preflight, lineage, and run sealing. The frozen
E3 eligibility pool, however, comes from naturally observed prior stale
Targets in E1. E3 must not silently condition CVRR on the six E2 second-hop
positive cases unless the frozen plan is explicitly reopened by human decision.

## 6. Source Correction and Sibling Isolation Audit

The frozen plan requires one immutable Source correction snapshot with at
least two sibling operations:

```text
immutable Source correction parent
├── correction-verification probe
└── correction-message generation
```

The current `Snapshot` dataclass and immutable `fork_snapshot` semantics are
sufficient for sibling isolation, but there is no Source-specific constructor.
The smallest future delta is an E3 wrapper that creates and seals a deterministic
Source correction parent bound to the original scenario plus an E3 overlay.
The frozen E1 `ScenarioRecord` should not be edited to add Source-correction
events.

The correction probe output must never be appended to the correction-message
history or become visible evidence for Target A/B/C. The Source is marked
`source_corrected=true` only after mechanical grading shows CURRENT / `v_new`.
Because the answer pool is closed and `v_old` has its own STALE class, a
canonical CURRENT probe is sufficient to verify that the Source no longer
selects `v_old` as the current value in this controlled categorical setting.

The correction message itself should be generated/frozen once from the
sibling branch and must be mechanically canonical. If it does not express the
current value, it cannot serve as a valid visible correction for condition C;
the future E3 preflight should fail closed rather than edit the message.

Static inspection finds no present need to change `awareness-v3` or
`decision-v2`. Any future proposal to change model-visible prompt semantics
must be justified at the E3 Implementation Map gate and must not be used as a
post-hoc rescue.

## 7. A/B/C Visibility and Cache-Identity Audit

### 7.1 Snapshot representation

`Snapshot` already separates:

- `message_ids` — branch/history membership; and
- `visible_message_ids` — model-visible evidence.

This is enough to represent an invisible correction without a schema redesign.
The helper `fork_snapshot` is not enough by itself because every addition is
currently placed in both sets. The smallest delta is an E3-only wrapper that
constructs a new immutable Snapshot with the correction recorded in history
where appropriate but excluded from `visible_message_ids` for B, and included
for C.

The exact B-condition delivery flag must be frozen in the E3 Implementation
Map. The frozen text defines B as corrected-but-invisible access control and C
as corrected + delivered + accessible. The implementation must encode these
flags explicitly and consistently; it must not infer them later from prose.
Only C can enter the headline CVRR denominator regardless of the B encoding.

### 7.2 Mandatory A/B cache alias when model-visible input is identical

`MessageCache` is keyed only by `EffectiveGenerationIdentity`, which contains
the complete model-visible prompt and generation parameters, not the E3
condition label or snapshot metadata.

Therefore, if A and B produce identical model-visible Target input — as they
should when the correction is unavailable/invisible and no correction-status
metadata is rendered to the model — A and B must resolve to the same cache key
and exact same model output. The implementation may log two logical condition
records if needed, but it must not cause two physical generations merely to
separate A from B.

This is a required integrity property, not an optimization. Artificially
namespacing A/B cache keys would violate the frozen cache contract and confound
correction visibility with an otherwise identical rerun.

C differs naturally because the exact correction message is model-visible.
Its changed prompt therefore receives a distinct effective generation identity.

## 8. Clean Matched Reference Audit

For every one of the nine natural stale-adopter scenarios, E1 already stores a
matched `current-peer` Target branch from the same original pre-exposure
snapshot. In all nine selected pairs that branch is not STALE.

That existing branch is the smallest clean reference source. E3 can
reconstruct it with the existing read-only helper and apply:

- the exact same frozen Source correction message used in C;
- the same visibility/accessibility setting;
- the same post-correction decision prompt;
- the same E3 phase construction; and
- the same model/config/seed policy.

The intended difference is prior stale adoption/history versus the matched
clean history. No fifth baseline, extra scenario family, or extra model is
needed.

The future metric output must report `CVRR_C` and the matched clean rate with
explicit denominators and IDs. The clean reference is a control for recovery,
not a population comparator.

## 9. CVRR and Gate-5 Metric Gap

`metrics.py` currently contains E0 SAR/CSAE, E1 metrics, `SRR_cond`, and the E2
FSCR tiers. It does not implement CVRR.

A future pure offline `evaluate_e3_residue(...)` should be able to recompute,
without model access:

- upstream candidate IDs;
- verified Source-corrected IDs;
- C correction-delivered IDs;
- C correction-accessible-at-decision IDs;
- completed C Target decision IDs;
- C denominator and exclusions;
- residual STALE numerator IDs/count/rate (`CVRR_C`);
- matched clean denominator/numerator/rate;
- paired `CVRR_C - CVRR_clean` contrast;
- correction-visible retransmission IDs/count where mechanically defined by the frozen trace; and
- Gate-5 status.

The Gate-5 evaluator must first enforce the frozen N requirement. At the
current pilot, N cannot exceed 9, so a positive Gate-5 label must be impossible.
The expected scale label is `NOT ESTIMABLE AT PILOT SCALE`, while descriptive
rates/counts remain reportable.

`OTHER/INVALID` completed outputs should remain in valid denominators and count
as non-STALE unless the frozen plan says otherwise; only infrastructure failure
or missing frozen eligibility conditions justify denominator exclusion.

## 10. Nested Re-infection Replay Audit

No re-infection call is eligible until a naturally generated C-condition
Target output is mechanically graded STALE after verified visible correction.

For each such case, the exact Target residual raw output should be frozen as an
immutable Target→Source replay envelope. The E2 exact-replay pattern is already
sufficient precedent: preserve raw content and content hash, assign new E3
message identity, and seal cross-stage origin/provenance separately rather
than rewriting the text.

Required topology:

```text
same verified-corrected Source parent
├── no-residual matched control
└── exact residual-Target-message treatment
```

The Source treatment/control must be siblings of the same corrected Source
snapshot. The residual message may never be researcher-authored, normalized,
summarized, or synthetically substituted.

If the no-residual control has exactly the same model-visible prompt and
parameters as an already generated corrected-Source ordinary decision, normal
cache identity requires reuse rather than regeneration. The E3 Implementation
Map must enumerate this identity explicitly so call accounting and cache-hit
expectations are deterministic before scientific execution.

Re-infection numerator: corrected Source returns to STALE / `v_old` under the
residual-message treatment. A matched treatment-minus-control contrast should
be retained so a Source already stale without residual exposure is not called
re-infected.

If fewer than five naturally eligible residual cases exist, the result remains
descriptive by frozen design.

## 11. Logging, Evidence, and Lineage Gap

### 11.1 CallRecord gap

The generic `CallRecord` currently stores `source_correction_status` and one
`correction_visibility` field. The frozen logging contract separately requires:

- `source_corrected`;
- `correction_delivered`; and
- `correction_accessible_at_decision`.

The current record cannot unambiguously carry all three as distinct booleans or
controlled statuses.

The preferred minimal solution is not to break every E0/E1/E2 constructor.
Instead, an E3-specific sealed evidence table/overlay keyed by `call_id`,
`message_id`, scenario, condition, and snapshot can carry the missing fields,
and E3 metrics/lineage must join it mechanically. A schema-wide change is not
currently justified by static inspection.

The exact sidecar schema is an Implementation Map decision. It must be written
once, hash-sealed in the E3 manifest, and sufficient to reconstruct all RQ3
eligibility without researcher text interpretation.

### 11.2 E3 lineage gap

`lineage.py` currently recognizes E2 relations and validates two-hop RQ1/FSCR
paths. It has no E3 vocabulary or validator for:

- verified Source correction;
- probe sibling isolation;
- correction-message origin;
- correction delivery;
- correction accessibility/visibility;
- prior-stale branch inheritance;
- post-correction Target residual output;
- clean-reference pairing;
- exact residual replay; or
- corrected-Source re-infection treatment/control.

A future `validate_e3_lineage` should fail closed on missing message IDs,
cross-scenario edges, cycles, correction-probe contamination, invisible
correction accidentally rendered to B, a non-visible correction counted in C,
wrong Source parent for re-infection, non-exact residual replay, or manufactured
residual evidence.

Every CVRR/re-infection claim must be reconstructable from sealed records and
lineage alone.

## 12. Preflight, Cache, Budget, and Persistence Audit

### 12.1 E3 preflight

`preflight.py` has E0/E1/E2 validators only. E3 needs a separate fail-closed
configuration/validator. It should validate the whole planned set before the
first downstream generation, including:

- exact E1 upstream run identity and nine-case natural prior-adopter set;
- unchanged model/revision/tokenizer/seed/decoding policy;
- at most three Agents and at most two communication rounds/hops;
- one immutable Source correction parent per scenario;
- isolated correction probe/message siblings;
- one exact correction message shared by B/C and clean reference;
- explicit A/B/C correction flags;
- matched infected/clean Target branch construction;
- A/B cache-identity equality when model-visible input is equal;
- C-only headline CVRR eligibility;
- residual-only nested re-infection eligibility;
- same corrected Source parent for re-infection treatment/control;
- exact residual replay provenance;
- run-store nonexistence/write-once safety;
- shared scientific cache-root identity; and
- exact logical-call and token projection under the 0.8M planning ceiling.

No tokenizer/model availability check should be performed until a later,
explicitly authorized preflight stage. This audit performed no model,
tokenizer, vLLM, CUDA, or GPU operation.

### 12.2 Candidate logical-call envelope

A straightforward nine-scenario mapping suggests, per scenario, at most:

- 1 Source correction-verification call;
- 1 Source correction-message call;
- 3 prior-stale Target decisions for A/B/C;
- 1 matched clean C decision.

That is 6 logical calls per scenario, or 54 logical calls before nested
re-infection. If every C case were residual, adding one re-infection treatment
and one matched control per case gives a conservative maximum of 72 logical
calls. Physical generations can be lower because identical A/B inputs and any
identical no-residual Source control must hit the normal cache.

This is an **audit projection only**, not a frozen E3 call plan. The E3
Implementation Map must determine exact call identities and then perform a
real tokenizer-only token projection before any scientific authorization.

### 12.3 Run persistence

`RunStore` and `manifest.py` are sufficient without redesign. E3 should add
write-once artifacts such as a sealed E3 overlay/correction-evidence table,
branch topology, upstream E1 references, residual replay provenance,
eligibility/exclusion tables, calls, lineage, report, and manifest hashes.

## 13. Candidate File-Level Delta

This table describes the smallest plausible future implementation delta. It is
not implementation authorization.

| Path | Future E3 role | Class | Audit finding |
| --- | --- | --- | --- |
| `state_mad/e3.py` | E1 resolver reuse, E3 overlay, Source correction siblings, A/B/C Target branches, clean reference, residual replay, nested re-infection, artifact assembly | **NEW** | Narrow isolated wrapper is the preferred ownership boundary. |
| `state_mad/preflight.py` | `E3RunConfig` + whole-set E3 fail-closed validation | **EXTEND** | E3-specific checks are absent. |
| `state_mad/lineage.py` | E3 correction/residue/re-infection relations and validator | **EXTEND** | Existing validator stops at E2. |
| `state_mad/metrics.py` | CVRR, clean contrast, Gate 5, Re-infection Rate | **EXTEND** | Frozen E3 metrics are absent. |
| `tests/state_mad/test_e3.py` | Model-free E3 contract tests | **NEW** | No E3 tests exist. |
| `state_mad/e2.py` | Import/reuse exact E1 resolver and branch reconstruction helpers | **REUSE** | Do not duplicate or weaken upstream validation. |
| `state_mad/schema.py` | Keep existing generic records; use sealed E3 sidecar for missing correction flags | **REUSE preferred** | Avoid a cross-stage schema migration unless later proven unavoidable. |
| `state_mad/snapshots.py` | Reuse immutable Snapshot; E3 wrapper handles hidden visibility | **REUSE** | No base mutation helper change is required. |
| `state_mad/prompts.py` | Reuse `awareness-v3` and `decision-v2` if Implementation Map confirms exact semantics | **REUSE** | Static audit finds no forced prompt change. |
| `state_mad/cache.py` / `backend.py` | Exact shared scientific caching for downstream E3 calls | **REUSE** | A/B identity reuse is mandatory when visible input is identical. |
| `state_mad/grading.py` | Closed-pool mechanical grading | **REUSE** | Already sufficient. |
| `state_mad/run_store.py` / `manifest.py` | Write-once E3 evidence and manifest sealing | **REUSE/WRAP** | Generic persistence already supports the needed artifacts. |
| `state_mad/scenarios.py` / `validation.py` | Frozen upstream E1 scenario set | **REUSE unchanged** | Use an E3 overlay; do not change E1 scenario hash. |
| `state_mad/e1.py` | Frozen upstream evidence only | **REUSE read-only** | No E1 regeneration or modification. |
| `src/**` | MAD-M² core | **REUSE unchanged** | No core change is indicated. |

The candidate minimum source change set is therefore:

- **NEW** `state_mad/e3.py`;
- **EXTEND** `state_mad/preflight.py`;
- **EXTEND** `state_mad/lineage.py`;
- **EXTEND** `state_mad/metrics.py`; and
- **NEW** `tests/state_mad/test_e3.py`.

Everything else should be reused or wrapped unless a later Implementation Map
identifies a concrete frozen requirement that cannot be met otherwise.

## 14. Required Model-Free Tests Before Any E3 Scientific Gate

A later implementation should include at least the following model-free tests:

1. exact nine-ID E1 prior-adopter resolution and no E1 mutation;
2. infected stale branch and clean current branch reconstruct from the same frozen E1 evidence;
3. immutable Source correction parent is not mutated by either sibling;
4. correction probe output cannot enter correction-message or Target histories;
5. Source is not marked corrected unless probe is canonical CURRENT;
6. a non-current correction message cannot qualify condition C;
7. B hides the exact correction from model-visible messages;
8. C exposes the exact same correction message used by the matched clean branch;
9. A/B identical model-visible input produces identical effective-generation identity/cache key;
10. prior-infected and clean C branches differ only in their frozen prior history, not correction rendering/task/config;
11. CVRR denominator rejects missing Source correction, delivery, accessibility, or post-correction completion;
12. completed OTHER/INVALID stays in denominator and is non-STALE;
13. Gate 5 cannot report pilot-positive when C eligible N < 10;
14. no residual Target output means zero re-infection calls are planned;
15. re-infection can use only a naturally produced C residual message;
16. residual replay raw text/content hash is exact and no hand editing is possible;
17. re-infection treatment/control share one corrected Source parent;
18. Source correction probe cannot contaminate re-infection branches;
19. lineage rejects invisible-as-visible, wrong-parent, cross-scenario, cyclic, or synthetic paths;
20. offline CVRR/Re-infection recomputation makes zero model/tokenizer/backend calls;
21. scientific preflight rejects >3 Agents, >2 rounds/hops, extra model/seed/scenario, wrong revisions, unsafe run-store/cache roots, or token ceiling violations; and
22. existing E0/E1/E2 tests continue to pass unchanged.

## 15. Risks and Ambiguities

1. **Gate-5 N is structurally below threshold.** The frozen upstream pool has at most 9 eligible prior stale adopters, while the positive gate requires 10. This is a claim/estimability limit, not an implementation bug.
2. **B delivery semantics need explicit encoding.** The frozen text says Source corrected but correction invisible; the Implementation Map must freeze `correction_delivered` and `correction_accessible_at_decision` separately and consistently.
3. **CallRecord is under-specified for E3 logging.** One `correction_visibility` field is insufficient for the three frozen correction checks. A sealed sidecar is the smallest non-invasive fix.
4. **Source-correction event IDs are not in E1 ScenarioRecord.** E3 should use a sealed overlay rather than rewrite frozen scenarios.
5. **Prompt reuse must remain causally clean.** Static inspection suggests awareness-v3/decision-v2 are sufficient; if later evidence shows a required semantic mismatch, stop at the Implementation Map rather than silently change prompts.
6. **A/B may be logically different but generatively identical.** That is expected. Condition metadata must not force duplicate model generation when model-visible input is identical.
7. **Correction-message validity is evidence, not formatting.** A failed/non-current Source correction message cannot be edited into compliance.
8. **Clean reference must stay matched.** A different scenario, prompt, correction text, visibility, or model configuration would defeat the frozen comparison.
9. **Re-infection is post-treatment sparse.** It is conditional on natural C residual cases and may be zero or too small for a standalone claim.
10. **No E2-conditioned substitution.** Restricting E3 to the six E2 second-hop-positive IDs would silently change E3 eligibility and is not authorized.
11. **No automatic sample rescue.** N<10 cannot be repaired by adding scenarios, seeds, models, Agents, or rounds without explicit human reopening.

## 16. STOP / Human-Decision Triggers

Any of the following requires **STOP — 需要人工决策** before implementation or
scientific execution:

- a proposal to enlarge the current pilot solely to make C eligible N reach 10;
- any change to the frozen RQ3 correction-visible definition or A/B/C roles;
- inability to authenticate the frozen E1 run and exact nine natural prior stale adopters without regeneration;
- any attempt to regenerate or alter frozen E1/E2 upstream messages;
- inability to keep Source correction verification and correction-message generation as isolated siblings;
- inability to encode correction delivery and accessibility separately enough for deterministic CVRR eligibility;
- a need to make hidden B-condition correction metadata model-visible merely to distinguish B from A;
- forced different cache keys for otherwise identical A/B effective generation inputs;
- any manufactured, hand-edited, normalized, or substituted residual message for re-infection;
- inability to provide the matched clean reference from frozen cached evidence;
- a proposed MAD-M² core (`src/**`) modification;
- >3 Agents, >2 main rounds/hops, extra model, extra seed, extra scenario family, extra baseline, RL, fine-tuning, learned stale detector/router, semantic parser, graph memory, or LLM-as-a-Judge;
- E3 scientific generation before a dedicated E3 Implementation Map, model-free implementation/test pass, tokenizer-only budget preflight, and separate human scientific authorization.

No stop trigger may be resolved automatically by expanding the research scope.

## 17. Special Questions and Audit Verdict

| Question | Audit answer |
| --- | --- |
| Can E3 reuse the existing exact E1 resolver? | **Yes.** Reuse the E2 whole-run fail-closed E1 resolver and branch reconstruction helpers. |
| Can E3 avoid E1/E2 regeneration? | **Yes.** All upstream infection and clean-reference evidence should be opened read-only. |
| Is the generic Snapshot record sufficient? | **Yes.** It already separates history membership from visibility; an E3 wrapper is needed because `fork_snapshot` exposes every addition. |
| Is a MAD-M² core change required? | **No.** No audited E3 requirement currently forces `src/**` changes. |
| Are new prompts required? | **Not shown by static audit.** Existing awareness and ordinary decision renderers appear reusable; exact semantics must be frozen in the E3 Implementation Map. |
| Can current CallRecord alone prove C eligibility? | **No.** It lacks separate correction-delivered and correction-accessible-at-decision fields. Use a sealed E3 evidence sidecar unless later planning proves a schema change unavoidable. |
| Is CVRR implemented? | **No.** Add a pure offline E3 metric extension. |
| Is re-infection implemented? | **No.** Add nested exact-residual replay orchestration plus pure metric/lineage logic. |
| Can Gate 5 be positive at the current 40-scenario pilot scale? | **No.** Maximum natural C candidate N is 9, below the frozen N>=10 requirement. The proper scale label is `NOT ESTIMABLE AT PILOT SCALE`, with descriptive evidence still allowed if later authorized. |
| Does this audit authorize E3 implementation or generation? | **No.** It authorizes nothing beyond this audit artifact. |

### Verdict

**READY FOR E3 IMPLEMENTATION MAP WITH PILOT-SCALE ESTIMABILITY LIMIT**

The repository already contains the hard parts needed for a minimal E3 path:
manifest-sealed E1 evidence resolution, immutable snapshots, exact message
preservation and replay, effective-input caching, deterministic grading,
generic run persistence, manifest hashing, and a proven wrapper-oriented E2
pattern. The missing E3 pieces are bounded: an isolated E3 orchestrator,
Source-correction and A/B/C visibility overlays, explicit correction-evidence
logging, CVRR/re-infection metrics, E3 lineage validation, E3 preflight, and
model-free tests.

The principal scientific limitation is not software: the frozen natural
prior-stale-adopter pool is 9, while Gate 5 requires C eligible N >= 10. Thus
the current pilot can support only descriptive / `NOT ESTIMABLE AT PILOT SCALE`
E3 evidence unless a future human decision explicitly reopens scale. This
limitation must be preserved rather than repaired automatically.

Next allowable stage after human review of this audit is a dedicated **E3
Implementation Map**. No implementation, tokenizer/model access, GPU work, or
E3 scientific execution is authorized by this document.
