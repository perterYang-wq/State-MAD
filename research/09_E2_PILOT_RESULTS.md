# State-MAD E2 Pilot Results

Status: FROZEN PILOT RESULT
Stage: E2 — Conditional Secondary Retransmission and False-Consensus Diagnostic

## 1. Scientific Run Provenance

| Field | Frozen value |
| --- | --- |
| Run ID | `e2-qwen25-7b-seed7-pilot-20260914-v1` |
| Repository commit | `e6ab020a856b79af876ef2ea426c42cf02094d44` |
| Upstream E1 run | `e1-qwen25-7b-seed7-pilot-20260912-v1` |
| Upstream E1 scientific commit | `b002fe3d3dce8fe5d94b83f946dde2e494e09d4e` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Model revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Tokenizer revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Decoding | seed `7`; temperature `0.0`; top-p `1.0`; max new tokens `32` |
| Selected / eligible / excluded | `9 / 9 / 0` |
| Calls | `72` logical; `27` Relay core; `45` final readout |
| Cache | `54` hits; `18` misses |
| Logical tokens | input `5601`; output `463`; total `6064` |
| Generated tokens | input `1307`; output `116`; total `1423` |
| Token projection | `7905 / 800000` |
| Scientific preflight | **PASS** |
| Post-run artifact audit | **PASS** |
| Result evidence audit | **PASS** |

The E2 scientific run reused the frozen E1 Target outputs exactly.
No E1 generation was repeated.

## 2. Eligibility and Relay Awareness

The frozen E2 execution subset contains the nine E1 treatment-only causal
primary stale adopters:

`e1-04`, `e1-10`, `e1-16`, `e1-18`, `e1-22`, `e1-28`, `e1-30`,
`e1-34`, `e1-40`.

All nine Relay Agents independently passed the current-awareness gate.

- Candidates / E2 eligible: `9 / 9`.
- Relay current-aware: `9 / 9`.
- Completed matched Relay pairs: `9 / 9`.
- Infrastructure exclusions: `0`.

## 3. Conditional Secondary Retransmission

| Measure | Frozen result |
| --- | ---: |
| Stale-replay Relay STALE | `6 / 9` |
| Current-replay Relay STALE | `0 / 9` |
| Paired Relay difference | `+0.6667` |
| `SRR_cond` | `0.6667` |
| Gate 4 | **SECOND-HOP-POSITIVE PILOT** |

Second-hop stale-adoption IDs:

`e1-04`, `e1-16`, `e1-18`, `e1-28`, `e1-30`, `e1-40`.

Among the nine E1 cases already verified as paired causal primary stale
adopters, exact replay of the stale Target output to an independently
current-aware Relay produced second-hop stale adoption in 6 of 9 cases,
versus 0 of 9 under exact matched current-output replay.

`SRR_cond` is conditional on the observed E1 causal-primary-adopter subset.
It is not an unconditional or population-level two-hop propagation rate.

## 4. False Stale Consensus Diagnostics

The nine scenarios each contributed stale and current matched system cases,
giving `18` complete synchronized non-communicative final-readout cases.

| Metric | Numerator | Denominator | Rate |
| --- | ---: | ---: | ---: |
| Ordinary FSCR | `6` | `18` | `0.3333` |
| Exposure-Induced FSCR | `6` | `18` | `0.3333` |
| Retransmission-Supported FSCR | `6` | `18` | `0.3333` |

All six numerator cases were stale-arm cases:
`e1-04`, `e1-16`, `e1-18`, `e1-28`, `e1-30`, and `e1-40`.

No current-arm case entered any numerator.

Every ordinary stale majority observed here also satisfied the frozen
exposure-induced predicate and the mechanically verified
retransmission-supported lineage predicate.

The permitted interpretation is limited: a verified Source → Target → Relay
second-hop path participated in these six false stale majorities.
The report interpretation remains `conditional/diagnostic`, with
`independent_retransmission_claim=false`.

## 5. RQ1 Status After E2

**CONDITIONAL SECOND-HOP RETRANSMISSION SUPPORTED AT PILOT SCALE**

E1 established the first-hop paired causal-adoption component.
E2 conditioned on the nine observed E1 causal primary adopters and tested
exact stale-Target replay against matched exact current-Target replay at
independently current-aware Relays.

The combined pilot evidence supports the frozen chain:

`current-aware Target → stale-peer causal adoption → exact Target stale output → current-aware Relay → second-hop stale adoption`

for the naturally observed conditional subset.

This result does not change the frozen RQ1 definition.

## 6. Claim Boundaries

E2 supports the bounded conclusion that, among these nine observed E1 causal
primary stale adopters, exact stale-output replay caused second-hop stale
adoption relative to matched exact current-output replay.

E2 does **not** establish:

- statistical significance;
- a population propagation probability or population prevalence;
- generalization across models, seeds, domains, or datasets;
- autonomous long-horizon propagation;
- an independent population-level false-consensus rate;
- correction-visible residual stale belief;
- re-infection after verified correction;
- any RQ3 result; or
- any mitigation / E4 result.

The nine-case E2 set is selected because those cases were observed paired
causal primary stale adopters in E1. This conditioning must remain explicit
in every downstream claim.
## 7. Artifact and Integrity Audit

| Artifact check | Frozen result |
| --- | ---: |
| `calls.jsonl` rows | `72` |
| `final_votes.jsonl` rows | `18` |
| `lineage.jsonl` rows | `135` |
| E2 message artifacts | `90` |
| `manifest.json` | present |
| `report.json` | present |
| Repository working tree after run | clean |

The `90` E2 messages consist of `18` exact E1 Target replay envelopes plus
`72` E2 logical-call outputs.

The finalized evidence audit confirmed the retransmission counts, all three
FSCR counts, cache accounting, token totals, and frozen generation identity.

## 8. Downstream Authorization State

E2 scientific Pilot: **COMPLETE**

E2 result evidence: **FROZEN**

RQ1 first-hop causal adoption: **SUPPORTED AT E1 PILOT SCALE**

RQ1 conditional second-hop retransmission: **SUPPORTED AT E2 PILOT SCALE**

False stale consensus: **CONDITIONAL / DIAGNOSTIC E2 EVIDENCE PRESENT**

E3: **NOT AUTHORIZED**

This artifact does not authorize E3, RQ3 execution, mitigation experiments,
additional models or seeds, larger samples, or any expansion beyond the
completed E2 pilot.
