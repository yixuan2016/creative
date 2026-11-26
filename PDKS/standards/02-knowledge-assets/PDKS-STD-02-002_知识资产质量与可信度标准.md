# PDKS-STD-02-002：知识资产质量与可信度标准

Status: Candidate Draft

## 质量维度
Provenance（来源）、Evidence（证据）、Accuracy（准确）、Completeness（完整）、Temporal validity（时效）、Consistency（一致）、Reusability（可复用）、Privacy（授权与隐私）。

## 可信状态
- source_observed：来源直接观察到。
- user_asserted：用户明确陈述。
- agent_inferred：Agent 推断，必须标记依据和不确定性。
- human_reviewed：经用户或授权审核者确认。
- disputed：存在冲突。
- superseded：被更新记录替代但保留历史。
- retracted：被撤回并保留原因。

不得用单一 AI 置信分数替代上述状态。

## 知识晋级
Source → Evidence → Candidate Knowledge → Reviewed Knowledge → Reusable Knowledge。

Agent 默认只能生成 Candidate。高影响、敏感或身份相关信息不得仅凭模型判断自动晋级为 Reviewed。

## 最低门槛
稳定 ID；有来源或明确标记为用户输入；区分事实、观点和推断；时间不伪造；敏感级别与授权明确；执行冲突检查；具有生命周期状态。
