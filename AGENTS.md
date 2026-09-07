# State-MAD — Codex Project Instructions

## 1. Project Purpose

This repository studies:

Stale-State Propagation in Multi-Agent Systems

The engineering base is the official MAD-M² repository.

The primary scientific contribution is phenomenon characterization
and controlled measurement, not a new general-purpose memory architecture.

The secondary contribution is a minimal controlled
supersession-aware mitigation.

Do not redefine the research problem during implementation.

---

## 2. Research Authority

Before planning or modifying code, read these files in this order:

1. `research/RESEARCH_CONTRACT.md`
2. `research/EXPERIMENT_PLAN_FROZEN.md`
3. `research/IMPLEMENTATION_REQUIREMENTS.md`
4. `research/03_EXPERIMENT_PLAN_REVIEW.md`

Lower-authority archival files:

- `research/02_EXPERIMENT_PLAN_DRAFT.md`
- `research/01_ARS_NOVELTY_REVIEW.md`

If files conflict, higher-authority files win.

ARIS skills, reviewer suggestions, implementation convenience,
and existing repository behavior are subordinate to the frozen
Research Contract.

Do not change RQ1-RQ4 without explicit human approval.

---

## 3. Mandatory Stage Gates

The required workflow is:

Stage 04:
Repository Audit

then

Stage 05:
Implementation Map

then

explicit human approval

then

minimal implementation

then

minimal dry run

then

E0 Sanity Test

then

human / frozen gate evaluation

then, only if authorized,

Pilot E1+.

### Before code modification

If `research/04_REPOSITORY_AUDIT.md` does not exist with a
PASS-type verdict:

- inspect only;
- do not modify experiment/source code.

If `research/05_IMPLEMENTATION_MAP.md` does not exist:

- do not begin implementation.

Even if both files exist, implementation requires explicit
human approval.

Do not skip directly from the frozen experiment plan to coding.

---

## 4. Frozen Scientific Definitions

### Erroneous memory

Wrong at creation.

### Stale / superseded memory

Correct at creation, but invalid after a later authoritative
state update.

Do not merge these two failure modes.

### Propagation

Propagation requires:

current-aware target
+
stale peer exposure
+
matched control
+
peer-induced stale adoption.

An Agent that simply missed the current update is not evidence
of State-MAD propagation.

### RQ3 residue

Residual stale belief requires:

source corrected
+
correction delivered
+
correction accessible to the target
+
measurement afterward.

Correction-invisible persistence does not support RQ3.

---

## 5. Frozen Contribution Boundary

Primary contribution:

- causal stale adoption;
- conditional secondary retransmission;
- false stale consensus characterization;
- correction-visible residual stale belief;
- possible re-infection;
- controlled measurement.

Secondary contribution:

- Controlled Supersession-Aware Mitigation.

Do NOT claim as novel:

- state identity;
- version;
- provenance;
- supersession;
- active/stale/conflicting labels;
- state-aware retrieval itself.

Do not build a new general memory architecture.

---

## 6. Resource Constraints

Phase 1 is frozen to:

- one open 7B/8B model;
- homogeneous Agents;
- no more than 3 Agents;
- no more than 2 main debate rounds;
- E0 = 16 scenarios;
- Pilot = 40 scenarios;
- deterministic or near-deterministic decoding;
- deterministic grading;
- total sanity + pilot planning ceiling = 0.8M tokens.

Do not automatically increase any of these limits.

Any expansion requires:

`需要人工决策`

---

## 7. Forbidden Phase-1 Expansion

Do not add:

- reinforcement learning;
- fine-tuning;
- learned stale detector;
- semantic stale classifier;
- learned router;
- dependency graph;
- StateMem clone;
- general natural-language state parser;
- LLM-as-a-Judge;
- RAG baseline;
- DAR baseline;
- graph memory;
- extra model sweep;
- extra Agent;
- extra main debate round;
- large dataset;
- new baseline.

A reviewer or ARIS skill recommendation does not override
this prohibition.

---

## 8. Implementation Principle

Reuse MAD-M².

Prefer, in order:

1. existing code unchanged;
2. thin wrapper;
3. small extension;
4. isolated new module;
5. core modification only when unavoidable.

Do not reimplement the MAD framework.

Any proposed invasive core modification must explain why
a wrapper or adapter cannot satisfy the frozen requirements.

---

## 9. State-MAD Data Requirements

Phase 1 uses direct categorical factual supersession only.

The implementation must support deterministic:

- `scenario_id`;
- `fact_id`;
- `version_id`;
- `v_old`;
- `v_new`;
- `v_wrong`;
- supersession relation;
- event order;
- answer pool;
- Agent visibility;
- message lineage;
- final decision phase.

No semantic state extraction is required.

---

## 10. Snapshot and Branch Integrity

Awareness probe and experimental conditions must branch from
the same immutable pre-exposure snapshot.

Awareness-probe output must never be written back into
treatment/control history.

Required E1 branches:

- no-peer;
- current-peer;
- stale-peer;
- static-wrong.

Do not mutate a parent snapshot while evaluating a sibling
branch.

---

## 11. Cache and Replay Integrity

Generate upstream messages once.

Replay exact cached messages downstream whenever only
visibility, ordering, metadata, masking, identity labeling,
or correction visibility changes.

Identical effective generation inputs and generation parameters
must reuse the same cache key.

Silent regeneration under an identical cache key is an
experimental-integrity failure.

Preserve raw messages.

Do not physically delete stale historical messages merely
because they are superseded.

---

## 12. Deterministic Evaluation

No LLM-as-a-Judge.

Map structured outputs mechanically to:

- CURRENT
- STALE
- STATIC_WRONG
- OTHER/INVALID

Metrics must be reproducible from structured records without
manual semantic interpretation.

Required metrics include:

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

---

## 13. Logging and Reproducibility

Record at minimum:

- run_id;
- scenario_id;
- experiment;
- condition;
- pair_id;
- message_id;
- author;
- recipient;
- parent_message_ids;
- fact_id;
- version_id;
- generation-time validity;
- decision-time validity;
- current-awareness status;
- source-correction status;
- correction visibility/accessibility;
- prompt hash;
- snapshot hash;
- model/revision;
- tokenizer revision;
- seed;
- config;
- raw output;
- parsed output;
- answer class;
- input/output/total tokens;
- cache hit/miss;
- eligibility/exclusion reason.

Every propagation/retransmission/residue claim must be
mechanically reconstructable from lineage.

---

## 14. E0 Boundary

Before E0 PASS, implementation scope is limited to
the minimum infrastructure needed for:

- scenario compiler;
- scenario validator;
- value counterbalancing;
- immutable branch/snapshot behavior;
- message cache;
- deterministic grader;
- lineage logging;
- token logging;
- minimal E0 runner.

Do not implement a complete E1-E4 experiment campaign before
E0 passes.

E0 tests only:

1. whether the model can use `v_new`;
2. whether the current-awareness gate works;
3. whether stale-peer exposure produces non-zero regression.

If E0 produces zero confirmed stale regressions:

STOP.

Do not rescue the result by adding models, scenarios, Agents,
rounds, or a new architecture.

---

## 15. Research Artifact Protection

The following files are frozen and read-only unless the user
explicitly reopens them:

- `research/RESEARCH_CONTRACT.md`
- `research/EXPERIMENT_PLAN_FROZEN.md`
- `research/IMPLEMENTATION_REQUIREMENTS.md`
- `research/03_EXPERIMENT_PLAN_REVIEW.md`

Do not silently edit these files to make implementation easier.

Stage-specific new artifacts such as:

- `research/04_REPOSITORY_AUDIT.md`
- `research/05_IMPLEMENTATION_MAP.md`

may be created only during their corresponding stages.

---

## 16. ARIS Skill Policy

ARIS skills are subordinate to this AGENTS.md and the frozen
research artifacts.

Recommended implementation/experiment skills:

- experiment-audit
- run-experiment
- monitor-experiment
- analyze-results
- result-to-claim
- system-profile

Optional review/debug skills:

- research-review
- web-debug-search

Do not invoke without explicit human approval:

- research-pipeline
- idea-discovery
- research-refine
- research-refine-pipeline
- experiment-plan
- experiment-bridge
- auto-review-loop
- ablation-planner

No skill may expand the research scope automatically.

---

## 17. Validation Discipline

Before changing code:

1. inspect repository architecture;
2. identify the smallest frozen requirement being implemented;
3. identify its hypothesis / metric / E0 requirement;
4. confirm it exists in the approved Implementation Map.

After code changes:

- run the smallest relevant tests;
- run deterministic dry-run tests before model inference;
- inspect `git diff`;
- report exactly which frozen requirement each change satisfies.

Do not report a test as passing unless it actually ran.

Do not fabricate experiment results.

---

## 18. Git and Output Safety

Respect the active Codex environment's Git policy.

Do not push, merge, or overwrite user work without explicit
authorization.

Do not commit:

- model weights;
- downloaded large datasets;
- transient caches;
- secrets;
- credentials;
- huge raw runtime artifacts unless explicitly required.

Keep code changes minimal and auditable.