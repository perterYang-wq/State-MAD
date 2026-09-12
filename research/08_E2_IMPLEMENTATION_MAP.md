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
metrics. It also confirms that the frozen documents define the three FSCR
predicates but **do not uniquely determine the three model decisions and their
visibility at the shared final phase**. Section H records the resulting stop
gate rather than selecting a scientifically consequential design for coding
convenience.

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
final_vote_phase_id=<authorized post-update phase>, overlay_schema="e2-overlay-v1"
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
scenario-set hash. If the final-vote phase is not human-resolved, overlay
sealing cannot complete and scientific preflight must stop.

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
final_vote_spec)`. Required fields/constraints are:

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
| final votes | complete authorized construction, three roles, one post-update phase |

Preflight also requires available model/tokenizer and seed support only where
scientific execution is authorized, verifies run-store nonexistence/write-once
safety and cache-root identity, and emits stable reason codes. Artifact
integrity, eligibility, overlays, branch plans, final-vote specification, and
resource projection are whole-set checks before the first downstream call.
Runtime-only failures remain fail closed. Existing E0/E1 validators are not
changed or weakened.

**Current blocker:** no `final_vote_spec` can pass until Section H receives a
human scientific decision.

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

### H.1 Determination: scientifically non-unique

The frozen artifacts require three Source/Target/Relay post-update decisions
with one `final_vote_phase_id`, but they define neither (a) whether E1/E2
decisions may be reused as votes nor (b) the information visible to each Agent
at a synchronized final phase. Current code produces only Target E1 decisions
and Relay would produce awareness plus matched decisions. There is no Source
post-update decision or final-vote orchestrator. Assigning the same phase ID
after the fact would not establish a shared phase or matched visibility.

Therefore the ten required questions cannot have one authority-derived answer:

1. **Source vote:** no frozen Source post-update call is selected.
2. **Target vote:** either the E1 stale/current Target decision is reused or a
   new synchronized Target call is generated; authority does not choose.
3. **Relay vote:** either the matched E2 Relay decision is reused or a new
   synchronized Relay call is generated; authority does not choose.
4. Consequently, the number of additional calls is unresolved.
5. Final-phase visibility (private branch history, full shared transcript, or
   fixed role-specific exposure) is unresolved.
6. The frozen causal chain supports Round/hop 1 = Source→Target and Round/hop 2
   = Target→Relay, but does not state whether a subsequent final-decision call
   is a readout within Round 2 or a prohibited third debate round.
7. Compliance with `<=2` communication rounds is clear only if final decisions
   are defined as non-communicative readouts; that definition is not frozen.
8. A common phase ID can be mechanically verified only after the underlying
   phase and visibility contract is chosen; merely relabeling cached calls is
   invalid.
9. Treatment/control systems could follow stale/current chains or differ only
   in Target→Relay replay while reusing E1 arms; the required matched system
   construction is not selected.
10. These alternatives change whether Tier B/C majority is a contemporaneous
    system state or an aggregate of causal-path decisions at different times.

### H.2 Competing minimal options requiring human decision

**Option 1 — Path-decision assembly.** Add one Source post-update decision;
reuse the selected E1 Target arm and E2 Relay arm as the three votes, placing
them under a common analytical phase. This minimizes calls but combines
decisions made at different causal times and cannot truthfully establish one
shared final phase merely by assigning an ID. It interprets FSCR as a
path-aggregate majority.

**Option 2 — Synchronized role-specific final readout.** After Relay matched
replay, generate new Source, Target, and Relay decision calls as
non-communicative readouts, with each role retaining its branch-specific
history. This creates a genuine common phase but requires freezing role-specific
visibility, deciding whether the final readout is inside the two-hop bound,
and adding three calls per treatment/control system. It interprets FSCR as a
simultaneous private-history system state.

**Option 3 — Synchronized shared-transcript final readout.** Generate all three
votes after exposing each role to one frozen shared post-update transcript.
This yields a common phase but adds a new exposure/consensus intervention not
specified by E2 and can alter the causal meaning of Tier B/C. It may constitute
an extra debate round.

**Option 4 — Hybrid reuse plus refreshed missing roles.** Reuse Relay (and
possibly Target), generate the remaining votes, and label all with one final
phase. This has asymmetric decision times/visibility and a scientifically
different consensus interpretation; it is not justified by cache economy.

No option is selected. The required resolution must state exact Source,
Target, and Relay calls; each role's visible message IDs; treatment/control
assembly; whether final readouts are a round; and the phase-ID rule. Until then:

> **STOP — HUMAN DECISION REQUIRED**

This stop does not authorize omitting FSCR, changing prompts, adding rounds, or
modifying MAD-M² core.

## I. Three FSCR metric contracts (blocked on H only for data construction)

Proposed pure `evaluate_e2_fscr(final_votes, lineage_report,
system_eligibility) -> dict` would implement the predicates once H is frozen.

| Metric | Denominator / eligibility | Numerator | IDs and exclusions | Label and `OTHER/INVALID` |
| --- | --- | --- | --- | --- |
| Ordinary FSCR | Complete system cases with exactly one Source, Target, Relay vote, all in one verified post-update `final_vote_phase_id` | At least two of three classes are `STALE` | Requires system-case ID, three call/message IDs, role IDs, phase ID; exclude missing/duplicate role, mixed/pre-update phase, infrastructure failure | Diagnostic Pilot system metric. Completed `OTHER/INVALID` is a non-stale vote; an incomplete call excludes the case. |
| Exposure-Induced FSCR | Complete same-phase cases for which paired causal-adoption lineage is evaluable | Ordinary stale majority and at least one stale-majority member has verified paired causal stale-adoption lineage | Adds causal-adopter call/message IDs and lineage membership; exclude unevaluable/invalid lineage | Conditional/diagnostic. `OTHER/INVALID` cannot be a stale-majority member but remains a completed vote. |
| Retransmission-Supported FSCR | E2 complete cases with eligible E1 primary adopter, complete matched Relay pair, and complete final phase | Source stale seed → current-aware Target → paired causal stale adoption → exact Target replay → current-aware Relay → Relay stale adoption → same-phase stale majority | Requires all Source seed, E1 probe/arm, E1 origin, E2 replay, Relay probe/arms, final-vote, phase, and majority-member IDs; exclude any broken/cross-arm/cross-scenario link | `conditional`, and `diagnostic` for sparse Pilot results. Completed `OTHER/INVALID` remains non-stale; no path promotion. |

For all tiers, pre-update `m_old` is exposure evidence and is categorically
rejected as a vote. Numerators and denominators, IDs, exclusions, counts, and
rates are emitted separately; no tier implies another causal claim beyond its
predicate.

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
conditional on H, complete same-phase votes and tier membership. It rejects
cycles, missing/duplicate edges, swapped arms, cross-scenario links, changed
content, probe ancestry, mismatched parents, and phase relabeling. Existing
three-field `LineageRecord` can represent graph edges unambiguously when joined
to sealed records, so no schema change is indicated. If implementation proves
otherwise: **STOP — HUMAN DECISION REQUIRED**.

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
| `calls.jsonl` | RunStore; during calls | Relay and, after H, final-vote `CallRecord`s | append-only; final digest in manifest |
| `messages/` | RunStore; before/during calls | exact replay envelopes and generated outputs | per-ID write once; inventory/digest table bound in manifest |
| `lineage.jsonl` | RunStore; before/during calls | controlled Section-J edges | append-only; final digest in manifest |
| `final_votes.jsonl` | final-vote assembler; after calls | system/arm, role, call/message, phase, class, eligibility | append-only; manifest hash; blocked pending H |
| `cache_provenance.json` | orchestrator; after calls | downstream identity hash, key, hit/miss, content/origin and usage | write once; manifest hash |
| `report.json` | pure metrics; after calls | SRR, contrast, Gate 4, three FSCR tiers, exclusions, tokens | finalized once; manifest hash |
| `manifest.json` | manifest wrapper; last | effective config, E1 external reference hashes, every E2 evidence hash, usage/cache stats | final write once; self-consistency check |

`branch_topology.json` is generated from the complete deterministic branch plan
before calls, not incrementally mutated. If actual call records disagree, the
run fails and no scientific report/manifest is finalized. The manifest must
bind a message inventory because individual E1-style message files are not
otherwise all named centrally.

## L. Token and call budget projection

For eligible maximum `N=9`, the resolved retransmission core has exactly:

* Relay awareness: `N = 9` logical calls;
* Relay stale replay: `N = 9` logical calls;
* Relay current replay: `N = 9` logical calls;
* core total: `3N = 27` logical calls.

Cache hits remain logical calls but generate zero new tokens. Upstream E1 calls
are exactly zero.

Final-vote ambiguity prevents one exact authorized total. Option 1 would add
`N` Source calls (total `4N = 36`) if one treatment system is counted, while
Option 2 would add `3N` for one system (total `6N = 54`) or `6N` for matched
treatment/control systems (total `9N = 81`). Options 3/4 vary similarly. These
figures are planning bounds, not authorization.

Without running a tokenizer, even the conservative 81-call option at the
frozen 32-output-token cap has at most `81 × 32 = 2,592` output tokens.
Input-token usage is unresolved until final visibility is selected; nevertheless
it would need to average more than roughly `9,844` total tokens per call to
reach `0.8M`, far above the compact existing prompts. This demonstrates only a
rough planning margin, not actual usage or tokenizer preflight. The authorized
design must recompute a deterministic ceiling before scientific calls.

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

The common-phase/final-vote fixtures cannot be frozen beyond invariant tests
until Section H is resolved. Every fixture is tiny and sealed; no tokenizer,
model, vLLM, GPU, or network call is permitted.

## N. File/function implementation table

| Path | Existing | Planned | Class | Inputs → outputs | Requirement / cache / lineage | Test / rollback / risk |
| --- | --- | --- | --- | --- | --- | --- |
| `state_mad/e2.py` | absent | immutable E2 records; `resolve_e1_replay_pair`; overlay/envelope/branch/request builders; orchestration; `assemble_final_votes` after H | NEW / WRAP | sealed E1 run + config → verified pairs, overlays, replay messages, calls/artifacts | exact read-only replay; upstream no cache/backend; downstream normal cache; owns cross-run IDs | Section-M resolver through phase tests; delete isolated file to roll back; high integrity/final-vote risk |
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
| P2-E2.6 final votes/FSCR | `e2.py`, `lineage.py`, `metrics.py`, `test_e2.py` | only after H authorization: exact construction, common phase, seed exclusion, all tiers | dedicated final-vote commit; currently blocked |
| P2-E2.7 model-free regression | `test_e2.py` only unless a defect stays inside candidate scope | full E0/E1/E2 model-free suite, diff/artifact checks | test-only commit / revert offending subphase |

If a defect requires any file outside the candidate scope, or a prompt/schema/
core change, stop rather than broadening a subphase.

## P. Human authorization boundary

The stages are strictly manual gates:

1. **E2 Implementation Map** — current task; planning only.
2. **Human review** — must resolve Section H or direct a bounded revision.
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
cache physical layout changes effective reuse; final-vote construction remains
unresolved; more than three Agents/two hops, a new sample/model/seed/baseline,
or the token ceiling would be required; another source file appears necessary;
or any change to `src/**`, `multi_agent_debate.py`, `configs.yaml`, prompts,
schema, E1 compiler/hash, or frozen research artifacts appears necessary.

No stop may be rescued by scope expansion or by treating estimability as
scientific evidence.

## Final verdict

**STOP — HUMAN DECISION REQUIRED**

The exact replay, overlay, Relay branching, cache, preflight, lineage,
conditional retransmission, artifact, test, and bounded file contracts are
implementation-ready. Implementation is nevertheless not authorized because
the frozen authority does not uniquely select the three same-phase final votes
or their visibility. Section H must be resolved scientifically before any E2
implementation authorization.

**NO GPU OR MODEL EXECUTION PERFORMED**
**E2 IMPLEMENTATION NOT AUTHORIZED**
**E2 SCIENTIFIC GENERATION NOT AUTHORIZED**
