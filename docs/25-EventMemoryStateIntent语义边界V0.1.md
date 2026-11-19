# Event / Memory / State / Intent 语义边界 V0.1

## 1. 四类对象

- **Event**：对过去发生事项的表达，有发生时间、来源、Evidence、认识状态和验证状态。
- **Memory**：对个人有持续价值的信息表达，允许有效时间、置信度、来源支持、修订和撤回。
- **State**：由 Event、Memory 和 Intent 在 as_of 时点投影出的状态快照，必须可重算。
- **Intent**：用户面向未来的目标、承诺、计划或行动方向，默认 proposed，用户激活后才是 active。

## 2. 不可违反的约束

1. Event 不因被提炼为 Memory 而删除或改写。
2. Reflection Candidate 不等于 Confirmed Memory。
3. Memory confidence 不是客观真值概率。
4. Memory 有效时间与记录时间分离。
5. State Snapshot 不覆盖源对象，来源变化后可失效并重算。
6. Intent 不等于任务系统记录，不自动触发外部行动。
7. Intent 只有用户显式激活才进入 Agent 默认上下文。
8. 支持事件被删除或撤回后，派生对象必须重新核验。
9. 个人域对象不得因共享本体自动进入企业域。
10. Agent 只读，不得自行确认、修订或撤回 Memory / Intent。

## 3. 生命周期

### Memory status
proposed / active / needs_review / superseded / retracted / rejected

### Memory epistemic status
observed / inferred / confirmed / disputed / retracted

### Intent status
proposed / active / blocked / on_hold / completed / cancelled / superseded

Lifecycle status 与 epistemic status 分离。例如 needs_review + disputed 表示内容暂时不可被视为有效记忆。

## 4. 时间语义

- recorded_at / created_at：系统何时记录对象；
- valid_from / valid_to：记忆内容在现实世界何时有效；
- expires_at：系统何时停止默认提供该记忆；
- as_of：状态投影针对的时间点；
- start_at / due_at：意图计划时间，不等于已发生时间。

## 5. 纠错与删除

Memory 修订保存前一版本快照、操作者、原因和时间。Source Purge 使支持引用失效；派生 Memory 失去全部有效支持时进入 needs_review。手动用户表达的 Memory 保留 manual 来源类型，不伪造外部证据。
