# PDKS-STD-03-001：File-first Vault 存储标准

Baseline: File-first Storage 0.1.0  
Status: Preview; one-way projection adapter exists

## 格式
- 知识资产：UTF-8 Markdown + YAML Frontmatter。
- 来源和证据：JSON / JSONL。
- 原始附件：原始二进制，推荐 SHA-256 内容寻址。
- 清单：PDKS-MANIFEST.json。
- 索引：SQLite 可重建，不作为唯一知识副本。

## 必需元数据
知识页必须包含稳定 pdks_id、pdks_type、schema_version、title、created_at、updated_at、status、domains、sensitivity 和来源引用。

## 兼容性
核心关系使用标准相对 Markdown 链接。Obsidian Wikilinks、Dataview、Canvas 和插件字段为可选扩展，不得作为唯一语义表达。

## 文件保护
原始证据追加写入；用户编辑冲突不得静默覆盖；文件写入原子化并校验哈希；文件移动不得改变 pdks_id。

## 成熟度限制
FileFirstVault 0.1.0 当前仅提供从现有 Runtime 向 Vault 的单向投影、哈希校验和独立索引重建。不是完整双向同步，也不重建 Consent、Token 和完整运行状态。当前 Vault 未静态加密，不适合保存敏感真实数据。
