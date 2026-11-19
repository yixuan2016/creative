# PDKS 0.5.2.1 — File Store Adapter 使用与验收指南

> 版本：FileFirstVault 0.1.0  
> Runtime：0.1.1（过渡阶段参考实现）  
> 研发边界：transitional_skill_development  
> 状态：Experimental / Preview

## 1. 本版本解决什么问题？

本版本在现有 Capture Runtime 旁边增加文件存储适配器，使当前数据库中的来源记录、证据和已确认知识可以投影为普通文件，供 Obsidian、VS Code、Typora 和其他 Markdown 工具直接查看。

它提供：
- PDKS Vault 初始化；
- Markdown + YAML Frontmatter 知识笔记；
- 来源与证据 JSONL；
- 原始附件 SHA-256 内容寻址；
- 文件清单与哈希校验；
- 可重建的独立 SQLite 文件索引；
- 避免静默覆盖用户编辑的冲突保护。

**重要：本版是从现有 Runtime SQLite 向文件 Vault 的单向投影/迁移原型。** 现有 CaptureRuntime operational DB 仍然是当前运行权威数据源。FileFirstVault 还不是事务性写入主库，不支持完整双向同步，也不能重建授权、Token、审计等全部运行状态。

## 2. 安装前提

本版本仍使用现有 Python Runtime，因此需要：
- Python 3.10 或更高版本；
- 已安装项目 Runtime 依赖；
- 本地可写目录；
- 用户明确同意将哪些现有数据投影到目标 Vault。

Node.js + TypeScript Bootstrap 仍是后续跨平台安装方向，当前没有声称已交付原生 `.exe`、`.pkg` 或 `.AppImage` 安装器。

## 3. 初始化 Vault

在已安装 Runtime 的终端中执行：

```bash
pdks-runtime vault-init --file-vault "$HOME/PDKS-Vault"
```

Windows PowerShell：

```powershell
pdks-runtime vault-init --file-vault "$HOME\PDKS-Vault"
```

初始化会创建：
- `README.md`
- `PDKS-MANIFEST.json`
- 用户可读知识目录；
- 来源与证据目录；
- `assets/sha256/`；
- `.pdks/index/` 等隐藏运行目录。

如果目标目录已经包含其他文件、且没有 PDKS manifest，命令会拒绝初始化，避免覆盖现有 Obsidian Vault 或个人文件夹。

## 4. 从当前 Runtime 投影数据

先向用户说明：
- 将投影哪些 owner 的数据；
- 是否包含候选知识；
- 是否复制原始附件；
- 目标文件夹是否会被 Obsidian 或其他同步软件同步。

默认只投影已确认知识，不复制原始附件：

```bash
pdks-runtime \
  --db ./data/pdks.sqlite3 \
  --vault ./data/blobs \
  vault-sync \
  --owner urn:pdks:owner:me \
  --file-vault "$HOME/PDKS-Vault"
```

如果用户明确批准复制原始附件，再加：

```bash
--include-raw-sources
```

如果用户明确批准同时导出尚未审核的候选知识，再加：

```bash
--include-candidates
```

候选知识会进入 `00-Inbox/Candidates/`，不会混入已确认知识目录。

## 5. 在 Obsidian 中打开

1. 打开 Obsidian。
2. 选择“打开文件夹作为 Vault”（Open folder as vault）。
3. 选择 `PDKS-Vault`。
4. 即可查看 PDKS 生成的 Markdown 知识页。

基础查看不需要安装 PDKS 插件。Obsidian 插件、Wikilinks、Dataview 均不是 PDKS 文件格式的前置条件。

其他软件：
- VS Code：打开 `PDKS-Vault` 文件夹；
- Typora：直接打开 `.md`；
- 其他 Markdown 编辑器：直接打开 `.md`。

## 6. 校验文件完整性

```bash
pdks-runtime vault-verify --file-vault "$HOME/PDKS-Vault"
```

该命令根据 `PDKS-MANIFEST.json` 校验纳入清单的文件数量、大小和 SHA-256。

当前 manifest 默认覆盖用户可读资产、JSONL 和附件；`.pdks/` 下的缓存、索引、运行状态不纳入可迁移资产哈希清单。

## 7. 重建文件索引

```bash
pdks-runtime vault-rebuild-index --file-vault "$HOME/PDKS-Vault"
```

重建位置：

```text
PDKS-Vault/.pdks/index/pdks-file-index.sqlite3
```

该 SQLite 仅用于加速文件搜索和元数据查询。删除它后，可以从 Markdown、JSONL 和附件重新生成。

**它不是 CaptureRuntime 的 operational DB。** 它不包含 consent、API token、完整审计日志、DWS 同步游标或全部运行状态。

## 8. 目录说明

```text
PDKS-Vault/
├── 00-Inbox/Candidates/       # 尚未审核的候选知识
├── 10-Daily/                  # 每日记录
├── 20-Events/                 # 事件知识页
├── 30-Projects/               # 项目和组织知识
├── 40-People/                 # 人物知识
├── 50-Meetings/               # 会议知识
├── 60-Decisions/              # 决策/断言
├── 70-Tasks/                  # 行动和任务
├── 80-Knowledge/              # 通用知识资产
├── 85-Life/                   # 个人生活域
├── 90-Source-Records/         # 原始来源、Evidence、附件索引 JSONL
├── 95-Archive/                # 归档
├── assets/sha256/             # 原始附件
├── PDKS-MANIFEST.json         # 可迁移文件哈希清单
└── .pdks/
    ├── index/                 # 可重建文件索引
    └── conflicts/             # 用户编辑冲突的 incoming 副本
```

## 9. 文件保护和冲突规则

- 来源 JSONL 以稳定对象 ID 去重；同一 ID 不同内容时拒绝静默覆盖。
- 附件以 SHA-256 去重；同内容不同文件名复用同一份内容文件。
- Markdown 知识页以稳定 `pdks_id` 生成文件名。
- 如果目标 Markdown 已被用户编辑，后续投影不会覆盖用户版本；新生成版本放入 `.pdks/conflicts/`，等待用户/Agent 比较处理。
- 不允许将 Token、密码或密钥写入 Markdown、JSONL 或 manifest。
- 不默认启用云同步、Git 远端或第三方备份。

## 10. 已知限制

| 能力 | 当前状态 |
|---|---|
| 初始化 PDKS Vault | 已实现 |
| Runtime → 文件 Vault 单向投影 | 已实现 |
| Markdown 知识页 | 已实现 |
| Source / Evidence JSONL | 已实现 |
| 附件内容哈希去重 | 已实现 |
| Manifest 哈希验证 | 已实现 |
| 文件索引重建 | 已实现 |
| Obsidian 直接打开样例 Vault | 结构兼容，建议用户本机验收 |
| 采集时实时双写文件 | 未实现 |
| Obsidian 编辑回写 Runtime | 未实现 |
| 完整冲突合并 UI | 未实现 |
| 文件 Vault 重建 operational DB | 未实现 |
| 静态加密和 OS Keychain | 未实现 |
| 多设备同步 | 未实现 |
| 原生 Node 安装器 | 未实现 |

## 11. 验收清单

- [ ] 在新目录初始化 Vault。
- [ ] 对测试 Runtime 执行 `vault-sync`。
- [ ] 使用 `vault-verify` 校验 manifest。
- [ ] 使用 `vault-rebuild-index` 重建索引。
- [ ] 在 Obsidian 中打开 Vault 并阅读 Markdown。
- [ ] 在 Obsidian 中编辑一篇笔记，再重复投影，确认原笔记未被覆盖。
- [ ] 复制整个 Vault 到另一目录，重复验证和索引重建。
- [ ] 确认云同步未在未经批准时开启。
- [ ] 仅使用合成或非敏感测试数据，直到加密和密钥管理验收通过。

## 12. 下一步

0.5.2.2 应完成事务性 Outbox 和文件持久化恢复；0.5.2.3 应完成 Markdown 双向变更检测与冲突解决；0.5.2.4 再将 Vault 初始化、迁移、校验和索引重建纳入 Node.js / TypeScript Bootstrap。

在完成上述能力前，本版本仍属于过渡阶段的参考实现，不应宣称已经实现完整个人数智底座。
