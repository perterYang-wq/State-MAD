# State-MAD Stage 04 — Repository Audit

**Status:** COMPLETE  
**Stage:** 04 — Repository Audit  
**Audit date:** 2026-09-07 (UTC)  
**Authority:** `research/RESEARCH_CONTRACT.md` > `research/EXPERIMENT_PLAN_FROZEN.md` > `research/IMPLEMENTATION_REQUIREMENTS.md` > `research/03_EXPERIMENT_PLAN_REVIEW.md`

## 1. Scope and method

This is an inspection-only audit of the repository as found. No implementation source, configuration, prompt, dataset, or experiment logic was changed. The audit maps the frozen requirements to existing MAD-M² code and identifies the minimum E0 gaps; it is not an Implementation Map and does not authorize implementation.

Inspected artifacts include the four authoritative research documents, the Git metadata, entry points, model wrapper, debate implementation, prompts, evaluators, utilities, configuration, datasets, requirements, and launch scripts. Static inspection was used; no model inference was attempted.

### Classification vocabulary

- **P0:** required for the minimal deterministic dry run and/or E0 validity; E0 must not run without it.
- **P1:** required after E0 PASS for a frozen pilot requirement, but not required to answer E0's three questions.
- **P2:** desirable hardening or reproducibility improvement that does not block E0.
- **DEFER:** explicitly outside the pre-E0 boundary, conditional on naturally eligible cases, or prohibited in Phase 1.
- **REUSE:** use existing behavior unchanged.
- **WRAP:** call existing code through a thin adapter without changing its core.
- **EXTEND:** make a small, localized addition to existing behavior only if a wrapper cannot suffice.
- **NEW MODULE:** isolated State-MAD-specific code is the least invasive option.
- **AVOID MODIFYING:** changing this code is unnecessary or scientifically risky.

## 2. Repository identity and integrity

| Item                | Audited value                                                | Assessment                                                   |
| ------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Working tree        | `/workspace/State-MAD`                                       | Repository is accessible.                                    |
| Branch              | `work`                                                       | Active branch identified.                                    |
| HEAD                | `84b13a9a7da5d2c9c435296f15d5d4911d69dc10`                   | Single inspected snapshot identifier.                        |
| HEAD subject        | `Add files via upload`                                       | Provides little upstream provenance.                         |
| Remote              | none configured                                              | Exact relationship to the official upstream cannot be mechanically verified from Git metadata. |
| Repository claim    | README identifies “Multi-Agent Debate with Memory Masking,” the MAD-M² ICLR 2026 code | Content is consistent with a MAD-M² research release, but this audit cannot certify upstream identity. |
| Initial dirty state | clean (`git status --short --branch` showed only `## work`)  | No pre-existing user modifications observed.                 |
| License file        | none in tracked file list                                    | README displays an MIT badge, but no tracked license text was found; provenance/reuse risk, not an E0 engineering blocker. |

**Identity conclusion:** treat this as the supplied MAD-M² snapshot, not as a cryptographically verified checkout of an official remote. Before paper-facing release, record or restore an authoritative upstream URL/tag/commit and license information. This is a **P2 repository-provenance risk**; it does not prevent an isolated E0 wrapper.

## 3. Current entry point and exact call graph

### 3.1 `multi_agent_debate.py`

The executable path is:

```text
multi_agent_debate.py:main
  ├─ src.args.parse_args
  ├─ src.config_utils.load_configs_from_yaml("configs.yaml")
  ├─ src.config_utils.LLMConfig(general, selected-model)
  ├─ select processed_data/<dataset>/<dataset>_test.jsonl
  ├─ construct one dataset-specific src.evaluator.*Eval
  ├─ functools.partial(src.utils.extract_answers, dataset_name=...)
  ├─ src.models.LanguageModel
  │    └─ vllm.LLM
  ├─ src.reasoning_models.MultiAgentDebate
  └─ BaseEvaluator.eval(mad, args)
       ├─ MultiAgentDebate.__call__(evaluator.data)
       │    ├─ preprocess_data
       │    ├─ _initial_round
       │    │    ├─ prompts_with_format(..., "cot")
       │    │    ├─ get_response_from_agent → LanguageModel.__call__
       │    │    └─ if_reach_consensus
       │    ├─ for later rounds (range(1, max_round))
       │    │    ├─ _subjective_prune | _objective_prune | naive pass-through
       │    │    └─ _debate_with_contexts
       │    │         ├─ prompts_with_format(..., "debate")
       │    │         ├─ get_response_from_agent → LanguageModel.__call__
       │    │         └─ if_reach_consensus
       │    └─ assemble final_results
       ├─ dataset-specific calculate_score
       ├─ MultiAgentDebate.get_summary
       ├─ MultiAgentDebate.save_debate_log
       └─ BaseEvaluator.save_results
```

The entry point hard-codes the existing benchmark family and chooses 100 samples for MATH/GSM8K/MMLU-Pro and full AIME datasets. It has no State-MAD scenario input, E0 mode, resume/cache mode, or structured run manifest. Therefore it should be **AVOID MODIFYING for E0** and retained as the official baseline launcher; a separate thin E0 entry point is safer.

### 3.2 Important execution defect

`MultiAgentDebate.__call__` assigns `common_answers` and `consensus_flags` only inside the later-round loop but consumes them after that loop. Thus `max_round=1` produces unbound locals. The frozen E0 calls for one exposure round but need not equate that with this class's round counter: an isolated branch runner should bypass this defect rather than changing the legacy core. If the legacy class is reused directly, this becomes P0. Under the recommended wrapper design it is a **P2 legacy risk**.

## 4. Existing MAD debate loop

### 4.1 Data shape and batching

`preprocess_data` reduces each item to `id`, `query`, and `answer`. `_initial_round` formats every question once and invokes the same `LanguageModel` object `num_agents` times over the complete batch. Responses are transposed into per-scenario contexts. A later round uses only the immediately preceding response set (`history[-1]`), not the full accumulated trajectory, to construct the next prompt.

The implementation represents homogeneous Agents as repeated calls to one shared model wrapper; there are no persistent Agent objects, Agent-local stores, stable author IDs, or per-Agent conversation histories. This is compatible with the frozen homogeneous-model constraint but insufficient for State-MAD identity, visibility, snapshots, and lineage without a wrapper.

### 4.2 Vanilla MAD

`prune_strategy="naive"` passes the prior response list directly to the next round. This is the official repository's Vanilla MAD path and is a strong **REUSE/WRAP** candidate. Note that its mask log is hard-coded as three `True` values, regardless of `num_agents`; E0 should not depend on this mask record.

### 4.3 Consensus behavior

`if_reach_consensus` normalizes answers by dataset and selects the most frequent value. Its threshold uses `count >= len(answers) / 2`, which labels a two-way tie among two Agents as consensus. It also relies on first-insertion order to break frequency ties. That behavior is unsuitable for frozen State-MAD consensus and deterministic categorical grading. **AVOID MODIFYING** it for E0; use a separate mechanical grader/metric layer. Full three-Agent post-update FSCR belongs after E0 PASS.

## 5. MAD-M² masking and evaluation pipeline

### 5.1 Subjective masking

`MultiAgentDebate._subjective_prune` constructs one `PRUNE_PROMPT` per prior response, asks the same LLM to emit `YES`, `NO`, or `NOT SURE`, and retains `YES`; `NOT SURE` is retained unless strict mode is enabled. This is model-based erroneous-memory evaluation, not benchmark-oracle supersession awareness. It creates extra model calls and does not expose per-call token records in the debate log.

### 5.2 Objective masking

`MultiAgentDebate._objective_prune` sorts per-response perplexities, selects a median threshold, and retains responses whose `ppl > threshold`. The implementation's `LanguageModel` computes `math.exp(mean(logprob))`, which is geometric mean probability rather than conventional perplexity (`exp(-mean(logprob))`). Consequently the variable is misnamed; nevertheless the objective baseline must preserve the official behavior for faithful reproduction rather than silently correcting it during State-MAD work.

For three Agents, strict `>` relative to the median generally retains only the largest stored value; ties can retain fewer or none. Masks are positional booleans only and carry no message identifiers or validity metadata.

### 5.3 Baseline mapping

- **Vanilla MAD:** `MultiAgentDebate(..., prune_strategy="naive")` — **REUSE through WRAP**.
- **MAD-M² subjective:** `prune_strategy="subjective"`, optional `strict` — official learned/model-visible masking path, **REUSE through WRAP after E0 PASS**.
- **MAD-M² objective:** `prune_strategy="objective"` — official score-based masking path, **REUSE through WRAP after E0 PASS**.
- The frozen plan names one MAD-M² baseline but the repository exposes two variants. Selecting the exact variant is a Stage-05 Implementation Map decision; do not silently combine or add both as extra methods. The most direct official path must be declared before Pilot.

The E4 four-method matrix, including State-MAD and sham, is **DEFER until E0 PASS**.

## 6. Message representation and history semantics

Current messages are mostly untyped Python values:

- model input: one flattened prompt string per call;
- vLLM chat wrapper: transient `[{'role': 'system'|'user', 'content': ...}]` built inside `LanguageModel.__call__`;
- parsed response: `{'think': ..., 'answer': ...}`;
- debate context: lists of parsed response dictionaries, stringified into prompt text;
- debate log: per-question rounds containing prompt, parsed response, and score.

There is no `message_id`, author, recipient, parent IDs, fact/version link, creation/decision validity, immutable raw byte/text object, or final decision phase. Contexts are ordinary mutable lists and dicts. Shallow list construction does not establish immutable snapshot semantics, and there is no fork API. Raw LLM text is not reliably preserved: successful parsing retains extracted `think`/`answer`, while the original complete response is discarded as a distinct field. Historical round records are saved, but they do not meet append-only raw trajectory or lineage requirements.

**P0:** introduce isolated immutable value objects/serialized records for snapshots and messages, retaining raw output exactly and recording content hashes/parents. **Do not retrofit Agent memory into the core MAD class.**

## 7. Prompt construction

`src.prompts` defines three global templates: CoT, debate, and prune. `prompts_with_format` concatenates question and context into a single user prompt, appends a fixed XML-like response instruction, and stringifies each response dict. The model wrapper optionally adds a system message and then applies the backend tokenizer's chat template.

Positive reuse:

- the separation between prompt formatting and `LanguageModel` calls can inform a thin backend adapter;
- deterministic strings can be hashed before generation;
- the existing vLLM chat-template path supports Qwen Instruct formatting.

Gaps:

- no current-awareness probe or distinct no-peer decision prompt;
- no categorical State-MAD scenario renderer;
- no canonical one-field answer skeleton suitable for exact E2 matching;
- no stale/static-wrong style-matched renderer;
- no explicit visibility/ordering/identity/validity metadata controls;
- no prompt/template hash;
- joining dict string representations couples prompts to Python representation rather than an explicit stable schema.

**P0 NEW MODULE:** deterministic E0 prompt renderers with separate awareness and ordinary-decision tasks, a canonical closed-pool answer format, and stable hashing. **AVOID MODIFYING** the general MAD prompt templates before E0.

## 8. Dataset and grading pipeline

### 8.1 Existing datasets

Tracked processed JSONL files cover AIME 2024/2025, GSM8K, MATH, and MMLU-Pro. They are static math/knowledge benchmark records, not authoritative temporal supersession scenarios. `BaseEvaluator.load_data` reads all JSONL records and optionally samples with NumPy. Dataset-specific evaluators grade numerical, symbolic, or option-letter answers.

### 8.2 Existing grading

The parsing path is tailored to those benchmark formats. It can fall back from the requested XML structure to boxed-answer extraction and may retain free-form text. It does not map answers to `CURRENT`, `STALE`, `STATIC_WRONG`, or `OTHER/INVALID`. Existing evaluators calculate ordinary benchmark accuracy and dispatch behavior by exact pipeline class name.

### 8.3 Required mapping

- Existing JSONL reading/writing patterns: **REUSE as implementation reference**, not as an E0 schema.
- Existing benchmark datasets/evaluators: **AVOID MODIFYING**; they remain baseline artifacts.
- Symbolic categorical scenario compiler and schema: **P0 NEW MODULE**.
- Mechanical validator including temporal invariants, one-to-one answers, event DAG, post-update phase, and E0 visibility: **P0 NEW MODULE**.
- Cyclic role and independently rotated option-position counterbalancing plus pre-call balance report: **P0 NEW MODULE**.
- Strict deterministic answer parser/classifier in which malformed outputs become `OTHER/INVALID`: **P0 NEW MODULE**.
- Frozen metrics: for E0, current awareness, treatment-only regressions, SAR/CSAE/current accuracy/token totals are **P0**; SRR_cond, three FSCR tiers, CVRR, and re-infection are **P1/DEFER until E0 PASS**.

No LLM judge or semantic parser is needed or permitted.

## 9. Cache and replay capabilities

The repository has **no model-output cache**. `LanguageModel.__call__` always invokes `self.llm.generate`; no key is computed, and no lookup, hit/miss, invalid state, or collision/integrity check exists. Saved result/debate JSON is terminal logging rather than an executable replay store. There is no mechanism to return exact cached upstream messages to sibling/downstream branches.

**P0 NEW MODULE:** a content-addressed, immutable message cache keyed by the frozen effective-input fields (scenario, phase/condition, role, snapshot, prompt, visible message content, model/revisions, decoding config, seed, and maximum output length). An existing valid key must return exact raw output; it must never silently regenerate. Cache status must distinguish miss, hit, and invalid/corrupt. E0 needs this to validate same-snapshot branching and replay even though E2/E3 are deferred.

The model wrapper should be **WRAPPED**, not used as the cache itself. All calls must pass through the cache boundary.

## 10. Logging and raw trajectory preservation

Existing strengths:

- per-question/per-round prompts, parsed responses, stored score-like values, consensus, and masks are written to JSON;
- final results include debate history, masks, and score history;
- aggregate token totals and coarse call history are saved.

Frozen-contract gaps:

- raw output is not a separately preserved immutable field;
- no run/scenario/experiment/condition/pair/message/fact/version/phase identifiers in call records;
- no author/recipient/parent lineage;
- no generation-time vs decision-time validity;
- no awareness/correction/visibility/accessibility/eligibility/exclusion flags;
- no prompt, snapshot, config, scenario-set, or template hashes;
- no model revision or tokenizer revision;
- no cache status;
- no repository/runtime/hardware/command manifest;
- logs are overwritten at predictable file paths rather than protected append-only records.

**P0 NEW MODULE:** E0 call/lineage records and an atomic run directory preserving immutable raw outputs, hashes, exact inputs, classification, cache state, and per-call tokens. **P1:** correction and full E1–E4 lineage fields may be present as explicit null/not-applicable fields pre-E0 but their execution logic is deferred. **P2:** checksums/read-only sealing and richer platform inventory.

## 11. Seed and determinism audit

The CLI accepts `--seed`, but the seed currently affects only NumPy dataset subsampling in `BaseEvaluator.load_data`. It is not passed to `SamplingParams`, and Python `random`, NumPy globally outside sampling, PyTorch, CUDA, or vLLM are not comprehensively seeded. The config defaults to `temperature: 1`; Qwen2.5-7B-Instruct inherits that value. `SamplingParams` receives temperature/top-p/max tokens but no seed. Model/tokenizer revision is unpinned. vLLM/GPU kernels may introduce additional nondeterminism.

The initial Agent repetitions also use identical prompt batches without explicit stable per-call seeds. Agent identity is absent, so repeated stochastic calls cannot be replayed/reconstructed by role.

**P0:** E0 configuration must explicitly use `temperature=0`, a fixed seed policy passed through the backend where supported, stable ordering, and recorded effective settings. Cache reuse is the hard reproducibility boundary. **P0:** record backend/model/tokenizer revision and warn if exact revisions cannot be resolved. **P2:** document backend-specific residual nondeterminism rather than claiming bitwise determinism.

Do not alter `configs.yaml` during Stage 04. Stage 05 should prefer a State-MAD-specific config/adapter rather than changing legacy baseline defaults.

## 12. Token accounting

`LanguageModel._answer_process` counts prompt token IDs and generated token IDs accurately at batch aggregate level and `TokenUsageTracker` records input/output/total values per `LanguageModel.__call__`. This is useful and is a **REUSE/WRAP** candidate.

It is insufficient because:

- a batch call yields one aggregate usage record rather than per scenario/Agent/message;
- returned results expose only batch totals;
- cache hits do not exist and cannot be distinguished from generations;
- masking calls are mixed into the same aggregate history without phase/method labels;
- no per-stage/scenario/method summaries or hard-ceiling guard exists.

**P0 EXTEND VIA WRAPPER:** derive per-output token counts directly from backend outputs (or tokenize exact prompt/raw response consistently), attach them to call records, record cache-hit zero-generation behavior separately, and aggregate offline. **P1:** hard planning-ceiling guard and full pilot method summaries.

## 13. Model and backend compatibility

### 13.1 Declared compatibility

The repository declares `vllm==0.6.3`, `transformers==4.46.2`, `torch`, and Qwen2.5-7B-Instruct in `configs.yaml`. `LanguageModel` uses vLLM's `LLM`, chat template, bfloat16, tensor parallelism, and a configurable model path. Architecturally, this is compatible with the frozen default open 7B model on suitable CUDA hardware.

### 13.2 Current environment

At audit time Python is 3.14.4; `torch`, `transformers`, `vllm`, `PyYAML`, and `numpy` are not installed, no CUDA device can be queried through PyTorch, and no cached Qwen/7B model directory was found in the inspected standard locations. No model inference or import-level execution can therefore run in this environment as found. vLLM 0.6.3 and the pinned 2024-era stack may also be incompatible with Python 3.14, so a supported isolated runtime is likely required.

There are configuration-name inconsistencies: CLI default is `qwen-2.5-7b`, while `configs.yaml` defines `qwen2.5-7b`; the README/scripts use `qwen2.5-7b`. The provided `run_all_mad_mm_variants.sh` requests 14B/32B/72B keys absent from the shown config. These are legacy launch risks, not reasons to expand State-MAD beyond one 7B model.

**Assessment:** backend code can support Qwen2.5-7B-Instruct, but the current container cannot execute it without environment/model provisioning. This is an explicit **minor repository/runtime risk**, not evidence that the codebase is structurally incapable. Stage 05 must specify a preflight check and pin exact model/tokenizer revisions. If the 7B checkpoint or compatible GPU runtime cannot be provisioned, stop with `需要人工决策`; do not substitute another model automatically.

## 14. Frozen requirement-to-code map

| Frozen capability               | Existing file/function                                       | Current status                         | Priority                          | Minimal disposition                        |
| ------------------------------- | ------------------------------------------------------------ | -------------------------------------- | --------------------------------- | ------------------------------------------ |
| Official baseline entry         | `multi_agent_debate.py:main`                                 | Present, benchmark-specific            | P1                                | REUSE for baseline; AVOID MODIFYING for E0 |
| Homogeneous model Agents        | `MultiAgentDebate.__init__`, `_initial_round`, `_debate_with_contexts` | Present as repeated shared-model calls | P0 support                        | WRAP backend calls                         |
| ≤2 rounds / ≤3 Agents           | CLI args and `MultiAgentDebate` loop                         | Configurable, not frozen-enforced      | P0                                | Enforce in isolated E0 runner              |
| Vanilla MAD                     | `prune_strategy="naive"`                                     | Present                                | P1                                | REUSE/WRAP                                 |
| MAD-M² subjective               | `_subjective_prune`; `PRUNE_PROMPT`                          | Present                                | P1                                | REUSE/WRAP after selecting variant         |
| MAD-M² objective                | `_objective_prune`; model logprobs                           | Present with noted score naming issue  | P1                                | REUSE/WRAP; preserve official behavior     |
| Scenario compiler               | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| Scenario validator              | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| Value/position counterbalance   | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| Current-awareness probe         | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| Distinct no-peer decision       | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| E1 four arms                    | none                                                         | Missing                                | P0 for minimal E0 subset; P1 full | NEW MODULE runner                          |
| Immutable snapshots/forks       | none; mutable `history` lists only                           | Missing                                | P0                                | NEW MODULE                                 |
| Immutable cache/exact replay    | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| Closed-pool parser/grader       | dataset-specific `extract_answers`/evaluators                | Not suitable                           | P0                                | NEW MODULE; AVOID MODIFYING old graders    |
| Stable message skeleton         | generic XML reasoning output only                            | Missing                                | P0                                | NEW MODULE renderer                        |
| Message lineage                 | round-only nested log                                        | Missing                                | P0                                | NEW MODULE                                 |
| Raw immutable trajectories      | parsed nested log                                            | Partial/insufficient                   | P0                                | NEW MODULE run store                       |
| Per-call token logging          | `LanguageModel._answer_process`, `TokenUsageTracker`         | Batch aggregate only                   | P0                                | WRAP/locally EXTEND adapter                |
| Seeded deterministic decode     | CLI seed; NumPy sampling only                                | Insufficient                           | P0                                | WRAP backend with effective seed/config    |
| Model/backend                   | `LanguageModel`; vLLM config                                 | Code path exists; runtime absent       | P0 preflight                      | REUSE/WRAP, provision externally           |
| E0 runner (16 scenarios)        | none                                                         | Missing                                | P0                                | NEW MODULE                                 |
| E0 metrics/gates                | none                                                         | Missing                                | P0                                | NEW MODULE/offline computation             |
| Full metric engine              | ordinary accuracy/consensus only                             | Missing                                | P1                                | NEW MODULE after E0 PASS                   |
| E2 matched replay/SRR_cond      | none                                                         | Missing                                | P1, execution DEFER               | Plan only after E0 PASS                    |
| FSCR tiers/final phase          | generic consensus only                                       | Missing                                | P1, execution DEFER               | Isolated metric/lineage logic later        |
| E3 correction/CVRR/re-infection | none                                                         | Missing                                | P1, execution DEFER               | Do not implement pre-E0                    |
| State-MAD mitigation/sham       | none                                                         | Missing                                | P1, execution DEFER               | Do not implement pre-E0                    |
| Reproducibility manifest        | coarse saved summary only                                    | Missing                                | P0 minimal, P1 complete           | NEW MODULE                                 |
| Offline analysis                | no State-MAD record reader                                   | Missing                                | P0 E0 summary, P1 full            | NEW MODULE; never call model               |

## 15. Gap register

### P0 — blocks deterministic dry run or E0

1. Direct categorical scenario compiler for exactly the frozen E0 scale, with deterministic IDs, versions, supersession, event order, answer pool, visibility, and final phase.
2. Mechanical validator and counterbalance report before calls.
3. Separate awareness and ordinary decision prompts plus style-matched current/stale/static-wrong message skeletons.
4. Immutable snapshot/fork representation proving probe and sibling non-mutation.
5. Exact-output message cache with complete effective-input key and fail-closed reuse semantics.
6. Deterministic categorical parser/grader and minimal E0 metrics/gate evaluator.
7. Structured raw call/message/lineage log, hashes, per-call tokens, and minimal run manifest.
8. Minimal E0 runner restricted to 16 scenarios, at most two Agents, one exposure round, one open 7B model, and the three E0 questions.
9. Deterministic decoding/seed policy and resource-bound validation.
10. Runtime/model preflight; the current environment cannot import or run the declared backend.

### P1 — required only after E0 PASS for Pilot

1. Full four-arm E1 orchestration and paired offline metric engine.
2. Declared adapter for exactly one official MAD-M² variant, plus Vanilla reuse.
3. E2 canonical-output eligibility, relay snapshots, exact paired replay, SRR_cond, and FSCR tiers.
4. E3 source correction verification, visible/invisible controls, clean reference, CVRR, and naturally triggered re-infection.
5. E4 frozen Round-1 pool, Controlled Supersession-Aware Mitigation, token-matched sham, and exactly four methods.
6. Complete reproducibility manifest and 0.8M-token guard/aggregations.

These must not be implemented as an end-to-end campaign before E0 PASS.

### P2 — hardening / repository risks

1. Establish authoritative upstream remote/tag/commit and tracked license.
2. Document or test the legacy `max_round=1` unbound-local defect without coupling E0 to it.
3. Record the objective-mask score-definition issue while preserving official baseline behavior.
4. Record residual vLLM/CUDA nondeterminism and environment lock information.
5. Prevent accidental overwrite/tampering of completed run artifacts with checksums or sealing.
6. Resolve unrelated legacy config/script name mismatches only if baseline reproduction requires them; do not broaden this project.

### DEFER / prohibited

- Full E1–E4 campaign execution before E0 PASS.
- E2/E3/E4 implementation beyond interfaces needed to avoid foreclosing the frozen design.
- Any RL, fine-tuning, learned stale detector/router, semantic parser, graph/dependency memory, RAG/DAR/StateMem clone, LLM judge, model sweep, extra baseline, extra Agent, extra round, or dataset expansion.
- Any modification of the four frozen research artifacts.
- Any redesign of MAD or physical deletion of stale raw history.

## 16. Recommended reuse boundary for Stage 05

### REUSE unchanged

- `LanguageModel`'s vLLM loading/chat-template/generation mechanics where the runtime is compatible.
- The official `MultiAgentDebate` paths as baseline reference/execution paths after E0.
- Existing processed benchmarks and evaluators for original-paper reproduction only.
- Existing JSON serialization idioms and token-ID accounting concepts.

### WRAP

- Put a backend protocol around `LanguageModel` so effective prompts/config/seeds are explicit and cache-controlled.
- Put thin baseline adapters around Vanilla and the selected MAD-M² variant; translate immutable State-MAD messages to their context input without rewriting core debate logic.
- Capture per-output raw text/token counts before legacy parsing discards information.

### EXTEND only if unavoidable

- A narrow `LanguageModel` return/API extension may expose raw output, per-output tokens, resolved revisions, and explicit seed. Prefer composition in the wrapper first.
- Avoid changing `MultiAgentDebate`; if a Pilot adapter cannot preserve exact frozen Round-1 inputs through public methods, expose the smallest possible hook and document why composition failed.

### NEW MODULE

Use an isolated State-MAD package/area for scenario schema/compiler/validator, immutable records and snapshots, prompt renderer, cache, deterministic grader, lineage/run store, E0 runner, offline E0 metrics, and reproducibility manifest. Exact filenames and APIs belong in Stage 05, not this audit.

### AVOID MODIFYING

- Frozen research documents.
- `src/reasoning_models.py` debate/pruning algorithms unless a later approved map proves a wrapper impossible.
- `src/prompts.py` generic baseline templates.
- `src/evaluator.py` and `src/utils.py` legacy benchmark graders/consensus.
- `configs.yaml`, existing datasets, scripts, and original entry points for the pre-E0 implementation.

## 17. Feasibility and risks

The repository supplies the essential reusable engineering core: a homogeneous open-model vLLM backend, a two-round/three-Agent MAD loop, Vanilla context reuse, both official MAD-M² masking variants, prompt construction, raw token-ID access, and JSON result persistence. The frozen E0 does not require a new memory architecture or invasive core edits. Its missing experimental-control layer is compact and can be isolated around the existing backend.

The principal risks are:

1. no immutable cache/snapshot/lineage infrastructure exists, so scientific integrity depends on building and testing that layer before inference;
2. parsed legacy logs do not preserve full raw outputs or per-message provenance;
3. the current runtime lacks dependencies, GPU verification, and the model checkpoint;
4. the Git snapshot lacks an upstream remote and license file, so “official” identity is claimed rather than independently verifiable;
5. the official MAD-M² variant for the single frozen baseline must be selected explicitly in Stage 05.

None requires changing RQ1–RQ4, exceeding the resource envelope, or reimplementing MAD. If runtime/model provisioning fails, execution must stop for human decision, but the repository structure itself supports the frozen plan through thin wrappers and isolated modules.

## 18. Stage boundary

This audit authorizes only the next gate: creation and approval of `research/05_IMPLEMENTATION_MAP.md`. It does **not** authorize code, config, prompt, dataset, or experiment changes, a dry run, E0 inference, or Pilot work.

**PASS WITH MINOR REPOSITORY RISKS — READY FOR IMPLEMENTATION MAP**