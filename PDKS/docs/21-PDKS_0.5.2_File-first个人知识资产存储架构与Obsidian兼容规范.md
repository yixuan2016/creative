# PDKS 0.5.2：File-first 个人知识资产存储架构与 Obsidian 兼容规范

> **架构决策记录（ADR）**
>
> 版本：PDKS File-first Storage 0.1.0  
> 适用研发线：PDKS 0.5.2 · Cross-platform Bootstrap  
> 阶段：过渡阶段 Skill / Runtime 参考实现  
> 状态：架构基线 + FileFirstVault 0.1.0 过渡阶段参考实现；完整生产文件存储尚未实现

## 0. 决策摘要

PDKS 的首要产品价值是个人知识资产的长期沉淀、可读、可迁移和跨 Agent 复用。因此，存储架构采用 **File-first（文件优先）**：

- Markdown：人类可读、可编辑的知识文档和语义投影。
- JSON / JSONL：结构化来源记录、事件、关系、运行清单和机器交换格式。
- 原始附件：保留录音、图片、PDF、Office 文件及其他源文件，采用内容哈希寻址。
- SQLite：本地索引、搜索元数据、同步游标、任务队列、授权状态和运行状态；原则上可从文件与清单重建，不作为唯一知识资产库。
- Agent：通过 PDKS Runtime API / CLI 读取、提议和更新知识；不能绕过授权直接改写原始证据。

**Obsidian 不是 PDKS 的数据库，也不是 PDKS 的必需依赖。** PDKS Vault 本身就是一个普通目录；Obsidian 可以直接把该目录作为 Vault 打开。其他支持 Markdown 的软件也可查看。

## 1. 核心原则

1. **文件可携带**：复制整个 Vault 即可迁移主要知识资产，不要求先导出专有数据库。
2. **开放格式**：优先使用 UTF-8 Markdown、YAML Frontmatter、JSON、JSONL 和原始二进制附件。
3. **来源与知识分层**：原始来源证据不可被 Agent 摘要覆盖；知识文档必须保留来源引用。
4. **索引可重建**：SQLite 是加速层和运行状态层，丢失后可由文件、manifest 和事件日志重建核心索引。
5. **跨软件兼容**：核心链接使用相对 Markdown 链接；Obsidian Wikilinks、Canvas、插件字段只能作为可选扩展。
6. **跨 Agent 共享**：Agent 通过统一 Runtime 接口访问，不依赖某个 Agent 私有记忆。
7. **隐私默认本地**：不默认上传云端；云同步、Git 远端和备份分别授权。
8. **用户可理解**：用户能在文件管理器中找到自己的资料，并用普通文档软件阅读。

## 2. 三层持久化模型

| 层 | 文件/技术 | 内容 | 权威性 |
|---|---|---|---|
| 原始证据层 | 原始文件、JSONL、附件 | 来源系统原始记录、转写、媒体、导入文件 | 证据权威层，追加写入 |
| 知识资产层 | Markdown + YAML Frontmatter | 人物、项目、会议、决策、任务、主题、日记、生活事件 | 人类可读的知识权威层 |
| 运行索引层 | SQLite、缓存、队列 | 搜索索引、关系索引、同步游标、任务状态、运行日志索引 | 可重建，不是唯一知识副本 |

### 2.1 为什么不是“全部存 Markdown”？

聊天消息、音频、图片、附件、事件原始字段不适合全部塞进 Markdown。它们应以原始格式或 JSONL 保留；Markdown 用于组织、解释和关联知识。

### 2.2 为什么不是“全部存 SQLite”？

数据库对 Agent 和程序方便，但不利于用户直接阅读、长期迁移和跨工具使用。SQLite 可作为运行时索引，但不能成为用户唯一能拿到的知识资产。

## 3. 推荐 Vault 目录结构

```text
PDKS-Vault/
├── README.md
├── PDKS-MANIFEST.json
├── 00-Inbox/                 # 待整理内容
├── 10-Daily/                 # 每日工作与生活时间线
│   └── 2026/11/2026-11-19.md
├── 20-Events/                # 事件语义页（可按年/月分区）
│   └── 2026/11/
├── 30-Projects/              # 项目与长期事项
├── 40-People/                # 人物与关系（严格权限）
├── 50-Meetings/              # 会议纪要与证据引用
├── 60-Decisions/             # 决策、依据、结果
├── 70-Tasks/                 # 任务、承诺、跟进
├── 80-Knowledge/             # 主题知识、方法、经验
├── 85-Life/                  # 个人生活域（独立授权与隔离）
├── 90-Source-Records/        # 来源记录索引与导入批次清单
│   └── dingtalk/
│       ├── messages/2026/11/*.jsonl
│       ├── minutes/2026/11/*.json
│       ├── calendar/2026/11/*.jsonl
│       └── todos/2026/11/*.jsonl
├── 95-Archive/               # 用户确认归档的知识
├── assets/                   # 原始附件/图片/音频/PDF
│   └── sha256/ab/cd/<hash>.<ext>
└── .pdks/                    # 隐藏运行目录（不作为知识阅读入口）
    ├── config/
    ├── schemas/
    ├── ontology/
    ├── index/pdks-index.sqlite3
    ├── state/
    ├── audit/
    ├── cache/
    └── secrets-ref/
```

### 3.1 用户日常主要看哪里？

- 每日回顾：`10-Daily/`
- 会议纪要：`50-Meetings/`
- 项目进展：`30-Projects/`
- 决策记录：`60-Decisions/`
- 任务和承诺：`70-Tasks/`
- 长期知识：`80-Knowledge/`
- 生活资料：`85-Life/`

`90-Source-Records/` 和 `.pdks/` 属于系统沉淀层，普通用户不需要手动整理。

### 3.2 是否要把整个 Vault 放在 Obsidian 目录里？

建议让 `PDKS-Vault` 本身就是 Obsidian Vault。用户在 Obsidian 中选择“打开文件夹作为 Vault”，即可查看 PDKS 生成的 Markdown。

不应再额外维护一个 Obsidian 专用副本，否则会出现双份数据、链接失效和同步冲突。

## 4. Markdown 文档标准

每个知识文档采用 UTF-8 Markdown + YAML Frontmatter。

```yaml
---
pdks_id: "urn:pdks:meeting:01J... "
pdks_type: "meeting"
schema_version: "0.1.0"
title: "项目周会"
created_at: "2026-11-19T09:00:00+08:00"
updated_at: "2026-11-19T10:30:00+08:00"
status: "reviewed"
domains:
  - work
sensitivity: "personal_work"
tags:
  - meeting
  - project/alpha
source_refs:
  - "urn:pdks:source:dingtalk:..."
related:
  - "../30-Projects/项目Alpha.md"
  - "../60-Decisions/项目Alpha-技术选型.md"
aliases:
  - "Alpha 周会"
---
```

文档正文使用常见 Markdown 标题、列表、表格和链接。

### 4.1 兼容性规则

- 必须：UTF-8、标准 Markdown、YAML Frontmatter、相对路径链接。
- 推荐：CommonMark / GFM 常用子集。
- 可选：Obsidian `[[wikilink]]`、`![[embed]]`、Canvas、Dataview 字段。
- 不允许把核心语义只写在 Obsidian 插件专有字段中。
- 外部工具不理解的 Frontmatter 字段应忽略而不是破坏文档。
- 所有 PDKS 对象必须有稳定 `pdks_id`，不能依赖文件名作为唯一标识。

### 4.2 关系链接

跨工具的规范链接使用相对 Markdown 链接：

```markdown
本次会议属于[项目 Alpha](../../30-Projects/项目Alpha.md)。
相关决策：[技术选型](../../60-Decisions/项目Alpha-技术选型.md)。
```

Obsidian 可识别普通 Markdown 链接。若未来生成 Wikilinks，应作为可选展示形式，不作为唯一持久化关系。

## 5. 原始证据与附件标准

### 5.1 来源记录

- 原始事件采用 JSONL（按来源、类型、日期分区），每行一个完整记录。
- 复杂单体对象可使用 JSON。
- 原始来源记录原则上追加写入，不允许 Agent 直接覆盖。
- 纠错通过新增修订/更正记录实现，并保留原始版本。
- 每条记录包含 `source_id`、`origin_system`、`source_locator`、`captured_at`、`occurred_at`（如来源提供）、`content_hash`、`consent_ref`、`sensitivity`。
- 对无法合法保留的第三方数据，仅保存必要元数据或引用，并尊重源系统与组织保留政策。

### 5.2 附件

附件按 SHA-256 内容寻址，避免文件重名和重复保存：

```text
assets/sha256/ab/cd/abcdef...1234.m4a
```

在 Markdown 中使用相对链接：

```markdown
[打开会议录音](../../assets/sha256/ab/cd/abcdef...1234.m4a)
```

同时在 Frontmatter 或 source JSON 中保留原始文件名、MIME 类型、大小、哈希和来源定位。

### 5.3 大文件与媒体

- 音频、视频、图片、PDF、Office 原件不转成超长 Markdown。
- 转写文本、OCR 和摘要作为独立衍生资产保存，并引用原件。
- 缩略图和预览属于缓存，可重建。
- 去重基于内容哈希，不基于文件名。

## 6. SQLite 的定位

SQLite 负责：
- 全文搜索与结构化索引；
- 对象 ID 到文件路径的映射；
- 关系和标签查询；
- DWS 同步游标、分页状态和任务队列；
- 授权状态和操作审计索引；
- 文件变更检测和索引版本。

SQLite 不应是唯一持久化副本。删除 SQLite 后，PDKS 应能通过扫描 `PDKS-MANIFEST.json`、Frontmatter、JSONL 和文件哈希重建知识索引。

### 6.1 写入顺序

1. 校验授权和数据范围。
2. 将原始来源记录写入临时文件。
3. 计算哈希并原子重命名到正式路径。
4. 更新 manifest / 记录索引。
5. 更新 SQLite 索引。
6. 写入审计日志。

如果中途失败，文件与索引之间必须能通过 reconciliation 任务恢复；不能静默丢失已采集的原始证据。

## 7. Obsidian 与其他文档系统兼容策略

| 工具 | 兼容方式 | 目标 |
|---|---|---|
| Obsidian | 直接打开 PDKS-Vault 文件夹 | 原生查看、双链、图谱 |
| VS Code | 打开文件夹 | 编辑 Markdown / JSON |
| Typora | 打开 Markdown 文件 | 阅读与编辑 |
| Logseq | Markdown 文件导入/打开能力需按版本实测 | 知识浏览 |
| MarkText | 打开 Markdown | 阅读与编辑 |
| Notion | 通过 Markdown / CSV 导入导出适配器 | 不承诺直接文件夹同步 |

PDKS 核心不依赖 Obsidian。Obsidian 是一个很好的用户知识浏览器，但不是必须安装的软件。

### 7.1 Obsidian 可选增强

未来可提供 `PDKS Obsidian Plugin`，用于：
- 一键查看来源证据；
- 从当前笔记查看关联 Event / Evidence；
- 将用户编辑的知识页同步回 Runtime；
- 展示采集状态和待确认候选知识。

插件不是基础查看能力的前提。第一阶段只需让 Obsidian 直接打开 Vault。

## 8. 同步、备份与冲突处理

### 8.1 默认本地优先

- 默认仅保存在用户本地。
- 用户可单独选择 iCloud Drive、OneDrive、Dropbox、Syncthing 或其他同步目录。
- 云同步必须明确提示：同步服务商可能处理文件内容，用户需自行确认合规与隐私条件。
- 不默认把敏感 Vault 推送到 GitHub。
- Git 版本管理仅适合用户明确选择的场景；删除文件并不会自动从 Git 历史中彻底消失。

### 8.2 哪些文件参与同步？

**可同步：**
- Markdown 知识文档；
- 原始 JSON / JSONL（在用户授权和政策允许时）；
- 附件；
- PDKS manifest 和 schema 版本。

**默认不同步：**
- SQLite 活跃索引；
- 运行时缓存；
- 锁文件；
- 临时文件；
- OAuth Token、App Secret、密码；
- 设备本地日志中的敏感调试内容。

每台设备维护自己的 SQLite 索引，由共享文件重建。多设备同时编辑同一文件时，必须检测冲突并保留双方版本，禁止静默覆盖。

### 8.3 备份和迁移

完整迁移包至少包含：
- `PDKS-Vault/` 文件目录；
- `PDKS-MANIFEST.json`；
- Schema / Ontology 版本；
- 可选的加密备份元数据；
- 不包含可直接复用的明文 Token。

迁移到新电脑后，Runtime 扫描文件、校验哈希、重建 SQLite 索引，再由用户重新授权外部数据源。

## 9. 安全与隐私要求

- Vault 敏感数据应支持静态加密；密钥保存在 OS Keychain / Credential Manager，不写入 Vault。
- 文件系统权限按当前用户最小化设置。
- 导出和云同步前展示敏感级别与数据范围。
- `personal_private`、`health`、`finance` 等域应支持独立授权、独立目录策略和独立加密策略。
- 企业内部资料应尊重企业政策，不默认复制到个人 Vault。
- 用户撤销来源授权后，停止未来采集；已有数据按用户选择和适用政策执行保留、导出或删除。
- Markdown 中不得嵌入 Token、密码或密钥。
- Agent 通过 Runtime 权限访问；不能因能读取本地目录就自动获得所有数据的授权。

## 10. Node.js / TypeScript Bootstrap 与 File-first 的关系

Node.js + TypeScript Bootstrap Engine 负责：
- 创建 Vault 目录；
- 初始化 manifest；
- 安装/管理 Runtime；
- 检查文件系统和权限；
- 运行迁移、备份和索引重建；
- 输出统一 JSON 结果供 Agent 使用。

它不定义新的专有文档格式，也不把知识写入 Node 私有数据库。

当前 Python Capture Runtime 可暂时保留，通过适配层写入上述文件标准；后续再逐模块迁移，不一次性重写所有业务逻辑。

## 11. 关键验收标准

| 验收项 | 标准 |
|---|---|
| 人类可读 | 任意 Markdown 编辑器可打开核心知识文档 |
| Obsidian | 直接打开 Vault，不需要 PDKS 插件 |
| 跨 Agent | 至少两个不同 Agent 可读取同一 Vault，遵守权限 |
| 数据可迁移 | 复制 Vault 后可重建 SQLite 索引 |
| 文件稳定 ID | 文件移动或重命名后 `pdks_id` 不变 |
| 证据保真 | 原始证据不可被摘要覆盖 |
| 附件去重 | 相同内容 SHA-256 只存一份 |
| 链接可用 | 核心关系使用相对 Markdown 链接 |
| 同步安全 | 默认不上传；冲突不静默覆盖 |
| 安全 | Token 不进入 Vault；敏感数据加密能力验收后才可生产使用 |

## 12. 版本实施路线

### 0.5.2.1 — File-first Storage Contract
- 冻结目录结构、Frontmatter、JSONL、manifest 和附件寻址规范。
- 提供样例 Vault 和校验器。
- 保留当前 SQLite Runtime，先建立文件写入适配层。

### 0.5.2.2 — File Store Adapter
- Source Asset / Evidence 文件化。
- Knowledge Record Markdown 化。
- SQLite 索引可重建。
- 文件原子写入、哈希、去重和 reconciliation。

### 0.5.2.3 — Obsidian Compatibility
- Obsidian 直接打开 Vault。
- 验证 Frontmatter、附件、相对链接、中文路径、重命名和移动。
- 评估可选 Obsidian 插件，不作为首发依赖。

### 0.5.2.4 — Node Bootstrap Integration
- Node Bootstrap 初始化和管理 Vault。
- Agent 通过 JSON 协议配置路径、权限和备份。
- Windows / macOS / Linux 安装器按平台打包。

### 0.5.2.5 — Migration / Backup / Sync
- 从旧 SQLite + Vault 结构迁移。
- 从 Obsidian 文件夹导入既有 Markdown。
- 提供可验证备份包与冲突恢复。

## 13. 最终架构判断

PDKS 的核心资产不是某个数据库文件，也不是某个 Agent 的记忆，而是用户拥有、可阅读、可迁移、可授权的个人知识文件资产。

因此，最终关系应为：

```text
DWS / Email / Calendar / Voice / Files / Life Sources
                         │
                         ▼
              PDKS Capture Runtime
                         │
                         ▼
          Source JSONL + Original Attachments
                         │
                         ▼
              PDKS Ontology / Agents
                         │
                         ▼
             Markdown Knowledge Vault
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Obsidian     VS Code     Other Agents
                         │
                         ▼
              Rebuildable SQLite Index
```

**PDKS 负责沉淀，Obsidian 负责浏览，Agent 负责理解和协作，SQLite 负责加速。个人知识资产始终由用户掌握。**


## 14. 0.5.2.1 参考实现状态

已在当前过渡阶段工程中实现 `FileFirstVault` 0.1.0：
- `vault-init`：初始化独立 PDKS Vault；
- `vault-sync`：从现有 CaptureRuntime SQLite 单向投影 Source Asset、Evidence、已确认知识和用户明确选择的原始附件；
- `vault-verify`：校验 PDKS-MANIFEST.json 中纳入清单的文件哈希；
- `vault-rebuild-index`：从 Markdown、JSONL 和 SHA-256 附件重建独立的文件搜索索引。

该参考实现仍有明确边界：
- CaptureRuntime 的 operational SQLite 仍是当前运行权威数据源；
- 文件 Vault 不是事务性主存储，尚无采集时双写和事务 Outbox；
- Obsidian 修改 Markdown 后尚未回写 Runtime；
- 重建的 SQLite 仅为文件索引，不恢复 Consent、API Token、DWS 游标和完整审计状态；
- 未实现静态加密、OS Keychain、多设备同步和生产级冲突合并。

因此，File-first 目前已从“纯架构设计”进入“可运行的单向投影与文件索引重建原型”，但尚不能宣称生产级文件优先存储完成。
