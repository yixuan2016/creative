# PDKS 个人数据持久化运行时与 ADS-WORK-09 接入设计

> PDKS-RUNTIME-003 · Runtime Prototype 0.3.0 · 2026-11-19  
> 关联：PDKS 0.1.0 / PDKS Agent Skill 0.2.0 / ADS-WORK-08 / ADS-WORK-09 / ADS-WORK-10
>
> **仓库同步说明：** 当前分支已同步本设计文档、HTML 阅读版和 README 索引；可执行原型源码及测试随独立 0.3.0 开发包交付，尚未逐文件合入 creative/prototype。

## 核心结论

0.2.0 解决 Agent 如何理解和处理个人数据；本阶段解决这些数据如何可靠留存、更新、检索、纠错和迁移。

PDKS 继续作为跨 Agent、跨产品的个人数据表达标准；ADS-WORK-08 负责语义与授权桥接；ADS-WORK-09 作为个人事件账本、持续记忆、Intent 和受约束 Agent 动作的运行时。本阶段在现有内存逻辑原型上增加 SQLite 持久化适配器和 PDKS→ADS 投影适配器，不改变 PDKS 0.1 或 ADS 既有 JSON Schema。

## 1. 架构位置

~~~text
多源输入 / PDKS Agent Skill
  语音转写 · 聊天 · 文档 · 邮件 · 手工记录
                │
                ▼
       PDKS 统一记录与证据链
  Entity / Source / Evidence / Event / Assertion
       Knowledge / Context / Action / Relation
                │
                ▼
       PDKS → ADS 语义与授权适配器
  Schema检查 · 来源解析 · 身份归属 · 授权校验
                │
       ┌────────┴────────┐
       ▼                 ▼
Personal Event       Candidate Memory
Ledger               + Candidate Intent
       └────────┬────────┘
                ▼
      ADS-WORK-09 Personal Runtime
   SQLite 本地持久化 · 版本 · 幂等 · 审计
                │
                ▼
      Context Builder / Personal Agent
  默认过滤候选与敏感内容；动作另走审批契约
~~~

## 2. 职责边界

| 层 | 负责什么 | 不负责什么 |
|---|---|---|
| PDKS Skill | 从输入中抽取标准记录、来源、证据和候选知识 | 不自动获得连接器权限或长期存储权限 |
| PDKS 数据标准 | 定义九类对象、字段、分类、治理和迁移 | 不绑定某个 Agent 或数据库 |
| ADS-WORK-08 | 语义映射、身份解析、个人/企业/领域授权边界 | 不替代个人数据所有权 |
| PDKS→ADS Adapter | 将可投影对象转换为 ADS 合同 | 不绕过授权，不创建企业事件 |
| ADS-WORK-09 Runtime | 事件账本、记忆、Intent、动作审批和上下文构建 | 不采集设备数据，不直接执行外部动作 |
| SQLite Adapter | 本地持久化、事务、版本冲突检测、元数据审计和备份 | 不是身份认证、加密或生产安全边界 |

## 3. 持久化数据模型

| 表 | 内容 | 设计目的 |
|---|---|---|
| owners | owner_ref、revision、时间戳 | 个人数据分区与乐观并发版本 |
| events | Personal Event Ledger JSON | 事件账本持久化 |
| memories | ADS Personal Memory Item JSON | 候选/确认记忆持久化 |
| intents | ADS Personal Intent Object JSON | 目标、承诺、任务和项目上下文 |
| actions | Personal Agent Action Proposal JSON | 保存提案、审批与执行结果 |
| suppressed_sources | 被撤回/抑制的来源事件 ID | 防止来源撤回后重新生成记忆 |
| audit_log | 操作、主体、版本、记录引用和状态摘要 | 追加式元数据审计，不复制记录正文 |
| schema_migrations | 存储结构版本 | 数据库结构升级管理 |

所有业务表使用 owner_ref 与 record_id 复合主键。每次状态变更使用 SQLite BEGIN IMMEDIATE 事务，原子更新业务记录、owner revision 和审计日志。

## 4. 关键运行机制

1. **原子提交与版本冲突**：每个 owner 维护单调递增 revision；写入时比较 expected_revision。若其他运行实例已经提交，当前写入拒绝并返回 ConcurrentWriteError，调用方先 refresh 再决定是否重试。
2. **幂等**：Event ID 不可被不同内容复用；相同 Event ID 和相同内容重复写入不产生新 revision；idempotency_key 重用但内容变化时拒绝。
3. **候选优先**：Agent 只能通过登记的 PDKS Bridge 身份写入 candidate Memory / inferred_candidate Intent；确认态必须由 owner 明确操作。
4. **上下文过滤**：默认不纳入 candidate Memory、personal_sensitive 内容和候选 Intent；已被 suppress 的来源不能参与上下文构建，也不能再次派生记忆。
5. **来源撤回传播**：派生 Memory 撤回；依赖来源的 Intent 暂停并标记 owner review，不静默删除人的承诺。
6. **审计最小化**：审计只保存操作类型、actor、record ID、revision、计数和状态摘要，不复制个人记录正文。

注意：当前 suppression 不等于物理删除原始事件/录音文件。原始来源、数据库和备份的真正删除仍需独立的删除传播工作流与回执。

## 5. PDKS → ADS 投影规则

| PDKS 对象 | ADS 目标 | 本阶段行为 |
|---|---|---|
| Event | Personal Event Ledger | 要求发生时间和可解析 Source Asset；按映射规则生成事件 |
| Knowledge Asset | Memory Item | 必须关联已成功投影事件；默认 candidate |
| Personal Context | Memory Item | 必须属于当前 owner 并关联事件；推断默认 candidate |
| Action | Intent Object | 必须属于当前 owner 并关联事件；默认 inferred_candidate / proposed |
| Assertion | 保留在 PDKS | 无直接等价对象，不升级成事实 |
| Entity | Ontology Identity Reference | 仅保留引用，不自动创建/合并主数据 |
| Source Asset / Evidence Segment | SourceRecord / Evidence 引用 | 保留原始来源和定位，不复制或伪造原始文件 |
| Relationship | Ontology Relation | 保留在 PDKS 语义层，后续按需映射 |

关键约束：

- device_capture 和 connector_sync 必须提供 governance.consent_ref，且该引用必须出现在可信授权解析器提供的 active authorization 集合中。
- 不允许将未经授权的设备采集降级为 manual_import 绕过门禁。
- PDKS Action 只映射为人的 Intent，不自动创建 Personal Agent Action Proposal。
- 一个事件未成功投影时，依赖该事件的 Memory / Intent 不得投影。
- 个人侧默认 personal_only，不创建企业投影，不扩大共享范围。

## 6. CLI 运行方式

在完整 0.3.0 开发包根目录安装测试依赖；若在 creative 仓库运行，需先将开发包 prototype/ 下的新增模块和测试文件复制到仓库 prototype/：

~~~bash
python -m pip install -r requirements-dev.txt
~~~

初始化个人本地库：

~~~bash
python prototype/personal_memory_cli.py init --db ./data/personal-memory.sqlite3 --owner <owner-ref>
~~~

从 PDKS JSON 记录目录生成 ADS 投影（默认执行 PDKS JSON Schema 与 Event Taxonomy 校验）：

~~~bash
python prototype/personal_memory_cli.py project-pdks --records-dir ./my-pdks-export/records --owner <owner-ref> --output ./data/pdks-projection.json --authorization-ref <trusted-active-consent-ref>
~~~

仅在有合法授权引用时才传入 authorization-ref。授权引用必须来自可信授权服务/适配器，不能由模型自行编造。仅合成测试数据可以使用 --skip-pdks-validation；真实数据不应跳过 Schema / Taxonomy 校验。

将投影原子写入个人库：

~~~bash
python prototype/personal_memory_cli.py apply-projection --db ./data/personal-memory.sqlite3 --owner <owner-ref> --projection ./data/pdks-projection.json
~~~

只有本人已经检查并明确确认投影中的 active Memory 时，才额外传入 --owner-confirmed；普通 Agent 导入只能写入 candidate。

构建个人工作上下文：

~~~bash
python prototype/personal_memory_cli.py context --db ./data/personal-memory.sqlite3 --owner <owner-ref> --purpose personal_planning
~~~

查看审计、备份与完整性：

~~~bash
python prototype/personal_memory_cli.py audit --db ./data/personal-memory.sqlite3 --owner <owner-ref>
python prototype/personal_memory_cli.py backup --db ./data/personal-memory.sqlite3 --output ./backup/personal-memory.sqlite3
python prototype/personal_memory_cli.py integrity-check --db ./data/personal-memory.sqlite3
~~~

## 7. 测试覆盖与验收

当前参考原型覆盖：

- SQLite 运行时 18 项测试：重启持久化、幂等、owner 分区、并发冲突、记忆确认/纠正/撤回、敏感过滤、来源 suppression、Intent 约束、Agent 审批、审计追加约束和备份。
- PDKS→ADS Adapter 15 项测试：正常映射、设备/连接器授权阻断、时间/身份校验、候选状态、原子投影、CLI 端到端和 ADS Schema 合同校验。
- 独立开发包本地测试：32 项中 31 项通过，1 项因未重复打包 ADS 官方 Schema 而跳过；完整 creative 仓库中会执行该 Schema 联合测试。
- CLI 端到端：1 Event + 2 candidate Memory + 1 candidate Intent；无 Agent Action Proposal，无企业投影。
- SQLite integrity_check：ok；备份库重新打开成功。

运行：

~~~bash
python -m unittest discover -s prototype -v
~~~

## 8. 尚未完成的生产化工作

| 项目 | 当前状态 | 生产化要求 |
|---|---|---|
| SQLite 本地持久化 | 参考原型完成 | 规模评估、迁移、恢复演练 |
| 乐观并发与事务 | 参考原型完成 | 多进程/多设备冲突策略与压力测试 |
| 审计日志 | 本地追加约束 | 外部防篡改审计、密钥与保留策略 |
| 加密 | 未实现 | OS Keychain/KMS、静态加密、密钥轮换 |
| 身份认证 | 未实现 | 宿主身份、owner 认证和会话授权 |
| 连接器 | 未实现 | 钉钉、录音设备、邮件、日历只读授权接入 |
| 授权解析器 | 仅接收可信引用集合 | 对接正式 Consent / Policy Service |
| 多端同步 | 未实现 | 设备注册、端到端加密、冲突合并和撤回传播 |
| 物理删除 | 未实现 | 原始文件、数据库、备份和派生记录的删除闭环 |
| Agent API | CLI / Python API | 身份验证、限流、审计、版本兼容和服务化部署 |

## 9. 下一阶段建议

1. 先在单用户、单设备、手工导入条件下跑通真实 PDKS 数据。
2. 接入一个只读来源，优先用户主动导出的钉钉/会议记录，不直接开启全量后台采集。
3. 用真实授权记录替换测试 authorization set。
4. 建立 PDKS 原始库与 ADS 运行库的可追溯 ID 映射和增量同步。
5. 加入加密、owner 身份认证、删除传播和备份恢复测试。
6. 最后才考虑多端同步、自动感知和企业投影。

## 最终判断

PDKS 是个人数据的统一语言；ADS-WORK-08 是语义与授权桥梁；ADS-WORK-09 是个人数据运行时；ADS-WORK-10 是用户体验入口。SQLite 适配器只是验证持久化机制的第一步，不是最终底座。最终系统必须保持数据可携带、权限可解释、来源可追溯、推断可纠错、动作可审批和用户可撤回。
