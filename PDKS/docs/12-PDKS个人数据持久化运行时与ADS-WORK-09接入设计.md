# PDKS 个人数据持久化运行时与 ADS-WORK-09 接入设计

> PDKS-RUNTIME-003 · V0.1 Runtime Prototype · 2026-11-19  
> 关联：PDKS 0.1 / PDKS Agent Skill 0.2 / ADS-WORK-08 / ADS-WORK-09 / ADS-WORK-10

## 核心结论

**0.2 解决 Agent 如何理解和处理个人数据；本阶段解决这些数据如何可靠地留存、更新、检索、纠错和迁移。**

PDKS 继续作为跨 Agent、跨产品的个人数据表达标准；ADS-WORK-08 继续负责个人/企业/领域之间的语义与授权边界；ADS-WORK-09 继续作为个人事件账本、持续记忆、Intent 和受约束 Agent 动作的运行时。本阶段在现有内存逻辑原型上增加 SQLite 持久化适配器和 PDKS→ADS 投影适配器，不改变 PDKS 0.1 或 ADS 既有 JSON Schema。

## 一、架构位置

```text
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
```

## 二、职责边界

| 层 | 负责什么 | 不负责什么 |
|---|---|---|
| PDKS Skill | 从输入中抽取标准记录、来源、证据和候选知识 | 不自动获得连接器权限或长期存储权限 |
| PDKS 数据标准 | 定义九类对象、字段、分类、治理和迁移 | 不绑定某个 Agent 或数据库 |
| ADS-WORK-08 | 语义映射、身份解析、个人/企业/领域授权投影 | 不替代个人数据所有权 |
| PDKS→ADS Adapter | 按映射规则将可投影对象转换为 ADS 合同 | 不绕过授权，不创建企业事件 |
| ADS-WORK-09 Runtime | 事件账本、记忆、Intent、动作审批和上下文构建 | 不采集设备数据，不直接执行外部动作 |
| SQLite Adapter | 本地持久化、事务、版本冲突检测、元数据审计和备份 | 不是身份认证、加密或生产安全边界 |

## 三、持久化数据模型

SQLite 原型包含以下表：

| 表 | 内容 | 设计目的 |
|---|---|---|
| `owners` | owner_ref、revision、创建/更新时间 | 个人数据分区与乐观并发版本 |
| `events` | Personal Event Ledger JSON | 事件账本持久化 |
| `memories` | ADS Personal Memory Item JSON | 候选/确认记忆持久化 |
| `intents` | ADS Personal Intent Object JSON | 目标、承诺、任务和项目上下文 |
| `actions` | Personal Agent Action Proposal JSON | 保存提案、审批与执行结果 |
| `suppressed_sources` | 被撤回/抑制的来源事件 ID | 防止来源撤回后重新生成记忆 |
| `audit_log` | 操作、主体、版本、记录引用和状态摘要 | 追加式元数据审计，不复制记录正文 |
| `schema_migrations` | 存储结构版本 | 数据库结构升级管理 |

所有业务表使用 `(owner_ref, record_id)` 作为复合主键，防止不同个人的数据在逻辑层发生 ID 冲突。数据库文件仍需要操作系统权限和设备加密保护。真实个人数据库、原始录音、导出记录和备份不得提交到 GitHub；使用 .gitignore 只能降低误提交风险，提交前仍需人工检查。

## 四、关键运行机制

### 4.1 原子提交与版本冲突

- 每次状态变更使用 SQLite `BEGIN IMMEDIATE` 事务。
- 每个 owner 维护单调递增 `revision`。
- 写入时携带读取时的 `expected_revision`。
- 若其他运行实例已经提交，当前写入拒绝并返回 `ConcurrentWriteError`；调用方先 `refresh()` 再决定是否重试。
- 同一事务中更新业务记录、revision 和审计日志，避免部分提交。

### 4.2 幂等

- Event ID 不可被不同内容复用。
- 相同 Event ID 和相同内容重复写入不产生新 revision。
- `idempotency_key` 重用但内容变化时拒绝写入。
- PDKS Event 投影 ID 由原始 PDKS object_id 稳定派生，并保留原始 ID 与版本。

### 4.3 个人上下文过滤

- 默认只纳入 active Memory。
- 默认不纳入 candidate Memory。
- 默认排除 `personal_sensitive`。
- Intent 默认只纳入 active、blocked、paused；候选 Intent 需显式允许。
- 已被 suppress 的来源不能参与上下文构建，也不能再次派生记忆。

### 4.4 记忆纠错和来源撤回

- 记忆确认、纠正、撤回都产生新的持久化 revision。
- 纠正通过新记录 `supersedes` 旧记录，不覆盖历史。
- 来源事件被用户要求忘记时，写入 suppression，并撤回所有依赖它的派生记忆。
- **当前 suppression 不等于物理删除原始事件/录音文件。** 原始来源的真正删除、备份清理和派生数据传播，仍需单独的删除工作流与回执。

### 4.5 审计

- `audit_log` 仅记录操作类型、actor、record ID、revision、状态摘要和计数。
- 不把完整个人记录正文复制到审计日志。
- 数据库触发器禁止对既有审计行 UPDATE/DELETE。
- 该机制提供本地原型级追加约束，不等于具备防管理员篡改能力的合规审计系统。

## 五、PDKS → ADS 投影规则

| PDKS 对象 | ADS 目标 | 本阶段行为 |
|---|---|---|
| Event | Personal Event Ledger | 要求发生时间和可解析 Source Asset；按映射规则生成事件 |
| Knowledge Asset | Memory Item | 必须关联已成功投影事件；默认 candidate |
| Personal Context | Memory Item | 必须属于当前 owner 并关联已成功投影事件；推断默认 candidate |
| Action | Intent Object | 必须属于当前 owner 并关联已成功投影事件；默认 inferred_candidate / proposed |
| Assertion | 无直接等价对象 | 保留在 PDKS，不升级成事实 |
| Entity | Ontology Identity Reference | 仅保留引用，不自动创建/合并主数据 |
| Source Asset / Evidence Segment | SourceRecord / Evidence 引用 | 保留原始来源和定位，不复制或伪造原始文件 |
| Relationship | Ontology Relation | 保留在 PDKS 语义层，后续按需映射 |

特别约束：

1. `device_capture` 和 `connector_sync` 必须提供 `governance.consent_ref`，且该引用必须出现在可信授权解析器提供的 active authorization 集合中。
2. 不允许将未经授权的设备采集降级为 `manual_import` 绕过门禁。
3. PDKS Action 只映射为人的 Intent，不自动创建 Personal Agent Action Proposal。
4. 推断 Memory / Intent 默认只能以 candidate / proposed 进入个人运行时；确认必须由 owner 完成。
5. 个人侧默认 `personal_only`，不创建企业投影，不扩大共享范围。
6. 一个事件未成功投影时，依赖该事件的 Memory / Intent 不得投影。

## 六、运行命令

在仓库根目录执行。先安装测试依赖：

```bash
python -m pip install -r requirements-dev.txt
```

初始化个人本地库：

```bash
python prototype/personal_memory_cli.py init \
  --db ./data/personal-memory.sqlite3 \
  --owner <owner-ref>
```

从 PDKS JSON 记录目录生成 ADS 投影（默认执行 PDKS JSON Schema 与事件 Taxonomy 校验）：

```bash
python prototype/personal_memory_cli.py project-pdks \
  --records-dir ./my-pdks-export/records \
  --owner <owner-ref> \
  --output ./data/pdks-projection.json \
  --authorization-ref <trusted-active-consent-ref>
```

仅在有合法授权引用时才传入 `--authorization-ref`。授权引用必须来自可信授权服务/适配器，不能由模型自行编造。

将投影原子写入个人库：

```bash
python prototype/personal_memory_cli.py apply-projection \
  --db ./data/personal-memory.sqlite3 \
  --owner <owner-ref> \
  --projection ./data/pdks-projection.json
```

若投影中包含已确认的 Memory，只有在本人已经检查并明确确认时才额外传入 `--owner-confirmed`；普通 Agent 导入只能写入 candidate。

构建个人工作上下文：

```bash
python prototype/personal_memory_cli.py context \
  --db ./data/personal-memory.sqlite3 \
  --owner <owner-ref> \
  --purpose personal_planning
```

查看候选记录（仅在明确需要人工复核时）：

```bash
python prototype/personal_memory_cli.py context \
  --db ./data/personal-memory.sqlite3 \
  --owner <owner-ref> \
  --purpose personal_review \
  --include-candidates
```

审计、备份与完整性检查：

```bash
python prototype/personal_memory_cli.py audit --db ./data/personal-memory.sqlite3 --owner <owner-ref>
python prototype/personal_memory_cli.py backup --db ./data/personal-memory.sqlite3 --output ./backup/personal-memory.sqlite3
python prototype/personal_memory_cli.py integrity-check --db ./data/personal-memory.sqlite3
```

## 七、测试覆盖与验收

本地原型新增：

- SQLite 运行时 18 项测试：重启持久化、幂等、owner 分区、并发冲突、记忆确认、敏感过滤、来源 suppression、Intent 约束、Agent 审批、审计追加约束和备份。
- PDKS→ADS Adapter 15 项测试（独立包本地 14 项通过；完整仓库额外执行 ADS Schema 联合校验）：正常映射、设备/连接器授权阻断、缺失发生时间、跨 owner 上下文、错误 assignee、原子投影和禁止创建 Agent Action Proposal。
- 在完整仓库中，额外启用 ADS Event Ledger / Memory / Intent 官方 Schema 校验测试。

运行：

```bash
python -m unittest discover -s prototype -v
```

## 八、尚未完成的生产化工作

| 项目 | 当前状态 | 生产化要求 |
|---|---|---|
| SQLite 本地持久化 | 参考原型完成 | 规模评估、迁移、恢复演练 |
| 乐观并发与事务 | 参考原型完成 | 多进程/多设备冲突策略与压力测试 |
| 审计日志 | 本地追加约束 | 外部防篡改审计、密钥与保留策略 |
| 加密 | 未实现 | OS Keychain/KMS、静态加密、密钥轮换 |
| 身份认证 | 未实现 | 宿主身份、owner 认证和会话授权 |
| 连接器 | 未实现 | 钉钉、录音设备、邮件、日历的只读授权接入 |
| 授权解析器 | 仅接收可信引用集合 | 对接正式 Consent / Policy Service |
| 多端同步 | 未实现 | 设备注册、端到端加密、冲突合并和撤回传播 |
| 物理删除 | 未实现 | 原始文件、数据库、备份和派生记录的删除闭环 |
| Agent API | CLI / Python API | 身份验证、限流、审计、版本兼容和服务化部署 |

## 九、下一阶段建议

1. 先在单用户、单设备、手工导入条件下跑通真实 PDKS 数据。
2. 接入一个只读来源（优先用户主动导出的钉钉/会议记录），不直接开启全量后台采集。
3. 用真实授权记录替换测试用 authorization set。
4. 建立 PDKS 原始库与 ADS 运行库的可追溯 ID 映射和增量同步。
5. 加入加密、owner 身份认证、删除传播和备份恢复测试。
6. 最后才考虑多端同步、自动感知和企业投影。

## 最终判断

PDKS 是个人数据的统一语言；ADS-WORK-08 是语义与授权桥梁；ADS-WORK-09 是个人数据运行时；ADS-WORK-10 是用户体验入口。SQLite 适配器只是验证持久化机制的第一步，不是最终底座。最终系统必须保持数据可携带、权限可解释、来源可追溯、推断可纠错、动作可审批和用户可撤回。
