# State-MAD Stage 05 — Implementation Map

Status: PLANNING ARTIFACT — NO IMPLEMENTATION AUTHORIZED

Stage: 05-Implementation-Map

Authority order: `RESEARCH_CONTRACT.md` → `EXPERIMENT_PLAN_FROZEN.md` → `IMPLEMENTATION_REQUIREMENTS.md` → `03_EXPERIMENT_PLAN_REVIEW.md` → this map.
Input audit: `04_REPOSITORY_AUDIT.md`, verdict **PASS WITH MINOR REPOSITORY RISKS — READY FOR IMPLEMENTATION MAP**.

## 1. Scope, stage boundary, and terminology

This document maps the frozen requirements onto the audited MAD-M² snapshot. It proposes interfaces and rollback boundaries only. It does **not** authorize implementation, configuration changes, a dry run, model inference, E0, or Pilot execution. Implementation remains gated on explicit human approval.

The design keeps legacy entry points and MAD-M² core behavior unchanged. The proposed implementation is an isolated `state_mad/` package plus `tests/state_mad/`. The only anticipated contact with existing code before E0 is composition around `src.models.LanguageModel`; a core edit is not planned. In particular, the pre-E0 patch must not modify `multi_agent_debate.py`, `src/reasoning_models.py`, `src/prompts.py`, `src/evaluator.py`, `src/utils.py`, `configs.yaml`, processed datasets, or existing launch scripts.

Disposition labels:

- **REUSE** — use existing behavior unchanged.
- **WRAP** — compose around an existing public object/function without changing it.
- **EXTEND** — make a narrow existing-code change only if the documented wrapper approach is proven insufficient and separately approved.
- **NEW MODULE** — add isolated State-MAD code; this is not a replacement MAD framework.

Priority labels in this map are stage labels, not permission to implement:

- **P0** — minimum infrastructure required before the deterministic dry run and E0.
- **P1** — additional capability required for E1 after E0 PASS and human/frozen gate authorization.
- **P2** — additional capability required for E2, E3, or E4 after their preceding gates authorize it.
- **DEFER** — hardening, legacy cleanup, campaign execution, or prohibited expansion not authorized now.

## 2. Proposed package boundary

```text
state_mad/
  __init__.py
  schema.py              # immutable typed records and canonical serialization
  scenarios.py           # deterministic compiler and balance report
  validation.py          # fail-closed mechanical validation
  prompts.py             # State-MAD-only deterministic renderers
  snapshots.py           # immutable snapshots and pure forks
  cache.py               # content-addressed exact-output cache
  backend.py             # cached adapter around src.models.LanguageModel
  grading.py             # strict closed-pool parser/classifier
  lineage.py             # call/message records and mechanical path checks
  run_store.py           # atomic append-only run artifacts
  manifest.py            # environment/repository provenance
  metrics.py             # offline-only E0 metrics initially
  e0.py                  # bounded E0 orchestration and gate report
  preflight.py           # resource/runtime/model validation
tests/state_mad/
  ...                    # deterministic unit/integration tests; fake backend only
```

The package owns experimental control, not general memory. `schema.py` carries direct categorical facts only; `prompts.py` renders known symbolic fields and never extracts state from natural language. `backend.py` is the only model-call boundary. `metrics.py` and all analysis consume saved structured records and have no backend dependency.

## 3. Common contracts used by the mappings

These interfaces are proposed so every requirement has a precise boundary. Names may change only through review without changing their semantics.

### 3.1 Immutable data types (`state_mad/schema.py`) — NEW MODULE

- `ScenarioRecord`: frozen record containing `scenario_id`, split, generator seed, template/counterbalance group, fact identity, ordered versions, `v_old`, `v_new`, `v_wrong`, one-to-one answer pool/positions, Agent roles, ordered events, visibility schedule, snapshot IDs, decision phase IDs, and post-update final-vote phase ID.
- `MessageRecord`: frozen record containing message identity/content hash, raw content, author/recipient, parents, fact/version, generation-time and decision-time validity, phase, and creation source (`deterministic` or `model`).
- `Snapshot`: frozen tuple of immutable event/message references plus fact-state and visibility records; it never contains probe output unless the probe is itself the branch being represented.
- `GenerationRequest`: immutable execution envelope that keeps two explicit parts separate: (A) lineage/execution metadata and (B) an `EffectiveGenerationIdentity`. Part A records provenance such as scenario/scenario-set hash, experiment, phase, condition, pair ID, Agent identity/role, snapshot/parent hashes, and branch ID, but it is not hashed into the cache key.
- `EffectiveGenerationIdentity`: only the fields that determine the actual model generation: exact serialized model-visible system/user input bytes (thereby including exact visible message content and ordering as rendered), model identity and resolved revision, tokenizer/chat-template identity and revision where they affect serialization, the complete effective decoding configuration, effective seed, `max_new_tokens`, and every other effective generation parameter. The cache key is the canonical hash of this record only.
- `GenerationResult`: exact raw output, derived parse/class, per-output input/output/total tokens, cache status, and immutable request/key references.
- `CallRecord` and `LineageRecord`: logging-contract fields with explicit null/not-applicable values where a later-stage concept does not apply.

Canonical hashes use UTF-8 bytes of sorted-key, fixed-separator JSON with an explicit schema version. Lists whose order affects model input remain ordered; unordered sets are sorted before serialization. Hash algorithms and schema versions are stored with each hash. Cache-key canonicalization is applied only to `EffectiveGenerationIdentity`; provenance hashes and identifiers remain in requests, manifests, call records, and lineage without independently entering that identity.

### 3.2 Backend boundary (`state_mad/backend.py`) — WRAP

```python
class GenerationBackend(Protocol):
    def generate(self, request: GenerationRequest) -> BackendOutput: ...

class CachedBackend:
    def generate(self, request: GenerationRequest) -> GenerationResult: ...
```

`LanguageModelBackend` will wrap one `src.models.LanguageModel` instance and translate a single explicit request to its existing `LanguageModel.__call__(prompts, answer_process=False)` path. E0 calls are deliberately single-output calls so existing batch-aggregate token totals are per-call totals. The wrapper retains the returned unparsed text and independently derives token counts consistently. The cache is outside the model wrapper: every call passes through `CachedBackend`.

If composition cannot expose raw text, per-output token counts, resolved revision, or a supported seed, the implementation must stop and present evidence before any **EXTEND** change to `src/models.py`. The only admissible fallback would be a narrow additive raw-generation method or return field; changing generation, parsing, or MAD behavior is outside the rollback boundary.

### 3.3 Artifact layout (`state_mad/run_store.py`) — NEW MODULE

Each run gets a new, non-overwriting directory containing canonical scenarios and balance report, manifest, calls in append-only JSONL, messages in content-addressed files, lineage records, cache manifest, and an offline gate/metric report. Creation uses a temporary directory/file plus atomic rename. Existing run IDs fail closed rather than overwrite. Historical stale messages are preserved.

## 4. P0 — required before deterministic dry run and E0

P0 implements only the minimum infrastructure enumerated by the E0 boundary. It supports 16 scenarios, at most two Agents, one exposure round, one open 7B model, deterministic/near-deterministic decoding, and the three E0 questions. It does not implement E2/E3/E4 behavior.

### P0.1 Symbolic scenario compiler

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Compile exactly 16 direct categorical factual-supersession scenarios with deterministic scenario/fact/version IDs; `v_old → v_new`; never-current `v_wrong`; event order; answer pool; Agent visibility; and final phase, without LLM semantic parsing. |
| Exact existing file/function  | No suitable compiler exists. Existing benchmark selection begins in `multi_agent_debate.py:main` (dataset-path/evaluator dispatch), and `src.evaluator.BaseEvaluator.load_data` is benchmark-oriented; neither is modified or used as a scenario compiler. |
| Proposed minimal modification | Add `state_mad/scenarios.py::compile_e0_scenarios(spec, seed) -> ScenarioSet` using a fixed direct-state template and deterministic cyclic assignments; add the frozen records in `state_mad/schema.py`. Scenario content is generated by code only. |
| Disposition                   | **NEW MODULE**.                                              |
| Interface                     | `compile_e0_scenarios(E0ScenarioSpec(count=16, template_id, value_pool, seed))`. Count other than 16 is rejected by the E0 runner. |
| Input / output                | Input: checked-in symbolic spec/value pool and integer seed. Output: immutable tuple of 16 `ScenarioRecord`s plus canonical `scenario_set_hash`; no prompts or model outputs. |
| Cache implications            | Scenario and answer mappings are not model cache entries. `scenario_id` and `scenario_set_hash` remain required provenance in manifests, call records, and lineage, but are not unconditional cache-key components. Scenario content influences a key only through a resulting change to the serialized model-visible input (or effective generation parameters). Recompilation with identical spec/seed must be byte-identical. |
| Lineage/logging implications  | IDs, supersession edges, ordered events, visibility, answer mapping, and phase IDs seed all later message/call records. Compiler version and generator seed enter the manifest. |
| Deterministic test            | `test_compile_e0_is_byte_stable_and_has_16_scenarios`; compile twice and compare canonical bytes/hash and deterministic IDs. |
| Rollback boundary             | Delete `state_mad/schema.py`, `state_mad/scenarios.py`, and their tests; no legacy source/data/config changes. |

### P0.2 Mechanical validation and value/position counterbalancing

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Before any call, reject non-distinct role values, invalid current history, ever-current `v_wrong`, non-authoritative measured state, missing Target current visibility, non-bijective answers, cyclic events, wrong stale reference, pre-update final vote, or failed value/option-position balance. Produce a balance report; each surface value occupies CURRENT/STALE/STATIC_WRONG as evenly as integer counts permit, independently of option position. |
| Exact existing file/function  | No suitable validator/counterbalancer exists. `src.utils.extract_answers`, `dataset_2_process_fn`, and evaluator graders parse benchmark answers and are explicitly not reused for this contract. |
| Proposed minimal modification | Add `state_mad/validation.py::validate_scenario_set` with pure fail-closed checks and `state_mad/scenarios.py::build_balance_report`. Compiler uses a cyclic Latin-square-style role rotation and a separate cyclic option-position rotation. |
| Disposition                   | **NEW MODULE**.                                              |
| Interface                     | `validate_scenario_set(scenarios, phase="E0") -> ValidationReport`; any error raises `ScenarioValidationError` before backend construction/call. |
| Input / output                | Input: immutable scenario set. Output: structured errors/warnings, per-value role counts, per-role option-position counts, max-min deltas, and `passed`; canonical JSON is saved. |
| Cache implications            | Validation occurs before cache lookup or model initialization. Invalid sets create no generation/cache entries. The validated set hash and validation-report hash enter the manifest. |
| Lineage/logging implications  | Validation establishes the authoritative IDs and eligibility prerequisites used by lineage. Validation failures are run-preflight records, never experimental exclusions. |
| Deterministic test            | Parameterized mutation tests for every frozen rejection rule, plus `test_e0_counterbalance_role_and_position_deltas_at_most_one`; spy backend proves zero calls on failure. |
| Rollback boundary             | Delete validator/balance functions and tests; compiler remains separable and legacy graders remain untouched. |

### P0.3 Deterministic prompts and matched message skeletons

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Use distinct awareness and ordinary-decision prompts; strict structured answers; style-matched current/stale/static-wrong peer messages with the same deterministic template, identity label, confidence style, syntax, structural fields, and near-equal tokenizer footprint. Preserve once-correct generation history for stale content. |
| Exact existing file/function  | `src.prompts.prompts_with_format` and generic prompt constants serve benchmark CoT/debate. They do not encode State-MAD phases or strict categorical outputs and remain unchanged. |
| Proposed minimal modification | Add pure renderers `render_awareness_probe`, `render_decision`, and `render_peer_message` in `state_mad/prompts.py`. Peer skeleton varies only the symbolic value and required temporal-history field. Render the source old-state record while old is current, then replay it after update. |
| Disposition                   | **NEW MODULE**; existing prompt machinery is not modified.   |
| Interface                     | Renderers accept `ScenarioRecord`, `Snapshot`, condition, role, and ordered visible `MessageRecord`s; return immutable `RenderedPrompt(text, template_id, template_hash, prompt_hash)`. |
| Input / output                | Input: validated symbolic records only. Output: deterministic UTF-8 prompt/message bytes and hashes; strict answer schema permits exactly one answer-pool symbol. |
| Cache implications            | Exact serialized model-visible bytes—including visible message content and ordering as rendered—enter `EffectiveGenerationIdentity`. Prompt hashes, template IDs, and visible-message IDs/content hashes are retained for provenance and integrity checking but do not independently enter the key. Awareness and no-peer rendered text must differ and therefore normally have distinct keys. A defensive assertion detects accidental byte-identical effective generation identities and forces shared reuse plus a `selected_degenerate` flag. |
| Lineage/logging implications  | Deterministic source/peer messages still receive message IDs, fact/version IDs, validity at generation/decision, author/recipient, and parents. Raw rendered bytes are preserved. |
| Deterministic test            | Golden-byte/hash tests; structural comparison confirms stale/static-wrong skeleton equality except allowed fields; test awareness/no-peer inequality and identical-effective-request defense. |
| Rollback boundary             | Delete State-MAD prompt module/tests; `src/prompts.py` remains unchanged. |

### P0.4 Immutable snapshots and branch isolation

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Awareness and all experimental conditions fork from the same immutable pre-exposure Target snapshot. Probe output never enters treatment/control history. Sibling evaluation never mutates the parent. E0 must also demonstrate replay/snapshot integrity. |
| Exact existing file/function  | `src.reasoning_models.MultiAgentDebate.__call__` builds mutable `history` lists and `_debate_with_contexts` derives later lists; it has no snapshot/fork API. It is unsuitable for the causal branch invariant and remains unchanged. |
| Proposed minimal modification | Add `state_mad/snapshots.py::make_pre_exposure_snapshot` and pure `fork_snapshot(parent, branch_id, additions)` over frozen tuples/content hashes. The E0 runner independently creates probe/current-peer/stale-peer (and dry-run-only no-peer/static-wrong render checks) from the same parent. |
| Disposition                   | **NEW MODULE**.                                              |
| Interface                     | `Snapshot.fork(branch_id, visible_message_ids=...) -> Snapshot`; no mutator methods. `snapshot_hash` covers ordered events/messages, state, visibility, phase, and schema version. |
| Input / output                | Input: validated scenario and immutable event/message references. Output: new immutable snapshot sharing parent references plus an explicit `parent_snapshot_hash`; parent bytes/hash remain unchanged. |
| Cache implications            | `snapshot_id`, complete `snapshot_hash`, `parent_snapshot_hash`, and branch labels remain authoritative lineage/provenance fields but do not independently enter keys. Only ordered model-visible content rendered from a snapshot can affect `EffectiveGenerationIdentity`. Sibling snapshots with different lineage metadata but identical serialized model-visible input and effective generation parameters must converge on one key. |
| Lineage/logging implications  | Each call records parent/current snapshot hashes and ordered visible messages. Probe result has its own branch/message record and is prohibited from decision-branch ancestry. |
| Deterministic test            | Attempted mutation fails; fork leaves parent canonical bytes/hash unchanged; sibling order does not alter outputs; graph assertion proves probe message absent from all decision ancestors. |
| Rollback boundary             | Delete snapshot module/tests; no modification to mutable legacy debate histories. |

### P0.5 Immutable message cache and exact replay

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Generate once; persist exact raw output and parsed fields; exact replay; key all effective inputs/parameters; distinguish miss/hit/invalid-corrupt; never silently regenerate an existing identity; retain raw historical messages. |
| Exact existing file/function  | No cache exists. `src.models.LanguageModel.__call__` always calls `self.llm.generate`; `MultiAgentDebate` holds only in-memory histories and evaluator JSON is not a cache. |
| Proposed minimal modification | Add `state_mad/cache.py::MessageCache`, content-addressed entries, canonical `build_cache_key`, atomic create-if-absent writes, checksum/schema validation, and fail-closed collision/corruption handling. Add `CachedBackend` in `state_mad/backend.py`; prohibit direct runner access to `LanguageModelBackend`. |
| Disposition                   | **NEW MODULE + WRAP** existing `LanguageModel`; no model-core edit planned. |
| Interface                     | `cache.lookup(key) -> MISS | HIT(entry) | INVALID(reason)`; `cache.commit_miss(key, result)` succeeds only if absent; `CachedBackend.generate(request)` calls backend only on a valid miss. There is no force-regenerate-on-invalid option in experiment code. |
| Input / output                | `build_cache_key` canonically hashes `EffectiveGenerationIdentity` only: exact serialized model-visible input bytes (including visible content/order), model and resolved revision, serialization-affecting tokenizer/chat-template revision, complete effective decoding parameters, effective seed, maximum output length, and any other effective generation parameter. Scenario/set hashes, experiment, phase, condition, pair ID, Agent identity/role, snapshot/parent hashes, branch IDs, prompt/template hashes, and message IDs remain attached provenance; none independently distinguishes an entry. If any such label changes rendering, that difference is already captured in the serialized input. Output is exact raw bytes plus derived fields/checksum and status. |
| Cache implications            | This is the cache boundary. Hits return exact stored raw content, report zero newly generated tokens while retaining original-generation usage by reference, and append a replay call record. Invalid/corrupt entries halt the run. |
| Lineage/logging implications  | Original generation and each replay are separate call/lineage events referencing the same immutable message ID/content hash and origin-call ID; status records `miss`, `hit`, or `invalid`. |
| Deterministic test            | Counting fake backend proves: metadata-only differences reuse one key and one exact output; different scenario/scenario-set, snapshot/parent/branch, Agent ID/role, experiment, phase, condition, and pair identifiers reuse one key when serialized model-visible input and effective parameters are identical; and any actual serialized input, visible content/order, model, resolved model revision, serialization-affecting tokenizer/chat-template revision, effective decoding parameter, seed, or maximum-output difference changes the key as appropriate. Corrupt entries and attempted duplicate commits fail closed without generation or overwrite. |
| Rollback boundary             | Delete isolated cache/backend adapters and test cache directories. No legacy output format or generation path is changed. |

### P0.6 Deterministic closed-pool grader

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Mechanically parse strict output and map to CURRENT, STALE, STATIC_WRONG, or OTHER/INVALID. Preserve raw output; no LLM judge or semantic interpretation. `OTHER/INVALID` stays in denominators where specified. |
| Exact existing file/function  | `src.utils.extract_answers` and `src.evaluator` graders are dataset-specific; `LanguageModel._answer_process` may fall back to benchmark parsing. They are not suitable and will be bypassed using `answer_process=False`. |
| Proposed minimal modification | Add `state_mad/grading.py::grade_output(raw_output, answer_pool)`. Accept exactly one canonical structured field/value and exact pool membership; duplicated fields, extra candidate values, malformed structure, or unknown answers map deterministically to OTHER/INVALID with reason code. |
| Disposition                   | **NEW MODULE**; legacy parser remains unchanged.             |
| Interface                     | `grade_output(bytes_or_text, FrozenAnswerPool) -> Grade(parsed_output, answer_class, status, reason)`. |
| Input / output                | Input: immutable raw output and scenario-specific bijective answer map. Output: derived parsed symbol and four-way class; raw data is neither normalized destructively nor replaced. |
| Cache implications            | Raw output is the cached authority. Parser/schema version and answer-pool hash accompany derived fields; regrading is offline and never changes cached raw content or calls the model. |
| Lineage/logging implications  | Call record stores raw reference, parsed output, class, parser version/status, and exclusion reason only for infrastructure failure—not for OTHER/INVALID. |
| Deterministic test            | Exhaustive fixtures for each pool value and malformed/duplicate/case/whitespace/unknown forms; repeat and permutation tests prove stable classification and no backend import/call. |
| Rollback boundary             | Delete grader/tests; no changes to `src/utils.py` or evaluators. |

### P0.7 Lineage logging, immutable run store, and raw preservation

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Record every mandatory call/replay field and make awareness, exposure, paired adoption, and later paths mechanically reconstructable. Preserve raw output append-only. E0 needs source seed → update/current-aware Target → matched current/stale exposure → decision lineage. |
| Exact existing file/function  | `MultiAgentDebate._initial_round`, `_debate_with_contexts`, and `save_debate_log` store prompts/parsed responses/perplexities in mutable nested JSON without required IDs/validity/lineage; evaluator save paths may overwrite. |
| Proposed minimal modification | Add `state_mad/lineage.py::{make_call_record, make_message_record, validate_e0_lineage}` and `state_mad/run_store.py::RunStore`. Use explicit null/not-applicable correction/E2/E4 fields so the schema can extend without pretending those events occurred. Atomic append and unique run directory; raw message payloads addressed by checksum. |
| Disposition                   | **NEW MODULE**. Existing JSON idiom is conceptually reused, not its schema/path. |
| Interface                     | `RunStore.create(run_id)`, `append_call(record)`, `put_message(message)`, `append_lineage(edge)`, `finalize(report)`; validators consume records and return structured violations. |
| Input / output                | Input: immutable scenario/snapshot/request/result/grade records. Output: JSONL call and lineage ledgers, content-addressed raw messages, status/eligibility/exclusion fields, and E0 reconstruction report. |
| Cache implications            | Cache content and run records are separate: cache is reusable immutable generation storage; each run logs its own hit/replay. Cache manifest links keys to content hashes and detects missing origins. |
| Lineage/logging implications  | Include all frozen fields: run/experiment/scenario/condition/pair/message/fact/version IDs; author/recipient/parents; both validity times; awareness; correction flags; decision/final phase; hashes; model/revisions; seed/config; prompts/visible messages; raw/parsed/class; tokens; cache status; eligibility/exclusion. E0 correction/final-consensus fields are explicit N/A. |
| Deterministic test            | Build a fake E0 trace and mechanically reconstruct awareness plus treatment-only stale regression; reject wrong parents, mismatched facts/versions, probe contamination, missing raw payload, or a stale message not valid at creation. Confirm reopening an existing run ID and rewriting a payload fail. |
| Rollback boundary             | Delete lineage/run-store modules and isolated test artifacts; legacy debate logs remain untouched. |

### P0.8 Per-call token accounting

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Record input/output/total tokens per call, cache hit, and E0 stage/scenario summaries from actual prompts/backend usage. Cache hits consume no generation tokens and must be distinct from original usage. |
| Exact existing file/function  | `src.models.LanguageModel._answer_process` counts `output.prompt_token_ids` and generated token IDs; `LanguageModel.__call__` exposes only batch totals and updates `src.model_utils.TokenUsageTracker`. |
| Proposed minimal modification | **REUSE** existing token-ID accounting by submitting one E0 request per backend call through `LanguageModel.__call__(..., answer_process=False)`, making batch totals per-call. `backend.py` maps totals to `TokenUsage`; offline aggregation lives in `metrics.py`. If backend output access is needed for independent verification, prefer tokenizer counts in the wrapper before seeking a narrow extension. |
| Disposition                   | **REUSE + WRAP**; **EXTEND only if unavoidable and separately approved**. |
| Interface                     | Each `GenerationResult.usage` has original input/output/total; each run-call record has `generated_usage` (zero on hit) plus `origin_usage_ref`. `summarize_tokens(records, group_by=...)` is offline. |
| Input / output                | Input: exact prompt/raw result and existing returned token totals. Output: integer usage with method/stage/scenario grouping and cache-hit/miss counts. |
| Cache implications            | Miss stores original usage. Hit never re-tokenizes as if generated and adds zero to generated-token ceiling, while retaining audit access to stored origin usage. |
| Lineage/logging implications  | Token fields live on every call/replay and aggregate reports; masking is not part of E0. Any unavailable/inconsistent count is an infrastructure failure, not silently estimated. |
| Deterministic test            | Fake outputs with known IDs verify exact counts; repeated cache hit preserves origin usage but adds zero generated tokens; sums by scenario/stage equal call ledger totals. |
| Rollback boundary             | Remove wrapper aggregation. No change to `TokenUsageTracker` or `src/models.py` unless separately approved after wrapper-failure evidence. |

### P0.9 Deterministic decoding, resource bounds, and runtime/model preflight

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | One open Qwen2.5-7B-Instruct checkpoint, homogeneous Agents, deterministic first phase (`temperature=0`, fixed seed where supported), stable ordering, exact model/tokenizer revisions, ≤2 E0 Agents, one exposure round, 16 scenarios, and no silent substitution. Validate environment before calls. |
| Exact existing file/function  | `src.config_utils.LLMConfig` loads model/temperature/top-p; `src.models.LanguageModel.__init__` constructs vLLM; `LanguageModel.__call__` constructs `SamplingParams` without seed. `multi_agent_debate.py:main` exposes seed/Agents/rounds but seed controls evaluator sampling, and `configs.yaml` defaults temperature to 1. Current audited runtime lacks required packages/GPU/model. |
| Proposed minimal modification | Add State-MAD-specific frozen `E0RunConfig` and `state_mad/preflight.py::validate_e0_preflight`; do not edit legacy config. Require exact configured model/tokenizer revisions, temperature 0, stable sorted scheduling, supported backend seed, maximums, and dependency/GPU/checkpoint checks before model construction. `LanguageModelBackend` supplies the effective configuration; inability to pass/verify seed or revision is reported, with cache as the hard replay boundary. |
| Disposition                   | **WRAP + NEW MODULE**; reuse `LLMConfig`/`LanguageModel` loading only after validation. |
| Interface                     | `validate_e0_preflight(config, scenarios, backend_probe) -> PreflightReport`; `build_language_model_backend(config)` only accepts a passed report. |
| Input / output                | Input: frozen run config, 16-scenario validated set, environment/model metadata. Output: resolved model/tokenizer/backend revisions, effective decode/seed/resource settings, warnings/errors, and pass/fail. |
| Cache implications            | All effective decoding and resolved revision fields enter keys. Unsupported/unresolved required identity fails before lookup/generation; no alternate model is selected. Stable scheduling ensures deterministic call order but key reuse remains the reproducibility boundary. |
| Lineage/logging implications  | Effective—not merely requested—settings enter every call and manifest. Runtime limitation is logged as preflight failure and produces no scientific results. |
| Deterministic test            | Pure tests reject 15/17 scenarios, >2 Agents, >1 exposure round, temperature ≠0, wrong/model-unresolved revision, unsupported seed, excessive rounds/model count, or projected bounds; fake passing probe records exact effective settings. |
| Rollback boundary             | Delete State-MAD preflight/config wrapper. Do not alter `configs.yaml`, CLI defaults, or environment. If Qwen/runtime cannot be provisioned, stop with `需要人工决策`; never substitute automatically. |

### P0.10 Minimal reproducibility manifest

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Save git SHA/branch/dirty state; config/scenario/prompt hashes; model/tokenizer identities/revisions; decoding/seeds; Python/packages/backend; GPU/quantization/batching/context; command/timestamps; tokens; raw trajectories; and cache manifest/hit statistics, sufficient for offline replay/analysis. |
| Exact existing file/function  | Existing evaluator summaries and `LanguageModel.get_token_usage_summary` are coarse and lack the required provenance. No manifest builder exists. |
| Proposed minimal modification | Add `state_mad/manifest.py::build_manifest` and finalization validation. Gather read-only repository/runtime facts and hashes of canonical artifacts. Record unavailable optional hardware fields explicitly; required model/revision fields must already pass preflight. |
| Disposition                   | **NEW MODULE**, conceptually reusing existing JSON serialization. |
| Interface                     | `build_manifest(run_config, artifacts, preflight, command, started_at) -> RunManifest`; `finalize_manifest(..., ended_at, usage, cache_stats)`. |
| Input / output                | Input: validated config/artifact hashes, repository/runtime probes, call ledger. Output: versioned canonical JSON manifest and hash. |
| Cache implications            | Manifest records cache root/schema/hash algorithm, keys/content hashes, origin/hit/miss/invalid counts; it does not mutate cache entries. |
| Lineage/logging implications  | Manifest binds scenario, prompts, calls, lineage, raw trajectories, code state, runtime, and totals into one auditable run. Dirty state is recorded, not hidden. |
| Deterministic test            | Fixed probe fixtures yield golden canonical manifest; required-field omission fails finalization; manifest totals reconcile with call/cache ledgers. |
| Rollback boundary             | Delete manifest module/tests and run manifests; no repository metadata is changed. |

### P0.11 Minimal E0 runner and branch/replay orchestration

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Enforce `minimal dry run → E0 only → Gate 1`; test only use of `v_new`, awareness viability, and non-zero stale regression. E0 has 16 scenarios, ≤2 Agents, one exposure round, same first-phase config as Pilot. Same-snapshot current-peer/stale-peer paired calls are required; no consensus/recovery/mitigation campaign. |
| Exact existing file/function  | `multi_agent_debate.py:main` and `MultiAgentDebate.__call__` run benchmark debate batches and do not provide controlled immutable sibling branches. They remain baseline paths, not the E0 runner. |
| Proposed minimal modification | Add `state_mad/e0.py::run_e0`. It compiles/validates, builds/fixes each pre-exposure snapshot after `v_new`, runs a non-writing awareness branch, and only for eligibility analysis runs ordinary current-peer and stale-peer decisions from the same parent. It creates/freeze/replays peer messages through cache and records every step. Add `run_e0_dry(fake_backend)` for infrastructure tests with no model. |
| Disposition                   | **NEW MODULE + WRAP** backend.                               |
| Interface                     | `run_e0(config, cached_backend, run_store) -> E0Report`; orchestration accepts only P0 condition enum and refuses E1/Pilot flags. Dry run uses the identical orchestration with a scripted fake backend. |
| Input / output                | Input: approved fixed E0 config and validated scenario set. Output: immutable call/message/lineage artifacts plus offline E0 report; no fabricated result if preflight/call fails. |
| Cache implications            | Source/current peer messages generate once only if model-rendered; deterministic skeletons are stored as immutable messages. Target branches use effective keys. Resume reuses valid entries and never regenerates them. |
| Lineage/logging implications  | Pair ID binds current/stale decisions to one parent snapshot; awareness status is derived from independent probe but its output is not an ancestor. Failures are logged and excluded only under frozen infrastructure rules. |
| Deterministic test            | Fake-backend integration verifies exact call count/order, two-Agent/one-round ceiling, parent equality, probe isolation, replay on rerun, all records, and refusal to invoke P1/P2 paths. |
| Rollback boundary             | Delete `e0.py` and tests; all baseline entry points/core remain intact. |

### P0.12 Offline E0 metrics and Gate 1

| Map field                     | Mapping                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| Frozen requirement            | Mechanically compute E0 current-state use, awareness, arm-specific SAR, paired CSAE, confirmed treatment-only stale regressions, Current-State Accuracy, Token Usage, and Gate 1. Thresholds: awareness ≥80%, ≥3 regressions, CSAE ≥0.10; hard stop on zero regressions or awareness <50%; `0 < CSAE <0.10` is human-decision ambiguous. |
| Exact existing file/function  | `src.utils.if_reach_consensus` and evaluator accuracy code do not implement paired State-MAD eligibility/metrics. They remain unchanged. |
| Proposed minimal modification | Add pure functions in `state_mad/metrics.py`: `compute_sar`, `compute_csae`, `compute_current_accuracy`, `summarize_tokens`, and `evaluate_e0_gate`; add a record-integrity validator before computation. No model/backend import. |
| Disposition                   | **NEW MODULE**.                                              |
| Interface                     | `evaluate_e0(records, scenarios) -> E0Report(status, counts, rates, exclusions, integrity_errors)`, where status is `PASS_TARGET`, `STOP`, `HUMAN_DECISION`, or `INCOMPLETE`; thresholds are labeled operational, never p-values. |
| Input / output                | Input: saved canonical scenarios plus call/message/lineage ledgers. Output: deterministic JSON report with numerators/denominators, paired scenario IDs, classes, exclusions, current accuracy, token/cache summaries, and gate rationale. |
| Cache implications            | Strictly offline; no backend reference or cache writes. It may verify recorded content hashes and cache-origin references read-only. |
| Lineage/logging implications  | Only independently current-aware Targets with complete same-snapshot current/stale pairs enter CSAE. OTHER/INVALID stays in completed denominators. Every included/excluded scenario ID and reason is emitted. |
| Deterministic test            | Hand-built fixtures cover PASS target, zero-regression STOP, awareness <50% STOP, ambiguous CSAE, incomplete infrastructure, OTHER/INVALID denominator behavior, and repeated byte-identical report generation while a fail-on-call backend proves offline operation. |
| Rollback boundary             | Delete P0 metric/gate functions and tests; saved raw artifacts remain readable JSON. |

### P0 completion acceptance matrix

No model inference may begin until the deterministic dry run passes all rows:

1. 16 scenarios compile byte-stably and validator/counterbalance report passes.
2. Awareness and ordinary decision prompts are distinct; peer skeleton matching passes.
3. Parent snapshot is unchanged and probe ancestry is absent from decision branches.
4. Identical `EffectiveGenerationIdentity` is generated once and replayed exactly despite metadata-only request differences; corruption fails closed.
5. Grader produces only the frozen four classes without model judgment.
6. E0 source/update/exposure/adoption lineage reconstructs mechanically.
7. Every call/replay has reconciled per-call token and cache fields.
8. Manifest binds repository/config/scenario/prompt/model/runtime/artifacts.
9. Runner refuses >16 scenarios, >2 Agents, >1 exposure round, nonzero temperature, extra model/method/experiment, and unapproved conditions.
10. Offline report invokes no generation path and applies Gate 1 exactly.

## 5. P1 — required for E1 only, after E0 PASS and authorization

P1 extends the P0 control layer to the 40-scenario Pilot E1; it is not part of the pre-E0 implementation approval unless a human explicitly says so.

### P1.1 Full four-arm E1 orchestration

- **Frozen requirement:** from one immutable pre-exposure Target snapshot, independently probe awareness and execute only `no-peer`, `current-peer`, `stale-peer`, and `static-wrong`; current-peer is primary control. Preserve once-correct old source message and style matching. Pilot uses 40 scenarios.
- **Exact existing location:** no controlled branch runner exists; `MultiAgentDebate.__call__` cannot enforce this invariant.
- **Minimal map/disposition:** **EXTEND the isolated runner**, not MAD core: `state_mad/e1.py::run_e1`, reusing P0 schema/snapshots/prompts/cache/backend/store. Add full no-peer/static-wrong generation and paired branch completeness.
- **Interface/I-O:** `run_e1(PilotConfig(count=40), CachedBackend, RunStore) -> E1Artifacts`; offline input/output remains canonical records.
- **Cache:** exact P0 key contract; deterministic/static messages do not regenerate; all siblings converge on effective-input identities.
- **Lineage/logging:** record all four arms, pair IDs, same parent hash, awareness exclusions, and distinct awareness/no-peer prompts.
- **Deterministic test:** fake-backend four-arm matrix proves one parent, probe isolation, expected cache calls, and 40-scenario/resource enforcement.
- **Rollback:** delete `e1.py` and P1 tests; P0 remains usable.

### P1.2 Full E1 offline metrics and pilot gates

- **Frozen requirement:** SAR by arm, CSAE stale-current, stale/no-peer and stale/static-wrong contrasts, Current-State Accuracy, tokens, treatment-only transitions, Gate 2 causal target/unsupported rule, and Gate 3 stale-specificity/concordance flag. Analysis is paired, current-aware, and offline.
- **Exact existing location:** no equivalent; legacy accuracy/consensus is unsuitable.
- **Minimal map/disposition:** **EXTEND** `state_mad/metrics.py` with `evaluate_e1`; no model dependency.
- **Interface/I-O:** saved E1 records → counts, denominators, paired differences, concordance, eligibility/exclusions, operational gate labels.
- **Cache:** read-only hash verification; no generation.
- **Lineage/logging:** list every qualifying paired transition and matched snapshot; keep OTHER/INVALID in denominators.
- **Deterministic test:** fixed 40-case tables exercise ≥30/≥5/0.10 targets, `|CSAE|<0.05` unsupported rule, and Gate 3 condition.
- **Rollback:** remove P1 metric functions only.

### P1.3 Pilot resource/manifest completion

- **Frozen requirement:** same single model, homogeneous Agents, ≤3 Agents, ≤2 main rounds, deterministic settings, Pilot 40, and cumulative sanity+pilot hard ceiling 0.8M actual/projected tokens.
- **Exact existing location:** CLI bounds are configurable but not enforced; no ceiling guard.
- **Minimal map/disposition:** **EXTEND isolated** preflight/manifest with `validate_pilot_budget` and method/stage summaries; do not change legacy CLI/config.
- **Interface/I-O:** planned/completed ledgers → projection/actual totals and `ALLOW` or `STOP_HUMAN_DECISION`.
- **Cache:** cache hits count as zero generated tokens; original origin usage remains auditable.
- **Lineage/logging:** manifest binds Pilot config and cumulative E0+Pilot token ledger.
- **Deterministic test:** exact boundary and one-token-over tests; no automatic parameter reduction/expansion.
- **Rollback:** remove P1 budget functions, leaving P0 manifest intact.

### P1.4 Baseline adapter declaration (interface only for later E4 execution)

- **Frozen requirement:** reuse official Vanilla MAD and exactly one declared MAD-M² path without reimplementing MAD. No baseline is needed to answer E0 or E1's causal four-arm question.
- **Exact existing location:** `src.reasoning_models.MultiAgentDebate` with `prune_strategy="naive"`, `_subjective_prune`, `_objective_prune`, and `_debate_with_contexts`; construction occurs in `multi_agent_debate.py:main`.
- **Minimal map/disposition:** define thin `state_mad/adapters.py::MadAdapter` protocol only when authorized. **REUSE/WRAP** `MultiAgentDebate`; preserve its official behavior. Adapter translates frozen immutable messages into contexts and captures outputs through the cached backend. Avoid `MultiAgentDebate` modification.
- **Interface/I-O:** frozen Round-1 message pool plus method enum → model-visible contexts/mask metadata and immutable outputs; no general memory abstraction.
- **Cache:** all effective calls still cross `CachedBackend`; frozen Round-1 content is replayed.
- **Lineage/logging:** adapter records method/prune path, visible/masked IDs, and parent messages without treating a mask as deletion.
- **Deterministic test:** fake Agent/context-spy shows Vanilla and selected MAD-M² receive the frozen inputs without mutation.
- **Rollback:** delete adapter; official baseline code is unchanged.
- **Approval note:** before the adapter is implemented, the human approval should name the single Phase-1 MAD-M² variant (`subjective` or `objective`). This does not block P0/E0. If it is not selected before baseline work, that work is held; the implementation must not choose silently.

## 6. P2 — required for E2/E3/E4, staged after preceding gates

These items are mappings only. Do not implement them before E0 PASS, and do not execute them until the applicable Pilot gate/human authorization permits progression.

### P2.1 E2 eligible primary adopters and exact Relay replay

- **Frozen requirement:** select only Target-current-aware paired treatment-only stale adopters whose cached stale/current outputs satisfy one canonical skeleton; independently establish Relay awareness; replay exact Target outputs in matched treatment/control from one Relay snapshot.
- **Existing location:** none; legacy debate contexts neither express eligibility nor exact cached replay.
- **Minimal map/disposition:** **NEW MODULE** `state_mad/e2.py::{select_primary_adopters, run_relay_replay}` reusing P0 cache/snapshot/backend. Canonical output validation extends `grading.py`; no hand editing.
- **Interface/I-O:** saved E1 records/cache + Relay snapshot → eligibility table, exact replay calls, Relay grades.
- **Cache:** E1 upstream is read-only and never regenerated; treatment/control reference exact content hashes. Only Relay calls may miss.
- **Lineage/logging:** Source seed → aware Target → paired adoption → exact Target retransmission → aware Relay → Relay decision, with exclusions.
- **Test:** fixtures reject every denominator failure and prove origin hashes and all held-fixed fields match.
- **Rollback:** delete E2 module/extensions; E1 cache remains intact.

### P2.2 E2 conditional retransmission and false-consensus metrics

- **Frozen requirement:** compute `SRR_cond` (explicitly conditional), paired Relay contrast, Ordinary FSCR, Exposure-Induced FSCR, and Retransmission-Supported FSCR using one post-update `final_vote_phase_id`; pre-update `m_old` is never a vote. Apply Gate 4 and diagnostic sparse label.
- **Existing location:** `src.utils.if_reach_consensus` is generic and uses `>= len/2`; it lacks phase/lineage semantics and is not reused for claims.
- **Minimal map/disposition:** **EXTEND isolated** `metrics.py` and `lineage.py` with frozen three-tier definitions.
- **Interface/I-O:** saved complete E2 structured records → exact numerator/denominator IDs, rates, eligibility, Gate 4 status.
- **Cache:** offline read-only, no calls.
- **Lineage/logging:** complete path required for tier C; same phase required for every vote.
- **Test:** hand-built traces distinguish all three tiers, exclude `m_old`, and cover `<8`, zero second-hop, and diagnostic outcomes.
- **Rollback:** remove P2 E2 metric/path functions.

### P2.3 E3 correction-visible residue and re-infection

- **Frozen requirement:** conditions are source uncorrected, corrected+invisible, and corrected+visible/accessibile. Headline CVRR includes only prior stale adopters after verified source correction, source no longer stale, delivered accessible correction, and later completed decision. Re-infection uses an exact naturally produced residual Target message and matched control; no artificial infection.
- **Existing location:** none.
- **Minimal map/disposition:** **NEW MODULE** `state_mad/e3.py` using proposed `SourceCorrectionSnapshot`, delivery/accessibility events, cache replay, and verification grades; extend offline metrics/lineage.
- **Interface/I-O:** eligible E2/E1 artifacts + three controlled visibility branches → correction verification, residual decisions, optional natural re-infection pair, CVRR/clean comparison and rate.
- **Cache:** correction generated once; visibility-only changes replay it. Natural residual message is exact cached content. No regeneration or fabrication.
- **Lineage/logging:** all five RQ3 prerequisites and temporal order are explicit; conditions A/B never enter headline CVRR_C.
- **Test:** denominator truth table, correction-visible ordering, source-verification failure, exact residual hash, invisible-control exclusion, and natural-trigger requirement.
- **Rollback:** delete E3 module and P2 extensions; retain immutable earlier artifacts.

### P2.4 E4 four-method controlled mitigation

- **Frozen requirement:** exactly Vanilla MAD, one selected MAD-M², Controlled Supersession-Aware Mitigation, and token-matched Sham Metadata; one frozen Round-1 pool reused across methods; minimal oracle supersession metadata; no general memory architecture; Gate 6 evaluates CSAE improvement and clean-accuracy harm.
- **Existing location:** Vanilla is `prune_strategy="naive"`; MAD-M² is `_subjective_prune` or `_objective_prune`. No mitigation/sham exists.
- **Minimal map/disposition:** **WRAP/REUSE** chosen legacy baseline via `MadAdapter`; **NEW MODULE** `state_mad/e4.py` with deterministic context renderer that marks known symbolic active/superseded/conflicting state and a token-matched non-semantic sham. It preserves every raw message and changes only controlled context construction.
- **Interface/I-O:** frozen Round-1 message IDs/content plus method and scenario oracle metadata → method-specific visible context and downstream calls; offline method contrasts.
- **Cache:** Round-1 pool is generated once and immutable across all four methods. Metadata/mask/visibility changes replay upstream content; only effective downstream prompts may generate.
- **Lineage/logging:** method, oracle metadata, sham payload/length, masks, visible IDs, prompt tokens, and common Round-1 origin hashes are recorded.
- **Test:** four-and-only-four enum, byte-identical Round-1 origins, stale history preserved, State-MAD vs sham token-footprint tolerance, no fifth baseline, and Gate 6 fixtures.
- **Rollback:** delete E4 module/renderers and adapter; no MAD core changes or historical deletion.

### P2.5 Complete formal offline analysis

- **Frozen requirement:** all frozen metrics plus paired bootstrap/McNemar/exact/permutation analyses operate on saved records without model calls; operational gates are not significance thresholds.
- **Existing location:** no State-MAD record reader/analysis exists.
- **Minimal map/disposition:** **NEW MODULE** `state_mad/analysis.py` or isolated scripts after data-schema freeze; deterministic seeded resampling and exact tests only.
- **Interface/I-O:** sealed scenarios/calls/lineage → versioned tables/statistics with analysis seed and included IDs.
- **Cache:** read-only integrity validation; never generate.
- **Lineage/logging:** every estimate links to exact unit IDs and eligibility rules.
- **Test:** golden small datasets and fail-on-model-import/call guard.
- **Rollback:** delete offline analysis module; raw run artifacts remain.

## 7. DEFER / do not implement under the next approval

### 7.1 Repository/runtime hardening risks

Defer until specifically needed and approved:

1. Verify authoritative upstream URL/tag/commit and tracked license status.
2. Diagnose or test the legacy `MultiAgentDebate.__call__` `max_round=1` unbound-local defect without coupling E0 to it.
3. Document the objective-mask score-definition issue while preserving official behavior.
4. Lock and document vLLM/CUDA residual nondeterminism; do not claim bitwise determinism beyond cache replay.
5. Add post-run checksum sealing/read-only hardening beyond P0's atomic non-overwrite/checksum validation.
6. Repair unrelated legacy CLI/config/script naming inconsistencies only if original baseline reproduction requires it.

Each item has a rollback boundary confined to documentation or its eventual isolated test/fix. None justifies a pre-E0 core modification.

### 7.2 Execution held behind gates

- Full E1 execution is deferred until E0 PASS and explicit authorization.
- E2/E3/E4 implementation and execution are deferred until E0 PASS and their prerequisites are authorized.
- Full campaign automation before E0 PASS is forbidden.
- If E0 yields zero confirmed stale regressions, stop; do not rescue with more models, scenarios, Agents, rounds, prompts, or architecture.
- If E0 is ambiguous (`0 < CSAE < 0.10`), stop for `需要人工决策`.
- If runtime/model provisioning fails, stop for `需要人工决策`; do not substitute a checkpoint.
- MAD-M² subjective-versus-objective selection must be explicit before baseline-adapter implementation.

### 7.3 Prohibited Phase-1 expansion

Do not add RL, fine-tuning, learned stale detection/classification/routing/scoring, semantic state extraction, dependency/graph memory, StateMem clone, RAG, DAR, LLM-as-a-Judge, extra baseline/model/Agent/round, expanded dataset, reasoning rewrite architecture, or physical deletion of stale raw history. Any apparent need for these is `需要人工决策`, not an implementation task.

## 8. Exact planned relationship to audited existing code

| Existing location                                           | Planned use                                                  | Planned pre-E0 modification |
| ----------------------------------------------------------- | ------------------------------------------------------------ | --------------------------- |
| `src.models.LanguageModel.__init__`                         | REUSE model/vLLM/chat-template loading behind adapter after preflight. | None.                       |
| `src.models.LanguageModel.__call__`                         | WRAP single explicit raw-output calls with `answer_process=False`. | None anticipated.           |
| `src.models.LanguageModel._answer_process`                  | REUSE existing token-ID counting concept/returned batch totals for single-call E0. | None anticipated.           |
| `src.model_utils.TokenUsageTracker`                         | REUSE coarse internal tracking only; State-MAD ledger is authoritative per call. | None.                       |
| `src.reasoning_models.MultiAgentDebate`                     | REUSE/WRAP later for Vanilla/selected MAD-M² baseline only.  | None.                       |
| `MultiAgentDebate._subjective_prune` / `_objective_prune`   | REUSE one explicitly selected official MAD-M² variant later. | None.                       |
| `MultiAgentDebate._initial_round` / `_debate_with_contexts` | Reference official round/context semantics; use later only if adapter preserves frozen inputs. | None.                       |
| `multi_agent_debate.py:main`                                | Original benchmark entry point remains available; not used for E0. | None.                       |
| `src.prompts.py`                                            | Original baseline prompts remain intact.                     | None.                       |
| `src.utils.py` / `src.evaluator.py`                         | Original benchmark grading/reproduction only; not State-MAD grading/metrics. | None.                       |
| `configs.yaml` / processed data / scripts                   | Legacy baseline assets remain intact.                        | None.                       |

Any proposed edit to the rightmost column must trigger a map amendment and human approval before the edit. A wrapper-first proof of insufficiency is mandatory for `src/models.py`; modification of `src/reasoning_models.py` is not authorized by this map.

## 9. Implementation sequence after explicit approval

Approval of this map should authorize **P0 only** unless the human explicitly says otherwise:

1. Add immutable schemas/canonical hashing.
2. Add compiler, independent counterbalancing, validator, and pure prompt renderers.
3. Add snapshots and prove non-mutation/probe isolation.
4. Add cache, fake backend, deterministic grader, lineage, and run store.
5. Add token adapter, manifest, bounds, and preflight.
6. Add offline E0 metrics/gate evaluator.
7. Add bounded E0 runner wired first to the fake backend.
8. Run smallest unit tests and deterministic no-model dry run; inspect diff and requirement traceability.
9. Only after dry-run success and runtime/model preflight, request/confirm permission for E0 inference if not already explicit.
10. Run E0 only, evaluate Gate 1 offline, and stop for human/frozen gate evaluation.

No step may silently expand to P1/P2. A narrow `src/models.py` extension, if proven necessary, is a separate approval point.

## 10. Approval decisions and current readiness

No frozen RQ, contribution boundary, resource limit, metric, or condition needs reopening for the mapped P0 design. The Repository Audit has a PASS-type verdict, and the wrapper/isolated-module design avoids invasive changes. Current missing packages/GPU/checkpoint are execution risks handled by fail-closed preflight, not a reason to alter the research design.

Human approval should state:

1. whether P0 implementation may begin under this map; and
2. optionally, which single MAD-M² variant will be used later (`subjective` or `objective`). Variant selection may remain pending without blocking P0/E0 infrastructure.

**READY FOR HUMAN IMPLEMENTATION APPROVAL**
