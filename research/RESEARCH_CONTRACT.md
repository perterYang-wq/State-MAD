# State-MAD Research Contract

Status: FROZEN FOR PILOT DESIGN

Authority:  
This file supersedes earlier drafts, chat formulations,  
and non-frozen experiment suggestions.

Core research questions and definitions may only be reopened  
by explicit human decision.

---

# 1. Problem

State-MAD studies a specific failure mode in multi-agent LLM systems in which information is **correct when created**, but becomes invalid after a later authoritative state update and is subsequently treated as current by other Agents through inter-agent communication.

The project must strictly distinguish the following two concepts.

## Erroneous Memory

**Erroneous Memory = wrong at creation.**

A memory/message is erroneous when it is already incorrect at the time it is generated.

Formally, for state/fact identity \(f\) at creation time \(t_0\):

\[
m(f,t_0) \neq G(f,t_0)
\]

where \(G(f,t_0)\) is the authoritative state at \(t_0\).

## Stale / Superseded Memory

**Stale / Superseded Memory = correct at creation, invalid after a later authoritative update.**

A memory/message may be fully correct when created:

\[
m(f,t_0)=G(f,t_0)
\]

but after a later authoritative update at \(t_1>t_0\):

\[
G(f,t_1)\neq G(f,t_0)
\]

The old value becomes superseded. If it is later treated as current, it is stale at use time.

The core distinction is therefore:

- **erroneous memory:** wrong-at-creation;
- **stale / superseded memory:** correct-at-creation, invalid-after-update.

State-MAD studies the second failure mode.

---

# 2. Novelty Boundary

State-MAD does **not** claim to be the first work to introduce or use:

- version;
- provenance;
- supersession;
- state identity;
- active/stale status;
- state-aware retrieval.

These are implementation primitives and state-management concepts, not the primary novelty claim of State-MAD.

## Primary Contribution

The primary contribution is **phenomenon / problem formulation / controlled measurement** of:

- causal stale adoption;
- secondary retransmission;
- false stale consensus;
- correction-visible residual stale belief;
- possible re-infection of an already corrected Agent.

## Secondary Contribution

The secondary contribution is:

> **minimal supersession-aware mitigation**

whose purpose is to test whether explicit state validity and supersession awareness can reduce the above failure mechanisms.

State-MAD must not be framed as a new general-purpose memory architecture.

---

# 3. Frozen Definition of Stale-State Propagation

The definition of stale-state propagation is frozen as a **causal adoption effect in a current-aware target Agent**.

Let a state/fact identity \(f\) have two versions:

\[
v_{old} \xrightarrow{\text{superseded by}} v_{new}
\]

A target Agent \(A_j\) must already have obtained or be able to access \(v_{new}\) before the stale peer exposure is evaluated.

Only when exposure to a peer-provided stale state makes \(A_j\) more likely to adopt \(v_{old}\) than a matched control is the event counted as stale-state propagation.

Formally:

\[
P(A_j \rightarrow v_{old} \mid
A_j\ knows\ v_{new},
\ stale\ peer\ exposure)
\]

\[
>
\]

\[
P(A_j \rightarrow v_{old} \mid
A_j\ knows\ v_{new},
\ matched\ control)
\]

The key causal structure is:

\[
\text{current-aware target}
+
\text{stale peer exposure}
\rightarrow
\text{causal stale adoption}
\]

## The following do **not** count as propagation

- Agent 没收到 update；
- retrieval 没取到 current state；
- Agent 本来不知道 \(v_{new}\)；
- single-agent stale persistence；
- 没有 peer exposure；
- 没有 matched control。

These cases may indicate state drift, update synchronization failure, retrieval failure, or incomplete information, but they are **not** evidence for the frozen State-MAD definition of stale-state propagation.

---

# 4. Frozen RQ1–RQ4

The following research questions are frozen. They may not be changed, expanded, or replaced without explicit human decision.

## RQ1

> **在 target Agent 已经获得 current state 的 controlled setting 中，暴露于 peer 的 superseded state 是否会导致 causal stale adoption，并进一步发生 inter-agent re-transmission？**

## RQ2

> **哪些因素影响 stale-state propagation 和 false consensus formation？**

RQ2 remains within the original research direction and does not authorize expansion into new research questions, architectures, topologies, or unrelated behavioral factors.

## RQ3

> **当原始 stale source Agent 已经获得 current-state correction，且该 correction 已经对先前暴露的 Agents 可见之后，系统中是否仍存在 residual stale belief、secondary stale retransmission，或对已纠正 Agent 的 re-infection？**

## RQ4

> **State-aware memory management 是否能够降低 stale propagation 并促进系统恢复？**

RQ4 is explicitly bounded to the **minimal mitigation** role. It does not authorize a new memory architecture or complex learned system.

---

# 5. Frozen Definition of Correction-Visible Residue

Residual stale belief is only counted under a strict **correction-visible** condition.

Assume:

\[
v_{old} \xrightarrow{\text{superseded by}} v_{new}
\]

and a source Agent \(A_s\) previously propagated \(v_{old}\).

A valid correction-visible residue measurement requires all of the following:

1. **source corrected** — \(A_s\) has obtained \(v_{new}\);
2. **source no longer treats \(v_{old}\) as current**;
3. **correction delivered** — the updated state/correction has been transmitted to the target Agent;
4. **correction visible/accessibile to target** — the target can access the correction at measurement time;
5. **measurement happens afterward** — residue is measured only after the above conditions hold.

Only if the target Agent still does one or more of the following after these conditions are satisfied does it count as residual stale belief:

- outputs \(v_{old}\);
- treats \(v_{old}\) as current;
- retransmits \(v_{old}\) to another Agent.

A re-infection event is counted when an Agent that has already been corrected to \(v_{new}\) later returns to \(v_{old}\) after exposure to secondary stale copies.

The following does **not** count as RQ3 evidence:

\[
\text{correction unavailable}
+
\text{old belief persists}
\]

RQ3 requires:

\[
\text{source corrected}
+
\text{correction visible}
+
\text{old belief persists or propagates}
\]

---

# 6. Minimal State-MAD

State-MAD is intentionally limited to a minimal state-management layer needed to test the frozen hypotheses and provide a lightweight mitigation.

## Must Have

- deterministic state/fact identity;
- simple version/order;
- deterministic supersession relation;
- active/stale/conflicting status;
- provenance for experiment logging;
- state-aware retrieval/context construction;
- historical raw message preservation.

## Provenance Boundary

By default, provenance is **measurement infrastructure**.

It is required for experiment logging and for reconstructing propagation paths such as:

\[
A \rightarrow B \rightarrow C
\]

It is **not** automatically a model-visible feature and must not be presented as the innovation of State-MAD.

## Core Intervention

> **A superseded factual state loses authority as the current state, but its historical message does not need to be physically deleted.**

Therefore State-MAD does **not** assume:

> stale = harmful = delete the whole message.

The system should prevent stale factual state from being treated as current while preserving historical raw messages for audit and possible historical reasoning value.

---

# 7. Method Boundary

State-MAD must **not** be packaged as:

> a new memory architecture.

The method contribution is secondary and minimal.

The first phase must not add:

- RL;
- fine-tuning;
- learned router;
- learned stale detector;
- dependency graph;
- semantic state parser;
- complex topology;
- unnecessary LLM-as-a-Judge.

The following are also outside the first-phase method boundary unless explicitly reopened by human decision:

- learned memory scorer;
- general-purpose LLM state extraction;
- large-scale graph memory;
- large model sweep;
- expanded Agent count;
- expanded debate depth.

The first phase should reuse the existing MAD-M² codebase rather than re-implementing the overall MAD framework.

---

# 8. Evidence Requirements

The project must preserve the following minimum evidence requirements.

## 8.1 Stale vs Static-Wrong Matched Evidence

The study must distinguish once-correct-then-superseded stale information from information that was already wrong at creation.

## 8.2 Communication-Specific Causal Adoption

The target Agent must already know or be able to access the current state. Evidence must show that stale peer exposure changes adoption relative to a matched control.

## 8.3 Secondary Retransmission Evidence

The study must test whether an Agent that adopts stale state can become a secondary carrier and transmit that stale state onward.

## 8.4 Correction-Visible Residue Evidence

Residual stale belief must be measured only after source correction is complete and the correction is visible/accessibile to the target.

## 8.5 State-MAD vs Sham Metadata / Context Control

Any mitigation improvement must be distinguished from gains caused merely by:

- extra tokens;
- longer context;
- generic metadata;
- non-semantic version labels;
- other context-formatting advantages.

The evidence chain must support the claim that any benefit comes from state/supersession awareness rather than metadata volume alone.

---

# 9. Resource Budget

The following budget is frozen for the staged study.

- **Agents:** \(\le 3\)
- **Main debate rounds:** \(\le 2\)
- **Sanity:** 10–20 scenarios
- **Pilot:** 30–50 scenarios
- **Stage 2:** around 100 scenarios
- **Final:** 200–300 scenarios
- **First phase model:** one open 7B/8B model
- **Final model families:** \(\le 2\)
- **Grading:** deterministic grading preferred
- **Raw trajectories:** cache all raw agent messages / trajectories
- **Replay:** offline replay whenever possible

All experiments must record:

- token usage;
- seed;
- model;
- prompt;
- configuration;
- raw message trajectories.

Before any experiment expansion, the project must first ask:

- Which hypothesis does this correspond to?
- Which paper claim would be weakened if it is not run?
- Can it be completed offline using existing cached results?

---

# 10. Stop / Hold Conditions

The following conditions must be preserved as stop/hold criteria.

## Condition 1 — Stale is not distinguishable from static wrong

If stale and static-wrong conditions show no meaningful distinguishable effect under matched controls, the distinct stale-state failure claim is undermined.

## Condition 2 — Peer exposure does not increase stale adoption

If current-aware targets exposed to stale peers do not adopt \(v_{old}\) more often than matched controls, the causal propagation claim fails.

## Condition 3 — Correction-visible residue disappears

If, once source correction is visible/accessibile, residual stale belief and re-infection disappear to the matched clean level, the correction-visible residue claim is not supported.

## Condition 4 — Mitigation is equivalent to sham control

If minimal State-MAD performs no better than sham metadata / context-length controls, the mitigation mechanism claim is not supported.

## Condition 5 — Identity / majority fully explains the phenomenon

If the apparent stale effect is fully explained by identity bias, majority influence, or generic conformity under matched controls, the stale-specific mechanism claim is not supported.

## Condition 6 — New literature fully covers the core mechanism

If new literature is found that fully covers the project’s core mechanism — including debate-mediated causal adoption, secondary retransmission, false stale consensus, and correction-visible residue — the project must be placed on HOLD for human review.

If two or more of the core novelty conditions fail, the project should not continue automatically.

---

# 11. Change Control

This Research Contract is frozen for pilot design.

Any suggestion that changes any of the following must be marked:

> **需要人工决策**

and must **not** be applied automatically:

- core RQ;
- novelty claim;
- major method component;
- >3 agents;
- >2 major rounds;
- large model sweep;
- RL / fine-tuning.

The same rule applies to any suggestion that would materially change the problem formulation, contribution hierarchy, or scope of State-MAD.

Automatic reviewer-driven expansion is prohibited.

---

# Frozen Contribution Hierarchy

For avoidance of ambiguity, the final contribution hierarchy is:

## Primary

- causal stale adoption;
- secondary retransmission;
- false stale consensus;
- correction-visible residual stale belief;
- possible re-infection;
- controlled measurement of these phenomena.

## Secondary

- minimal supersession-aware mitigation.

## Not Claimed as Novel

- state identity;
- version;
- provenance;
- supersession;
- active/stale/conflicting status;
- state-aware retrieval itself.

---

# Frozen Core Logic

\[
\boxed{v_{old}\text{ once correct}}
\]

\[
\downarrow\ \text{authoritative state update}
\]

\[
\boxed{v_{new}\text{ becomes current}}
\]

\[
\downarrow
\]

\[
\boxed{\text{target Agent already knows / can access }v_{new}}
\]

\[
\downarrow\ \text{stale peer exposure}
\]

\[
\boxed{\text{causal adoption of }v_{old}}
\]

\[
\downarrow
\]

\[
\boxed{\text{secondary retransmission / false stale consensus}}
\]

Then:

\[
\boxed{\text{source corrected} + \text{correction visible}}
\]

If stale state still persists or propagates afterward:

\[
\boxed{\text{correction-visible residual stale belief}}
\]

State-MAD then tests whether:

\[
\boxed{\text{minimal supersession-aware mitigation}}
\]

reduces the above phenomena.

---

**End of frozen Research Contract.**
