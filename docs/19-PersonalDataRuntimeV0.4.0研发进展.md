# Personal Data Runtime V0.4.0 Alpha 研发进展

**定位：** PDKS / Personal AI Life OS 个人数据运行时与多 Agent 协同验证
**语义基线：** Event Ontology V0.1、ADS 两级本体、三级数智底座
**状态：** 本地 Alpha 原型；不是生产系统

## 本轮目标

V0.3.x 已建立多源采集、证据关联、人工确认、状态上下文和来源生命周期治理。V0.4 增加两项能力：跨来源事件融合候选，以及有用途和敏感级别约束的 Agent Pull Runtime。

## WP 交付状态

| 工作包 | 状态 | 边界 |
|---|---|---|
| WP1 PALOS Adapter | 契约准备 | 已有只读 Schema Inspector/Profile；未取得真实 PALOS Schema，不声明生产兼容 |
| WP2 DingTalk DWS | Blocked | 等待官方 CLI 版本、帮助输出和脱敏 JSON；不猜测命令 |
| WP3 Event Fusion | Alpha 实现 | 可解释候选评分、人工裁决；不自动合并 Event |
| WP4 Agent Runtime | Alpha 实现 | Pull Inbox、一次性 Token、用途/敏感度过滤、Ack 和撤权 |

## ADS 对齐

- 上层共同本体继续表达 Source、Evidence、Observation、Event、Assertion、Participant、Relation、时间、认识状态和治理属性。
- 下层领域本体继续定义会议、决策、承诺、交付、风险等领域类型。
- 个人数智底座保留原始个人事件控制权；企业数智底座只接收经独立授权的业务投影；中心数智底座提供标准与治理，不因共享本体获得个人数据读取权。
- Personal AI Life OS 负责个人身份、记忆体验、任务、Agent 生命周期和交互入口；Event Intelligence Lab 是其中的事件运行时研究模块。

## 验证

- 86 项自动化测试通过；
- Python compileall 通过；
- UI JavaScript node --check 通过；
- Agent Pull 示例 Python 语法检查通过；
- OpenAPI 41 paths；
- 独立 MVP ZIP 解压后复测 86 passed。

## 重要限制

- Event Fusion 分数不是概率；未在真实个人语料上建立 Precision / Recall 结论。
- Agent Runtime 仅本地 Pull，不调用外部 Agent、不执行外部副作用。
- Agent 已复制到外部记忆的数据，不能由本地撤权自动擦除。
- 未连接真实 PALOS 数据库，未执行钉钉 DWS CLI。
- 不开放个人到企业自动投影，不支持多主机分布式运行时。

## 下一步

V0.4.1 建立融合黄金评测集；V0.4.2 基于脱敏 PALOS Schema 完成真实映射评审；V0.4.3 设计 Agent Memory Revocation Hook；之后再推进 Worker Heartbeat 和个人—企业受控投影。