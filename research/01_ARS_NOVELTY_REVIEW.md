# State-MAD — ARS Novelty Review

Status: ARCHIVED REVIEW  
Stage: 01-ARS-Novelty-Review

This file records the Stage-01 review.  
Where it conflicts with `RESEARCH_CONTRACT.md`,  
`RESEARCH_CONTRACT.md` has higher authority.

---

# 01 Executive Verdict

- **Novelty Grade: B — Distinct but Vulnerable**
- **Confidence: Medium–High (~0.82)**
- **Biggest Novelty Risk:** State-MAD 的**方法组件本身几乎不能作为主要 novelty**。StateMem 已经覆盖 supersession、stale state、provenance-like source tracking、dependency propagation、current-state evaluation；额外的 2026-09 公开文献核查还发现，已有工作直接使用了 **“stale propagation”** 这一术语来描述 multi-agent shared memory 中的跨 Agent 过期状态问题。
- **Strongest Defensible Contribution:** 不是“我们发明了 version / provenance / supersession”，而是：

> **在受控 asynchronous state-update 条件下，研究 once-correct-but-later-superseded state 如何通过 MAD 的自然语言通信发生 message-mediated adoption、re-transmission、false consensus，以及在 source 已经被纠正且 correction 已经可见之后，secondary stale copies 是否仍会持续并重新感染已纠正 Agent。**

- **Recommendation: GO WITH REVISION**

这里的 revision **不改变冻结的 RQ1–RQ4**，而是必须收紧 novelty claim 和 operational definition。

## 关键判决

### A. Project Sources

MAD-M² 明确把问题建模为 previous-round 的 incorrect / fallacious / erroneous memories，并通过 subjective/objective masking 去除它们；其 Figure 1 展示的是“上一轮已经错的回答”把原本正确的 Agent 带错。它没有 state update、supersession 或 source-correction lifecycle。

StateMem 则已经非常明确地提出：事实、约束、决策会被 later revision supersede，系统必须回答 current state 而不是 superseded state；它还实现 source、supersession、dependency recheck，并把 superseded history 保留用于 audit。

Post-Removal Logical Residue 已经覆盖“问题源离开以后，被影响 Agent 仍携带 retained context，并继续污染新的 Agent/environment”这一**结构性的 persistence/contagion pattern**。因此 RQ3 并不是天然新颖，必须证明“legitimate state supersession + correction”产生的是另一类 residue。

`PROJECT_SOURCES.md` 对这三个边界的原始定位基本正确，但从 reviewer 角度必须再收紧。

### B. External novelty check recorded in the Stage-01 review

Stage-01 review 当时记录了以下风险：已有工作已经把 **stale propagation、temporal supersession、provenance、policy-governed propagation** 放进 multi-agent shared-memory formalism；另有工作研究 explicit validity、revocation、superseded history retained for audit，以及 distributed LLM-agent team 中 stale plan / superseded requirement 的问题。

因此，Stage-01 review 的结论是：

> **“State-MAD 是第一个研究 multi-agent stale-state propagation 的工作”目前不能成立。**

### C. Reviewer inference

这还没有达到 D / Novelty Failure，因为上述 multi-agent work 主要是：

- shared-memory synchronization；
- distributed state consistency；
- stale plan validation；

而不是：

- MAD natural-language debate；
- stale claim 被其他 Agent **采纳**；
- secondary Agent 再次 **re-transmit**；
- stale copies 通过社会/共识机制被强化；
- source correction 已可见后仍有 residual stale belief；
- corrected source 被 secondary stale carrier **re-infected**。

因此真正的 novelty 必须落在 **communication-mediated contagion dynamics**，而不是“multi-agent + stale”这个大组合。

**需要人工决策：** 是否继续使用非常宽泛的标题/claim “Stale-State Propagation in Multi-Agent Systems”。RQ 不需要改变，但论文标题和 “first” claim 需要在实验前重新审定。

---

# 02 Source-grounded Problem Boundary

## Erroneous Memory

MAD-M² 使用 erroneous memory 指 previous debate round 中 incorrect reasoning responses / fallacious content，并研究这些错误 memory 如何误导下一轮 Agent。

Stage-01 review 使用的 operational definition：

> 一个 memory/message 在它被生成的时间 \(t_0\) 就不符合该时间点的 ground truth。

即：

\[
m(f,t_0)\neq G(f,t_0)
\]

关键属性：**wrong-at-creation**。

## Stale Memory

StateMem 已经明确使用 stale / superseded state 概念，并把 state drift 定义为：相关信息存在，但系统使用的不是 decision time 正在生效的 state。

Stage-01 review 使用的 operational definition：

> 一个 claim 在生成时符合当时 ground truth，但后续 authoritative update 使其对应 state version 不再 operative，而该 claim 仍被作为 current 使用。

即：

\[
m(f,t_0)=G(f,t_0)
\]

但存在 \(t_1>t_0\)：

\[
G(f,t_1)\neq G(f,t_0)
\]

而 decision time \(t_d\geq t_1\) 仍使用 \(G(f,t_0)\)。

关键属性：**correct-at-creation, invalid-at-use**。

## Superseded State

StateMem 明确把旧 unit 标成 superseded，同时加入新 active unit；旧 unit 继续存储用于 audit，但不作为 active current state 注入回答阶段。

State-MAD 不应声称 supersession 本身是新概念。

## Residual Stale Belief

Stage-01 review 收紧后的 operational definition 是：

> 原始 stale source Agent 已经获得并输出 current version，且这个 correction 已经对目标 Agent 可见之后，目标 Agent 仍继续输出 superseded version；或者已经纠正的 source 在接触 secondary stale copies 后重新回到 superseded version。

这里必须包含 **“correction visible”**。否则无法排除 target 根本没有接收到新信息。

## Stale-State Propagation

Stage-01 review 指出，不能把 propagation 定义成：

> Agent B 没收到 update，所以 B 继续说旧值。

更严格的 operationalization 应是：

> **一个原本已经有 current-state evidence 的 Agent，因为接触到另一个 Agent 的 stale message，而提高输出 superseded state 的概率。**

形式化：

\[
P(\text{stale output}\mid \text{stale peer exposure,current known})
>
P(\text{stale output}\mid \text{no stale exposure,current known})
\]

进一步的 re-transmission 是：

\[
A_{\text{stale}}\rightarrow B_{\text{adopts stale}}\rightarrow C_{\text{adopts stale}}
\]

其中 B 已不只是旧状态持有者，而成为新的 secondary stale carrier。

---

# 03 Comparison with MAD-M²

MAD-M² 明确研究 previous-round erroneous reasoning、错误 memory 对下一轮的误导，以及 subjective/perplexity-based masking；其理论假设直接用 previous-round erroneous-memory count \(N_e\) 来调节下一轮正确概率。

| Dimension | MAD-M² erroneous memory | State-MAD stale state |
|---|---|---|
| 产生机制 | 生成/推理时已经错 | 生成时正确，随后 update |
| 时间属性 | 基本静态 | validity 随时间改变 |
| Ground truth | 固定 query 的静态答案 | \(G_t\) 随 state update 改变 |
| Detection | 判断 response 是否正确/可信 | 判断 state identity + temporal order + supersession |
| Intervention | mask/drop bad response | revoke current authority；history 可保留 |
| Propagation | wrong message 影响下一轮 | stale version 在不同 Agent 版本之间传播 |
| Recovery | mask bad previous-round memory | update propagation + secondary-copy cleanup + post-correction recovery |

## Reviewer objection

> “Stale memory ultimately 也是 wrong memory，所以 State-MAD 只是 MAD-M² 的另一种 masking condition。”

### 1. 最强支持该批评的论据

这个批评**有相当强的成立部分**。

在 decision time，stale value 确实是 wrong value。

如果实验只是：

1. 放一个旧答案进 context；
2. Agent 被带错；
3. 把旧答案 mask；
4. accuracy 提高；

那么从 MAD-M² reviewer 角度，这几乎就是 replication：

> “只是把错误消息的来源从 arithmetic mistake 改成 old fact。”

尤其 State-MAD 最终同样采用 binary drop/filter 时，方法层面非常容易被归为 temporal masking。

### 2. 最强反驳

关键不是 stale 是否在使用时 wrong，而是：

> **一个 message 的 validity 能否仅由 message 自身确定。**

MAD-M² 中一个错误推导原则上在生成出来时就已经错误。

但例如“budget = $600”可以在周一完全正确，在周三被修改为 $800 后才变成错误。

因此同一个 text representation：

- 在 \(t_0\) 应保留；
- 在 \(t_1\) 应撤销 current authority。

检测 stale 必须知道一个 **state transition relation**，而不是只判断 message quality。

### 3. 真正反驳 reviewer 所需实验

Stage-01 review 要求必须做 **matched stale-vs-static-error experiment**，至少包括：

- Current-correct message
- Static erroneous message
- Once-correct → superseded message
- No-peer-message

并确保 target Agent **已经获得 current update**。

比较：

- stale adoption；
- recovery；
- MAD-M² masking；
- State-MAD state-aware policy。

如果 stale 和 static-wrong 在所有行为、masking、recovery 上完全一样，而且 MAD-M² 同样解决，则该 novelty objection 基本成立。

---

# 04 Comparison with StateMem

这是 State-MAD 最大的方法 novelty 风险。

StateMem 已经有：

- evolving state；
- state drift；
- supersession；
- source field；
- active / superseded / needs_recheck；
- dependency graph；
- deterministic rechecking；
- current-state benchmark；
- length/cost-matched control。

因此：

## METHOD NOVELTY

**Low。**

如果 State-MAD 宣称：

> “我们的创新是加入 fact ID、version、provenance、supersession、active/stale status。”

reviewer 很容易判 incremental。

这些 primitives 不能作为主要创新。

## PHENOMENON / SYSTEMS NOVELTY

仍然存在，但必须严格限定。

| Dimension | StateMem | State-MAD |
|---|---|---|
| Unit of analysis | memory system → current answer | Agent/message/version transition |
| Inconsistency source | revisions in one memory history | asymmetric versions across Agents |
| Information distribution | effectively one memory system accesses transcript | different Agents see different updates |
| State visibility | centralized/assembled | heterogeneous/local |
| Propagation | dependency update inside state graph | Agent → Agent message adoption |
| Retransmission | not central | core phenomenon |
| Consensus | not central | core system outcome |
| Source correction | user/state revision | stale source Agent itself corrected |
| Residual belief | stale state may persist | other Agents retain/retransmit after source correction |
| Intervention target | memory store | cross-agent active context |
| Metrics | current-state / drift | transmission, false consensus, residual, reinfection |

StateMem 已经有 dependency propagation，那么 State-MAD 还剩下的 scientific question，不是“更新 A 后也应该更新 B”，而是：

> “Agent A 的旧 belief 被 Agent B 复制后，A 自己被修正是否足够？B 是否已经成为一个新的独立传播源？”

这相当于从：

**state consistency**

转向：

**socially reproduced state inconsistency**。

这是能成立的 scientific question。

但论文不能声称：

> “single-agent state tracking 没有人扩展到 multi-agent。”

可防守的 claim 应是：

> **现有 state-memory / distributed-memory work 主要研究 store synchronization 或 state resolution；State-MAD 研究 natural-language inter-agent reasoning 中，stale state 如何被复制、强化、重新传播并形成错误共识。**

这也是 Stage-01 review 给出 B 而不是 A 的主要原因。

---

# 05 Comparison with Post-Removal Logical Residue

PLR 明确研究：

1. malicious Agent 在 exposure stage 影响 benign Agent；
2. malicious Agent 被移除；
3. exposed Agent 保留 prior interaction state；
4. exposed Agent 与 fresh Agent 继续协作；
5. residue 继续影响/污染 collaboration。

从系统结构看，这与 State-MAD 的：

> source → recipient → source removed/corrected → residual → new propagation

非常接近。

| Dimension | PLR | State-MAD |
|---|---|---|
| maliciousness | intentional HYLQ | legitimate state evolution |
| correctness-at-creation | plausible/low-utility adversarial reasoning | explicitly correct |
| exposure | adversarial phase | normal state sharing |
| source removal | core intervention | secondary control |
| source correction | not core | core |
| retained context | core | core |
| behavioral residue | core | possible |
| factual/state residue | not primary | primary |
| propagation path | exposed → fresh Agent | stale source → secondary carrier → others |
| recovery | CIRPS | state-aware supersession/retrieval |

因此 reviewer objection：

> “你只是把 malicious residue 换成 stale factual residue。”

**Severity: High。**

但不是 Fatal。

Stage-01 review 要求的关键区分是：State-MAD 的 post-event intervention 不能只是 source removal，而应是更严格的：

> **source correction + visible updated state**

并证明：

- 原信息 creation 时正确；
- 更新来自 legitimate state transition；
- correction 已对 recipient 可见；
- recipient 仍输出具体 superseded version；
- version-aware intervention selectively 修复该 factual residue。

如果只做 source removal，这个 objection 很难反驳。

---

# 06 Secondary Overlap Check

## DAR / Hear Both Sides

DAR 已经明确把 **what messages are propagated** 作为 MAD 的核心设计问题，通过 disagreement/diversity selection 保留消息，而不是全量广播。

所以：

> “State-MAD 也是 message filtering。”

这个批评成立到 mechanism 层。

但 selection criterion 不等价。

DAR 的目标是：

\[
\text{maximize informative disagreement}
\]

State-MAD 的目标是：

\[
\text{preserve current validity}
\]

这两个轴可能冲突：一个 superseded answer 恰好是唯一不同于当前 majority 的 minority message，那么 DAR 可能优先保留它。

Stage-01 review 建议的最干净控制是：

- 固定两条 message 的 semantic diversity；
- 只交换它们的 temporal validity；
- DAR 的 preference 理论上不应改变；
- state-aware policy 应改变。

反方向：

- 固定 validity；
- 改变 diversity；
- State-MAD 不应该把 diversity 当 state validity。

因此 temporal validity 不是 diversity 的简单 proxy。

## Wrong but Useful

这篇论文对 State-MAD 是**直接的方法论警告**。

它通过 cached-message replay 证明：

- wrong message 可能帮助 downstream；
- correct message 也可能伤害 downstream；
- proposal correctness 不决定 trajectory value。

因此：

> **“stale = harmful = delete whole message” 不能成为 State-MAD 的设计原则。**

Stage-01 review 建议冻结为：

> **Prevent stale factual state from being treated as current, while preserving historical records and potentially useful reasoning.**

这不意味着第一阶段需要开发 reasoning extractor。

最简单做法是：

- raw message 留在 archive/log；
- stale state 失去 current authority；
- active retrieval 不把 stale factual value 当 current；
- 不物理删除原 message。

## Identity Bias

这是一个真正的 confound。

Identity Bias paper 显示 Agent 会根据 “self” / “peer” attribution 改变 belief update；其核心指标 Conformity / Obstinacy 就是在 disagreement 时测量跟随 peer 或坚持 self。

因此当 Agent 从 current 转到 stale 时，不能直接说：

> “这是 stale propagation。”

也可能只是：

> “peer said it, so I copied peer。”

Stage-01 review 给出的最小 identity control 是：

同一组 cached messages：

- visible identity；
- anonymized identity；
- speaker label permutation。

并保持：

- content；
- ordering；
- token length；
- state version；
- majority structure

不变。

如果 stale adoption 在 anonymization 后消失，则测到的主要可能是 identity bias，而不是 stale-specific propagation。

---

# 07 Novelty Matrix

下表严格使用四类判断：Supported / Partially Supported / Not Supported / Unclear。

| Capability / Phenomenon | MAD-M² | StateMem | Post-Removal Residue | DAR | Wrong but Useful | Identity Bias | State-MAD |
|---|---|---|---|---|---|---|---|
| erroneous-at-generation | Supported | Partially Supported | Partially Supported | Supported | Supported | Partially Supported | Partially Supported |
| correct-at-generation | Partially Supported | Supported | Partially Supported | Supported | Supported | Supported | Supported |
| later superseded | Not Supported | Supported | Not Supported | Not Supported | Not Supported | Not Supported | Supported |
| explicit version | Not Supported | Partially Supported | Not Supported | Not Supported | Not Supported | Not Supported | Supported |
| provenance | Partially Supported | Supported | Partially Supported | Partially Supported | Partially Supported | Partially Supported | Supported |
| supersession | Not Supported | Supported | Not Supported | Not Supported | Not Supported | Not Supported | Supported |
| dependency propagation | Not Supported | Supported | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported |
| multi-agent transmission | Supported | Not Supported | Supported | Supported | Partially Supported | Supported | Supported |
| re-transmission | Partially Supported | Not Supported | Supported | Partially Supported | Not Supported | Partially Supported | Supported |
| false consensus | Partially Supported | Not Supported | Supported | Partially Supported | Not Supported | Partially Supported | Supported |
| source removal | Not Supported | Not Supported | Supported | Not Supported | Partially Supported | Not Supported | Partially Supported |
| source correction | Partially Supported | Partially Supported | Not Supported | Not Supported | Not Supported | Partially Supported | Supported |
| residual effect | Partially Supported | Partially Supported | Supported | Not Supported | Not Supported | Supported | Supported |
| recovery | Partially Supported | Supported | Supported | Supported | Not Supported | Supported | Supported |
| message filtering | Supported | Partially Supported | Partially Supported | Supported | Partially Supported | Not Supported | Supported |
| trajectory replay | Not Supported | Not Supported | Not Supported | Not Supported | Supported | Not Supported | Supported |
| deterministic gold | Supported | Supported | Partially Supported | Supported | Partially Supported | Partially Supported | Supported |
| state-validity metric | Not Supported | Supported | Not Supported | Not Supported | Not Supported | Not Supported | Supported |

Stage-01 review 特别指出：

- StateMem 的 explicit version 标为 Partially Supported，因为其公开 state-unit representation 主要通过 id / content / source / deps / status / supersession / date 等表达 temporal precedence，并非简单显式 `version=N` schema。
- State-MAD 的 dependency propagation 暂时写 Not Supported 是刻意的，因为第一阶段没有必要复制 StateMem 的 dependency graph，否则会主动扩大 method overlap。

---

# 08 Three Reviewer Attacks

## Reviewer 1 — MAD-M² author perspective

**Strongest objection**

> “At decision time your stale memory is simply an incorrect memory. MAD-M² already shows incorrect previous-round memories mislead correct Agents and that filtering them improves MAD. Your `stale` tag is merely a new masking criterion.”

**Why it matters**

如果成立，State-MAD 的核心现象退化成 MAD-M² 的 dataset variation，而方法只是换 mask predicate。

**Severity: High**

**Minimum evidence needed**

必须同时提供：

- matched static-wrong vs stale-wrong；
- target Agent 在 stale exposure 前已经知道 current state；
- MAD-M² baseline；
- state-aware baseline；
- propagation/recovery metric，而不只是 final accuracy。

如果 stale 与 static wrong 没有 behavior difference，且 MAD-M² 完全解决，则 Reviewer 1 赢。

## Reviewer 2 — StateMem author perspective

**Strongest objection**

> “We already defined state drift, supersession, stale state, dependency rechecking, provenance/source tracking, current-state accuracy, and length-matched controls. State-MAD is StateMem with multiple copies of the same memory attached to different Agents.”

**Why it matters**

这是目前最危险的 method novelty attack。

**Severity: High**

如果论文把主要贡献写成 state representation，则接近 **Fatal**。

**Minimum evidence needed**

必须证明至少一个 **communication-specific effect**：

\[
\text{same state histories + peer communication}
\neq
\text{same state histories + no communication}
\]

并观察到：

- current-aware Agent 被 stale peer 带回旧状态；
- secondary carrier 再传播；
- false stale consensus；
- source corrected 后 secondary copies 仍存在。

如果 communication 不增加任何 stale adoption，则 State-MAD 基本退化为 distributed StateMem。

## Reviewer 3 — PLR author perspective

**Strongest objection**

> “We already showed that after the original harmful source disappears, exposed Agents retain contamination and become new infection sources. You replaced adversarial reasoning residue with stale factual residue.”

**Why it matters**

它攻击的是 State-MAD 最有潜力的 RQ3。

**Severity: High**

**Minimum evidence needed**

必须让 State-MAD 的 post-event intervention 是：

> **source correction + visible updated state**

而不仅是 source removal。

并证明：

- 原信息 creation 时正确；
- 更新来自 legitimate state transition；
- correction 已对 recipient 可见；
- recipient 仍输出具体 superseded version；
- version-aware intervention selectively 修复该 factual residue。

如果只做 source removal，则 Reviewer 3 的 objection 很难挡住。

---

# 09 Revised but Still Frozen RQ1–RQ4

Stage-01 review 当时给出的措辞优化如下：

**RQ1**  
在 controlled state-update setting 中，once-correct but later-superseded state 是否会通过 inter-agent communication 被其他 Agent 采用、转述并继续传播？

**RQ2**  
在 stale state propagation 已发生的条件下，information distribution、peer multiplicity / majority structure、source identity 和 communication order 等因素如何影响 stale adoption 与 false consensus formation？

**RQ3**  
当原始 stale source Agent 已经获得并传播 current-state correction 后，secondary Agents 中是否仍存在 residual stale belief，并可能重新影响已经纠正的 Agent？

**RQ4**  
在不增加模型能力、上下文长度或 learned components 的条件下，state-aware memory handling 是否能减少 stale adoption / propagation 并提高 post-update recovery？

> **注意：本节是 ARCHIVED REVIEW 内容。后续人工冻结修改后的最终 RQ 以 `RESEARCH_CONTRACT.md` 为准。**

---

# 10 Falsifiable Hypotheses

## H1 — Communication causes stale adoption

**Hypothesis**

当 target Agent 已经获得 current version 后，暴露于 peer 的 superseded version 会提高其输出 superseded state 的概率。

**Independent variable**

Peer exposure：

- no peer；
- current peer；
- stale peer。

**Dependent variable**

Stale Adoption Rate：

\[
SAR=P(\text{output}=v_{old}\mid v_{new}\text{ already available})
\]

**Control**

- 相同 target state；
- 相同 message count；
- speaker/order matched；
- 另设 static-wrong control。

**Falsification condition**

stale-peer condition 的 SAR 不高于 current/no-peer control。

**Minimum scale**

- sanity：12–20 scenarios；
- pilot：30–50。

## H2 — Secondary transmission / social reinforcement exists

**Hypothesis**

Stale information 被一个新的 Agent 采纳并再次传播时，会进一步提高 system-level stale prevalence 或 false stale consensus，而不只是原 source 的一次直接影响。

**Independent variable**

- direct stale source only；
- secondary retransmission；
- stale-minority vs stale-majority exposure。

**Dependent variable**

- secondary stale transmission；
- number of stale Agents；
- False Stale Consensus Rate。

\[
FSCR=P(\text{final majority}=v_{old})
\]

**Control**

- anonymized identities；
- same message/order budget；
- current-majority mirror condition。

**Falsification condition**

增加 secondary carrier / stale support 不增加传播或 false consensus，并且没有可观察 hop-2 effect。

**Minimum scale**

30–50 scenarios；优先复用 H1 cached messages。

## H3 — Visible source correction does not guarantee recovery

**Hypothesis**

原始 source 已获得 current version 且 correction 已对其他 Agent 可见之后，先前形成的 secondary stale copies 仍可能导致 residual stale output，甚至使 corrected source 回退。

**Independent variable**

Source lifecycle：

- uncorrected；
- removed；
- corrected + correction visible。

**Dependent variable**

- Residual Stale Rate；
- Re-infection Rate。

**Control**

- clean state；
- correction visible but no prior stale exposure。

**Falsification condition**

一旦 correction visible，所有 stale output 都回到 clean baseline，且 corrected source 不发生任何回退。

**Minimum scale**

30 scenarios 即可做 pilot；大量条件可以从 H1/H2 cache replay。

## H4 — State awareness, not extra metadata, drives mitigation

**Hypothesis**

显式 supersession/status-aware context construction 能比 naive MAD、MAD-M² 及 length-matched sham metadata 更有效减少 stale adoption 和 residual stale belief。

**Independent variable**

Memory policy：

- naive full memory；
- MAD-M²；
- sham metadata / length-matched；
- State-MAD。

**Dependent variable**

- SAR；
- FSCR；
- residual stale rate；
- current-state accuracy；
- token usage。

**Control**

同一批 cached upstream messages；相同模型、seed、prompt budget。

**Falsification condition**

State-MAD 与 MAD-M²/sham 不存在可靠差异，或增益在 context/token matching 后消失。

**Minimum scale**

30–50 pilot；通过后再进入 100-scenario phase。

---

# 11 Alternative Explanations and Minimal Controls

| Alternative explanation | 最小控制 | 尽量如何低成本完成 |
|---|---|---|
| 1. majority effect | stale-majority 与 current-majority mirror；保持 2:1 数量一致 | cached message replay |
| 2. identity bias | visible identity vs anonymized vs shuffled labels | 同 message 只改 attribution |
| 3. prompt recency | stale/current message 交换 order/position | downstream replay |
| 4. context-length effect | same-length neutral replacement | footprint control |
| 5. retrieval failure | primary SAR 只统计 target 已经看到 current update 的 case | deterministic log |
| 6. reasoning failure | 第一阶段只用 direct state slot / closed-pool state；先不做复杂 derived reasoning | deterministic gold |
| 7. random decoding | temperature 0、固定 seed/config；小 subset 做 repeated replay | 仅重复 downstream |
| 8. generic conformity | current-peer、stale-peer、no-peer 三条件；anonymization | cached |
| 9. stale 只是普通错误 | matched static-wrong vs once-correct-then-stale | 核心实验 |
| 10. metadata 本身提升 | shuffled version、meaningless metadata、same-token sham metadata | offline context construction + replay |

Stage-01 review 特别强调：

> **不知道 update 的 Agent 继续输出旧值，不算 State-MAD 所需要证明的 causal propagation。**

那只能证明 distributed information asymmetry。

---

# 12 Minimal State-MAD

## 方法设计风险审查

| Question | Reviewer judgment |
|---|---|
| 1. stale 一定删除吗？ | **No** |
| 2. historical stale state 保留用于 audit？ | **Yes** |
| 3. stale fact 与 useful historical reasoning 分离？ | **原则上 Yes；第一阶段不需要复杂 extractor** |
| 4. version 必须显式存在？ | benchmark 内建议 Yes；理论上 supersession order 已足够 |
| 5. provenance 影响性能吗？ | **未知；主要先用于 measurement** |
| 6. supersession 可 deterministic？ | **第一阶段必须 deterministic** |
| 7. state identity 需要 LLM extraction？ | **No，synthetic benchmark 不应使用** |
| 8. 可避免 LLM-as-Judge？ | **Yes** |
| 9. 要复制 StateMem 整套系统？ | **No，而且不应复制** |
| 10. 最小组件？ | fact identity + order/version + supersession + local status + provenance logging + state-aware retrieval |

## Must Have

1. Deterministic state identity
2. Temporal ordering / version
3. Supersession relation
4. Agent-local state status
5. Provenance logging
6. State-aware retrieval/context construction
7. Deterministic evaluator

## Nice to Have

- model-visible provenance；
- explicit timestamps；
- DAR comparison；
- limited dependency propagation；
- reasoning-vs-state separation；
- replay-based message influence score。

## Do Not Implement Yet

- StateMem TurnEncoder clone；
- general-purpose semantic state extraction；
- dependency graph over arbitrary natural language；
- learned stale detector；
- learned router；
- RL；
- fine-tuning；
- LLM judge；
- >3 Agents；
- >2 major debate rounds；
- graph DB；
- complex consensus architecture。

> **注意：后续人工冻结修改进一步将 Method contribution 降级为 secondary minimal mitigation；最终 Method Boundary 以 `RESEARCH_CONTRACT.md` 为准。**

---

# 13 Minimum Sufficient Experiment Set

Stage-01 review 判断：在冻结预算下，**核心 claim 可以验证**，但只支持 short-horizon controlled stale propagation，不能支持 large-scale epidemic cascade / long-horizon network dynamics。

## E0 — Sanity Test

**10–20 scenarios**

验证：

1. old state 在 update 前能被模型正确使用；
2. current state 单独给模型时能正确使用；
3. 加入 stale peer message 后至少存在非零 regression。

如果第 3 点不存在，不进入 pilot。

## E1 — Stale vs Static Error

对应 H1，同时是 MAD-M² novelty gate。

同一 scenario：

- static wrong；
- once-correct → stale；
- current；
- no exposure。

**30–50 scenarios。**

## E2 — Propagation / Consensus

对应 H2。

用 E1 已缓存的 stale messages：

- one source；
- secondary copy；
- stale/current majority mirror。

只重新调用 downstream Agent，不需要重新生成 upstream trajectory。

## E3 — Source Correction / Residue

对应 H3。

利用同一批 trajectories：

1. source 首先传播 v1；
2. source 获得 v2；
3. v2 correction 对其他 Agent 可见；
4. 检查 secondary Agent；
5. 检查 corrected source 是否被 secondary stale message 带回 v1。

## E4 — Minimal State-MAD

对应 H4。

比较：

- naive MAD；
- MAD-M²；
- State-MAD；
- length/token-matched sham metadata。

全部尽量复用 E1–E3 的 message cache。

> **注意：这是 Stage-01 review 的 ARCHIVED hypothesis-level experiment sufficiency 记录。后续具体实验设计不由本文件授权，必须以冻结 Research Contract 为边界。**

---

# 14 Fatal Risks

Stage-01 review 列出的 Fatal / Hold risks：

## Fatal Risk 1 — Stale indistinguishable from static error

如果 matched experiment 中：

\[
\text{stale}\approx\text{static wrong}
\]

并且 MAD-M² 同样有效，则“stale 是另一种 wrong memory” objection 基本成立。

## Fatal Risk 2 — No communication-specific propagation

如果拥有 current state 的 Agent 在“有 stale peer”和“无 stale peer”条件下结果没有差异，则 multi-agent propagation claim 失败，剩下的是 StateMem-style tracking。

## Fatal Risk 3 — No residual after visible correction

如果 source correction 一旦可见，secondary stale belief 消失，corrected source 不会重新回退，则 RQ3 的主要新现象不成立。

## Fatal Risk 4 — State-MAD gain is metadata/context

如果 random version labels、neutral extra tokens、sham metadata 获得相同提升，则 RQ4 mechanism claim 失败。

## Fatal Risk 5 — Identity / majority fully explains the effect

若 anonymization 或 majority matching 后 stale effect 基本消失，则观察到的主要不是 temporal validity failure。

## Fatal Risk 6 — External literature closes the remaining gap

如果后续完整 related-work audit 发现已有工作同时研究 natural-language inter-agent stale copying、secondary retransmission、false consensus、source correction 后 residue，则应重新评级为 C/D。

Stage-01 review 当时的结论仍是：**B — Distinct but Vulnerable**。

---

# 15 Original Research Contract Draft

以下为 Stage-01 review 当时输出的原始 `RESEARCH_CONTRACT_DRAFT`，仅作归档。后续人工冻结修改已在文末单独记录，并由 `RESEARCH_CONTRACT.md` 覆盖。

## Problem

Multi-agent LLM systems may hold different temporal versions of the same state. A fact that was correct when generated can become superseded after a legitimate update, yet remain present in Agent memories and inter-agent messages.

## Gap

Existing work separately establishes:

- erroneous-memory vulnerability in MAD；
- evolving-state / supersession failures in Agent memory；
- post-removal adversarial residue；
- message filtering and identity-driven conformity。

What remains insufficiently characterized is:

> **whether a superseded but once-correct state is causally adopted and re-transmitted through natural-language multi-agent debate, produces false consensus, and persists after the original source has been visibly corrected.**

Broad “multi-agent stale propagation” itself was not treated as safely claimable as novel in the Stage-01 review.

## Novelty Claim

Primary contribution:

> **Phenomenon + measurement**, not architecture.

State-MAD studies **message-mediated stale-state contagion and post-correction residual stale belief** under controlled heterogeneous state visibility.

Secondary contribution:

> a minimal state-aware memory policy showing that stale state should lose current authority without requiring deletion of historical messages.

## RQ1

Stale state 是否以及如何通过 inter-agent communication 传播？

## RQ2

哪些因素影响 propagation 与 false consensus？

## RQ3

source 被纠正且 correction 可见后，是否仍有 residual stale belief / re-infection？

## RQ4

state-aware memory handling 是否促进 recovery？

## H1

Current-aware Agents exposed to stale peer messages exhibit higher stale adoption than matched controls.

## H2

Secondary transmission / stale support increases system-level stale prevalence or false consensus.

## H3

Visible source correction does not necessarily eliminate secondary stale belief or prevent re-infection.

## H4

State-aware supersession/retrieval reduces stale propagation beyond MAD-M² and token/metadata-matched controls.

## Method Boundary

**Include only:**

- deterministic fact identity；
- version/order；
- supersession；
- local status；
- provenance logging；
- state-aware retrieval/context construction；
- archived historical messages。

**Exclude:**

- RL；
- fine-tuning；
- learned router；
- learned memory scorer；
- general LLM state extraction；
- large dependency graph；
- complex topology；
- large judge model。

## Baseline Boundary

**Must:**

- no-peer / no-communication；
- naive MAD；
- MAD-M²；
- static-wrong matched condition；
- sham metadata / length-matched control。

**Pilot-only if needed:**

- DAR filtering comparison；
- anonymization identity control。

StateMem and PLR are primarily **scientific comparators**, not systems that must be fully transplanted into the codebase.

## Evidence Required

The project does **not** pass novelty validation without all four:

1. stale-vs-static-error matched evidence；
2. communication-specific adoption / retransmission evidence；
3. visible-correction residual evidence；
4. state-aware-vs-metadata/context control。

## Resource Budget

- ≤3 Agents；
- ≤2 main debate rounds；
- sanity 10–20；
- pilot 30–50；
- stage-2 100；
- final 200–300；
- first phase one open 7B/8B model；
- final ≤2 model families；
- deterministic grading；
- all messages cached；
- record seed/model/prompt/config/token usage/raw trajectories；
- offline replay whenever possible。

## Stop Conditions

**STOP / HOLD if two or more occur:**

- stale behaves no differently from static wrong；
- peer communication does not increase stale adoption；
- visible source correction eliminates residue completely；
- State-MAD is not better than token/metadata-matched controls；
- identity/majority explains the apparent stale effect；
- additional literature is found that already covers debate-mediated retransmission + post-correction residual。

---

## Post-Review Human Revisions

以下三项是在 Stage-01 review 完成后，由人工明确提出并冻结的修改。它们**不是 ARS 原始结论的回写**，而是对后续 Research Contract 的权威覆盖。

### Revision 1 — Propagation frozen as causal adoption in a current-aware target

Propagation 不再使用宽泛的“旧状态存在/传播”定义，而冻结为：

> **只有当 target Agent 已经获得或能够访问 current state \(v_{new}\)，并在暴露于 peer 提供的 stale / superseded state 后，相对于 matched control 更可能采用 \(v_{old}\)，才计为 stale-state propagation。**

形式化：

\[
P(A_j \rightarrow v_{old}\mid A_j\ knows\ v_{new},\ stale\ peer\ exposure)
>
P(A_j \rightarrow v_{old}\mid A_j\ knows\ v_{new},\ matched\ control)
\]

以下不再计为 propagation：

- Agent 没收到 update；
- retrieval 没取到 current；
- Agent 本来不知道 \(v_{new}\)；
- single-agent stale persistence；
- 没有 peer exposure；
- 没有 matched control。

### Revision 2 — RQ3 frozen as correction-visible residue

RQ3 不再接受仅仅“source 被移除/纠正”的宽泛条件，而冻结为：

> **source corrected + source no longer treats \(v_{old}\) as current + correction delivered + correction visible/accessible to target + measurement occurs afterward。**

只有在上述条件之后，target 仍采用、传播 \(v_{old}\)，或 secondary stale copies 使已纠正 Agent 再次回退，才计为 residual stale belief / retransmission / re-infection。

### Revision 3 — Method contribution downgraded to minimal mitigation

State-MAD 不再把以下组件作为主要 novelty claim：

- state identity；
- version；
- provenance；
- supersession；
- active / stale / conflicting status；
- state-aware retrieval。

冻结后的贡献层级是：

**Primary contribution:**

- phenomenon / problem formulation / controlled measurement；
- causal stale adoption；
- secondary retransmission；
- false stale consensus；
- correction-visible residual stale belief / possible re-infection。

**Secondary contribution:**

- **minimal supersession-aware mitigation**。

核心 intervention：

> **A superseded factual state loses authority as the current state, but its historical message does not need to be physically deleted.**

---

**Archive note:** For all future work, `RESEARCH_CONTRACT.md` is authoritative where any conflict exists.
