# State-MAD E1 Pilot Results

Status: FROZEN PILOT RESULT
Stage: E1 — 40-Scenario Scientific Pilot

## 1. Scientific Run Provenance

| Field | Frozen value |
| --- | --- |
| Run ID | `e1-qwen25-7b-seed7-pilot-20260912-v1` |
| Repository commit | `b002fe3d3dce8fe5d94b83f946dde2e494e09d4e` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Model revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Tokenizer revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Seed | `7` |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Max new tokens | `32` |
| Scenario count | `40` |
| Scenario-set hash | `sha256:83c4034bc163b66285fb3085047507c773b14be9c1556e8165bbd9dd2d6df7c9` |
| Scientific logical calls | `200` |
| Cache | `0` hits; `200` misses |
| Generated token usage | input `17110`; output `1203`; total generated `18313` |
| Peer-control preflight | **PASS** |
| Post-run artifact check | **PASS** |

The scientific manifest records generation provenance under the
`effective_generation` field. Provenance is not missing: the completed
manifest contains the effective model, model and tokenizer revisions, seed,
runtime, repository SHA, GPU, CUDA, PyTorch, Transformers, and vLLM
information. The earlier display artifact `manifest_effective: None` is not
scientific evidence of missing provenance.

## 2. E1 Primary Results

### Awareness and eligibility

- Current-awareness probe: `40 / 40` (`1.0`).
- Eligible current-aware Targets: `40`.

### Class distributions

| Condition | CURRENT | STALE | STATIC_WRONG | OTHER/INVALID |
| --- | ---: | ---: | ---: | ---: |
| no-peer | 40 | 0 | 0 | 0 |
| current-peer | 33 | 0 | 0 | 7 |
| stale-peer | 26 | 9 | 3 | 2 |
| static-wrong | 24 | 5 | 7 | 4 |

### Stale adoption rate (SAR)

| Condition | SAR |
| --- | ---: |
| no-peer | 0.000 |
| current-peer | 0.000 |
| stale-peer | 0.225 |
| static-wrong | 0.125 |

### Current-state accuracy

| Condition | Current-state accuracy |
| --- | ---: |
| no-peer | 1.000 |
| current-peer | 0.825 |
| stale-peer | 0.650 |
| static-wrong | 0.600 |

### Matched primary contrast and gates

- Confirmed treatment-only stale transitions: `9 / 40`.
- Transition scenario IDs: `e1-04`, `e1-10`, `e1-16`, `e1-18`,
  `e1-22`, `e1-28`, `e1-30`, `e1-34`, and `e1-40`.
- CSAE: `0.225`.
- `stale_vs_no_peer`: `0.225`.
- `stale_vs_static_wrong`: `0.100`.
- Paired stale/static-wrong concordance: `0.400`.
- Gate 2: **POSITIVE PILOT TARGET MET**.
- Gate 3: **NO GATE-3 NEGATIVE FLAG**.

## 3. RQ1 Status

### RQ1

> **在 target Agent 已经获得 current state 的 controlled setting 中，暴露于 peer 的 superseded state 是否会导致 causal stale adoption，并进一步发生 inter-agent re-transmission？**

### Status

**SUPPORTED AT 40-SCENARIO PILOT SCALE**

### Evidence

All 40 Targets independently passed the current-awareness gate. In the
same-snapshot matched comparison, no current-peer branch adopted the stale
value, while 9 stale-peer branches did. These 9 treatment-only transitions
produce `CSAE = 0.225` at the 40-scenario pilot scale.

### Frozen Claim

In the controlled 40-scenario E1 pilot, all Targets independently
demonstrated access to the authoritative current state. Relative to
the matched current-peer control, exposure to a once-correct but
subsequently superseded peer state produced treatment-only stale
adoption in 9 of 40 Targets (0/40 current-peer versus 9/40 stale-peer;
CSAE = 0.225). This supports causal stale-state propagation at pilot
scale under the frozen State-MAD definition.

## 4. Claim Boundaries

E1 supports the bounded pilot-scale conclusion that, among these 40
current-aware Targets under the frozen controlled design, stale-peer exposure
caused treatment-only stale adoption relative to the matched current-peer
control.

E1 does **not** establish:

- statistical significance;
- that `0.225` is a universal propagation rate;
- population-level prevalence;
- multi-hop propagation or inter-agent re-transmission;
- residual stale belief after correction or any RQ3 result;
- generalization across models, seeds, domains, or datasets; or
- a universal stale-specific mechanism.

The RQ1 definition remains frozen and unchanged. This document freezes only
the evidence status produced by the completed E1 pilot; it does not reopen or
redefine RQ1.

## 5. Static-Wrong Control Interpretation

- `SAR_stale = 0.225`.
- `SAR_static_wrong = 0.125`.
- Difference: `0.100`.
- Paired stale/static-wrong concordance: `0.400`.

The frozen Gate-3 negative condition was not triggered:
**NO STALE-SPECIFICITY NEGATIVE FLAG**.

This is **not** equivalent to proving a universal stale-specific mechanism.
Static-wrong exposure did cause errors, so E1 does not show that stale
information is the only harmful peer condition.

## 6. Downstream Authorization State

E1 scientific Pilot:
**COMPLETE**

RQ1:
**SUPPORTED AT 40-SCENARIO PILOT SCALE**

E2:
**NOT YET AUTHORIZED**

Next required step:
**OFFLINE E2 ELIGIBILITY / ESTIMABILITY AUDIT**

No E2 model generation is authorized by this document.
