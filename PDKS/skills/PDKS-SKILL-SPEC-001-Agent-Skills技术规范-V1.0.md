---
document_id: PDKS-SKILL-SPEC-001
title: PDKS Agent Skills 技术规范
version: 1.0
status: review-draft
date: 2026-11-20
---

# PDKS-SKILL-SPEC-001：Agent Skills 技术规范

**版本：** V1.0 评审稿  
**适用范围：** PDKS 官方 Skills、第三方兼容 Skills、Agent Host 适配器和 PDKS Runtime 工具接口

## 1. 目的与定位

PDKS Skill 是面向 Agent 的可复用能力说明与执行编排单元。它告诉 Agent 在什么条件下调用哪些 PDKS 能力、需要什么输入、如何遵循授权、如何解释结果，以及失败时如何恢复。

**Skill 本身不是数据连接器、权限系统、数据库或后台服务。** Skill 不会因为被安装就自动获得本地文件、钉钉、邮箱、日历或其他系统的访问权限。真正的数据读取和写入必须由用户已配置、已授权的本地工具、MCP Bridge、Runtime 或受控 API 完成。

PDKS 的核心原则是：一个标准、一套共享运行时和存储契约、多个 Agent Host 适配入口。不得让每个 Agent 自己定义一套不兼容的数据结构和知识目录。

## 2. 架构关系

| 层次 | 职责 | 约束 |
|---|---|---|
| Agent Host | Codex、WorkBuddy、Claude 等执行环境 | 提供 Skill 加载和工具调用能力；宿主差异由适配层处理 |
| Skill | 工作流说明、输入输出约定、策略提示和错误处理 | 不得声称拥有 Skill 未提供的权限或工具 |
| Agent Bridge / MCP | 为 Agent 暴露类型化工具、状态和必要交互 | 工具应有明确读写属性和授权要求 |
| PDKS Runtime | 执行采集、标准化、校验、检索和存储 | 负责幂等、事务、检查点和审计 |
| Connector | 对接具体数据源 | 每个来源独立授权，声明范围和能力 |
| Storage | 保存文件、证据、结构化记录和运行状态 | 权威边界明确，可导出和恢复 |

### 2.1 当前工程基线

PDKS 0.5.3 预览版采用 Node-native Agent Bootstrap 初始化 File-first Vault；可选 Capture Runtime 仍为独立 Python 组件。Node-native 初始化不要求 Python；启用当前 Capture Runtime 时才需要其 Python 环境。该技术分工属于当前过渡阶段，不应被 Skill 文档写成永久架构限制。

当前预览版边界：

- 初始化不会自动连接数据源、导入历史数据或启动后台采集。
- 初始化不会自动修改 Agent Host 的配置。
- Vault 文件尚未实现静态加密。
- File Store Adapter 0.1.0 为单向投影，不是双向同步。
- 真实 DWS 租户交付和跨宿主兼容性仍有待验证。
- 不得将 0.5.3 预览版宣传为生产就绪的个人数据平台。

## 3. Skill 分类

### 3.1 按职责分类

1. **Setup Skills：** 环境诊断、安装计划、用户确认、初始化、验证和故障排查。
2. **Capture Skills：** 调用指定连接器采集授权范围内的数据。
3. **Processing Skills：** 标准化、分类、事件提取、事实提取、去重和冲突检测。
4. **Knowledge Management Skills：** 候选确认、归档、更新、版本和生命周期管理。
5. **Knowledge Application Skills：** 检索、上下文构建、日报/周报、项目记忆和经验复用。
6. **Publishing Skills：** 将经确认且获准发布的知识投影到 Obsidian、Markdown 或其他目标。

### 3.2 按优先级分批

| 优先级 | Skill / 能力 | 目标 |
|---|---|---|
| P0 | `pdks-setup` | 安装前检查、计划、审批、初始化、验证 |
| P0 | `pdks-personal-knowledge` | 统一知识捕获、结构化、验证、保存、检索和迁移入口 |
| P0 | `dingtalk-capture` | 通过官方 DWS CLI 采集经授权的钉钉数据 |
| P0 | `file-capture` | 导入本地文档、图片、表格和 PDF |
| P0 | `event-extractor` | 从消息、文档和会议素材提取事件候选 |
| P0 | `knowledge-classifier` | 按统一知识分类和个人领域分类 |
| P0 | `knowledge-archiver` | 将已确认或按策略允许的候选写入标准 Vault |
| P0 | `personal-recall` | 依据授权范围检索并返回证据引用 |
| P1 | `email-capture`、`calendar-capture` | 邮件和日历只读接入 |
| P1 | `meeting-capture` | 录音、转写、说话人和时间戳处理 |
| P1 | `browser-capture`、`ai-conversation-capture` | 网页和 AI 对话采集 |
| P1 | `knowledge-validator`、`knowledge-deduplicator` | 质量、重复和冲突检查 |
| P1 | `obsidian-publisher`、`knowledge-lifecycle` | 知识投影、更新、过期和归档 |
| P2 | `daily-review`、`weekly-review` | 周期复盘 |
| P2 | `project-memory`、`experience-reuse`、`knowledge-insight` | 项目记忆、经验复用和规律发现 |

优先级表示研发顺序，不表示所有能力已实现。技能注册表必须记录每项能力的真实状态。

## 4. 标准 Skill 包结构

推荐每个 Skill 使用独立目录：

```text
<skill-id>/
├── SKILL.md                 # Agent 必须读取的主说明
├── README.md                # 面向开发者和用户的说明
├── references/              # 标准、字段字典、规则和边界
├── scripts/                 # 可选的确定性脚本
├── schemas/                 # 输入、输出和配置 Schema
├── examples/                # 合成或非敏感样例
├── tests/                   # 单元、契约和安全测试
└── assets/                  # 仅放必要的静态资产
```

不需要的目录可以省略。禁止将用户 Vault、令牌、密码、私钥、个人真实样本或运行缓存打包进 Skill。

## 5. SKILL.md 最低要求

每个 Skill 的 `SKILL.md` 必须包含：

1. YAML Frontmatter：稳定的 `name` 和清晰的 `description`。
2. Skill ID 与版本。
3. 目标、适用场景和不适用场景。
4. 运行前提：Agent Host、Bridge、Runtime、连接器和依赖。
5. 能力清单：可读、可写、可执行的操作分别说明。
6. 输入参数：必填项、可选项、默认值和校验。
7. 输出契约：返回对象、文件路径、状态和证据引用。
8. 授权与隐私：需要的授权范围、用户确认节点和敏感数据边界。
9. 执行流程：先检查、再计划、再授权、再执行、最后验证。
10. 幂等与恢复：重复调用、断点续跑、重试和回滚行为。
11. 错误处理：错误码、用户可理解的解释和恢复建议。
12. 测试与已知限制：自动化测试、未执行测试和兼容性状态。

Description 必须准确描述触发条件，避免过宽泛描述导致 Agent 在不适当场景中调用。

## 6. 工具调用契约

工具名称应使用稳定、可发现的命名空间，例如：

- `pdks_native_doctor`
- `pdks_native_plan`
- `pdks_native_apply`
- `pdks_native_verify`
- `pdks_capture_preview`
- `pdks_capture_run`
- `pdks_record_validate`
- `pdks_knowledge_search`
- `pdks_knowledge_publish`

以上为命名建议，不表示每个工具当前都已实现。实际工具清单以发布包和工具注册表为准。

每个工具必须声明：

| 契约项 | 要求 |
|---|---|
| tool_id | 稳定且唯一 |
| version | 工具契约版本 |
| description | 清楚描述功能和限制 |
| input_schema | 类型化输入、必填项、范围和枚举 |
| output_schema | 结构化结果和状态 |
| access_mode | read、draft、write 或 external_side_effect |
| required_scope | 最小授权范围 |
| approval | 是否需要用户确认及确认内容 |
| idempotency | 幂等键或重复执行策略 |
| audit | 运行 ID、来源、操作者、时间和结果 |
| errors | 稳定错误码和恢复说明 |

工具输出必须区分成功、部分成功、待确认、被拒绝、失败和未执行。Agent 不得仅凭工具调用已发起就向用户宣称执行成功。

## 7. 操作安全分级

| 级别 | 操作 | 默认规则 |
|---|---|---|
| R0 | 读取状态、检查配置、查询权限 | 可在已有授权内执行 |
| R1 | 生成计划、摘要、候选知识和预览 | 不改变权威数据 |
| R2 | 写入候选区、生成草稿、更新索引 | 按用户预先设置的策略执行；首次或敏感操作需确认 |
| R3 | 修改已确认知识、删除、批量导入、改变授权 | 必须显示影响范围并取得明确确认 |
| R4 | 对外发送、共享、发布、代表用户承诺或执行不可逆操作 | 必须单独授权和审批；不得由知识沉淀 Skill 擅自执行 |

确认必须绑定具体操作、目标、数据范围和计划摘要。用户对旧计划的确认不能自动授权内容或范围已变化的新计划。

## 8. 标准执行模式

### 8.1 初始化模式

当前预览版标准流程：

`doctor → plan → show plan → explicit approval → apply → verify`

- doctor：只读检查环境。
- plan：生成确定性计划，包含目标路径、文件变更、版本和风险提示。
- approval：用户确认具体计划；不能把一般性的“可以”解释为对任何数据采集的授权。
- apply：仅执行已确认计划。
- verify：检查文件、版本、哈希和实际状态。

当前 `pdks-setup` Skill 采用精确确认短语和未加密存储风险确认；后续版本可调整交互，但不得降低安全要求。

### 8.2 数据采集模式

`source_status → scope_preview → consent_check → capture_plan → capture → normalize → validate → report`

采集过程必须先验证来源授权。历史回补、后台持续采集、云端备份和新增数据类别均视为独立授权事项。

### 8.3 知识沉淀模式

`source_record → evidence_binding → extraction → candidate → quality_check → review/confirm → publish`

Agent 必须把模型生成内容与原始来源分开保存。低置信度、冲突或敏感候选应进入待确认区。

### 8.4 检索模式

`request → purpose_and_scope_check → authorized_retrieval → evidence_ranking → cited_answer`

返回内容应尽可能携带来源、时间和原文定位。没有证据的模型推断必须明确标注。

## 9. Agent Host 兼容规范

1. 同一个 Skill 的核心输入输出和数据语义不得因 Agent Host 不同而变化。
2. 宿主差异通过薄适配层处理，不得复制一套新的业务规则。
3. 优先采用标准 Skill 文件与 MCP 工具；宿主不支持 MCP Apps 时必须提供文本工具回退。
4. 云端 Agent 无本地文件访问能力时，必须通过用户显式配置的本地 Bridge 或受控同步机制访问；不得假设云端 Agent 可以访问用户电脑。
5. 安装 Skill 不代表自动修改宿主设置。涉及宿主配置的写入必须展示差异并单独确认。
6. 兼容性声明必须逐一列出实际测试的 Agent Host、版本、操作系统和测试结果。

## 10. 安装、更新和卸载

- 安装前检查操作系统、运行时版本、Agent Host 能力和目录冲突。
- 安装器应优先采用跨平台、可校验、可回滚的方式。
- 安装过程不得默认启动采集服务或连接数据源。
- 更新必须检查 Skill 与 Runtime、Schema、Taxonomy、Ontology 的兼容矩阵。
- 卸载 Skill 不得擅自删除用户 Vault；数据删除是独立且需确认的操作。
- 所有安装和更新过程应提供 dry-run 或计划预览。

## 11. 日志、审计和可观测性

每次运行至少记录：run_id、skill_id、skill_version、tool_versions、source_id（适用时）、授权范围摘要、开始/结束时间、输入摘要、输出摘要、执行状态、错误码和重试次数。

日志不得包含明文凭据或不必要的个人原文。调试日志应可关闭、可清理并遵循保留策略。

## 12. 发布和版本治理

- Skill 使用独立语义版本；工具契约、Record Schema、Event Taxonomy 和 Ontology 分别维护版本。
- 破坏性变化必须增加主版本或提供明确迁移方案。
- 发布包应包含文件清单、SHA-256、测试报告、依赖清单、已知限制和回滚说明。
- 每项能力必须标记 `implemented`、`experimental`、`planned` 或 `blocked`。
- 未完成真实来源、跨平台或安全验证的能力必须如实披露。

## 13. 安全红线

- 不得在聊天中收集密码、Token、API Key、私钥或支付凭据。
- 不得在未经授权时读取、上传、共享或持续采集个人数据。
- 不得把模型推断静默写成确认事实。
- 不得覆盖原始证据来修正摘要。
- 不得在没有审批的情况下批量删除、改变授权或对外发布。
- 不得绕过本地安全策略、访问控制或用户设置。
- 当前未实现静态加密的预览版不得用于真实敏感个人数据。

## 14. 与验收矩阵的关系

每个 Skill 发布前必须完成适用的契约测试、安全测试、宿主兼容测试和用户旅程测试。具体项目和准入门槛见《PDKS-SKILL-ACCEPTANCE-001：Skills 验收矩阵》。

---

**规范声明：** 本文件定义 Skill 的设计和交付要求，不代表 PDKS 技能目录中的所有规划项已经实现。
