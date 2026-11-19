# Personal Assistant OS · Interactive Prototype

ADS-WORK-10.1 浏览器交互原型。所有演示数据均为虚构内容，所有状态变更仅在当前页面会话内存中生效。

## 快速体验

直接打开 \`index.html\`，或在仓库根目录启动一个静态 HTTP 服务：

\`\`\`bash
python -m http.server 8000
\`\`\`

然后访问：

\`\`\`
http://localhost:8000/prototype/personal-assistant-os/
\`\`\`

无需 npm install、外部前端库、API Key 或账号连接。

## 页面与功能

1. **今日**：每日摘要、日程、待确认、目标进度、Agent 审批和快速记录。
2. **收集箱**：新增文字、模拟语音转写、形成事件、沉淀记忆候选。
3. **时间线**：30 天逐日浏览、工作/生活/学习筛选和关键词搜索。
4. **目标与承诺**：目标进度、承诺责任确认、完成和暂停。
5. **我的 AI**：记忆确认/纠正/撤回、来源暂停/恢复/撤销、隐私偏好和自动化开关。

其他交互：
- Ctrl/⌘ + K 打开全局快速入口；
- Agent 动作可以查看内容预览、风险和副作用，并批准或拒绝；
- 演示会话可以导出 JSON；
- 重置演示可恢复初始样例数据。

## 工程结构

- \`index.html\`：语义化页面结构；
- \`styles.css\`：响应式视觉设计；
- \`demo-data.js\`：与 examples 下 JSON fixture 一致的虚构数据；
- \`core.js\`：无网络副作用的交互领域逻辑；
- \`core.test.js\`：Node.js 内置测试。

## 运行测试

在仓库根目录：

\`\`\`bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s prototype -v
node --check prototype/personal-assistant-os/core.js
node --check prototype/personal-assistant-os/app.js
node --check prototype/personal-assistant-os/demo-data.js
node --test prototype/personal-assistant-os/core.test.js
\`\`\`

## 明确限制

- 不连接真实钉钉、日历、邮件、文档或企业系统；
- 不调用麦克风，不进行后台录音；
- 不调用真实 AI 模型；
- 不执行真实任务创建、消息发送、企业投影或外部 Agent 操作；
- 不使用浏览器持久化存储；
- 刷新页面会恢复初始样例数据；
- 撤回记忆只是演示状态变化，不代表生产环境已删除派生索引、缓存或副本。

生产实现需接入 ADS-WORK-08 授权控制、ADS-WORK-09 个人运行时和 PDKS 个人数据标准，并通过安全、隐私和业务评审。
