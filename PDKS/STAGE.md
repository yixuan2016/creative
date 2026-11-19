# PDKS 0.5.3 — 过渡阶段 Skill 与 Node-native Bootstrap 工程版

**当前研发阶段：`transitional_skill_development`。** 本版本依然是实验性 Skill 工程和本地参考运行时，不是最终个人数智底座，不是生产级服务，也不是已完成的 Personal AI Life OS。

## Version matrix

- PDKS Track: `0.5.3`（Experimental / Preview）
- Agent Bridge: `0.2.0`（Node.js MCP STDIO + optional MCP Apps）
- Native Bootstrap: `0.2.0`（Node built-in APIs；初始化 Vault 不需要 Python）
- Setup Skill: `0.3.0`
- Personal Knowledge Skill: `0.3.4`（保持不变）
- Capture Runtime: `0.1.1`（可选 Python Runtime）
- File Store Adapter: `0.1.0`（单向投影参考实现）
- DWS Connector: `0.1.0`（真实租户投递尚未验证）
- PDKS Standard: `0.1.0`（冻结）
- Record Schema: `0.1.x`（冻结基线）
- Ontology: `0.2.1`（冻结）
- Event Taxonomy: `0.1.0`（冻结）

## 0.5.3 本轮研发定位

将首次知识库初始化从 Python Bootstrap Engine 中解耦，改为 Node.js 原生 File-first 初始化。用户通过本地 Agent 的 MCP 工具或可选交互面板完成环境检查、路径确认、Vault 创建和本体资产校验。Python Capture Runtime、数据源连接和自动采集仍是后续独立授权阶段。

## 已实现

- Node Native Bootstrap 0.2.0：doctor / deterministic plan / apply / verify。
- 采用 Node 内置模块创建用户配置目录、Vault 目录、Markdown 模板和 Ontology 0.2.1 资产。
- 计划 SHA-256 + 精确确认短语 + 未加密风险确认。
- 符号链接逃逸检查、目录重叠检查、拒绝非 PDKS 非空目录。
- 重复初始化保留用户编辑的 Markdown；受保护 Ontology 资产进行 SHA-256 验证。
- MCP Server 增加 `pdks_native_*` 工具；MCP Apps 向导切换到 Node 原生流程。
- Setup Skill 更新为 Node 原生初始化优先、Python Runtime 可选。
- CLI 继续保留，作为开发者与故障排查入口。

## 仍未实现或未验收

- npm registry 依赖安装与 Vite 构建未执行（当前环境无法联网，且本地无依赖缓存）。
- MCP SDK 端到端协议联调、MCP Apps 实际宿主渲染未执行。
- Claude、Cursor、Codex、WorkBuddy 等真实宿主逐一兼容性验收未执行。
- 自动写入 Agent 配置、签名安装器、托管 Node 发行版未实现。
- Capture Runtime 仍依赖 Python；尚未 Node 原生化。
- 静态加密、OS Keychain、云同步、多设备冲突合并未实现。
- DWS 真实租户事件投递未验证。

## 阶段门禁

- 保持 `transitional_skill_development`，不得宣称生产就绪。
- PDKS Standard、Record Schema、Ontology、Event Taxonomy 冻结基线不变。
- Vault 初始化、Runtime 安装、数据源授权、历史导入、后台采集、云同步为不同授权阶段。
- 默认不连接任何数据源，不采集，不启动后台服务，不开启云同步。
- 不将模拟数据测试表述为真实宿主或真实租户验收。
- 未加密版本不得用于敏感真实数据。