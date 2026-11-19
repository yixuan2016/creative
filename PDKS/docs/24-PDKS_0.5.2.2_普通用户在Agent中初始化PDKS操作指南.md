# PDKS 0.5.2.2 — 普通用户在 Agent 中初始化 PDKS 操作指南

> 目标：让普通用户尽可能在 Codex、WorkBuddy 或其他支持本地 MCP 的 Agent 中完成 PDKS 初始化。  
> 版本：Agent Bridge 0.1.0 · Setup Skill 0.2.0  
> 当前边界：仍是实验性过渡版本；尚未完成自动修改所有 Agent 配置文件。

## 1. 先理解一次性准备和日常使用的区别

**一次性准备**：在本地 Agent 中安装 PDKS Agent Bridge，并把 MCP 服务添加到 Agent。此步骤需要 Node.js 22.12+、npm、Python 3.10+，并需要用户批准依赖安装和 MCP 配置。

**日常使用**：连接完成后，不需要再打开命令行。用户可以直接在 Agent 对话中说“初始化 PDKS”“检查我的 PDKS”“打开知识库配置”等，由 Agent 调用 MCP 工具完成。

云端 Agent 如果没有本机执行桥，不能直接读写本地电脑文件。请使用具备本地命令执行能力的桌面 Agent。

## 2. 一次性安装 Agent Bridge

将完整 PDKS 工程包解压到本机一个稳定目录，例如：

```text
~/Applications/PDKS/
```

然后在支持本地文件和终端操作的 Agent 中提出：

> 请先阅读 PDKS 包里的 `skills/pdks-setup/SKILL.md` 和 `agent-native/README.md`。检查 Node.js、npm 和 Python 环境；展示将要安装的 npm 依赖与本地改动；得到我确认后，运行 `setup/install-agent-bridge.sh`（Windows 使用 `setup/install-agent-bridge.ps1`）。不要修改任何 Agent 配置文件，先只生成连接配置片段供我审阅。

安装脚本第一次只展示计划；用户确认后，Agent 使用 `--confirm "INSTALL PDKS AGENT BRIDGE"`（Windows 使用 `-Confirm "INSTALL PDKS AGENT BRIDGE"`）再次运行。脚本只会在 `agent-native/` 下安装 npm 依赖并构建 MCP Apps UI，不会自动修改 Agent 配置。

## 3. 把 PDKS MCP 服务添加到 Agent

安装脚本最后会输出一个通用 MCP 配置片段。其核心结构如下：

```json
{
  "mcpServers": {
    "pdks": {
      "command": "node",
      "args": ["/absolute/path/to/PDKS/agent-native/bin/pdks-agent.js", "mcp"],
      "env": { "PDKS_BUNDLE_ROOT": "/absolute/path/to/PDKS" }
    }
  }
}
```

将路径替换为真实解压路径，并通过 Agent 自己的 MCP 设置界面或配置文件添加。不要把示例路径原样复制。保存后按 Agent 要求重启或重新加载 MCP 服务。

PDKS 0.5.2.2 只生成配置片段，不自动改写宿主配置文件；不同 Agent 的配置格式、位置和能力需按实际版本确认。

## 4. 在 Agent 中完成初始化

连接后，直接对 Agent 说：

> 帮我初始化 PDKS，先检查环境并展示安装计划，不要立即安装。

Agent 应依次调用：

1. `pdks_doctor`：只读环境检查；
2. `pdks_bootstrap_plan`：生成安装计划和哈希；
3. `pdks_setup_wizard`：如果宿主支持 MCP Apps，则打开交互式配置面板；
4. 用户查看安装位置、Vault 位置、依赖下载和未加密风险；
5. 用户输入 `CONFIRM INSTALL PDKS`，并明确确认本地数据未加密；
6. Agent 调用 `pdks_bootstrap_apply`；
7. Agent 调用 `pdks_verify`。

如果 Agent 不支持 MCP Apps，仍然可以通过普通对话和 MCP 工具完成相同流程。

## 5. 初始化后如何查看知识库

默认 Vault 位于当前用户 Home 目录下的 `PDKS-Vault`。默认不放在 Documents、OneDrive 或 iCloud 等可能自动云同步的目录中；用户可以在初始化计划里主动选择其他位置。

打开 Obsidian，选择“打开文件夹作为 Vault”，选择 `PDKS-Vault` 即可。也可以使用 VS Code、Typora 或任何 Markdown 编辑器。

初始化会复制 Ontology 0.2.1 版本化文件，并创建运行配置；不会自动采集钉钉、邮件、日历、会议录音或其他个人数据。

## 6. 当前版本还不能做什么

- 不能自动为所有 Agent 修改 MCP 配置文件；
- 不能保证每个 Agent 都支持 MCP Apps；
- 不能在没有本地执行桥的云端 Agent 上安装本机程序；
- 不能自动安装托管 Python 运行时；
- 不能自动登录 DWS、订阅数据源或回填历史数据；
- 不提供静态加密、OS Keychain、云同步和多设备同步。

SQLite 和本地文件未加密。仅使用合成数据或非敏感测试材料。

## 7. 推荐的下一步产品完善

PDKS 0.5.2.3 应继续降低一次性接入门槛：提供 Agent Host 识别、配置文件 Plan / Apply、配置备份与回滚；同时完成 MCP Inspector 测试和各宿主真实版本兼容验收。随后再做托管 Python Runtime 或 Node-native Runtime，避免用户手工安装 Python。
