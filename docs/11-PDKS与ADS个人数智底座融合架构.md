# PDKS 与 ADS 个人数智底座融合架构

> ADS-PDKS-INT-001 · V0.1 Integration Design · 2026-11-19  
> 关联：ADS-WORK-08 / ADS-WORK-09 / ADS-WORK-10

## 核心结论

**PDKS 作为个人数据的统一表达与互操作标准；ADS-WORK-08 作为语义与授权桥梁；ADS-WORK-09 作为个人运行时；ADS-WORK-10 作为产品体验。**

二者互补，不互相替代。PDKS 保持跨产品、跨 Agent 的中立性；ADS 保持事件账本、持续记忆、目标承诺、审批执行和 Personal Assistant OS 的运行完整性。

## 一、职责分工

| 层次 | 体系 | 职责 |
|---|---|---|
| 个人数据表达 | PDKS 0.1 | 九类对象、事件分类、来源证据、知识、个人上下文、治理和迁移 |
| 语义互操作 | ADS-WORK-08 | 共同本体、个人/企业/领域边界、身份映射、授权投影 |
| 个人运行时 | ADS-WORK-09 | Personal Event Ledger、Memory Item、Intent Object、Personal Agent Action Proposal |
| 产品体验 | ADS-WORK-10 | 自然感知入口、多终端协同、主动服务、用户控制 |

## 二、九类对象映射

| PDKS 对象 | ADS 目标 | 映射规则 |
|---|---|---|
| event | Personal Event Ledger | 直接映射；必须有发生时间、来源资产和合规采集方式 |
| action | Personal Intent Object | 人的任务/承诺，不触发 Agent 执行 |
| personal_context | Memory Item | 必须关联已映射事件；推断保持 candidate |
| knowledge_asset | Memory Item | 必须关联来源事件；映射 episodic/semantic/procedural |
| assertion | 无直接等价对象 | 保留观点、假设、问题和说话人归属 |
| entity | Ontology Identity Reference | 不自动创建或合并主数据 |
| source_asset | core.SourceRecord 引用 | 保留来源系统、原生 ID 和采集授权 |
| evidence_segment | core.Evidence 引用 | 保留定位、摘录和证据质量 |
| relationship | Ontology Relation | 保留谓词、证据、状态、置信度和有效期 |

## 三、三个不能混淆的概念

1. PDKS Event 是发生记录；ADS Memory Item 是从事件派生的可纠错认知。
2. PDKS Action 是人的任务、计划或承诺；ADS Personal Agent Action Proposal 是 AI 的受约束执行提案。
3. PDKS Assertion 是有说话人归属的表达，不等于已经核验的事实。

正确链路：

`PDKS Action → ADS Intent → Context Package → Agent Action Proposal`

每一步均有独立状态、来源和治理要求。

## 四、事件映射规则

PDKS 事件类型：

`work.meeting.internal_meeting`

映射为 ADS 个人事件代码：

`personal.work.meeting_internal_meeting`

保留原始 PDKS taxonomy code 和版本于 ADS payload。

时间规则：
- `payload.start_at` → `occurred_at`；缺失即阻止映射。
- Source Asset `captured_at` → `observed_at`；缺失时可回退 `created_at`，但必须产生 warning。
- PDKS `created_at` → `recorded_at`。
- 不得用记录创建时间伪造事件发生时间。

授权规则：
- `manual_upload` / `api_import` → `manual_import`。
- `system_sync` → `connector_sync`，必须有 `governance.consent_ref`。
- `device_capture` → `device_capture`，必须有 `governance.consent_ref`。
- `automatic` → `connector_sync`，必须有授权引用。
- 缺少授权引用时阻止映射，禁止降级 capture mode 绕过权限检查。

ADS 个人侧默认：
`default_scope=personal_only`、`projection_allowed=false`。

## 五、记忆与 Intent 映射

Personal Context：
- role / capability / responsibility / constraint / working_style → semantic
- goal → goal
- preference → preference
- relationship → relationship
- current_focus → project_context

Knowledge Asset：
- method / procedure → procedural
- experience / case → episodic
- concept / fact / principle / lesson / insight → semantic

推断上下文和 draft 知识必须保持 candidate。Personal Context、Knowledge Asset 和 Action 只有在至少关联一条已成功映射的来源事件时才进入 ADS 对应集合。

PDKS Action 映射到 ADS Intent Object，不自动创建 Personal Agent Action Proposal。Agent Action Proposal 必须由 ADS Planner 另行创建，并具备风险等级、能力白名单、禁止动作、副作用、前置条件、审批、计划哈希、有效期和执行核验。

## 六、企业投影是独立流程

个人侧 PDKS → ADS 映射不代表企业有权读取。企业投影必须通过 ADS-WORK-08 独立完成：
1. 明确业务目的和接收责任人；
2. 验证授权引用、字段范围、用途和有效期；
3. 建立个人对象到企业权威主数据的身份映射；
4. 仅投影最小必要字段；
5. 正式业务状态由企业有权主体确认；
6. 创建企业侧独立事件 ID，并记录 projected_from 关系；
7. 支持授权撤回和派生数据处理；
8. 个人生活上下文默认不进入企业工作上下文。

## 七、0.3.0 原型验证

- 14/14 自动化测试通过。
- 29 条 PDKS 示例记录严格引用校验通过。
- 正向映射：1 Event + 2 Memory Items + 1 Intent。
- 负向映射：无授权 device_capture 被阻止，依赖该事件的 Memory/Intent 同步阻止。
- 默认不创建企业投影，不创建 Agent Action Proposal，不扩大共享范围。

尚未完成：ADS 官方 Schema 完整运行校验、ADS Memory Engine 数据库接入、企业投影授权服务和撤回传播、真实连接器、多设备同步及真实语料评测。

## 八、研发路线

P0 标准冻结 → P1 本地互操作 → P2 ADS 个人运行时接入 → P3 多源授权采集 → P4 Personal Assistant OS → P5 企业授权投影试点 → P6 跨 Agent 迁移。

## 最终判断

PDKS 是个人数据的统一语言；ADS-WORK-08 是责任域之间的语义和授权桥梁；ADS-WORK-09 是个人记忆和受约束行动的运行时；ADS-WORK-10 是用户使用这一体系的产品入口。

先统一语义，再连接运行时；先确保个人可控，再开展企业投影；先证明记录可信，再提高 Agent 自主程度。
