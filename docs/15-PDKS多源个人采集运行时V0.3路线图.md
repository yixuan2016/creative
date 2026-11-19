# PDKS 多源个人采集运行时 V0.3 路线图

## 1. 核心判断

PDKS / PALOS 的长期价值不是“把更多数据塞进知识库”，而是持续理解个人每天正在发生什么，并在明确授权下把事件、状态、经验和上下文沉淀为个人可控的数智资产。

因此，多源采集运行时必须同时解决：来源连接、身份和权限、证据定位、事件抽取、跨源融合、持续记忆、状态重建、Agent 上下文与撤权删除。

## 2. 分层运行时

1. **Connector Layer**：文件、日历、邮件、会议、聊天、任务、录音设备、浏览器和 Agent 来源。
2. **Capture Layer**：增量游标、checkpoint、幂等、版本、限流、重试、断点恢复。
3. **Evidence Layer**：内容哈希、原文引用、页码/段落/时间码、敏感度和保留策略。
4. **Event Intelligence Layer**：Observation、Event Candidate、Assertion、Entity Resolution、Event Linking。
5. **Memory & State Layer**：事件账本、持续记忆、对象状态、决策和承诺追踪。
6. **Context & Agent Layer**：任务级最小上下文、Agent 订阅和消费、执行审批。
7. **Governance Layer**：Consent、Purpose Limitation、Data Subject、Retention、Revocation、Audit、Deletion。

## 3. 连接器优先级

### 第一批
- 本地文件夹和手动导入；
- 日历只读；
- 钉钉官方 DWS CLI 只读；
- 邮件只读；
- 任务系统只读。

### 第二批
- 会议转写与录音卡/设备；
- ASR/OCR；
- 浏览器与桌面活动摘要；
- 个人 Agent 工具调用和工作产物。

所有连接器必须遵守同一 Connector Manifest、Consent Grant、Source Identity、Checkpoint、SyncRun 和 Audit 契约。

## 4. 钉钉 DWS CLI 的适配原则

不猜测 CLI 参数。必须先获取用户实际安装的官方 CLI 版本、帮助输出、命令样例和脱敏 JSON 输出。执行时使用 argv 数组而非 shell 字符串，只允许经过审核的白名单只读子命令，设置超时、输出大小限制和审计。不得把 Access Token、Cookie 或密钥写入日志或 Source 元数据。

## 5. 个人—企业事件投影

个人域事件默认由个人控制。某条事件即使涉及企业项目，也不自动成为企业数据。

跨域投影至少需要：
- 数据主体和数据控制者；
- 明确的企业项目/业务用途；
- 最小字段/断言白名单；
- 用户授权和企业策略同时通过；
- 来源证据与原始内容隔离；
- 可撤回、可追溯、可删除；
- 企业侧只消费授权投影，不读取个人原始材料。

健康、财务、家庭等高敏感生活数据不进入首批工作试点。

## 6. V0.3.3—V0.4 建议顺序

| 阶段 | 工作包 | 验收 |
|---|---|---|
| V0.3.3 | PALOS 实际 Schema 映射评审 | 结构指纹、字段语义和主键关系确认 |
| V0.3.4 | Worker Heartbeat / 运维恢复 | 长任务租约续期、取消、失败重放 |
| V0.3.5 | 钉钉 DWS 只读适配 | 使用真实 CLI Profile，白名单 argv 和脱敏输出 |
| V0.3.6 | 日历/邮件/任务连接器 | 授权、游标、幂等和证据链一致 |
| V0.4 | 多源融合与持续记忆 | 误合并、漏合并、状态准确率和人工修正成本可测 |
| V0.5 | Multi-Agent Event Runtime | Agent 事件提交/订阅/消费与权限隔离 |

## 7. 明确不做

- 不建设无授权的全量个人监控；
- 不将个人数据默认汇聚到企业；
- 不用相似度自动合并现实事件；
- 不让 Agent 直接写权威事实；
- 不在未取得 PALOS Schema 时生成生产迁移；
- 不在未核验官方 DWS CLI 时执行未知命令；
- 不以合成数据指标宣称真实准确率。
