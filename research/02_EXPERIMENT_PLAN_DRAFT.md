# State-MAD Experiment Plan — Draft

Status: DRAFT — PENDING STAGE-03 REVIEW  
Stage: 02-ARIS-Experiment-Design

Authority Notice:

This file is the Stage-02 experiment-plan draft.  
It is NOT the final implementation contract.

After Stage 03, EXPERIMENT_PLAN_FROZEN.md  
will supersede this file.

If this file conflicts with RESEARCH_CONTRACT.md,  
RESEARCH_CONTRACT.md has higher authority.

Stage-02 File State Note:

This was the file state observed during Stage 02.  
If RESEARCH_CONTRACT.md has since been created,  
the formal Research Contract supersedes the  
chat-embedded contract text used during Stage 02.

# EXPERIMENT_PLAN

先说明一个文件状态：我没有把不存在的文件当作“已读”。当前可检索的 Project 上传文件，以及已连接的 `perterYang-wq/State-MAD` `main` branch 全量 tree 中，都没有出现 `RESEARCH_CONTRACT.md`；当前仓库仍基本保持 MAD-M² 的代码结构。fileciteturn10file0L1-L2 因此，本计划把**你本轮消息中完整给出的冻结 RQ、定义、贡献边界和资源限制**视为最高优先级 Research Contract 文本。进入 Codex 实现前必须先定位/补入正式 `RESEARCH_CONTRACT.md` 并做一致性检查；如有差异，以正式冻结文件为准。

下述设计不增加 RQ，不引入新的 major method component。Project Sources 已明确：MAD-M² 是工程底座，StateMem 是 evolving-state/benchmark 参考，PLR 是 residue 对照，Wrong-but-Useful 是 caching/replay 方法参考，Identity Bias 工作主要提供“failure mode → metric → controlled test → lightweight mitigation”的实验组织范式。fileciteturn7file17

---

## 1. Experimental Principles

### 1.1 第一阶段只回答“failure mechanism 是否存在”

核心证据链冻结为：

\[
\text{current acquired}
\rightarrow
\text{stale peer exposure}
\rightarrow
\text{stale adoption}
\rightarrow
\text{secondary retransmission}
\rightarrow
\text{false stale consensus}
\]

以及 recovery 链：

\[
\text{source correction}
\rightarrow
\text{correction visible}
\rightarrow
\text{residual stale belief?}
\rightarrow
\text{retransmission/reinfection?}
\]

不会把普通错误、没看到 update、忘记 current state、或者 source 本身持续输出 stale 全都叫 propagation。

这也是 State-MAD 与 MAD-M² 的关键边界：MAD-M² 明确研究 previous-round **erroneous memories** 如何误导后续 Agent；其典型例子是一个 Agent 本来答对，却被另一条错误推理带错。fileciteturn8file0 State-MAD 第一阶段必须保证 seed stale message 在生成时是正确的，只是在后续 supersession 后变 stale。

### 1.2 使用行为级 current-awareness gate

不能仅仅因为 prompt 中出现过 `v_new` 就称 target 为 current-aware。

每个 target 在 treatment 前建立一个：

```text
target_current_snapshot
```

然后从同一 snapshot 分叉：

```text
branch A → awareness probe
branch B → no-peer
branch C → current-peer
branch D → stale-peer
branch E → static-wrong
```

`awareness probe` 必须回答 `v_new` 才进入 SAR/CSAE denominator。

**关键点：awareness probe 的模型输出不写回 treatment history。**

因此它能验证 target 的 current-awareness，但不会因为“刚刚自己说过一次 v_new”而额外 priming treatment。所有 treatment/control 都从同一个 pre-probe snapshot 分叉。

这种 matched disagreement / simple-peer 的设计思路也符合 identity-bias 工作中用最简单 single-peer disagreement setting 隔离 peer influence 的原则。fileciteturn9file2

### 1.3 第一阶段固定配置

第一阶段默认：

- Model：`Qwen2.5-7B-Instruct`
- homogeneous agents
- temperature = `0`
- top_p = `1.0`
- max_new_tokens：建议 `64–96`
- agents：E0/E1 ≤2，E2/E4 ≤3
- main debate rounds：≤2
- Sanity：16 scenarios
- Pilot：40 scenarios
- 只有 1 个 model checkpoint
- 不做 multi-model sweep
- 不做 fine-tuning / RL
- 不做 LLM-as-a-Judge grading
- 不进行 benchmark expansion

选择 Qwen2.5-7B-Instruct 是因为它位于冻结的 7B/8B 资源范围内，而且是 MAD-M² 官方实验模型之一；MAD-M² 的默认 MAD 设置也是 3-agent、2-round。fileciteturn7file0

### 1.4 Seed exposure 与 downstream behavior 分离

第一阶段的核心因果测量不能依赖 source Agent 偶然生成什么。

对于每个 scenario：

1. `m_old` 在 `v_old` 仍为 current 时产生并缓存；
2. update 发生；
3. target 获得 `v_new`；
4. treatment 把**同一条已经缓存的 `m_old`**重新暴露给 target。

因此 treatment 的 stale message 在生成时是真实、正确的。

`static-wrong` 则使用一个从未属于该 `fact_id` current history 的 `v_wrong`。

这就是：

```text
stale = once-correct → superseded
static-wrong = never-current
```

不能混合。

### 1.5 Closed-pool + deterministic grading

StateMemBench 的一个关键优点是 closed-pool 可以机械地区分 current、superseded 和其他错误，并把 state tracking 与一般 retrieval/error 分开。fileciteturn8file1

State-MAD 第一阶段直接采用更简单版本：

```text
Question: What is the CURRENT value of fact F?
(A) ...
(B) ...
(C) ...
(D) ...
```

选项位置每 scenario 随机 permutation。

模型只允许：

```xml
<answer>A</answer>
```

评分程序直接从 `answer label → symbolic value` 映射：

```text
CURRENT
STALE
STATIC_WRONG
OTHER/INVALID
```

不需要 LLM judge。

---

# 2. Operational Definitions

设一个 state identity：

\[
f
\]

具有：

\[
v_1=v_{old}
\]

以及 update：

\[
v_1 \xrightarrow{\text{superseded by}} v_2=v_{new}
\]

### Current-aware Target

Target \(A_t\) 只有在 treatment 前，从 identical state snapshot 单独执行 awareness probe 并输出 \(v_{new}\)，才标记：

```text
current_aware = true
```

仅“prompt 中包含 v_new”不够。

### Stale Peer Exposure

peer message \(m_s\)：

- 在 \(v_{old}\) 仍有效时产生；
- 后续发生 \(v_{old}\to v_{new}\)；
- decision time 仍把 \(v_{old}\) 作为当前答案传给 target。

### Causal Stale Adoption

如果 current-aware target 在 stale-peer treatment 下输出：

\[
v_{old}
\]

并且 matched stale exposure 相对于 matched control 提高这种概率，才支持 propagation。

### Secondary Retransmission

Target \(A_t\) 因 stale peer exposure 采用 \(v_{old}\) 后，其**真实生成且已缓存**的 message 被发送给另一个 current-aware Agent \(A_r\)。

若 \(A_r\) 随后输出 \(v_{old}\)，构成 secondary retransmission。

### False Stale Consensus

默认按 MAD system decision 的 majority rule 定义：

\[
\operatorname{mode}(y_1,y_2,y_3)=v_{old}.
\]

同时必须分两类：

```text
ordinary stale consensus
```

至少存在形成 majority 的 Agent 并非 current-aware，不能归因于传播；

以及：

```text
peer-induced false stale consensus
```

至少有一个组成 stale majority 的 current-aware Agent 是经过 causal stale exposure 后转向 stale。

另外记录 `strict_unanimous_stale`，但它只作为 diagnostic，不作为 headline FSCR，以避免 3-agent pilot 中过于稀疏。

### Correction-Visible Residue

只在以下全部成立时：

```text
prior stale exposure
+
prior stale adoption
+
source corrected
+
source emits/commits current
+
correction visible to target
+
correction accessible at target decision time
```

target 仍输出 \(v_{old}\)，才算 CV residue。

PLR 工作强调 post-removal persistence 必须与 active source effect 分开，并需要 matched clean reference；State-MAD 在这里进一步加强为 **correction-visible** residue。fileciteturn9file0

### Re-infection

若 source 已经：

```text
corrected → outputs v_new
```

随后收到 correction-visible target 残留的 stale message，并重新输出 \(v_{old}\)，记为 re-infection。

---

# 3. Metrics

| Metric | Numerator | Denominator | Inclusion criteria | Exclusion criteria | Deterministic rule |
|---|---|---|---|---|---|
| **SAR** | post-exposure 输出 `v_old` 的 current-aware target 数 | 所有完成该 arm inference 的 current-aware target | awareness probe=`v_new` | 仅 infrastructure failure，如 OOM/请求未完成 | `answer_class == STALE` |
| **CSAE** | paired scenario 中 `I(stale_treat)-I(control)` 的总和 | 两个 arm 均有效的 paired scenarios | current-aware，same scenario/snapshot | 任一 arm infrastructure failure | `mean(I_stale-I_control)` |
| **SRR** | relay Agent 输出 `v_old` | 所有 E1 target 已 stale-adopt 且其 message 被实际发给 current-aware relay 的 cases | primary stale adoption + relay current-aware | upstream 未采用 stale；relay awareness fail | relay `answer_class==STALE` |
| **FSCR** | final majority=`v_old` | complete 3-agent system cases | 所需 target current-awareness 已验证 | infrastructure incomplete | deterministic majority |
| **CVRR** | correction-visible 后 target 仍输出 `v_old` | prior stale adopters 中满足完整 correction-visible 条件的 cases | source corrected + correction accessible | correction source 未正确更新；target 从未采用 stale | exact stale answer |
| **Re-infection Rate** | corrected source 再次输出 `v_old` | source 已 corrected 且实际收到 residual stale target message 的 cases | CV residual message exists | source correction verification failed | exact stale answer |
| **Current-State Accuracy** | designated decision 输出 `v_new` | designated valid decisions | 按 experiment 的 eligibility | infrastructure failure | exact current answer |
| **Token Usage** | total input/output/combined tokens | completed call 或 scenario-method | 全部 model calls | none | tokenizer/API usage counter |

CSAE 的 **primary matched control 冻结为 current-peer control**：

\[
CSAE =
SAR_{\text{stale-peer}}
-
SAR_{\text{current-peer}}.
\]

同时必须报告两个辅助 contrast：

\[
SAR_{\text{stale}}-SAR_{\text{no-peer}}
\]

以及：

\[
SAR_{\text{stale}}-SAR_{\text{static-wrong}}.
\]

最后一个不是新 headline metric，而是 stale-specificity / MAD-M²-overlap diagnostic。

对于 FSCR 必须分别输出：

```text
ordinary_stale_consensus_rate
peer_induced_false_stale_consensus_rate
```

不能把两者合并成同一个现象。

对于 Token Usage 同时保留：

```text
input_tokens
output_tokens
total_tokens
calls
tokens_per_call
tokens_per_scenario
tokens_per_method
cache_hits
```

Invalid format 不从 denominator 删除，而分类为 `OTHER/INVALID`，因此 SAR numerator 不增加，但 Current-State Accuracy 会把它视为错误。

---

# 4. Scenario Schema

第一阶段只需要 direct factual supersession，不需要依赖图、derived reasoning、semantic parser。

建议冻结为类似：

```json
{
  "scenario_id": "pilot_0001",
  "split": "pilot",
  "generator_seed": 2001,
  "template_id": "direct_state_categorical_v1",

  "fact": {
    "fact_id": "fact_0001",
    "state_type": "categorical",
    "entity": "Project Orion",
    "attribute": "deployment_zone"
  },

  "versions": [
    {
      "version_id": "v1",
      "value": "Amber",
      "valid_from_event": "e01",
      "superseded_by": "v2"
    },
    {
      "version_id": "v2",
      "value": "Cobalt",
      "valid_from_event": "e03",
      "superseded_by": null
    }
  ],

  "static_wrong": {
    "value": "Silver",
    "was_ever_current": false
  },

  "update_event": {
    "event_id": "e03",
    "fact_id": "fact_0001",
    "from_version": "v1",
    "to_version": "v2"
  },

  "agents": {
    "source": "agent_1",
    "target": "agent_2",
    "relay": "agent_3"
  },

  "visibility": {
    "source_sees_v1": true,
    "target_sees_update": true,
    "relay_sees_update": true,
    "target_sees_stale_peer": true,
    "relay_sees_target_message": true,
    "target_sees_correction": false
  },

  "event_order": [
    "e01_establish_v1",
    "e02_source_message_v1",
    "e03_update_to_v2",
    "e04_target_current_snapshot",
    "e05_peer_exposure",
    "e06_target_decision"
  ],

  "answer_pool": {
    "A": "Cobalt",
    "B": "Silver",
    "C": "Amber",
    "D": "Other"
  },

  "ground_truth": {
    "current_version": "v2",
    "current_value": "Cobalt",
    "stale_value": "Amber",
    "static_wrong_value": "Silver"
  },

  "message_lineage": [
    {
      "message_id": "m_source_old",
      "author": "agent_1",
      "fact_id": "fact_0001",
      "version_id": "v1",
      "generated_when_current": true,
      "later_status": "stale"
    }
  ],

  "replay": {
    "target_snapshot_id": "snap_target_current_0001",
    "relay_snapshot_id": "snap_relay_current_0001"
  }
}
```

必须有 validator 在任何 model call 前验证：

```text
v_old != v_new
v_wrong != v_old
v_wrong != v_new
v_old was once current
v_new is current at decision time
target sees v_new before treatment
answer option mapping is one-to-one
event order is acyclic
stale treatment references m_source_old
```

StateMemBench 同样通过 symbolic event program 和 deterministic replay 确定 gold，而不是让 judge 事后猜 failure mechanism。fileciteturn8file1

---

# 5. E0 Sanity Test

| Field | Specification |
|---|---|
| **Hypothesis** | H0-Sanity：简单 direct state 条件下模型能可靠持有 `v_new`，同时 stale peer 至少能诱发可测 regression signal |
| **Independent Variable** | no-peer / current-peer / stale-peer / static-wrong |
| **Dependent Variable** | awareness success、SAR、Current-State Accuracy |
| **Matched Control** | primary = current-peer；secondary = no-peer |
| **Confounds controlled** | same target snapshot、same question、same option mapping、same peer identity/format、probe output不写回 |
| **Scenario count** | 16 |
| **Agents** | 2 |
| **Rounds** | current snapshot + 1 exposure round |
| **Model** | Qwen2.5-7B-Instruct |
| **Calls required** | upper bound ≈ 8/scenario = 128 |
| **Cache reusable?** | Yes |
| **Offline analysis?** | 完全可以 |
| **Expected artifact** | `e0_calls.jsonl`, `e0_predictions.jsonl`, `e0_metrics.csv`, run manifest |
| **Estimated token cost** | 约 35k–50k total tokens |

### E0 pass criterion

必须同时：

```text
current-awareness >= 80%
```

即至少约 `13/16` target 能在 awareness probe 回答 `v_new`；

并且：

```text
≥ 3 confirmed stale-treatment regressions
```

且：

```text
SAR(stale) - SAR(current-peer) >= 0.10
```

这是 **sanity go gate**，不是论文显著性阈值。

### E0 failure / stop

如果：

```text
0 confirmed stale regressions
```

则直接停止进入 Pilot。

如果 current-awareness `<50%`，说明 benchmark/model 无法稳定完成最基本 state acquisition，也停止。

如果出现 signal 但极弱：

```text
0 < CSAE < 0.10
```

标为 `AMBIGUOUS`，不自动增加 scenarios，不自动换模型；进入人工决定。

---

# 6. E1 Causal Adoption

E1 是第一阶段最关键实验。

### Event sequence

```text
t0: v_old current
t1: source produces m_old
t2: update v_old -> v_new
t3: target receives v_new
t4: create target_current_snapshot
t5: independently verify target awareness
t6: branch four experimental arms
t7: target decision
```

因此 `m_old` 是**在产生时正确**，而非 generation-time erroneous。

### Four arms

**No-peer**

```text
target history + no peer message
```

**Current-peer**

```text
same target snapshot + peer states v_new
```

**Stale-peer**

```text
same target snapshot + cached m_old stating v_old
```

**Static-wrong**

```text
same target snapshot + peer message stating v_wrong
where v_wrong was never current
```

| Field | Specification |
|---|---|
| **Hypothesis** | H1：stale peer exposure 对 current-aware target 产生正 CSAE |
| **Independent Variable** | peer memory temporal status，4 levels |
| **Dependent Variable** | SAR、CSAE、Current-State Accuracy |
| **Matched Control** | current-peer primary |
| **Confounds controlled** | identical target snapshot、model、question、answer pool、identity labels、prompt skeleton |
| **Scenario count** | 40 pilot scenarios |
| **Agents** | 2 |
| **Rounds** | 1 exposure round |
| **Model** | Qwen2.5-7B-Instruct |
| **Calls required** | upper bound ≈ 320 calls |
| **Cache reusable?** | 全部 upstream + branch outputs 均可缓存 |
| **Offline analysis?** | Yes |
| **Expected artifact** | paired arm matrix + raw trajectories + causal transition table |
| **Estimated token cost** | 95k–130k |

### Primary analysis

每 scenario 生成：

```text
no_peer_stale
current_peer_stale
stale_peer_stale
static_wrong_stale
```

形成完全 paired matrix。

Primary effect：

\[
CSAE =
\frac{1}{N}
\sum_i
[
I(y_i^{stale}=v_{old})
-
I(y_i^{current}=v_{old})
].
\]

### E1 pass criterion

Pilot Go：

```text
eligible current-aware targets >= 30
AND
CSAE >= 0.10
AND
at least 5 treatment-only stale transitions
```

这里的 “treatment-only transition” 是：

```text
stale-peer = STALE
current-peer != STALE
```

### E1 failure criterion

若至少有 30 个 eligible scenarios，但：

\[
|CSAE| < 0.05
\]

则把 propagation effect 视为 practically near-zero：

```text
RQ1 causal propagation claim unsupported
```

不进入更大规模 propagation experiment。

### Static-wrong gate

必须比较：

\[
SAR_{\text{stale}}
\quad vs \quad
SAR_{\text{static-wrong}}.
\]

如果：

```text
|difference| < 0.05
```

并且两 arm 的 per-scenario behavior 高度一致，例如 `>=90%` concordance，则记录：

```text
STALE-SPECIFICITY NOT SUPPORTED
MAD-M² novelty overlap risk
```

此时不能把结果写成 stale-specific phenomenon。

需要人工决定是否值得继续；不能自动增加新机制来“救” novelty。

---

# 7. E2 Secondary Retransmission

E2 不重新生成 E1 target messages。

这是整个 cache 设计最重要的一处。

Wrong-but-Useful 的 replay protocol 明确将 message pool 固定，只改变 downstream solver 是否获得某条 cached message，从而避免重新生成 upstream message 引入 attribution confound。fileciteturn8file2

State-MAD 采用同样原则：

```text
source -> target output
```

一旦在 E1 生成，立即冻结。

然后：

```text
cached target output -> relay Agent
```

### Chain

```text
Agent S: cached once-correct stale seed
        ↓
Agent T: current-aware primary target
        ↓
Agent R: independently current-aware relay
```

只有 `T` 在 stale treatment 下实际采用 stale 的 cases 才进入 SRR denominator。

| Field | Specification |
|---|---|
| **Hypothesis** | H2：causally stale-adopting T 可以成为新的 stale transmitter |
| **Independent Variable** | cached upstream message 来自 stale / current / static-wrong / no-peer E1 branch |
| **Dependent Variable** | SRR、FSCR、Current-State Accuracy |
| **Matched Control** | relay receives cached T output from current-peer E1 branch |
| **Confounds controlled** | same relay snapshot、same target identity、no upstream regeneration |
| **Scenario count** | candidate pool = same 40 |
| **Agents** | 3 |
| **Rounds** | E1 first hop + E2 second hop，≤2 main rounds |
| **Model** | same 7B |
| **Calls required** | ≤200 new downstream calls |
| **Cache reusable?** | E1 upstream 100% reused |
| **Offline analysis?** | all metrics after calls are offline |
| **Expected artifact** | hop-level lineage matrix |
| **Estimated token cost** | 65k–90k |

### SRR eligibility

必须：

```text
T current-aware
AND
T received stale peer
AND
T output v_old
AND
T's exact cached output is sent to R
AND
R independently demonstrated current-awareness
```

然后：

```text
R -> v_old
```

才计 secondary retransmission。

### False stale consensus

三 Agent 最终状态使用 deterministic majority。

报告：

```text
ordinary stale consensus
peer-induced false stale consensus
strict unanimous stale (diagnostic)
```

其中 peer-induced 必须能沿 lineage 回溯至少一个：

```text
current-aware → stale exposure → stale adoption
```

不能仅因为 2/3 最终都错就归因传播。

### E2 pass criterion

Secondary retransmission claim 的 pilot gate：

```text
>= 8 eligible primary stale adopters
AND
>= 2 confirmed second-hop stale adoptions
AND
SRR(stale lineage) > matched current-peer lineage
```

如果有：

```text
>= 2 peer-induced stale-majority scenarios
```

则允许继续保留 false-consensus claim。

### E2 failure / stop

若有至少 10 eligible stale-adopting transmitters，但：

```text
secondary stale retransmission = 0
```

则停止 secondary retransmission claim。

如果 secondary transmission 存在、但 stale majority 始终为 0，则只支持 propagation，不支持 false stale consensus。

如果 E1 本身产生 `<8` eligible adopters，E2 标为：

```text
NOT ESTIMABLE AT PILOT SCALE
```

而不是自动扩数据。

---

# 8. E3 Correction-Visible Residue

E3 只运行在 E1 中实际 stale-adopt 的 targets。

所以严格来说：

```text
candidate pool = 40
executed residue pool = N_prior_stale_adopters
```

不会为了凑 denominator 重新构造“假 infected” target。

### Three required conditions

#### A. Source uncorrected

```text
source continues stale
correction does not occur
```

这个 condition 只能说明 persistent exposure。

**不能支持 RQ3。**

#### B. Source corrected, correction invisible

```text
source switches to current
target cannot see correction
```

这个 condition 可以区分 source state 和 target information access。

**仍不能支持 RQ3。**

#### C. Source corrected + correction visible

```text
source switches to v_new
source correction verified
correction message enters target-accessible state
target decision happens afterward
```

只有 C 可以计算 headline CVRR。

### Source correction verification

建议 source correction 同样采用 snapshot branching：

```text
source correction snapshot
    ├── correction verification probe
    └── emitted correction message
```

只有 source 输出 `v_new` 才满足：

```text
source_corrected=true
```

### Matched clean reference

另外使用 E1 的 **current-peer branch history** 建立 `C_clean`：

```text
never stale-adopted
+
same correction
+
same visibility
+
same decision prompt
```

这不是新增 baseline，而是 E1 clean branch 的 downstream replay。

| Field | Specification |
|---|---|
| **Hypothesis** | H3：即使 correction visible，部分 previously induced stale beliefs 仍可能残留 |
| **Independent Variable** | A uncorrected / B corrected-invisible / C corrected-visible |
| **Dependent Variable** | CVRR、SRR after correction、Current-State Accuracy、Re-infection |
| **Matched Control** | C_clean |
| **Confounds controlled** | same prior infected message、same target snapshot、same correction content |
| **Scenario count** | all E1 prior stale adopters，max 40 |
| **Agents** | ≤3 |
| **Rounds** | post-exposure correction/recovery phase，不增加 main debate round |
| **Model** | same |
| **Calls required** | roughly `4 × N_adopter + reinfection calls` |
| **Cache reusable?** | E1 histories/messages 全部复用 |
| **Offline analysis?** | Yes after downstream calls |
| **Expected artifact** | A/B/C recovery transition matrix |
| **Estimated token cost** | expected 30k–60k；worst-case ≈110k |

### CVRR

\[
CVRR =
\frac{
\#(\text{prior stale adopter remains stale under C})
}{
\#(\text{eligible correction-visible prior stale adopters})
}.
\]

### RQ3 pass criterion

至少：

```text
N_C_eligible >= 10
```

且：

```text
CVRR_C >= CVRR_clean + 0.10
```

并至少存在：

```text
2 correction-visible residual stale cases
```

才把 RQ3 作为 pilot-positive。

### RQ3 failure criterion

如果：

```text
|CVRR_C - CVRR_clean| < 0.05
```

且没有 correction-visible retransmission，则：

```text
RQ3 unsupported
```

即 stale effect 在 correction visible 后已经恢复到 clean baseline。

这必须作为完全合法的论文结果，而不能引入更复杂 memory architecture 强行制造 residue。

---

## Re-infection nested test

仅当 C 中真的存在 residual stale target 时运行。

事件：

```text
S was stale
→ S corrected
→ S verified v_new
→ T still emits v_old after seeing correction
→ cached T residual message returned to S
→ test S again
```

如果：

```text
S -> v_old
```

则 re-infection。

Matched replay：

```text
same corrected S snapshot
without residual T message
```

用于确认不是 source 自己自然回退。

如果 residual cases `<5`，Re-infection Rate 仍记录，但不能作为独立 paper claim。

---

# 9. E4 Minimal Mitigation

RQ4 不以“State-MAD 打败所有 baseline”为前提。

它只问：

> 一个 minimal supersession-aware intervention 是否降低已经被 E1–E3 证明存在的 failure mode？

### Baselines 固定四个

```text
1. Vanilla MAD
2. MAD-M²
3. State-MAD minimal
4. token/length-matched sham metadata
```

不增加 DAR、graph memory、RL、RAG 等 baseline。

MAD-M² 的原方法在 round 间做 evaluation + masking，并有 subjective / objective variants。fileciteturn8file0 对当前单一 Qwen2.5-7B 第一阶段，建议只实现：

```text
MAD-M² subjective, loose
```

即：

```text
YES -> keep
NO -> mask
NOT SURE -> keep
```

而不再跑 objective variant；MAD-M² 自己的分析也显示弱 7B 上 strict subjective rule 可能降低表现。fileciteturn7file0

这不是额外 LLM judge，而是复现 baseline 本身的 masking mechanism。

---

## State-MAD minimal mitigation

不实现复杂 memory system。

场景的 state identity / version / provenance / supersession 都来自 benchmark gold schema，不由 LLM 推断。

在 answer/debate context 中增加一个 deterministic state block，例如：

```text
FACT: F017
active_version: v2
active_value: Cobalt

peer_memory:
version: v1
status: superseded
superseded_by: v2
source: agent_1
```

并使用一个最小规则：

```text
When multiple versions refer to the same fact,
use the active version.
A superseded version may be historical evidence,
but must not be treated as the current state.
```

不新增 classifier、judge、graph inference、learned retriever。

这是 mitigation，不作为 representation novelty。

### Sham metadata

Sham 与 State-MAD：

```text
same model
same messages
same answer pool
same number of metadata fields
same prompt position
same token budget, target ±3 tokens
```

但字段变成无 temporal semantics 的 opaque metadata，例如：

```text
record_id
group_code
revision_code
source_code
flag_code
```

不能出现：

```text
current
stale
superseded
active
latest
```

StateMem 的 wrapper experiment 同样专门使用 length/cost-matched generic control 来区分“state structure 有效”与“只是多给了文字”。fileciteturn8file1

### E4 cache structure

Round-1 pool：

```text
generate once
freeze
```

四种 method 都看同一份 immutable messages。

仅重新运行 method-specific Round 2。

DAR 虽然不是 State-MAD baseline，但其 index-based retention 强调保留原始 messages 不改写，正好支持这里“selection/rendering intervention 不重新生成 upstream content”的工程原则。fileciteturn9file1

| Field | Specification |
|---|---|
| **Hypothesis** | H4：State-MAD minimal 降低已观测 stale failures，并优于 sham |
| **Independent Variable** | 4 method conditions |
| **Dependent Variable** | SAR / SRR / FSCR / CVRR / Current-State Accuracy / Tokens |
| **Matched Control** | Vanilla + token-matched sham |
| **Confounds controlled** | identical frozen R1 pool、same agents、same ordering、same downstream prompt budget |
| **Scenario count** | same 40 pilot |
| **Agents** | 3 |
| **Rounds** | 2 |
| **Model** | same 7B |
| **Calls required** | propagation slice ≤520 new calls；recovery slice conditional |
| **Cache reusable?** | Round-1 100% reusable |
| **Offline analysis?** | Yes |
| **Expected artifact** | method × scenario paired matrix |
| **Estimated token cost** | ≈180k–260k propagation；recovery additional ≤90k |

### E4 pass criterion

State-MAD mitigation 必须满足：

```text
failure metric vs Vanilla improves >= 0.10
```

以及至少：

```text
failure metric vs sham improves >= 0.05
```

同时 clean current-peer condition 下 Current-State Accuracy 不允许明显损伤：

```text
accuracy drop <= 0.05
```

Token budget 应与 sham 基本一致。

这组阈值是**建议预注册的 pilot Go/No-Go threshold**，不是来源论文给出的统计阈值。

### E4 failure

若：

```text
|State-MAD - sham| < 0.05
```

则：

```text
mitigation-specific claim unsupported
```

即便 State-MAD 比 Vanilla 好，也不能排除只是多 metadata / prompt volume。

State-MAD 不需要在 pilot 中显著优于 MAD-M² 才能保留 primary phenomenon contribution；mitigation 本来就是 secondary contribution。

---

# 10. Cache and Replay Strategy

这里冻结为：

```text
GENERATE ONCE
```

的对象包括：

- scenario symbolic program
- answer mapping
- `m_source_old`
- current peer message
- static-wrong peer message
- target current snapshot
- relay current snapshot
- E1 all branch outputs
- source correction
- E2 relay outputs
- E3 residual messages
- E4 Round-1 pool

之后凡是只改变：

```text
message visibility
message order
identity label
metadata rendering
mask
correction visibility
```

都**不得重新生成 upstream agent message**。

只重新运行受到 intervention 影响的 downstream Agent。

Wrong-but-Useful 的核心 measurement protocol 正是缓存 message pool，然后在 identical downstream integration context 中进行 available-vs-hidden replay。fileciteturn8file2

每个 cache key 至少包含：

```text
scenario_hash
agent_id
snapshot_hash
prompt_hash
model_id
model_revision
tokenizer_revision
temperature
seed
max_new_tokens
```

如果 key 完全一致：

```text
MUST REUSE CACHE
```

不得重新调用模型。

所有统计、bootstrap CI、表格、transition matrix、lineage analysis 都只能读取缓存，不再产生 token。

---

# 11. Logging and Reproducibility

每个 model call 建议输出 immutable JSONL record：

```json
{
  "run_id": "...",
  "experiment": "E1",
  "scenario_id": "...",
  "condition": "stale_peer",
  "agent_id": "agent_2",
  "snapshot_id": "...",

  "model": "Qwen2.5-7B-Instruct",
  "model_revision": "...",
  "tokenizer_revision": "...",

  "seed": 41,
  "temperature": 0.0,
  "max_new_tokens": 96,

  "system_prompt": "...",
  "user_prompt": "...",
  "prompt_hash": "...",

  "visible_message_ids": ["m_source_old"],
  "parent_message_ids": ["m_source_old"],
  "fact_id": "fact_0001",

  "raw_output": "...",
  "parsed_answer": "C",
  "answer_class": "STALE",

  "input_tokens": 312,
  "output_tokens": 18,
  "total_tokens": 330,

  "cache_hit": false,
  "latency_ms": 0,
  "status": "complete"
}
```

此外每 run 必须保存：

```text
git commit SHA
config SHA
scenario set SHA
prompt template SHA
Python version
torch version
transformers version
vLLM version if used
CUDA/GPU metadata
command line
start/end timestamp
```

Raw response 永远保留，parser output 是 derived field，不能覆盖 raw text。

---

# 12. Token / Compute Budget

在最终 prompt audit 前只能给 planning estimate，不应该伪造精确 compute 时间。

建议第一阶段 ceiling：

| Stage | Approx. calls | Approx. tokens |
|---|---:|---:|
| E0 | ≤128 | 35k–50k |
| E1 | ≤320 | 95k–130k |
| E2 | ≤200 | 65k–90k |
| E3 | conditional | 30k–110k |
| E4 propagation | ≤520 | 180k–260k |
| E4 recovery | conditional | 0–90k |

因此完整 sanity + 40-scenario pilot 的合理 planning envelope 为：

```text
~0.4M–0.7M total tokens
```

建议 hard ceiling：

```text
0.8M tokens
```

超过 ceiling 必须停止并重新审查，而不是自动继续。

实际值必须由 tokenizer 对**真实 prompt**计算后替换。

不预估 GPU-hours，直到 Repository Audit 确认：

```text
backend
quantization
GPU
batching
context length
vLLM configuration
```

否则 GPU-hour 数字没有可信依据。

---

# 13. Stop / Go Gates

建议正式冻结以下 gates：

**Gate 0 — Pre-implementation**

`RESEARCH_CONTRACT.md` 必须存在并与本轮冻结文本一致；完成 Repository Audit + Implementation Map 后才允许 Codex 写代码。

**Gate 1 — E0**

如果没有任何 stale regression：

```text
STOP
```

不进入 Pilot。

**Gate 2 — E1 causal adoption**

如果：

\[
|CSAE| < 0.05
\]

且有足够 eligible cases：

```text
STOP propagation claim
```

不得扩大 sample 来追信号。

**Gate 3 — stale specificity**

如果 stale 与 static-wrong：

```text
behaviorally indistinguishable
```

则：

```text
mark MAD-M² overlap / novelty risk
STOP stale-specific claim
```

需要人工决策。

**Gate 4 — E2 propagation depth**

若有足够 E1 adopters 但：

```text
SRR = 0
```

停止 secondary retransmission claim。

如果 SRR >0、FSCR=0，只保留 transmission，不保留 false-consensus claim。

**Gate 5 — E3 residue**

若 correction visible 后：

```text
CVRR_C ≈ clean baseline
```

则：

```text
RQ3 not supported
```

不增加复杂 persistent-memory mechanism。

**Gate 6 — E4 mitigation**

如果：

```text
State-MAD ≈ sham metadata
```

则：

```text
no State-MAD mitigation claim
```

Primary phenomenon claim 是否成立由 E1–E3 独立决定。

任何 `AMBIGUOUS` gate 都进入：

```text
需要人工决策
```

不能自动切模型、增加 agents、增加 rounds 或扩大数据量。

---

# 14. Minimal Final Tables and Figures

最终论文真正必要的结果表只保留三张：

### Table 1 — Causal stale adoption

列：

```text
Condition
Eligible N
SAR
Current-State Accuracy
CSAE vs current-peer
Delta vs static-wrong
Input tokens
Output tokens
```

四行：

```text
No Peer
Current Peer
Stale Peer
Static Wrong
```

这是 RQ1 + stale-vs-erroneous boundary 的核心表。

### Table 2 — Propagation and Recovery

列：

```text
Primary adoption
SRR
Ordinary stale consensus
Peer-induced FSCR
CVRR-A
CVRR-B
CVRR-C
Clean recovery
Re-infection
```

支持 RQ1–RQ3。

### Table 3 — Minimal Mitigation

四行：

```text
Vanilla MAD
MAD-M²
State-MAD
Sham Metadata
```

列：

```text
SAR
SRR
FSCR
CVRR
Current-State Accuracy
Total Tokens
```

支持 RQ4。

必要 figures 只需两个。

**Figure 1 — State-MAD causal protocol timeline**

```text
v_old valid
 ↓
source message generated
 ↓
update to v_new
 ↓
target obtains current
 ↓
matched stale/control exposure
 ↓
adoption
 ↓
retransmission
 ↓
correction
 ↓
residue / recovery
```

主要作用是让 reviewer 一眼看清“erroneous”与“stale”的区别。

**Figure 2 — Failure trajectory**

同一 panel 展示：

```text
1-hop SAR
→ 2-hop SRR
→ false consensus
→ correction-visible CVRR
```

按 treatment/control 做 paired rates + CI。

不需要单独制作：

- architecture figure
- token figure
- model sweep figure
- agent-count scaling figure
- round-count scaling figure
- LLM judge agreement figure

这些都不是第一阶段 claim 所必需。

---

# 15. Implementation Requirements Draft

这是下一阶段 Repository Audit 完成后交给 Codex 的**requirements draft**，现在不对应具体文件修改。

### A. Scenario compiler

必须能够：

```text
generate symbolic scenarios
validate supersession
freeze answer pool
randomize answer order
emit scenario JSONL
```

绝不能调用 LLM 解析 state identity。

### B. Snapshot-capable experiment runner

必须支持：

```text
create immutable agent snapshot
fork multiple matched branches
probe awareness without mutating parent snapshot
```

这是 causal design 最关键的 implementation requirement。

### C. Immutable message cache

每个 upstream message 生成一次。

API 至少逻辑上支持：

```text
get_or_generate(cache_key)
replay(message_id, downstream_snapshot)
```

同一 cache key 不允许 silent regeneration。

### D. Intervention renderer

只允许实现冻结条件：

```text
no-peer
current-peer
stale-peer
static-wrong
correction-hidden
correction-visible
Vanilla
MAD-M²
State-MAD
sham
```

不得自己加入第五个 mitigation。

### E. Deterministic grader

实现：

```text
parse <answer>X</answer>
map X -> symbolic value
classify CURRENT / STALE / STATIC_WRONG / OTHER
```

不调用 LLM。

### F. Lineage tracker

每条 message 必须知道：

```text
author
parent_message_ids
fact_id
version_id
generation-time validity
decision-time validity
recipients
```

这样 E2/E3 才能机械判断：

```text
primary adoption
secondary retransmission
re-infection
```

而不是事后读文本猜 contagion。

### G. Metric engine

应直接从 structured records 生成：

```text
SAR
CSAE
SRR
FSCR
CVRR
Re-infection
Current-State Accuracy
Token Usage
```

同一个 raw run 反复运行 metric code 不产生 model calls。

### H. Baseline adapters

只实现：

```text
Vanilla MAD
MAD-M² subjective-loose
State-MAD minimal
Sham metadata
```

MAD-M² 尽量直接复用现有 official code path，而不是重新实现 MAD。MAD-M² 原论文的核心就是在 previous-round memory 与下一 round generation 之间插入 evaluation/masking。fileciteturn8file0

### I. Reproducibility manifest

任何 run 没有：

```text
model
revision
seed
prompt
config
git SHA
scenario SHA
token usage
raw trajectories
```

都视为 invalid experimental run。

### J. Repository gate

下一步不是直接 Coding。

按照项目规则，顺序必须是：

```text
RESEARCH_CONTRACT verification
        ↓
Repository Audit
        ↓
Implementation Map
        ↓
minimal implementation
        ↓
unit tests / dry run
        ↓
E0 sanity
        ↓
只有 E0 PASS 才能进入 40-scenario Pilot
```

这份 plan 因而已经把第一阶段的 **measurement unit、controls、denominators、cache boundaries、call boundaries、go/no-go gates 和 expected artifacts** 冻结到足以进入 Repository Audit / Implementation Map 的程度；下一阶段不需要重新做 research ideation。
