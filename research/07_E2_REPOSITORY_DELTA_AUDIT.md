# State-MAD E2 Repository Delta Audit

Status: **AUDIT ONLY — NO IMPLEMENTATION AUTHORIZED**

## 1. Audit Scope and Authority

This artifact is a read-only, E2-specific delta audit of the repository at
`b241290073a359403ea025a70317ae608a02f820`. The checkout branch is `work`;
the sandbox has neither a local `main` ref nor a configured remote. `HEAD`
nevertheless equals the human-specified expected starting `main` commit, so
the audit proceeds against that exact object. No claim is made that the
sandbox can independently verify the GitHub remote.

The audit applied authority in this order:

1. `research/RESEARCH_CONTRACT.md`;
2. `research/EXPERIMENT_PLAN_FROZEN.md`;
3. `research/IMPLEMENTATION_REQUIREMENTS.md`;
4. `research/03_EXPERIMENT_PLAN_REVIEW.md`;
5. the PASS-type Stage-04 repository audit;
6. the approved Stage-05 implementation map; and
7. the frozen E1 Pilot result.

The task-supplied offline eligibility result is accepted as a frozen audit
input, not reproduced here and not treated as E2 evidence. This audit did not
run a model, tokenizer, vLLM, or GPU; did not reconstruct or copy scientific
run artifacts; and did not modify code or a frozen planning artifact.

The narrow question is whether the completed E1 infrastructure can support
the frozen E2 conditional secondary retransmission design, and what the
smallest future implementation delta would be. This document does **not**
authorize that delta.

## 2. Frozen E1 Upstream Evidence

### 2.1 Scientific provenance

| Field | Frozen value |
| --- | --- |
| Run ID | `e1-qwen25-7b-seed7-pilot-20260912-v1` |
| Scientific repository commit | `b002fe3d3dce8fe5d94b83f946dde2e494e09d4e` |
| Scenario-set hash | `sha256:83c4034bc163b66285fb3085047507c773b14be9c1556e8165bbd9dd2d6df7c9` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Model revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Tokenizer revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Seed | `7` |
| E1 Gate 2 | `POSITIVE PILOT TARGET MET` |

The nine frozen E1 treatment-only primary stale adopters are `e1-04`,
`e1-10`, `e1-16`, `e1-18`, `e1-22`, `e1-28`, `e1-30`, `e1-34`, and
`e1-40`.

### 2.2 Offline E2 estimability input

- `candidate_n = 9`
- `eligible_primary_adopter_n = 9`
- `excluded_n = 0`
- Gate 4 estimability: **ESTIMABLE AT PILOT SCALE**

For all nine, the task-supplied audit says that the stale-peer Target class is
`STALE`, the matched current-peer Target class is `CURRENT`, both raw outputs
meet the canonical structured skeleton, and exact upstream outputs exist.
This establishes only an eligible denominator candidate set. It is not
evidence that a Relay retransmitted or adopted stale state.

### 2.3 Canonical E1 run-store layout and field map

For a scientific configuration, `prepare_e1_run` places the run at:

`<run_store_root>/scientific/e1-qwen25-7b-seed7-pilot-20260912-v1/`

and the scientific cache at:

`<cache_root>/scientific/`

The configured absolute roots are deployment inputs; they are not present in
this Git checkout. The run directory created by `RunStore` has this relevant
layout:

```text
<e1-run>/
├── calls.jsonl
├── lineage.jsonl
├── cache_provenance.json
├── manifest.json
├── report.json
├── scenarios.json
└── messages/
    └── <sha256(message_id) with ':' replaced by '_'>.json
```

| Required datum | E1 storage and resolution |
| --- | --- |
| `calls.jsonl` | One canonical `CallRecord` JSON object per line, appended in call order. |
| `raw_output` | Duplicated exactly in `CallRecord.raw_output`; the corresponding model-output `MessageRecord.raw_content`; and the scientific cache payload `raw_output`. |
| `parsed_output` | `CallRecord.parsed_output`, derived mechanically by `grade_output`; it never replaces raw text. |
| `answer_class` | `CallRecord.answer_class`, one of the frozen deterministic classes. |
| cache key | Not in `CallRecord`; `cache_provenance.json` maps `call_id` to `cache_key`. The cache entry repeats it as payload `cache_key`. |
| cache origin call ID | `cache_provenance.json.origin_call_id`; also in the cache payload. |
| message ID | `CallRecord.message_id`; `MessageRecord.message_id`; peer parent IDs in `parent_message_ids`; lineage endpoints. |
| content hash | `cache_provenance.json.content_hash`; model-output `MessageRecord.content_hash`; cache payload `content_hash`. It is `digest(raw_output)`, i.e. SHA-256 over canonical JSON serialization of the string, not a bare-byte SHA-256. |
| scenario ID | `CallRecord.scenario_id`; `ScenarioRecord.scenario_id`; indirectly encoded in the E1 message/call IDs. |
| condition | `CallRecord.condition`; for the required records exactly `stale-peer` or `current-peer`. |
| snapshot hash | `CallRecord.snapshot_hash`; `report.json.branch_topology` also records branch and common parent hashes. |
| lineage | `CallRecord.parent_message_ids`; each `MessageRecord.parent_message_ids`; and explicit `lineage.jsonl` parent/child/relation edges. |
| cache provenance | `cache_provenance.json`: `call_id`, effective-generation-identity hash, cache key/status, content hash, origin call ID/run ID, and origin resolution. |

The sufficient unambiguous lookup key for each required upstream call is the
tuple `(frozen run_id, scenario_id, experiment="E1", condition, author="target")`,
with `condition` in `{stale-peer,current-peer}`. It must resolve to exactly one
`CallRecord`. That record supplies `call_id`, `message_id`, `raw_output`,
grade, snapshot hash, and generation provenance. `call_id` then resolves
exactly one cache-provenance row, while `message_id` resolves exactly one
message artifact and lineage node. Replay must fail closed unless all copies
agree on exact raw string, `digest(raw_output)`, message ID, call ID, and
condition.

## 3. E2 Frozen Requirements

For each of the nine candidate paired causal primary adopters, E2 must:

1. use a Relay pre-exposure snapshot in which `v_new` is already available;
2. run an independent `awareness-v3` probe as an isolated sibling;
3. exclude awareness output from Relay decision histories;
4. fork stale-replay and current-replay decisions from the same immutable
   Relay parent;
5. insert the exact E1 Target stale-peer `raw_output` into treatment;
6. insert the exact matched E1 Target current-peer `raw_output` into control;
7. preserve raw text without regeneration, normalization, summarization, or
   editing;
8. hold downstream effective generation settings fixed; and
9. grade Relay output mechanically.

`SRR_cond` is conditional second-hop susceptibility among observed causal
primary adopters. It is neither a population propagation rate nor an
unconditional two-hop propagation probability. Its denominator additionally
requires Relay awareness and both complete, same-parent matched calls. Its
numerator is Relay `STALE` under exact stale-Target replay. E2 must also report
the paired difference between Relay stale adoption under stale-Target replay
and current-Target replay.

## 4. Current Repository Capability Map

| Operation | Classification | Present capability / smallest gap |
| --- | --- | --- |
| Read exact E1 output | **WRAP** | Generic JSON artifacts are present by contract, but there is no read-only E1 run loader/resolver. |
| Verify E1 artifact linkage | **WRAP** | Existing `digest`, IDs, manifest hashes, messages, calls, lineage, and cache-provenance rows are sufficient; a fail-closed cross-check is needed. |
| Regenerate E1 upstream | **Not permitted** | No E2 path may invoke `CachedBackend.generate` for an upstream E1 call, even on a cache hit. |
| Preserve exact Target text | **REUSE** | `CallRecord.raw_output`, `MessageRecord.raw_content`, and cache payload preserve the string. |
| Construct Target→Relay replay envelope | **WRAP** | Create a new E2 exposure `MessageRecord` whose `raw_content` is byte/text-identical to the resolved E1 `raw_output`, with new identity and explicit linkage held in E2 provenance. |
| Relay parent/forks | **REUSE** | Frozen `Snapshot`, `make_pre_exposure_snapshot`, and `fork_snapshot` already provide immutable sibling semantics. |
| Relay awareness | **REUSE** | `render_awareness_probe` / `awareness-v3` is role-neutral and checks `v_new` availability. |
| Relay decision rendering | **REUSE** | `render_decision` / `decision-v2` concatenates `MessageRecord.raw_content` unchanged. |
| E2 orchestration | **NEW** | A narrow E2 module remains absent, as deliberately stated by E1. |
| Downstream generation/cache | **REUSE** | `CachedBackend`, `MessageCache`, and effective-input identity work for Relay calls. |
| E2 preflight | **EXTEND** | Add E2-only frozen config and fail-closed checks; do not relax E0/E1 checks. |
| Deterministic grading | **REUSE** | `grade_output` already yields the required four classes. |
| E2 metric | **EXTEND** | `metrics.py` has E0/E1 only; add pure offline `SRR_cond` and paired contrast. |
| E2 lineage validation | **EXTEND** | Generic edge records are usable, but the validators stop at E1. |
| Run persistence | **REUSE/WRAP** | `RunStore` writes calls, messages, lineage, and write-once JSON; E2 needs new provenance/table artifacts, not a storage redesign. |
| Manifest | **REUSE/WRAP** | Generic artifact hashing and effective-generation provenance work; E2 must supply additional artifact hashes and frozen E1 references. |
| MAD-M² core | **REUSE unchanged** | No `src/` edit is required. |

## 5. Exact E1 Output Replay Audit

### 5.1 Can exact text already be reused?

**Yes, with a thin read-only resolver and replay envelope.**

`CachedBackend` returns a cache hit's `payload["raw_output"]` unchanged, and a
miss stores the backend's raw string unchanged. More importantly, E2 should
not ask the backend for the upstream E1 call at all: the manifest-sealed E1
`calls.jsonl` is the immutable scientific evidence source. Its selected
`raw_output` can be assigned directly to an E2 exposure
`MessageRecord.raw_content`; `render_decision` inserts that value directly via
newline joining and performs no normalization or semantic rewriting.

The renderer necessarily adds the fixed `decision-v2` framing around peer
content. That is downstream prompt construction, not a change to the replayed
Target text. The exact E1 string remains the complete model-visible peer
content inside the `Peer evidence` slot.

### 5.2 Authoritative source and verification chain

The authoritative source for the **model-visible Target message text** must be:

> the unique selected Target `CallRecord.raw_output` line in the frozen E1
> run's `calls.jsonl`, under the run identified and sealed by that run's
> `manifest.json`.

Reasons:

- the manifest's `artifact_hashes.calls` seals `digest(calls)` for the ordered
  scientific call records;
- `calls.jsonl` contains both exact raw output and the scientific selection
  keys/grade;
- cache files are operational generation cache, not the sole scientific run
  record, and cache location/lifetime is external to the run;
- `cache_provenance.json` contains hashes and origins but not raw text; and
- message artifacts contain replay-ready text and metadata but are not listed
  as individually sealed manifest artifacts by current E1 code.

The corresponding message artifact is the authoritative E1 message/lineage
metadata companion and must agree with the call. `cache_provenance.json` is
the authoritative companion for cache origin/key metadata and must also
agree. The scientific `MessageCache` entry is optional corroboration only: if
available, it must match, but its absence must not trigger regeneration and
does not erase a valid manifest-sealed run record.

If the frozen deployment has separately sealed raw bytes/files outside what
this checkout shows, that stronger seal may be validated as an additional
constraint; it must not be silently assumed or invented.

### 5.3 Required fail-closed resolution

For each condition, the future resolver must:

1. validate the E1 run ID, scientific commit, scenario-set hash, model and
   tokenizer revisions, seed, decoding, and manifest integrity;
2. find exactly one matching Target call;
3. find exactly one `call_id` cache-provenance row and one `message_id`
   artifact;
4. require `CallRecord.raw_output == MessageRecord.raw_content`;
5. recompute the existing canonical `digest(raw_output)` and require equality
   with both content hashes;
6. require the expected E1 condition, grade, parent IDs, snapshot/pair, author,
   and phase;
7. require the stale and current calls to form the frozen paired E1 evidence;
8. record, without altering it, all actually available origin metadata; and
9. stop rather than substitute, synthesize, or generate if resolution is
   missing, duplicated, corrupt, or ambiguous.

Calling `CachedBackend.generate` with an E1 `GenerationRequest` merely to
obtain a cache hit is not acceptable: on a missing entry it would regenerate
forbidden upstream evidence. Offline reconstruction must not instantiate a
scientific backend.

## 6. Relay Snapshot and Awareness Audit

### 6.1 Snapshot sufficiency

The existing abstraction is sufficient. `Snapshot` is a frozen dataclass;
its hash covers its state. `make_pre_exposure_snapshot` installs the first
three scenario events, an empty message history, `version_new_id` as current,
and the post-update decision phase. `fork_snapshot` constructs a new object,
retains the parent's hash and event set, and appends only explicitly supplied
message IDs to the child's histories.

It can therefore represent:

- a Relay parent with `v_new` available before exposure;
- an awareness sibling with no replay message;
- stale-Target and current-Target decision siblings with their respective
  replay message IDs; and
- a parent whose canonical bytes/hash remain unchanged throughout.

Smallest delta: **none in `snapshots.py`**. The E2 wrapper should assign
Relay-specific branch/snapshot IDs, capture the parent hash before all forks,
assert both decisions' `parent_snapshot_hash` equals it, and ensure the
awareness output message ID is absent from both decisions' ancestor sets.
There is no need for mutable memory or a Relay-specific snapshot class.

### 6.2 Awareness-v3

`awareness-v3` is reusable unchanged. It depends on the scenario and a
snapshot whose current version equals `version_new_id`; it does not name
Target or Source. E2 can issue it with `agent_id="relay"` and
`agent_role="relay"` in the request metadata. The awareness output must be
graded independently and retained as evidence, but never appended to the
Relay decision parent or siblings.

No repository evidence requires a prompt redesign. A change to awareness-v3
would break comparability and is not authorized by this audit.

## 7. Relay Matched-Branch Audit

### 7.1 Replay message identity and provenance

The stale and current E1 Target outputs are distinct source messages. For
downstream exposure, each needs a distinct E2 message identity, for example a
deterministic identity derived from E2 run/pair/arm plus the E1 source
`message_id`; it must not masquerade as a newly generated Target output.

Each E2 replay envelope can reuse `MessageRecord` with:

- `raw_content`: exact E1 `CallRecord.raw_output`;
- `content_hash`: exact verified E1 content hash;
- `author="target"` and `recipient="relay"`;
- `parent_message_ids`: including the original E1 Target output message ID;
- the E1 fact/version identity;
- deterministic generation-time and decision-time validity derived from the
  frozen arm (`not_applicable`/`decision_output` applies to the original
  Target model decision; E2 must separately record whether the replayed
  content is stale/current at Relay decision time);
- Relay exposure phase; and
- `creation_source` explicitly indicating replay rather than pretending a new
  model generation occurred.

`MessageRecord` contains enough core message and lineage data to render exact
Target→Relay content, but **does not by itself contain enough cross-run cache
provenance**. It has no source run ID, source call ID, source cache key,
origin call ID/run ID/resolution, or source condition/snapshot fields. The
smallest safe solution is not a global schema redesign: retain the existing
message record and write a separate, immutable E2 `upstream_replay_provenance`
table keyed by E2 replay message ID. That table must contain actual E1
references and verified hashes. Do not invent values where E1 says
`legacy_unresolved`.

The lineage edge from original E1 Target output to E2 replay envelope should
be a mechanical relation such as `exact_replay`; the edge from replay envelope
to Relay output remains `exposure`. This preserves cross-run identity without
changing raw content.

### 7.2 Decision-v2

`decision-v2` is reusable unchanged. It accepts ordered visible
`MessageRecord`s and inserts their `raw_content` without transformation. With
exactly one replay message in the same position in each arm, it holds the
question, answer pool, known current update, and framing fixed. The two prompts
differ only where the frozen E1 raw Target outputs differ, as intended.

No E2-only template is justified by repository evidence. A wrapper is needed
only to construct and validate the replay `MessageRecord`, order it, and pass
it to the existing renderer. New provenance must remain machine metadata,
not model-visible additions. Any future evidence that the required original
Target author label must be visible but cannot be represented without changing
the fixed prompt would require human review before a template change; current
`decision-v2` did not display author labels in E1 and should not be changed
speculatively.

## 8. Cache and Identity Audit

### 8.1 EffectiveGenerationIdentity

`build_cache_key` is the digest of `EffectiveGenerationIdentity`, whose fields
are:

- system input;
- full rendered user input;
- model and model revision;
- tokenizer and tokenizer revision;
- chat-template revision;
- ordered decoding parameters;
- seed; and
- maximum new tokens.

This is sufficient for **effective downstream generation identity**:

- Relay awareness differs from decisions through the full user input
  (`awareness-v3` text versus `decision-v2` text);
- stale replay differs from current replay through the exact Target raw output
  embedded in the full user input; and
- all frozen model/tokenizer/template/decoding values remain identity fields.

Agent ID, role, experiment, condition, snapshot hash, message IDs, and
provenance are not direct identity fields. This is intentional and correct
when they do not change model-visible input: equal effective generation input
and parameters must converge to the same key. The scenario fact, answer pool,
current update, and visible peer content already enter through `user_input`.
Adding an experiment namespace only to force separation would violate the
frozen identical-input reuse rule.

The future E2 runner must still log the metadata in `GenerationRequest` and
`CallRecord`, verify prompt/content/snapshot hashes, and test that meaningful
model-visible differences change keys. `EffectiveGenerationIdentity` needs no
schema extension for E2.

### 8.2 Upstream evidence versus downstream cache

These must be separate concepts and preferably separate paths:

**A. Immutable upstream evidence source**

- frozen E1 `manifest.json` plus manifest-sealed `calls.jsonl`;
- corresponding E1 message artifacts and `lineage.jsonl` for message identity
  and causal ancestry;
- corresponding `cache_provenance.json` for original key/origin metadata;
- optional matching scientific `MessageCache` entry only as corroboration.

This source is read-only. E2 does not call a backend for it and does not copy
or promote it into a new upstream generation cache.

**B. Downstream E2 generation cache**

- a distinct E2 run-configured `MessageCache` used only for Relay awareness
  and Relay treatment/control outputs;
- normal `CachedBackend` hit/miss behavior under effective Relay identities;
- downstream cache provenance identifying Relay calls, while separately
  linking each replay envelope to frozen E1 evidence.

An E2 downstream cache hit may prevent a Relay regeneration. It cannot serve
as proof of which E1 upstream record was replayed; that proof comes from the
cross-run provenance table and verified hashes.

## 9. Lineage Audit

### 9.1 Existing support

The repository already has:

- stable message IDs and content hashes;
- message-local parent IDs;
- explicit `LineageRecord(parent_message_id, child_message_id, relation)`;
- E1 Source exposure → Target output edges;
- an E1 validator that checks complete matched arms, awareness isolation, and
  temporal validity of peer messages; and
- E1 call records containing awareness class, pair/condition, snapshot, grade,
  and phase.

Those records can reconstruct the first-hop Source seed/exposure and paired
causal Target adoption for the selected nine, provided the frozen external E1
artifacts pass integrity checks.

### 9.2 Minimum missing support

`lineage.py` has no E2 validator, no cross-run resolver, and no function that
requires the full second-hop path. A minimal pure validator must require:

1. the original stale seed exposure parent;
2. independently `CURRENT` Target awareness with no probe contamination;
3. same-parent E1 stale/current Target decisions and the treatment-only rule;
4. canonical skeleton validity for both exact E1 outputs;
5. an `exact_replay` edge/reference from the selected original E1 Target
   message to the correct E2 exposure envelope, with equal content hash/text;
6. independently `CURRENT` Relay awareness with no probe contamination;
7. stale/current Relay siblings sharing one parent snapshot;
8. exposure edge from the appropriate replay envelope to each Relay output;
9. completed deterministic Relay grades; and
10. no semantic inference beyond stored classes and exact IDs/hashes.

The existing three-field edge type is sufficient if cross-run message IDs are
globally namespaced and the separate replay-provenance record supplies source
run/call/cache details. Otherwise ambiguous ID collisions force a stop, not
invented lineage.

## 10. Metric Audit

`metrics.py` currently computes token summaries, E0 metrics, and E1 metrics.
It does **not** compute `SRR_cond`, the matched Relay contrast, or any of the
three false-consensus tiers.

The minimum E2 metric extension is a pure offline function that:

- accepts structured eligibility, Target pair, Relay awareness, Relay pair,
  replay-integrity, and snapshot-integrity records;
- excludes candidates for each frozen explicit reason;
- includes `OTHER/INVALID` Relay decisions as completed non-STALE outcomes
  rather than silently dropping them (unless the call itself is incomplete or
  infrastructure-failed);
- defines denominator IDs only when all frozen requirements pass;
- counts treatment `answer_class == "STALE"` for the numerator;
- reports treatment and control stale counts/rates and their paired
  difference;
- reports candidate, eligible-primary-adopter, Relay-aware, completed-pair,
  included, and excluded IDs/counts;
- labels interpretation `conditional`; and
- applies the frozen Gate-4 labels without calling a model.

No current false-consensus implementation is reusable: the legacy generic
consensus helper is scientifically insufficient, and `state_mad/metrics.py`
has none. Although the frozen full E2 plan names consensus outputs, the
task-specific Pilot request is to determine the minimum delta for conditional
secondary retransmission. Therefore consensus must not be smuggled into this
minimal implementation. If a later E2 authorization explicitly requires
final-vote/FSCR execution now, the already mapped deterministic three-tier
extension can be separately authorized; until then it remains a known
unimplemented capability, not a blocker to `SRR_cond` and matched Relay
contrast.

## 11. Run-Store and Manifest Audit

### 11.1 Reusable storage

`RunStore` is generic and sufficient to create a unique E2 directory, append
calls/lineage, store distinct message records by message ID, and write
non-overwritable JSON artifacts. `manifest.py` can hash supplied artifacts and
record repository/config/effective generation. Neither needs a core redesign.

### 11.2 Minimum required E2 artifacts

A future E2 run should contain, at minimum:

- `manifest.json`;
- an E2 config/preflight record;
- `scenarios.json` or a manifest-bound reference to the exact frozen E1
  scenario artifact and scenario-set hash;
- `eligibility.json` with all nine candidates and mechanical inclusion/
  exclusion reasons;
- `upstream_e1_provenance.json` recording the frozen run ID, repository SHA,
  scenario-set hash, model/tokenizer revisions, seed, E1 manifest hash, and
  relevant E1 artifact hashes;
- `upstream_replay_provenance.json` mapping every E2 exposure message to its
  E1 run/call/message/condition/content hash/cache key/origin fields;
- `calls.jsonl` for Relay awareness and matched Relay decisions only;
- `messages/` for E2 replay envelopes and Relay outputs;
- `lineage.jsonl`, including cross-run exact-replay references;
- `branch_topology.json` or equivalent report data proving the common Relay
  parent and isolated awareness sibling;
- downstream `cache_provenance.json` for E2-generated Relay calls;
- `report.json` with deterministic `SRR_cond`, matched contrast, denominator,
  exclusions, tokens, and Gate-4 status; and
- a manifest hash for every above scientific artifact or reference table.

The current `finalize_manifest` minimum required-name check can remain; E2
must pass the additional artifact names/hashes to the manifest and its E2
preflight must reject missing upstream provenance. A thin E2 orchestration
wrapper can do this without modifying `manifest.py`. If central enforcement
of E2-specific required names is desired later, that is a small extension,
not required by current mechanics.

Do not claim an origin run where current E1 provenance says
`legacy_unresolved`; preserve that exact status. For the frozen scientific run
described in `06_E1_PILOT_RESULTS.md`, the expected 200 misses should resolve
to current-run origins, but the implementation must verify rather than infer
that fact.

## 12. MAD-M² Core Impact

**E2 can be implemented without changing MAD-M² core.** The necessary path is
an isolated State-MAD orchestrator around existing scenario, prompt, snapshot,
cache/backend, grading, and run-store components. No edit is needed under
`src/`, to `multi_agent_debate.py`, or to the official MAD-M² debate engine.

The proposed design uses exactly three logical homogeneous Agents—Source,
Target, Relay—and one frozen model. E1 already supplies Source→Target; E2 adds
only Target→Relay matched exposure. It requires no more than two main
communication hops/rounds, retains temperature `0`, top-p `1`, fixed seed and
revision, and makes no new upstream call.

If static inspection during implementation proves that a `src/` core edit is
necessary, the required action is **STOP — HUMAN DECISION REQUIRED**. This
audit finds no such necessity.

## 13. Model-Free Test Requirements

Before any E2 scientific authorization, add only model-free tests using tiny
sealed fixtures and a backend that fails if touched during upstream loading.

1. **Exact stale replay:** resolved stale `raw_output` equals replay-envelope
   `raw_content` exactly and has the same canonical content hash.
2. **Exact current replay:** the same invariant for current-peer control.
3. **No upstream regeneration:** missing E1 cache and missing/ambiguous E1
   artifacts fail closed; the fake/spy backend records zero calls while E1
   evidence is reconstructed.
4. **Manifest/artifact integrity:** wrong run ID, repository SHA, scenario-set
   hash, manifest call hash, message hash, call/message text, provenance row,
   origin reference, or duplicate selector is rejected.
5. **Cache inheritance:** E1 evidence remains read-only; no cache files or run
   artifacts are changed; `legacy_unresolved` remains unresolved.
6. **Same Relay parent:** awareness, stale replay, and current replay are
   siblings, and both decision branches have one identical parent hash.
7. **Awareness isolation:** neither Relay decision has awareness output as a
   visible message or ancestor; parent canonical bytes/hash are unchanged.
8. **Deterministic paired prompts:** treatment/control use `decision-v2`, one
   peer position, identical held-fixed framing/config, and only exact selected
   upstream content differs.
9. **Effective cache identity:** repeated identical effective Relay inputs
   yield the same key; awareness versus decision differs; stale versus current
   differs when raw content differs; metadata-only experiment/branch changes
   do not force separation.
10. **Downstream cache behavior:** an identical Relay request hits exact raw
    output and reports zero generated tokens; corrupt/duplicate entries fail.
11. **Lineage correctness:** validate the full Source→Target→exact replay→
    Relay chain and reject swapped arms, wrong source call, altered content,
    missing parent, awareness contamination, and cross-scenario links.
12. **Conditional denominator:** truth-table every denominator requirement,
    including Target causal adoption, skeleton, exact availability, Relay
    awareness, both complete calls, and common parent.
13. **`OTHER/INVALID`:** a completed Relay `OTHER/INVALID` is included as a
    non-stale outcome; a Target skeleton failure excludes before Relay replay;
    an incomplete/infrastructure-failed Relay pair is excluded with reason.
14. **Matched contrast and Gate 4:** hand-built rows produce exact numerator,
    denominator, treatment/control rates, paired difference, and frozen labels;
    no population interpretation is emitted.
15. **E1 regression preservation:** all existing E1 tests remain unchanged and
    pass; E2 loading does not mutate E1 files or alter E1 metrics.
16. **Resource/preflight bounds:** exactly three Agents maximum, one model,
    deterministic decoding, at most two rounds, expected revisions/seed, and
    explicit scientific paths; violations fail before a downstream call.
17. **Offline metric purity:** E2 eligibility, lineage, and metric recomputation
    complete with zero model/backend/tokenizer calls.

No test should invoke a tokenizer merely to compare the already accepted
canonical E1 output skeleton. Skeleton validity is character/structure based
and deterministic.

## 14. Candidate File-Level Delta

This is a candidate map for a later explicitly authorized implementation, not
a list of changes made now.

| Path | Current role | E2 need | Class | Reason | Risk |
| --- | --- | --- | --- | --- | --- |
| `state_mad/e2.py` | Absent by design | Read-only E1 resolver, eligibility verification, replay envelope construction, Relay sibling orchestration | **NEW** | Keeps E2 isolated and implements approved Stage-05 P2.1 | Highest: accidental upstream generation or ambiguous artifact resolution; must fail closed |
| `state_mad/snapshots.py` | Immutable parent/fork primitives | Use unchanged for Relay | **REUSE** | Already supports current version and sibling forks | Low; wrapper must assert parent preservation |
| `state_mad/prompts.py` | `awareness-v3`, `decision-v2` and peer renderers | Use first two unchanged | **REUSE** | Role-neutral awareness and exact raw peer insertion already work | Low; do not expose new provenance text |
| `state_mad/cache.py` | Immutable key-addressed cache | Downstream Relay cache only | **REUSE** | Exact hit behavior and duplicate protection already exist | Medium; never use as upstream resolver with generation fallback |
| `state_mad/backend.py` | Cached generation and model adapters | Relay calls only | **REUSE** | Existing effective-input cache behavior is adequate | Medium; enforce no upstream request path |
| `state_mad/schema.py` | Frozen general records | Reuse records; put cross-run provenance in an E2 table | **REUSE** | `MessageRecord` is rendering-capable; separate table avoids invasive schema change | Medium; E2 wrapper must validate/table-bind missing cross-run fields |
| `state_mad/grading.py` | Canonical deterministic grader | Grade Relay and validate existing skeleton | **REUSE/WRAP** | Current one-line skeleton is sufficient; a small E2 selector wrapper can require both valid | Low |
| `state_mad/run_store.py` | Generic non-overwrite run artifacts | Persist E2 records/tables | **REUSE** | Existing append/message/write-once operations suffice | Low |
| `state_mad/manifest.py` | Generic manifest builder/finalizer | Bind E1 references and E2 artifacts | **WRAP** | E2 orchestrator can supply hashes without changing generic code | Medium; all new evidence tables must actually be hashed |
| `state_mad/preflight.py` | Frozen E0/E1 config validation | Add E2 config and fail-closed bounds/provenance checks | **EXTEND** | E2 requires three Agents and upstream evidence checks without weakening E1 | Medium |
| `state_mad/lineage.py` | E0/E1 ancestry validation | Validate full cross-run exact-replay second hop | **EXTEND** | Current validators stop at Target | Medium-high; false path acceptance would invalidate claims |
| `state_mad/metrics.py` | E0/E1 deterministic metrics | Add `SRR_cond`, paired Relay contrast, exclusions, Gate 4 | **EXTEND** | No E2 metric exists | Medium; denominator/interpretation must remain conditional |
| `tests/state_mad/test_e2.py` | Absent | Model-free resolver/replay/snapshot/cache/lineage/metric tests | **NEW** | Isolates E2 tests and zero-call guards | Low |
| `state_mad/e1.py` | Completed E1 runner/artifact writer | Consume outputs read-only; no edit | **REUSE** | E1 must not change or rerun | High if modified; explicitly avoid |
| `src/**` / MAD-M² core | Official engineering base | No E2 change | **REUSE** | Wrapper path is sufficient | Stop trigger if an edit appears necessary |

### Minimum future source-file change set

For the minimum authorized `SRR_cond` Pilot path, the candidate source changes
are exactly:

- **NEW** `state_mad/e2.py`;
- **EXTEND** `state_mad/preflight.py`;
- **EXTEND** `state_mad/lineage.py`; and
- **EXTEND** `state_mad/metrics.py`.

Add **NEW** `tests/state_mad/test_e2.py` for model-free validation. Existing
cache, backend, schema, snapshot, prompt, grading, run-store, manifest, and E1
files should be reused unchanged. This minimum assumes the E2-specific module
owns its read-only artifact decoder and provenance-table validation. A shared
generic run reader could instead be a small new module, but is not necessary
at Pilot scale and should not be added absent demonstrated reuse need.

## 15. Risks / Ambiguities

1. **Scientific artifacts are not in this checkout.** Static code proves the
   format and task input asserts all nine outputs exist, but this audit cannot
   inspect their deployment paths or bytes. Implementation authorization must
   be preceded by fail-closed access/integrity preflight against the frozen E1
   run.
2. **No local `main` ref/remote.** `HEAD` matches the requested expected SHA,
   but remote movement cannot be independently checked in this sandbox.
3. **Message files are not individually manifest-listed.** Therefore calls are
   the sealed raw-text authority and messages are required cross-checked
   metadata, not the sole byte authority.
4. **Canonical digest semantics.** `digest(raw_output)` hashes canonical JSON
   encoding of the string. A future resolver must use the repository function
   rather than assume ordinary file-byte SHA-256.
5. **Cross-run provenance is not in `MessageRecord`.** It must be carried by a
   separately sealed E2 table; pretending it is present would fabricate
   provenance.
6. **Legacy unresolved origins.** E1 replay runs can report
   `legacy_unresolved`; E2 must preserve that status and stop if the required
   scientific source cannot otherwise be unambiguously authenticated.
7. **`creation_source` vocabulary is not enforced.** A replay marker can be
   recorded, but its exact controlled value should be frozen in the E2
   implementation authorization/map rather than improvised during execution.
8. **Visible author label.** `decision-v2` uses raw peer content but does not
   separately render `MessageRecord.author`. E1 did the same. Metadata can
   establish `author=Target`; changing model-visible labeling would change the
   prompt and requires explicit human review.
9. **Consensus scope.** No false-consensus metric exists. It is unnecessary
   for the minimum conditional retransmission runner requested here, but the
   full frozen E2 output list includes the three tiers. Their timing must be
   explicitly decided before scientific authorization; they must not be
   silently approximated.
10. **No inference from estimability.** Nine eligible cases permit the frozen
    Gate-4 pilot attempt; they do not imply a positive second hop.

## 16. Human-Decision Triggers

Any of the following requires **STOP — HUMAN DECISION REQUIRED**:

- checked-out/base `main` is shown to differ from
  `b241290073a359403ea025a70317ae608a02f820` for unrelated reasons;
- the frozen E1 run, manifest, required call, message, lineage, or provenance
  artifact is missing, duplicated, corrupt, mismatched, or ambiguous;
- any required exact stale/current E1 raw output cannot be resolved without
  regeneration, substitution, normalization, editing, or invented provenance;
- frozen E1 run ID, scientific commit, scenario-set hash, model/tokenizer
  revision, seed, decoding, or selected IDs do not match the supplied values;
- the nine-case eligibility result cannot be mechanically reproduced from the
  available records at implementation preflight;
- a Target output fails the canonical skeleton or stale/current matched-pair
  requirements;
- Relay branching cannot preserve a common immutable parent or isolate the
  awareness output;
- exact Target author/identity presentation is judged to require changing
  model-visible `decision-v2` semantics;
- upstream and downstream caches cannot be cleanly separated;
- an identical effective generation identity would be forced into separate
  keys merely by experiment namespace;
- a MAD-M² core (`src/**`) modification appears necessary;
- implementing the requested E2 path would exceed three Agents, two rounds,
  one frozen model, deterministic settings, the frozen sample, seed, or token
  ceiling;
- scientific E2 execution is requested before explicit implementation and
  generation authorization; or
- full E2 consensus outputs are required now but their final-vote construction
  is not explicitly authorized in the minimal Pilot delta.

No trigger may be resolved by adding models, Agents, rounds, scenarios, seeds,
semantic classifiers, judges, or architecture.

## 17. Special-Question Answers and Audit Verdict

| Question | Finding |
| --- | --- |
| **A. Can E2 avoid MAD-M² core changes?** | **Yes.** An isolated State-MAD wrapper is sufficient. |
| **B. Can frozen E1 outputs be used without regenerating an E1 call?** | **Yes.** Read manifest-sealed E1 run records directly; never send upstream requests to `CachedBackend`. |
| **C. Authoritative model-visible replay source?** | The unique selected `CallRecord.raw_output` in frozen E1 `calls.jsonl`, under its validated `manifest.json`; cross-check the corresponding message artifact and cache-provenance row. |
| **D. Is the snapshot abstraction sufficient?** | **Yes.** Frozen parent plus immutable awareness/treatment/control forks already express the design. |
| **E. Is awareness-v3 reusable unchanged?** | **Yes.** Use Relay request metadata and keep probe output isolated. |
| **F. Is decision-v2 reusable unchanged?** | **Yes.** It inserts exact `raw_content`; an E2 wrapper supplies one verified replay message. |
| **G. Is MessageRecord provenance sufficient?** | **Partly.** It is sufficient for exact content, identity, author/recipient, validity, phase, and parents, but not original cross-run call/cache provenance; add a separate sealed E2 replay-provenance table, not a schema redesign. |
| **H. Is EffectiveGenerationIdentity sufficient?** | **Yes** for deterministic downstream generation cache identity because it includes complete model-visible inputs and generation parameters. Metadata remains logged outside the key. |
| **I. Minimum future source changes?** | New `state_mad/e2.py`; extend `preflight.py`, `lineage.py`, and `metrics.py`; add model-free `tests/state_mad/test_e2.py`. Reuse other files unchanged. |
| **J. What forces STOP?** | Any ambiguous/unverifiable exact E1 evidence, need to regenerate/edit/substitute, integrity/provenance mismatch, inability to preserve matched immutable branches, scope/resource expansion, or apparent MAD-M² core change. |

### Verdict

**READY WITH MINOR GAPS**

The repository already provides exact raw text preservation, effective-input
caching, immutable sibling snapshots, reusable awareness/decision prompts,
deterministic grading, generic run persistence, and sufficient core message
lineage. The narrow gaps are an E2-only read/verify/replay orchestrator,
E2 preflight, full second-hop lineage validation, conditional metric logic,
and model-free tests. These are wrapper/isolated extensions; they require no
MAD-M² core, prompt, schema, cache, backend, E1, or snapshot modification.

This verdict means ready for human review of a dedicated E2 implementation
map/authorization. It does **not** authorize E2 implementation or scientific
generation.
