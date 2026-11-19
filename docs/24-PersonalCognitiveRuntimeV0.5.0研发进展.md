# Personal Cognitive Runtime · V0.5.0 Alpha 研发进展

**日期：** 2026-11-19  
**定位：** PDKS / Personal AI Life OS 个人持续记忆、状态与意图运行时  
**状态：** 本地研究验证原型，不是生产系统

## 1. 阶段定位

V0.4 已建立个人事件账本、跨来源事件融合候选和 Pull-only Agent Runtime。V0.5 从“记录事件”推进到“持续理解个人的记忆、状态和意图”，增加 Memory、State、Intent、Reflection 四个引擎。

目标不是让 AI 自动判断一个人的完整生活，而是先建立可追溯、可修订、可撤回、用户可控的认知运行时。

## 2. 本轮实际交付

### Memory Engine
- 类型化记忆：profile_fact、preference、principle、decision、lesson、experience、relationship、skill、commitment。
- 用户手动表达的记忆可直接记录为 active / confirmed。
- Reflection 派生记忆默认 proposed / inferred。
- 记录来源 Event / Evidence 引用、有效时间、到期时间、置信度、敏感度和用途范围。
- 支持 confirm、edit、reject、retract、supersede。
- 修订保存前一版本快照、原因、操作者和时间。

### Intent Engine
- 类型：goal、commitment、plan、milestone、task、aspiration。
- 状态：proposed、active、blocked、on_hold、completed、cancelled、superseded。
- 创建默认 proposed，只有用户显式激活才进入当前状态。
- 状态变化有审计记录；支持优先级、项目、父级、开始/截止时间和下一步行动。
- 来源失效后设置 review_required，Agent 隐藏该意图；来源重新有效后用户可以 revalidate。

### Reflection Engine
- 只处理 personal 域、已确认、验证通过、P0/P1 的事件。
- DecisionEvent → decision memory candidate。
- LearningEvent → lesson memory candidate。
- CommitmentEvent → commitment intent candidate。
- DeliverableEvent → experience memory candidate。
- Preview 只读；Run 才物化候选。
- 不自动确认记忆、不自动激活意图、不推断人格或心理状态。

### State Engine
- 生成 person / self 状态快照。
- 输出 current_focus、active_goals、open_commitments、blocked_items、next_actions、durable_memories、recent_confirmed_events 和 pending_review。
- 快照包含 as_of、支持事件引用、记忆引用、意图引用和 projector_version。
- 来源变化后可失效并重算。

### Agent Context
- 增加 Agent Memory、Intent、State 三个只读端点。
- 复用 V0.4 一次性 Token 和订阅授权。
- 每次读取重新验证用途、敏感度、订阅状态、来源事件和证据关系。
- Agent 不能写入记忆、激活意图或触发外部动作。

## 3. 四类对象语义边界

| 对象 | 语义 | 核心问题 |
|---|---|---|
| Event | 过去发生事项及其证据 | 发生了什么？ |
| Memory | 对个人有持续价值的信息表达 | 哪些值得记住？ |
| State | 某一时点的状态投影 | 现在有哪些已知状态？ |
| Intent | 用户面向未来的目标/承诺/计划 | 准备实现什么？ |

Event 不因提炼为 Memory 而被覆盖；State 是可重算快照；Intent 不是执行指令。

## 4. 治理闭环

- Event / Evidence 是来源。
- Memory / Intent 通过支持关系引用来源。
- 来源删除会使 Evidence 支持失效。
- 失去有效支持的反思记忆进入 needs_review / disputed。
- 失去有效支持的 Intent 进入 review_required。
- Agent 不再读取需要复核的派生对象。
- 证据恢复有效后，用户可以重新确认记忆或 revalidate 意图。
- 本地运行时不能自动擦除 Agent 已复制到外部存储的数据，仍需未来 Memory Revocation Hook。

## 5. 验证

- 自动化测试：96 passed。
- Python compileall：通过。
- UI JavaScript node --check：通过。
- FastAPI OpenAPI：55 paths。
- 使用合成数据测试 Memory、Intent、Reflection、State、Agent Context 和 Source Purge。
- Fresh ZIP extraction regression：96 passed。

测试证明本地确定性行为，不代表真实用户长期记忆准确率、偏好推断质量或生产安全认证。

## 6. 下一阶段

V0.5.1：记忆质量评测集，包括准确性、过期率、冲突率、人工纠错成本和来源撤回成功率。  
V0.5.2：完善 Event—Memory—Intent 本体关系、有效时间与冲突处理。  
V0.5.3：Agent Memory Revocation Hook、引用追踪和删除回执。  
V0.6：用户授权下接入真实生活数据源，先影子运行和人工对照，再逐步开放自动化。

**阶段结论：V0.5 已把事件账本延伸为可治理的个人持续认知运行时，但距离真正理解个人生活仍需要真实数据、长期评测和用户纠错闭环。**
