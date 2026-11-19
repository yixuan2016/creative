# PDKS 0.5.0 普通用户试用指南

> 这是本地实验原型，不是生产服务。首次只建议使用自己主动提供的少量非敏感测试材料。

## 你需要做什么？

1. 下载完整工程包并解压。
2. 安装 Python 3.10+。
3. 按下面命令启动本地 Runtime。
4. 给你使用的 Agent 配置一个独立 Token 和工具适配器。
5. 把一段文字或文件交给 Agent，Agent 自动整理成候选记录。
6. 由你确认后，才成为正式个人记录。

你不需要自己编写 JSON、RDF 或 Ontology。

## 第一次安装

在解压后的工程包根目录：

```bash
python -m venv .venv
```

激活环境：

```bash
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

安装依赖并初始化：

```bash
python -m pip install -e runtime

pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault init --owner urn:pdks:owner:me
```

## 启动本地 Runtime

```bash
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault serve --host 127.0.0.1 --port 8765
```

保持终端窗口运行。服务仅监听本机，不要修改为公网地址。

## 给不同 Agent 分别创建 Token

另开一个终端，激活相同虚拟环境：

```bash
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault token-create --owner urn:pdks:owner:me --agent-id my-agent --scopes capture:read,capture:write,records:read,records:propose
```

每个 Agent 应使用自己的 Token。Token 只显示一次，不要发到聊天、截图或代码仓库。当前还需要宿主侧配置 HTTP 工具，Runtime 不会自动把工具安装到所有 Agent。

## 运行完整合成演示

在 `runtime/` 目录运行 `python examples/demo_local_flow.py`，可体验采集、候选记录、用户确认和导出校验的完整流程。演示只使用临时目录和合成会议材料。

## 手工试用一条文字

```bash
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault capture-text --owner urn:pdks:owner:me --domain work --text "今天开会讨论了项目计划，决定先验证手机端采集入口。"
```

## 哪些材料现在能提取？

| 文件类型 | 当前处理 |
|---|---|
| TXT / MD / CSV / JSON | 可提取文本 |
| HTML | 可提取可见文本 |
| EML / ICS | 可提取部分正文和字段 |
| DOCX | 可提取正文段落 |
| PDF | 暂存原文件，等待 PDF 提取器 |
| 图片 / 音频 / 视频 | 暂存原文件，等待 OCR / ASR / 多模态提取器 |
| XLSX / PPTX | 原文件保留，暂未实现深度提取 |

会议录音上传成功，不代表已经转写。要先有转写文本或未来 ASR 适配器。

## 当前自动化边界

- 手工输入和上传：本地可用。
- 钉钉、微信、邮件、日历原生连接器：未实现；可以先由用户导出再导入。
- 麦克风、录音卡、定位、桌面活动：未实现，默认关闭。
- 远程 Agent 访问本地 Runtime：未实现。云端 Agent 不能直接访问用户电脑的 127.0.0.1。
- 本地 SQLite 未加密。请先使用非敏感测试材料，不要把数据库放到公共同步目录。

## 重要提醒

1. 用户上传材料不代表可以违反公司保密规定或第三方隐私。
2. 自动连接器、设备采集必须有明确授权。
3. Agent 生成的是候选记录，需要用户审核。
4. 撤销授权只阻止未来采集，不会自动清除已有材料。
5. 本地删除不能清除历史备份、外部副本或 OS 快照。
6. 不要把 API Token 写进 Skill 文件或 GitHub。
