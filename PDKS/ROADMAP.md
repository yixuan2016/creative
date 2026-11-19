# PDKS 演进路线

## Stage A — Transitional Skill Development（当前）

目标是把 Agent Skill 做成跨宿主、可迁移、可验证的个人认知规范，并建设独立的个人采集运行时参考实现。当前仍是 Experimental / Preview。

### 0.5.0 — Personal Capture Runtime Architecture & Reference Implementation
- 六层 Runtime 架构；
- 多 Agent 共享 API 设计；
- 本地文本/文件采集；
- 来源、证据、哈希和授权；
- 候选记录、Schema 校验、用户审核；
- 本地导出和删除。

### 0.5.1 — Official DWS CLI Connector Reference Implementation（当前）
- DWS 官方 CLI 安全子进程封装；
- DWS OAuth 只读状态与显式 profile 检查；
- 33 个公开个人事件键目录与 Schema 发现；
- NDJSON 实时事件流、ready marker、订阅 ID 和优雅退出；
- DWS → PDKS Source Asset / Evidence 映射、Consent、幂等；
- 听记摘要显式读取；
- 历史回填 Schema 发现，但不实现分页回填器；
- 当前未进行真实账号和租户事件投递验收。

### 0.5.2 — DWS Historical Backfill & Runtime Hardening
- 真实账号验证 DWS 查询 Schema；
- 聊天消息、听记、日历、待办、审批历史分页回填；
- 增量游标、断点、重试、时间窗重叠去重；
- 后台服务管理、开机自启、订阅监督和崩溃自动重启；
- 备份恢复、删除传播和数据库迁移演练；
- 加密与本地身份模型设计。

### 0.5.4 — DWS Context Enrichment
- 会议纪要、转写、消息引用和附件补充；
- 参与人、群、项目实体关联；
- 证据定位、媒体下载和来源权限核验。

### 0.6.0 — First Multi-source Connectors
- 邮件、日历、云文档等来源适配器；
- 复用统一 Connector Contract；
- 每个来源单独授权和撤销。

### 0.7.0 — Multimodal Extraction
- ASR 会议语音转写；
- OCR 图片和扫描件；
- PDF / Office 文档抽取；
- 时间戳、页码、帧和片段证据定位。

### 0.8.0 — Secure Multi-Agent Runtime
- ChatGPT、Claude、Codex、Cursor 等宿主 Adapter；
- MCP / OpenAPI / 安全 Relay；
- TLS、身份认证、密钥管理和 Agent 隔离；
- 多设备同步研究。

### 0.9.0 — Personal Context & Life OS Prototype
- 跨来源事件关联；
- 工作与生活时间线；
- 可解释记忆和持续上下文；
- 用户纠错反馈闭环。

## Stage B — Personal Digital Foundation Prototype（未来）

只有在来源授权、数据生命周期、加密、身份、安全评审、跨 Agent 实测和用户可用性验证通过后，才进入个人数智底座原型阶段。

## Stage C — Personal / Enterprise / Center Collaboration Research（未来）

研究共享语义核心、作用域扩展、映射契约、数据最小化和跨域治理。个人、企业、中心的协同仍是研究提案，不代表已经实现数据共享或组织访问。


## 0.5.2 — File-first Storage & Cross-platform Bootstrap

**新增架构决策：个人知识资产采用文件优先存储，PDKS Vault 可直接由 Obsidian 打开。**

- Markdown + YAML Frontmatter：人类可读的知识资产。
- JSON / JSONL：来源记录、事件和机器交换。
- 原始附件：SHA-256 内容寻址。
- SQLite：可重建索引、同步游标和运行状态，不作为唯一知识副本。
- Node.js + TypeScript：跨平台 Bootstrap Engine；现有 Python Capture Runtime 暂时保留，通过文件存储适配层演进。
- 默认本地存储；云同步、Git 远端、历史数据导入均独立授权。
- Obsidian 无需 PDKS 插件即可直接打开 Vault；Obsidian 专有语法只作为可选扩展。

实施顺序：
1. 冻结 File-first Storage Contract 与 Vault 样例。
2. 开发 File Store Adapter、原子写入、哈希去重和索引重建。
3. 完成 Obsidian / VS Code / Typora 兼容验收。
4. Node Bootstrap 初始化与管理 Vault。
5. 迁移、备份、同步和冲突恢复。


## 0.5.2.1 — File Store Adapter Reference Implementation (current)

Implemented in the transition-stage Runtime:
- `FileFirstVault` creates the portable `PDKS-Vault` directory structure.
- Markdown + YAML Frontmatter knowledge-note projection.
- Immutable JSONL source/evidence records with ID-based idempotency.
- SHA-256 content-addressed attachments and attachment index.
- `PDKS-MANIFEST.json` hash verification.
- A disposable SQLite file index rebuildable from Markdown / JSONL / assets.
- User-edit conflict protection: generated notes do not silently overwrite manual edits.
- CLI: `vault-init`, `vault-sync`, `vault-verify`, `vault-rebuild-index`.

Important boundary:
- `vault-sync` is a one-way projection from the current CaptureRuntime database.
- The operational CaptureRuntime database remains authoritative in this preview.
- Continuous file-first writes, bidirectional Obsidian edit reconciliation, encrypted Vault, cloud sync, and complete operational DB rebuild are not implemented.
- The rebuilt SQLite is only a portable file-search index; it does not restore consent grants, API tokens, or audit/runtime state.

Next:
1. Add a transactional outbox so capture and file persistence can recover from partial failures.
2. Promote source/evidence files to the authoritative record with safe deletion and retention semantics.
3. Implement bidirectional Markdown reconciliation and conflict resolution.
4. Add encryption and OS keychain integration before sensitive data use.
5. Integrate Node.js/TypeScript Bootstrap to create, validate, back up and migrate the Vault.


## PDKS 0.5.2.2 — Agent-native Bootstrap (current preview)

- [x] Node.js local MCP Bridge source and CLI
- [x] Read-only doctor / deterministic plan / approval-gated apply / verify tools
- [x] Optional MCP Apps interactive setup wizard source
- [x] Text-only MCP fallback and generic host configuration preview
- [x] User-visible File-first Vault initialization with Ontology 0.2.1 seed assets
- [x] Explicit confirmation phrase and unencrypted-storage acknowledgement
- [ ] Install official MCP SDK dependencies and build the MCP App UI in an online packaging environment
- [ ] MCP Inspector integration test and host-specific Agent validation
- [ ] Managed Python distribution or Node-native Runtime migration
- [ ] At-rest encryption and OS keychain before sensitive-data onboarding


## 0.5.3 — Node-native Agent Bootstrap (current preview)

- [x] Node-native doctor / deterministic plan / apply / verify.
- [x] File-first Vault directory and Markdown starter templates.
- [x] Copy Ontology 0.2.1 and verify protected assets with SHA-256.
- [x] Preserve user-edited Markdown on reinitialization.
- [x] MCP tools and optional MCP Apps panel wired to native flow.
- [ ] npm install/build in a network-enabled release environment.
- [ ] MCP Inspector protocol test and actual MCP Apps rendering.
- [ ] Host-by-host tests for Claude, Cursor, Codex and WorkBuddy.
- [ ] Signed self-contained Node installer and automatic host configuration adapters.
- [ ] Static encryption, OS Keychain and multi-device conflict resolution.
- [ ] Node-native Capture Runtime replacement.

The project remains in `transitional_skill_development`.


### 0.5.3 — Node-native Agent Bootstrap（当前预览）
- [x] Node 原生 doctor / plan / apply / verify。
- [x] 通过 MCP 工具与可选 MCP Apps 初始化 File-first Vault。
- [x] 复制冻结 Ontology 0.2.1 并校验 SHA-256。
- [x] 用户编辑文件保护、路径与符号链接安全检查。
- [ ] npm install/build 与 MCP Inspector 联调。
- [ ] Claude、Cursor、Codex、WorkBuddy 宿主逐一验收。
- [ ] 签名安装器、托管 Node 发行版与 Agent 配置适配器。
