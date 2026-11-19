# 普通用户指南：在 Agent 里初始化 PDKS 0.5.3

## 你需要准备什么？

- 一个支持本机文件与命令执行的 Agent，例如 Codex 或 WorkBuddy；
- Node.js 22.12+；
- PDKS 0.5.3 发布包已经下载并解压；
- 不需要先安装 Python，也不需要先配置钉钉。

如果你使用的是纯云端 Agent，没有本地执行能力，它无法直接创建你电脑上的文件。请换成本地 Agent，或先配置经过授权的本地桥接。

## 第一次安装 Agent Bridge

1. 把解压后的 PDKS 文件夹交给本地 Agent。
2. 对 Agent 说：

   > 请检查这个 PDKS 包，先只做环境检测和安装计划，不要安装或修改文件。把将要安装的依赖、路径、网络访问和风险告诉我。

3. 检查 Agent 给出的 Node.js 版本与 npm 依赖计划。
4. 确认后，让 Agent 执行对应平台脚本：

   macOS / Linux：

   ```bash
   ./setup/install-agent-bridge.sh --confirm "INSTALL PDKS AGENT BRIDGE"
   ```

   Windows PowerShell：

   ```powershell
   .\setup\install-agent-bridge.ps1 -Confirm "INSTALL PDKS AGENT BRIDGE"
   ```

5. 让 Agent 运行 `node agent-native/bin/pdks-agent.js config --host generic`，查看 MCP 配置。
6. 通过 Agent 自己的 MCP 设置界面添加配置并重载连接。当前版本只生成配置预览，不会自动改写宿主设置。

## 在 Agent 中初始化

连接成功后，直接说：

> 帮我初始化 PDKS。先检查环境和推荐路径，展示计划。不要连接任何数据源，也不要开始采集。

Agent 应按顺序执行：

1. `pdks_native_doctor`：检查环境；
2. `pdks_native_plan`：生成初始化计划；
3. 展示应用配置目录、Vault 目录、Ontology 版本、写入动作和未加密风险；
4. 让你确认精确计划；
5. 你输入 `CONFIRM INITIALIZE PDKS` 并明确接受未加密风险；
6. `pdks_native_apply`：创建本地目录、模板和 Ontology 文件；
7. `pdks_native_verify`：检查文件与哈希。

如果 Agent 没有交互面板，以上步骤也可以完全通过普通对话完成。

## 初始化后会得到什么？

默认知识库位置：`~/PDKS-Vault`。可用 Obsidian 直接打开这个文件夹，也可用 VS Code 或普通文件管理器查看。

你会看到 Inbox、Events、Knowledge、Entities、Tasks、Projects、Reflections、Archive 和 Source Records 等目录。

## 当前不会自动做什么？

- 不会读取你的钉钉、邮件、日历、录音或私人文件；
- 不会自动安装或登录 DWS；
- 不会导入历史数据；
- 不会开启后台常驻采集；
- 不会开启云同步；
- 不会自动修改其他 Agent 的配置。

## 关于 Python Runtime

这次初始化不需要 Python。若未来需要自动采集，需单独安装仍基于 Python 的 Capture Runtime，并为每个数据源分别授权。请不要把“初始化 Vault”理解成“同意自动采集”。

## 安全提醒

当前版本的本地文件没有静态加密。请先使用合成数据或非敏感测试材料，不要存放密码、身份证件、财务隐私、医疗资料或其他敏感信息。

## 常见问题

**我可以不用 Obsidian 吗？** 可以。PDKS Vault 是普通文件夹，Markdown 与 JSON 文件可用其他工具打开。

**为什么要输入确认短语？** 确认绑定到已审阅的精确路径与计划哈希，防止 Agent 在路径或计划改变后仍沿用旧授权。

**能否换一个 Agent？** 可以。新 Agent 只需接入同一个本地 PDKS MCP Server，并按授权范围使用同一 Vault。

**云端 ChatGPT 能否直接创建我电脑里的 Vault？** 不能仅凭远程 MCP 地址做到。必须有经过授权的本地执行桥接。

**现在就能自动记录所有生活和工作数据吗？** 不能。当前是初始化与过渡阶段采集 Runtime。自动采集、DWS、邮件、日历和录音接入仍需后续独立实施与授权。
