# PDKS 0.5.2.2.1 — Agent 初始化安全边界与交互契约

> 版本：Agent Bridge 0.1.1  
> 阶段：`transitional_skill_development`  
> 成熟度：Experimental / Preview

## 1. 产品原则

PDKS 初始化应当由用户当前使用的 Agent 发起，通过 MCP 工具完成环境检查、计划生成、用户确认、执行和验收。CLI 作为备用入口保留，不是普通用户的必经路径。

Agent 是交互入口，不是权限主体。真正执行文件系统变更的是用户设备上的本地 PDKS Bridge；云端 Agent 没有本地 Bridge 时，不得声称能够访问用户电脑。

## 2. 初始化状态机

```text
NOT_INSTALLED
  -> DIAGNOSING (read-only)
  -> PLAN_READY (read-only, exact paths + dependencies + actions + warning)
  -> AWAITING_APPROVAL
  -> APPLYING (mutating, exact plan hash + phrase + risk acknowledgement)
  -> VERIFYING (read-only)
  -> READY | DEGRADED | FAILED
```

取消、拒绝或超时都必须保持在未安装状态，不得产生部分安装的隐式副作用。若执行中失败，必须报告实际完成步骤和恢复建议，不得宣称成功。

## 3. 工具权限分级

| 工具 | 权限 | 是否需要逐次确认 |
|---|---|---|
| `pdks_doctor` | 只读 | 否 |
| `pdks_bootstrap_plan` | 只读 | 否 |
| `pdks_vault_status` | 只读元数据 | 否 |
| `pdks_agent_config_preview` | 只读预览 | 否 |
| `pdks_verify` | 只读 | 否 |
| `pdks_setup_wizard` | 交互展示 | 否；执行另行确认 |
| `pdks_bootstrap_apply` | 文件写入、依赖安装 | 是，必须精确确认 |

未来新增数据源连接、历史导入、后台服务、云同步、备份上传和删除操作，必须作为独立授权能力，不能继承安装确认。

## 4. 双路径安全约束

### 4.1 路径范围

- 安装目录和 Vault 目录必须位于当前用户主目录内。
- 现有路径组件在检查时进行真实路径解析，不能只用字符串前缀判断。
- 符号链接最终指向主目录之外时拒绝执行。
- 安装目录与 Vault 目录不能相同，也不能互相嵌套。
- 不覆盖非 PDKS 的非空目录，不覆盖用户编辑的配置或本体文件。
- 默认 Vault 避开常见自动同步目录；云同步必须独立授权。

### 4.2 计划绑定

安装计划必须包含平台、版本、安装目录、Vault 目录、依赖、网络访问、执行动作和风险说明。用户批准的 SHA-256 必须与执行前重新生成的计划一致。任何路径或依赖变化都必须重新生成计划并重新征求确认。

### 4.3 明确风险确认

当前预览版 SQLite 与 Vault 未提供静态加密。执行安装前必须展示该事实，并要求用户明确承认。用户拒绝时停止安装。此确认不代表用户同意连接任何数据源或开始采集。

## 5. 交互降级策略

优先级如下：

1. MCP Apps：宿主支持时提供路径选择、检查状态、计划预览和确认面板。
2. MCP Elicitation：宿主支持结构化确认时请求确认字段。
3. 对话确认：不支持 Apps/Elicitation 时，Agent 用普通对话展示完整计划，用户明确输入确认短语。
4. CLI：仅作为开发者、运维和故障排查备用路径。

任何一种 UI 都不能绕过同一套后端审批校验。

## 6. 跨 Agent 兼容原则

- MCP 工具名、参数 schema、返回结构和安全契约保持宿主无关。
- Skill 负责教 Agent 何时调用、如何解释结果、何时停下等待用户。
- MCP Server 负责能力执行和硬性校验。
- MCP Apps 仅是可选呈现层，不是唯一初始化路径。
- Agent 配置默认只生成预览，不自动修改宿主配置文件。
- 云端 Agent 必须通过用户明确安装的本地 Bridge 才能访问本地文件。

## 7. 当前实现与未完成项

已实现：Node.js 本地 MCP Bridge 源码、工具定义、可选 MCP Apps 向导源码、计划哈希确认、Python Bootstrap Engine 调用、路径真实解析和目录重叠拒绝、CLI 备用入口。

未完成或未验收：npm 依赖安装、MCP Inspector 握手、MCP Apps 构建、Claude/Cursor/Codex/WorkBuddy 真实宿主联调、托管 Python 运行时、Node 原生 Runtime、静态加密、Keychain、远程 Relay、多设备同步。

## 8. 验收用例

- 主目录内正常路径可通过。
- 主目录外路径必须拒绝。
- 指向主目录外的符号链接必须拒绝。
- 安装目录与 Vault 相同必须拒绝。
- 安装目录包含 Vault 或 Vault 包含安装目录必须拒绝。
- 计划哈希不匹配必须拒绝。
- 确认短语不匹配必须拒绝。
- 未确认未加密风险必须拒绝。
- 拒绝安装后不得创建目标目录或修改 Agent 配置。
- 无 MCP Apps 宿主仍可通过普通 MCP 工具和对话完成完整流程。
