# State-MAD E2 Implementation Map

**Status:** PLANNING ARTIFACT — NO IMPLEMENTATION AUTHORIZED
**Stage:** E2-Specific Implementation Map

**Authority:**

`RESEARCH_CONTRACT.md`
→ `EXPERIMENT_PLAN_FROZEN.md`
→ `IMPLEMENTATION_REQUIREMENTS.md`
→ `03_EXPERIMENT_PLAN_REVIEW.md`
→ `07_E2_REPOSITORY_DELTA_AUDIT.md`
→ this map

The existing Stage-05 Implementation Map remains the general repository map.
This file is the E2-specific refinement only. It does not alter RQ1–RQ4,
authorize implementation, authorize model access, or amend a frozen artifact.

## 0. Provenance, scope, and planning result

### 0.1 Checkout and scientific inputs

| Item | Frozen value |
| --- | --- |
| Planning checkout / requested base | `8b8a856c5f0fedb51f773ed1331dc1c07865fb78` |
| E1 scientific run | `e1-qwen25-7b-seed7-pilot-20260912-v1` |
| E1 scientific repository commit | `b002fe3d3dce8fe5d94b83f946dde2e494e09d4e` |
| E1 scenario-set hash | `sha256:83c4034bc163b66285fb3085047507c773b14be9c1556e8165bbd9dd2d6df7c9` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Model revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Seed | `7` |
| Candidate / eligible / excluded N | `9 / 9 / 0` |
| Candidate IDs | `e1-04`, `e1-10`, `e1-16`, `e1-18`, `e1-22`, `e1-28`, `e1-30`, `e1-34`, `e1-40` |
| Gate-4 estimability | `ESTIMABLE AT PILOT SCALE` (not retransmission evidence) |

The tokenizer revision and the complete E1 decoding record are not inferred
from the model revision. The future resolver must read their exact values from
the validated E1 manifest and require agreement with an explicitly authorized
E2 configuration.

### 0.2 Frozen boundary

E2 is limited to conditional secondary retransmission among the nine observed,
paired E1 causal primary adopters. It uses three homogeneous logical Agents
(Source, Target, Relay), no more than two communication hops, one frozen model,
deterministic grading, and exact E1 replay. It does not add scenarios, Agents,
rounds, models, seeds, baselines, semantic classifiers, an LLM judge, or a new
memory architecture.

Static inspection confirms the approved delta-audit reuse path for exact E1
loading, an E2 overlay, Relay sibling branches, cache behavior, and conditional
metrics. The human-frozen Section-H decision now uniquely fixes the three
role-specific final readouts, their branch-local visibility, matched-system
assembly, and non-communicative round accounting.

## A. Exact read-only E1 upstream resolver

### A.1 Proposed pure interface and ownership

`state_mad/e2.py` would own immutable value objects
`E1RunExpectation`, `E1ReplaySelection`, and `ResolvedE1ReplayPair`, plus:

```text
resolve_e1_replay_pair(
    e1_run_dir: Path,
    expectation: E1RunExpectation,
    scenario_id: str,
) -> ResolvedE1ReplayPair
```

The function is pure with respect to repository and run state: it reads a
sealed directory, returns immutable decoded records and digests, writes
nothing, accepts no backend/cache-generation object, and has no recovery path.
Its two selected arms are exactly `stale-peer` and `current-peer`; the unique
Target `CallRecord.raw_output` is the model-visible authority.

### A.2 Fail-closed selection and integrity predicate

Before returning a pair, the resolver must perform all checks as one atomic
predicate:

1. validate `manifest.json`, its finalized status, artifact-name/hash bindings,
   E1 run ID, E1 scientific repository SHA, scenario-set hash, model ID,
   resolved model and tokenizer revisions, seed, temperature, top-p,
   `max_new_tokens`, and all other decoding fields;
2. require the scenario ID to be in the frozen nine-ID set and in the
   manifest-bound E1 scenario artifact;
3. select exactly one Target call for each tuple
   `(scenario_id, condition, role=Target)`; require E1 experiment, expected
   pair ID, expected snapshot/parent pair, correct phase, call ID, message ID,
   fact/version fields, and condition;
4. resolve exactly one corresponding `messages/<message_id>.json` artifact and
   exactly one `cache_provenance.json` row per call;
5. require byte-for-code-point equality
   `CallRecord.raw_output == MessageRecord.raw_content`, equality of the stored
   content hashes, and `digest(raw_output)` equality using
   `state_mad.schema.digest` (canonical JSON-string hashing, not ad-hoc file
   SHA-256);
6. require cache key, origin call ID, origin run ID/resolution, and cache status
   to agree across the call/provenance evidence; preserve
   `legacy_unresolved` literally and reject it if authentication of a selected
   scientific origin is thereby ambiguous;
7. mechanically grade both raw outputs with the frozen answer pool; require the
   one-line canonical `ANSWER=<pool member>` skeleton without normalization,
   stale arm class `STALE`, and current arm class not `STALE`;
8. verify the frozen E1 awareness call is uniquely `CURRENT`, both decisions
   are siblings of the same E1 parent snapshot, and lineage establishes the
   treatment-only causal-adopter relation; and
9. require the recomputed eligible ID set to equal the frozen nine IDs exactly.

Missing, duplicate, malformed, unmanifested, hash-inconsistent, cross-scenario,
cross-condition, swapped-arm, or scientifically inconsistent evidence raises
one typed `E2IntegrityError` with a stable reason code and produces no partial
pair. `resolve_e1_replay_pair` must have no reference to
`CachedBackend.generate`; an upstream backend call is a hard implementation
test failure, never a fallback.

## B. E2 sealed role / visibility overlay

### B.1 Object and deterministic construction

`state_mad/e2.py` would own frozen `E2ScenarioOverlay` records. One overlay is
constructed per eligible scenario by joining only the manifest-validated E1
`ScenarioRecord`, its resolved replay pair, and explicit E2 constants:

```text
scenario_id, e1_scenario_set_hash, e1_scenario_digest,
source_agent_id="source", target_agent_id="target", relay_agent_id="relay",
relay_current_version_id=<ScenarioRecord.version_new_id>,
relay_current_evidence_event_ids=<deterministically selected update events>,
relay_parent_snapshot_id, relay_parent_snapshot_hash,
final_vote_phase_id=<ScenarioRecord.final_vote_phase_id>, overlay_schema="e2-overlay-v1"
```

Agent IDs are distinct and sorted/serialized in fixed Source/Target/Relay field
order. The Relay parent is deterministically derived from the frozen scenario
using `make_pre_exposure_snapshot` through an E2 wrapper; its explicit E2 ID is
`<scenario_id>:relay:parent`, and its event/current-version content must prove
that `v_new` is available before exposure. The overlay digest is
`digest(E2ScenarioOverlay)`.

### B.2 Persistence and validation

The ordered nine-record array is written once as
`e2_scenario_overlay.json` before a downstream call. Preflight recomputes every
record and the aggregate digest, checks its E1 scenario/hash binding, distinct
roles, `v_new`, event ordering, Relay parent ID/hash, and post-update
`final_vote_phase_id`, and rejects unknown fields or rows. It neither edits nor
recompiles the frozen E1 scenarios and therefore does not change their bytes or
scenario-set hash. The phase is copied from
`ScenarioRecord.final_vote_phase_id`; E2 must not fabricate a replacement
phase. A mismatch prevents overlay sealing and fails scientific preflight.

## C. Relay snapshot, awareness, and matched branching

### C.1 Required topology

Reuse unchanged `make_pre_exposure_snapshot`, `fork_snapshot`,
`render_awareness_probe` (`awareness-v3`), and `render_decision`
(`decision-v2`) through E2 wrappers. For each scenario:

```text
immutable Relay parent (v_new visible; hash P captured)
├── awareness sibling              parent=P; no replay
├── stale-replay decision sibling  parent=P; stale replay message only
└── current-replay decision sibling parent=P; current replay message only
```

The wrapper captures canonical parent bytes and `P` before any fork, then
asserts them after all forks. The awareness output is graded independently and
stored, but is absent from each decision snapshot's messages,
`visible_message_ids`, parent IDs, prompt, and transitive lineage. Both
decision siblings have `parent_snapshot_hash=P`; held-fixed fields are equal,
and the selected exact replay raw content is the only intended model-visible
difference.

### C.2 IDs and record ownership

Freeze these deterministic E2 IDs:

* calls: `<e2_run_id>:<scenario_id>:relay:<awareness|stale-replay|current-replay>:call`;
* generated messages: the same prefix ending `:output`;
* replay envelopes: `<e2_run_id>:<scenario_id>:target-relay:<stale|current>:replay`;
* branches: `relay-awareness`, `relay-stale-replay`, `relay-current-replay`;
* pair: `<scenario_id>:e2-relay-pair`.

Relay `CallRecord`s own generated awareness/decision outputs. Replay envelopes
are `MessageRecord`s authored by `target`, addressed to `relay`, and are the
sole parents of the respective Relay decision outputs. Prompts and schemas are
reused unchanged. Any need to change `awareness-v3` or `decision-v2` is
**STOP — HUMAN DECISION REQUIRED**.

## D. Exact Target→Relay replay envelope

`make_e2_replay_envelope(pair, arm, overlay, e2_run_id)` in `e2.py` would be a
pure constructor over the existing `MessageRecord`. Its `raw_content` is
assigned directly from the selected E1 `CallRecord.raw_output`; no `.strip()`,
normalization, re-encoding transformation, rewrite, summary, provenance label,
or author prefix is permitted. `content_hash` is the verified E1 content hash.

Freeze `MessageRecord.creation_source = "e2_exact_e1_target_replay"` and
`LineageRecord.relation = "exact_replay"` for the cross-run replay edge. Freeze
the other new relation names in Section J. The envelope has Target author,
Relay recipient, the scenario fact/version represented by the selected output,
post-update decision validity derived mechanically from its grade, and the E2
Relay-exposure phase. The visible text remains only the exact raw output.

Because `MessageRecord` has no cross-run fields, the separate sealed
`upstream_replay_provenance.json` row binds:

```text
e2_replay_message_id, relation="exact_replay", creation_source,
e1_run_id, e1_call_id, e1_message_id, e1_condition,
e1_pair_id, e1_snapshot_hash, e1_parent_snapshot_hash,
content_hash, cache_key, origin_call_id, origin_run_id,
origin_resolution, e2_scenario_id, target_agent_id, relay_agent_id
```

No `MessageRecord` redesign is planned.

## E. Cache contract

### E.1 Upstream versus downstream

**Frozen upstream E1 evidence** is opened read-only by direct artifact readers.
No upstream request, cache lookup with generation fallback, cache write, or
backend call is permitted. E1 artifacts and their filesystem metadata must be
unchanged across reconstruction.

**Downstream Relay generation** uses the existing scientific `MessageCache`
and `CachedBackend`. Its key remains exactly
`build_cache_key(EffectiveGenerationIdentity)`. E2 experiment, run, branch,
metadata, replay provenance, and stage names must not be inserted merely to
separate runs. Identical complete model-visible inputs and generation
parameters therefore reuse one key; differing exact stale/current text yields
different keys naturally.

### E.2 Physical root

`E2RunConfig.cache_root` names the already authorized shared scientific cache
root. E2 passes that exact root to `MessageCache`; it must not append `/E2`, a
run ID, or a condition. `run_store_root` remains separate and E2-run-specific,
so run artifacts cannot collide with cache entries. Scientific preflight
resolves both paths, rejects equality/nesting that would put run artifacts in
the cache, and verifies the cache backend/root before the first call. Cache
hits preserve exact output and report zero generated usage under the existing
contract.

## F. E2 preflight

### F.1 Proposed configuration

Extend `state_mad/preflight.py` with frozen `E2RunConfig` and
`validate_e2_preflight(config, overlays, replay_pairs, backend_probe,
final_vote_spec)`. The required human-frozen mode is
`final_vote_mode = "synchronized-role-specific-noncommunicative-v1"`. Required
fields/constraints are:

| Field | Required constraint |
| --- | --- |
| `experiment`, `method`, `mode` | `E2`, `state-mad-e2`, `dry-run|scientific` |
| `models` | exactly `("Qwen/Qwen2.5-7B-Instruct",)` |
| `model_revision` | exactly `a09a35458c702b33eeacc393d103063234e8bc28` |
| `tokenizer_revision` | explicit, resolved, equal to validated E1 policy |
| decoding | seed `7`, temperature `0`, top-p `1`, max-new-tokens `32` |
| resources | Agents `3`, main rounds/hops `2`, one model, projected total below `800000` |
| candidates | exact ordered frozen nine-ID tuple; no extras or omissions |
| E1 reference | explicit read-only run directory, run ID, scientific SHA, scenario hash |
| E2 destinations | non-default explicit run ID, run-store root, shared scientific cache root |
| scientific backend | production language-model backend only in scientific mode |
| overlays | nine unique, sealed, digest-valid, E1-bound, Relay has `v_new` pre-exposure |
| replay pairs | nine exact canonical pairs passing all Section-A predicates |
| final votes | frozen mode; two system cases; one shared Source, two Target, and two Relay logical calls; one `ScenarioRecord.final_vote_phase_id`; zero readout communication |

Preflight also requires available model/tokenizer and seed support only where
scientific execution is authorized, verifies run-store nonexistence/write-once
safety and cache-root identity, and emits stable reason codes. Artifact
integrity, eligibility, overlays, branch plans, final-vote specification, and
resource projection are whole-set checks before the first downstream call.
Runtime-only failures remain fail closed. Existing E0/E1 validators are not
changed or weakened.

Preflight mechanically verifies two matched system cases per scenario; exactly
one shared Source final call, two Target final calls, and two Relay final calls;
one frozen post-update phase for every counted triplet; zero final-output
visibility to another Agent; no stale seed as a vote; identical Source state and
call reference across arms; correct Target/Relay branch mappings; and exactly
two communication hops. Metadata-only condition, phase, run, and system-case
fields must not alter `EffectiveGenerationIdentity`.

## G. `SRR_cond` and paired Relay contrast

Extend `metrics.py` with pure
`evaluate_e2_retransmission(rows, eligibility, topology, integrity) -> dict`.
It performs no I/O and no generation.

The denominator ID set is the intersection of: eligible E1 paired causal
primary adopter; canonical exact stale/current replay pair; independently
`CURRENT`-aware Relay; complete stale/current Relay calls; identical Relay
parent hash; and no infrastructure failure. A completed `OTHER/INVALID` Relay
output stays in the denominator and is non-`STALE`. An incomplete output or
infrastructure failure is excluded with exactly one primary stable reason and
all applicable secondary reasons.

The numerator is denominator scenarios whose stale-replay Relay treatment is
`STALE`. Report candidate, E1-eligible, Relay-aware, completed-pair, and
included IDs/N; excluded IDs/reasons; treatment stale count/rate; control stale
count/rate; paired difference `treatment_rate - control_rate`; `SRR_cond`
(equal to treatment stale count / included N); and interpretation
`"conditional"`.

Gate 4 is deterministic:

* eligible N `<8`: `NOT ESTIMABLE AT PILOT SCALE`;
* eligible N `>=8`, treatment stale count `>=2`, and paired difference `>0`:
  `SECOND-HOP-POSITIVE PILOT`;
* eligible N `>=10` and treatment stale count `0`:
  `SECONDARY RETRANSMISSION UNSUPPORTED`;
* otherwise: `NO POSITIVE/UNSUPPORTED GATE CONCLUSION`.

The report must never describe `SRR_cond` as a population propagation
probability.

## H. Final-vote construction decision

### H.1 RESOLVED BY HUMAN DECISION

**Option 2 — Synchronized Role-Specific Non-Communicative Final Readout** is
human-frozen for the E2 Pilot. This resolves the former scientific ambiguity;
it does not authorize implementation or scientific execution.

Communication remains exactly:

1. Round/Hop 1: Source → Target;
2. Round/Hop 2: Target → Relay; then
3. Final Readout Phase: a non-communicative measurement phase.

The final readout is **not** a third debate/communication round. No readout
output is shown to another Agent, no transcript is shared, and no new
Agent→Agent information flows. All counted votes are new logical final-readout
calls carrying the existing post-update `ScenarioRecord.final_vote_phase_id`.
Historical E1/E2 calls are never relabeled as final votes.

### H.2 Branch-local final-readout rule

"Retains branch-local state" means: no new inter-Agent message is appended;
awareness output remains excluded; the existing exposure history is unchanged;
rendering uses the corresponding frozen branch; no transcript sharing, prior
self-output injection, or treatment/control contamination occurs. A lightweight
immutable fork may assign the existing final phase while preserving the exact
model-visible branch state. It must not mutate an old snapshot or historical
`CallRecord`.

`e2.py` reconstructs each manifest-validated branch snapshot and uses the
existing immutable fork machinery to create measurement-only snapshots named
`<scenario_id>:<condition>:snapshot`. Source forks from one post-update
authoritative-current no-peer parent; Target stale/current forks respectively
from the frozen E1 stale-peer/current-peer branch state; Relay stale/current
forks respectively from the E2 stale-replay/current-replay branch state. Each
fork retains the same visible exposure message IDs and current version as its
parent, adds no message ID, and changes only snapshot identity/phase to the
existing `ScenarioRecord.final_vote_phase_id`. Parent canonical bytes and
historical calls remain unchanged.

Use unchanged `render_decision` / `decision-v2` for these ordinary readouts if
it expresses that state. No shared transcript, consensus prompt, new peer
exposure, or feedback of a prior final answer is allowed. If `decision-v2`
cannot express this design unchanged: **STOP — HUMAN DECISION REQUIRED**.

### H.3 Exact Source, Target, and Relay votes

The **Source final vote** is a post-update authoritative-current no-peer
readout: `v_new` is available, no Target/Relay evidence is visible, and the
ordinary frozen answer mapping is mechanically graded. The pre-update `m_old`
seed is historical exposure evidence only and is never the Source vote. This
readout is not the E3 source-correction intervention; even a `CURRENT` result
must not set `source_corrected=true` or alter E3 semantics.

The **treatment Target vote** is a new logical readout from the frozen E1
stale-peer branch-local state, retaining its historical Source stale exposure
and receiving no Relay/final-phase message. The **control Target vote** is the
corresponding readout from the frozen E1 current-peer branch-local state.

The **treatment Relay vote** is a new logical readout from the E2 stale-replay
branch-local state containing the exact frozen stale-Target replay. The
**control Relay vote** is the corresponding readout from the E2 current-replay
branch containing the exact frozen current-Target replay. Neither receives a
new final-phase message.

### H.4 Matched systems, conditions, and IDs

Freeze two system cases per eligible scenario:

* `<scenario_id>:e2-system:stale` — shared Source no-peer final, Target stale
  final, Relay stale final;
* `<scenario_id>:e2-system:current` — the identical shared Source call/message,
  Target current final, Relay current final.

Source is held fixed and no other treatment difference is introduced. Freeze
logical condition names exactly as `source-final`, `target-stale-final`,
`target-current-final`, `relay-stale-final`, and `relay-current-final`. These
metadata conditions do not alter `EffectiveGenerationIdentity` unless the
model-visible prompt actually differs.

For each condition, freeze call ID
`<e2_run_id>:<scenario_id>:<condition>:call` and generated message ID
`<e2_run_id>:<scenario_id>:<condition>:output`. Each is a new logical
`CallRecord`, may be a cache hit, and never overwrites a historical call. The
record binds E2 run/scenario, both system-case references as applicable, role,
condition, frozen final phase, snapshot and parent hash, prompt hash, answer
class, cache provenance, and exact message ID. The single Source call/message
is referenced by both system cases.

### H.5 Round accounting and rejected alternatives

Main communication rounds/hops equal `2`. Final readout adds no debate round
because it introduces no Agent→Agent information flow. This accounting is
human-frozen for the E2 Pilot.

* **Option 1 — NOT SELECTED:** it lacks a genuine synchronized final phase.
* **Option 3 — NOT SELECTED:** it adds a shared-transcript intervention.
* **Option 4 — NOT SELECTED:** it creates asymmetric timing and visibility.

The selected construction remains within three Agents, two communication hops,
unchanged prompts/schemas, and the isolated E2 wrapper boundary.

## I. Three FSCR metric contracts

Proposed pure `evaluate_e2_fscr(final_votes, lineage_report,
system_eligibility) -> dict` implements the predicates over the human-frozen synchronized readout records.

| Metric | Denominator / eligibility | Numerator | IDs and exclusions | Label and `OTHER/INVALID` |
| --- | --- | --- | --- | --- |
| Ordinary FSCR | Complete system cases with exactly one Source, Target, Relay vote, all in one verified post-update `final_vote_phase_id` | At least two of three classes are `STALE` | Requires system-case ID, three call/message IDs, role IDs, phase ID; exclude missing/duplicate role, mixed/pre-update phase, infrastructure failure | Diagnostic Pilot system metric. Completed `OTHER/INVALID` is a non-stale vote; an incomplete call excludes the case. |
| Exposure-Induced FSCR | Complete same-phase cases for which paired causal-adoption lineage is evaluable | Ordinary stale majority and at least one stale-majority member has verified paired causal stale-adoption lineage | Adds causal-adopter call/message IDs and lineage membership; exclude unevaluable/invalid lineage | Conditional/diagnostic. `OTHER/INVALID` cannot be a stale-majority member but remains a completed vote. |
| Retransmission-Supported FSCR | E2 complete cases with eligible E1 primary adopter, complete matched Relay pair, and complete final phase | Source stale seed → current-aware Target → paired causal stale adoption → exact Target replay → current-aware Relay → Relay stale adoption → same-phase stale majority | Requires all Source seed, E1 probe/arm, E1 origin, E2 replay, Relay probe/arms, final-vote, phase, and majority-member IDs; exclude any broken/cross-arm/cross-scenario link | `conditional`, and `diagnostic` for sparse Pilot results. Completed `OTHER/INVALID` remains non-stale; no path promotion. |

For all tiers, pre-update `m_old` is exposure evidence and is categorically
rejected as a vote. Numerators and denominators, IDs, exclusions, counts, and
rates are emitted separately; no tier implies another causal claim beyond its
predicate.

### I.1 Interpretation and claim boundary

E2 FSCR is a diagnostic system-level characterization of final branch-local
state after the frozen two-hop causal path. It is not an independent
population-level propagation probability. E2 treatment cases are conditionally
selected from E1 causal primary adopters, and Tier C additionally conditions on
verified second-hop lineage; Retransmission-Supported FSCR may therefore be
structurally correlated with `SRR_cond`. It must not be presented as
statistically independent evidence of retransmission. Later result-to-claim
work must preserve this limitation.

## J. Lineage contract

Extend `lineage.py` with pure
`validate_e2_lineage(messages, edges, replay_provenance, calls, topology,
final_votes)`. Reuse frozen `LineageRecord` unchanged; the separate sealed
provenance table disambiguates cross-run identity.

Freeze this relation vocabulary exactly:

* `source_stale_seed`
* `source_to_target_exposure`
* `target_awareness_sibling`
* `target_paired_causal_adoption`
* `e1_target_output_origin`
* `exact_replay`
* `target_to_relay_exposure`
* `relay_awareness_sibling`
* `relay_matched_sibling`
* `relay_stale_adoption`
* `final_vote_member`
* `tier_b_stale_majority_member`
* `tier_c_complete_path`

The validator requires exact IDs/digests at every edge; original once-correct
Source stale seed; Source→Target exposure; isolated Target awareness; E1
treatment/control siblings and causal adoption; exact E1 Target origin;
replay-envelope/provenance equality; Target→Relay exposure; isolated Relay
awareness; Relay matched siblings; Relay treatment stale adoption; and,
complete synchronized same-phase votes and tier membership. It rejects
cycles, missing/duplicate edges, swapped arms, cross-scenario links, changed
content, probe ancestry, mismatched parents, and phase relabeling. Existing
three-field `LineageRecord` can represent graph edges unambiguously when joined
to sealed records, so no schema change is indicated. If implementation proves
otherwise: **STOP — HUMAN DECISION REQUIRED**.

Final-readout membership uses only `final_vote_member`. There are no
communication relations from `source-final` to `target-*-final`, from a
`target-*-final` to a `relay-*-final`, or from any final output to another final
output. The validator requires zero such edges and proves that no final output
appears in another Agent's visible messages; final votes are branch-local
measurements, not retransmitted messages.

## K. E2 run artifacts and manifest contract

All artifacts are canonical JSON/JSONL, non-overwriting, and hash-bound in the
final manifest. `e2.py` wraps existing `RunStore` and manifest functions; no
`manifest.py` change is planned.

| Artifact | Writer / timing | Source and minimum content | Immutability / binding |
| --- | --- | --- | --- |
| `preflight.json` | preflight wrapper; before calls | config, resolved probes, all check results/reasons, budget | write once; manifest hash |
| `eligibility.json` | E1 resolver; before calls | candidate/eligible/excluded IDs, reasons, selected E1 IDs/digests | write once; manifest hash |
| `e2_scenario_overlay.json` | overlay builder; before calls | nine sealed overlays and aggregate digest | write once; manifest hash |
| `upstream_e1_provenance.json` | resolver; before calls | E1 manifest/artifact identities and verified scientific constants | write once; manifest hash |
| `upstream_replay_provenance.json` | envelope builder; before calls | Section-D rows for both arms | write once; manifest hash |
| `branch_topology.json` | orchestrator; planned before and finalized without mutation before calls | parent/fork IDs/hashes and visible IDs for all siblings | write once only after complete plan; manifest hash |
| `calls.jsonl` | RunStore; during calls | Relay and five-per-scenario logical final-readout `CallRecord`s | append-only; final digest in manifest |
| `messages/` | RunStore; before/during calls | exact replay envelopes and generated outputs | per-ID write once; inventory/digest table bound in manifest |
| `lineage.jsonl` | RunStore; before/during calls | controlled Section-J edges | append-only; final digest in manifest |
| `final_votes.jsonl` | final-vote assembler; after calls | one row per system case: scenario/system-case ID, `arm=stale|current`, frozen phase, Source/Target/Relay call and message IDs and answer classes, completeness/exclusion, stale-majority, Tier-B and Tier-C predicates; paired rows reference the same Source call/message | append-only/write once; manifest hash |
| `cache_provenance.json` | orchestrator; after calls | downstream identity hash, key, hit/miss, content/origin and usage | write once; manifest hash |
| `report.json` | pure metrics; after calls | SRR, contrast, Gate 4, three FSCR tiers, exclusions, tokens | finalized once; manifest hash |
| `manifest.json` | manifest wrapper; last | effective config, E1 external reference hashes, every E2 evidence hash, usage/cache stats | final write once; self-consistency check |

`branch_topology.json` is generated from the complete deterministic branch plan
before calls, not incrementally mutated. If actual call records disagree, the
run fails and no scientific report/manifest is finalized. The manifest must
bind a message inventory because individual E1-style message files are not
otherwise all named centrally.

## L. Token and call budget projection

For the frozen eligible maximum `N=9`, budget without assuming cache hits:

| Logical calls | Formula | Maximum |
| --- | --- | ---: |
| Relay awareness | `N` | 9 |
| Relay stale replay | `N` | 9 |
| Relay current replay | `N` | 9 |
| **Core subtotal** | `3N` | **27** |
| Source final (shared across systems) | `N` | 9 |
| Target stale final | `N` | 9 |
| Target current final | `N` | 9 |
| Relay stale final | `N` | 9 |
| Relay current final | `N` | 9 |
| **Final-readout subtotal** | `5N` | **45** |
| **Total logical E2 calls** | `8N` | **72** |
| **Upstream E1 regeneration** | `0` | **0** |

New logical calls do not imply forced generation. An identical valid
`EffectiveGenerationIdentity` must hit the existing cache, but budgeting assumes
no hit. At `max_new_tokens=32`, `72 × 32 = 2,304` is the output-token upper
bound if every logical call generates output. It is not a total-token bound;
input tokens and therefore total E2 tokens remain unknown until a separately
authorized tokenizer-only preflight if required. The compact design is plainly
within the `0.8M` planning ceiling, but preflight must measure and enforce the
full deterministic ceiling before scientific authorization.

## M. Model-free test map

All tests belong only in future `tests/state_mad/test_e2.py`; none are created
by this planning task.

| Test | Target function(s) |
| --- | --- |
| exact stale/current replay and skeleton | `resolve_e1_replay_pair`, `make_e2_replay_envelope` |
| zero E1 generation / zero tokenizer-model calls | `resolve_e1_replay_pair` with trap objects |
| wrong run/SHA/scenario/model/tokenizer/decoding provenance | `resolve_e1_replay_pair` |
| corrupt artifact/hash/text/provenance rejection | `resolve_e1_replay_pair` |
| duplicate selector and ambiguous origin rejection | `resolve_e1_replay_pair` |
| sealed overlay, frozen E1 hash, Relay `v_new` availability | `build_e2_overlay`, `validate_e2_preflight` |
| same Relay parent and parent non-mutation | `plan_relay_branches` |
| awareness isolation | `plan_relay_branches`, `validate_e2_lineage` |
| `decision-v2` exact raw insertion | `render_relay_decision` wrapper |
| effective identity reuse / metadata-only invariance | existing `build_cache_key` through E2 request builder |
| downstream exact hit and generated-usage zero | E2 orchestration with `CachedBackend` fixture |
| complete Source→Target→Relay path | `validate_e2_lineage` |
| swapped-arm, wrong parent, cross-scenario rejection | `validate_e2_lineage` |
| conditional denominator truth table | `evaluate_e2_retransmission` |
| completed `OTHER/INVALID` inclusion as non-stale | `evaluate_e2_retransmission`, `evaluate_e2_fscr` |
| Gate-4 boundary table | `evaluate_e2_retransmission` |
| all three FSCR tiers | `evaluate_e2_fscr`, `validate_e2_lineage` |
| common phase and exactly three unique roles | `assemble_final_votes`, `evaluate_e2_fscr` |
| pre-update `m_old` rejected as vote | `assemble_final_votes`, `evaluate_e2_fscr` |
| incomplete final phase exclusion | `evaluate_e2_fscr` |
| E1 regression preservation | existing E1 suite plus read-only before/after digest assertion |
| resource, paths, backend, revisions, nine IDs | `validate_e2_preflight` |

Final-readout fixtures additionally prove: exactly five logical calls per
scenario; identical shared Source reference across arms; correct Target and
Relay branch mappings; one frozen phase per triplet; no mixed arm IDs; no
readout output in another Agent's visible messages; no final-output
communication edge; no historical-call relabeling; cache-key reuse for
identical effective inputs; metadata-only cache invariance; authoritative
no-peer Source semantics without E3 correction status; no `m_old` vote; exactly
two communication hops; mechanical recognition of non-communication; correct
three-tier FSCR; and fail-closed Source-held-fixed validation.

Every fixture is tiny and sealed; no tokenizer, model, vLLM, GPU, or network
call is permitted.

## N. File/function implementation table

| Path | Existing | Planned | Class | Inputs → outputs | Requirement / cache / lineage | Test / rollback / risk |
| --- | --- | --- | --- | --- | --- | --- |
| `state_mad/e2.py` | absent | immutable E2 records; `resolve_e1_replay_pair`; overlay/envelope/branch/request builders; orchestration; synchronized final-readout builder; `assemble_final_votes` | NEW / WRAP | sealed E1 run + config → verified pairs, overlays, replay messages, calls/artifacts | exact read-only replay; upstream no cache/backend; downstream normal cache; owns cross-run IDs | Section-M resolver through phase tests; delete isolated file to roll back; high integrity/final-vote risk |
| `state_mad/preflight.py` | E0/E1 configs/validators | `E2RunConfig`, `validate_e2_preflight` | EXTEND | config + sealed plans/probes → pass/reasons | bounds and all fail-closed checks before calls; no cache-key change; validates lineage inputs | preflight matrix; revert E2-only additions; medium risk of weakening old gates (forbidden) |
| `state_mad/lineage.py` | E0/E1 validators | `validate_e2_lineage` and fixed relation allowlist | EXTEND | records/provenance/topology → paths/tier predicates/errors | full two-hop/exact replay/final-phase path; cache IDs cross-checked | lineage adversarial tests; revert E2 functions; medium-high false-positive risk |
| `state_mad/metrics.py` | E0/E1 pure metrics | `evaluate_e2_retransmission`, `evaluate_e2_fscr` | EXTEND | stored rows/validated predicates → deterministic report | SRR/contrast/Gate 4/FSCR; no cache or calls; consumes verified lineage | truth tables; revert E2 functions; high denominator/tier risk |
| `tests/state_mad/test_e2.py` | absent | Section-M tests | NEW | tiny fixtures → deterministic assertions | proves exactness, zero upstream calls, cache and lineage/metric contracts | delete file rollback; low product risk |
| `state_mad/snapshots.py` | parent/fork functions | none | REUSE | scenario/snapshot → immutable siblings | common parent | existing + wrapper tests; no change |
| `state_mad/prompts.py` | awareness-v3/decision-v2 | none | REUSE | scenario/snapshot/exact message → prompt | exact text affects normal identity | exact insertion; no change; prompt change is stop |
| `state_mad/cache.py`, `backend.py` | identity cache/generation | none | REUSE | downstream request → exact result | no upstream recovery; no namespace | cache tests; no change |
| `state_mad/schema.py`, `grading.py` | records/digest/grader | none | REUSE / WRAP from e2.py | raw records/output → immutable evidence/classes | separate provenance avoids schema expansion | skeleton/digest tests; no change |
| `state_mad/run_store.py`, `manifest.py` | write-once artifacts/manifest | none | REUSE / WRAP from e2.py | E2 artifacts → sealed run | every evidence hash bound | artifact tests; no change |
| `state_mad/e1.py`, `scenarios.py`, `validation.py` | frozen E1 path | none | REUSE | read only | no E1 rerun/hash change | regression/digest tests; no change |
| `src/**`, `multi_agent_debate.py`, `configs.yaml` | MAD-M² core | none | REUSE | none | no core impact | any proposed edit is immediate stop |

No additional future source file is justified by current static evidence.

## O. Bounded implementation phase order (not authorized)

Every phase below is independently reviewable, has its own rollback, and says
**NO MODEL / GPU CALLS AUTHORIZED**. No phase automatically advances.

| Phase | Allowed files | Acceptance tests | Rollback boundary |
| --- | --- | --- | --- |
| P2-E2.0 read-only resolver | `e2.py`, `test_e2.py` | exact arms, manifest/digest/provenance, duplicate/corruption, trap backend/tokenizer | resolver commit only |
| P2-E2.1 sealed overlay | `e2.py`, `preflight.py`, `test_e2.py` | deterministic hash, E1 hash unchanged, roles/Relay `v_new`, invalid overlay fail | overlay/preflight commit only |
| P2-E2.2 Relay orchestration | `e2.py`, `test_e2.py` | exact envelope, same parent, isolation, no mutation, decision-v2, cache identity/hit | orchestration commit only |
| P2-E2.3 whole-set preflight | `preflight.py`, `e2.py`, `test_e2.py` | all frozen fields, paths, resources, nine pairs before backend trap | E2 preflight commit only |
| P2-E2.4 lineage | `lineage.py`, `e2.py`, `test_e2.py` | complete path plus swapped/cross-scenario/probe-contamination rejection | lineage commit only |
| P2-E2.5 SRR/contrast | `metrics.py`, `test_e2.py` | denominator/OTHER/Gate-4 truth tables and conditional label | retransmission metrics commit only |
| P2-E2.6 synchronized role-specific non-communicative final readout + `final_votes.jsonl` + three FSCR metrics | `e2.py`, `preflight.py`, `lineage.py`, `metrics.py`, `test_e2.py` | five logical calls, matched systems/shared Source, branch isolation, common phase, no communication, seed exclusion, all tiers | dedicated final-readout/FSCR commit |
| P2-E2.7 model-free regression | `test_e2.py` only unless a defect stays inside candidate scope | full E0/E1/E2 model-free suite, diff/artifact checks | test-only commit / revert offending subphase |

If a defect requires any file outside the candidate scope, or a prompt/schema/
core change, stop rather than broadening a subphase.

## P. Human authorization boundary

The stages are strictly manual gates:

1. **E2 Implementation Map** — current task; planning only.
2. **Human review** — Section H is resolved; review this amended map.
3. **Explicit bounded E2 implementation authorization** — names exact files
   and final-vote contract.
4. **Model-free implementation/tests** — no scientific inference.
5. **Frozen E1-artifact integrity preflight on AutoDL** — read-only and
   fail-closed.
6. **E2 tokenizer/token-budget preflight if actually required** — separately
   authorized; no scientific generation.
7. **Explicit human scientific GPU authorization** — required after all prior
   gates pass.
8. **One frozen E2 scientific Pilot execution** — one run only under the
   authorized manifest/configuration.

No stage authorizes or automatically advances to the next.

## Q. Human-decision and stop triggers

Stop for explicit human decision if: the expected planning base differs for
unrelated reasons; any selected E1 artifact is missing, duplicate, corrupt,
ambiguous, or mismatched; the frozen nine-case eligibility cannot be reproduced;
exact text would require regeneration or normalization; origin provenance is
unresolvable; Relay `v_new` or immutable siblings cannot be proved; awareness
contaminates a decision; exact author presentation requires a prompt change;
cache physical layout changes effective reuse; the frozen final-readout design
cannot be implemented in the bounded files without prompt/schema/core change;
more than three Agents/two hops, a new sample/model/seed/baseline,
or the token ceiling would be required; another source file appears necessary;
or any change to `src/**`, `multi_agent_debate.py`, `configs.yaml`, prompts,
schema, E1 compiler/hash, or frozen research artifacts appears necessary.

No stop may be rescued by scope expansion or by treating estimability as
scientific evidence.

## Final verdict

**READY FOR BOUNDED E2 IMPLEMENTATION AUTHORIZATION**

The human-frozen synchronized role-specific non-communicative final readout
resolves the only prior scientific ambiguity. Static consistency review finds
no new prompt, schema, MAD-M² core, Agent, round, model, seed, or scenario
requirement. This verdict means ready for a separate explicit bounded
authorization; it does not itself authorize implementation or execution.

**NO GPU OR MODEL EXECUTION PERFORMED**
**E2 IMPLEMENTATION NOT AUTHORIZED**
**E2 SCIENTIFIC GENERATION NOT AUTHORIZED**
