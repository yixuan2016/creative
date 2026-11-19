# creative｜ADS 数智底座与 AI 工作感知研究

本仓库用于沉淀围绕 ADS、个人数智底座、企业数智底座、业务领域中心数智底座，以及 AI 工作感知、企业运行上下文、运行认知引擎与数智资产化的研究成果。

## 研究专题

### 专题 01：多源工作感知与个人—企业数智资产协同

**基于多源工作感知的个人与企业数智资产生成及协同机制研究**

- [研究总报告（Markdown）](docs/01-基于多源工作感知的个人与企业数智资产生成及协同机制研究.md)
- [研究总报告（HTML 阅读版）](docs/01-基于多源工作感知的个人与企业数智资产生成及协同机制研究.html)

核心议题：多源工作感知、个人工作记忆、工作事件账本、个人资产到企业资产的授权晋升、企业标准业务数据、跨人能力复用验证。

### 专题 02：企业工作上下文基础设施与企业运行认知

**企业工作上下文基础设施与企业运行认知体系研究**

- [研究总报告（Markdown）](docs/02-企业工作上下文基础设施与企业运行认知体系研究.md)
- [研究总报告（HTML 阅读版）](docs/02-企业工作上下文基础设施与企业运行认知体系研究.html)

核心议题：企业工作上下文模型、企业运行状态、事件与业务对象关联、状态可信度、决策链、依赖关系、任务级 Agent 上下文包、企业运行认知能力。

### 专题 03：企业工作上下文统一数据模型与运行认知引擎

**企业工作上下文统一数据模型与运行认知引擎架构设计**

- [架构设计报告（Markdown）](docs/03-企业工作上下文统一数据模型与运行认知引擎架构设计.md)
- [架构设计报告（HTML 阅读版）](docs/03-企业工作上下文统一数据模型与运行认知引擎架构设计.html)

核心议题：统一事件模型、业务对象身份映射、关系与状态断言、决策/任务/风险/证据模型、运行认知引擎、Agent 上下文包、服务 API、数据治理和工程实施路线。

### 专题 04：企业工作上下文标准规范与最小可运行原型

**企业工作上下文标准规范与最小可运行原型设计**

- [工程规范与原型设计（Markdown）](docs/04-企业工作上下文标准规范与最小可运行原型设计.md)
- [工程规范与原型设计（HTML 阅读版）](docs/04-企业工作上下文标准规范与最小可运行原型设计.html)
- [JSON Schema 数据契约](schemas/ads-work-context-v0.1.schema.json)
- [OpenAPI 3.1 接口草案](openapi/ads-work-context-v0.1.yaml)
- [项目交付模拟数据](examples/project-delivery-seed-data.json)
- [Python 最小认知引擎](prototype/ads_context_engine.py)
- [原型行为测试](prototype/test_ads_context_engine.py)
- [Schema 合同测试](prototype/test_contract_schemas.py)
- [开发测试依赖](requirements-dev.txt)
- [原型运行说明](prototype/README.md)
- [GitHub Actions 测试工作流](.github/workflows/ads-context-prototype.yml)

核心议题：标准事件信封、JSON Schema、OpenAPI、幂等接入、权威状态重建、冲突保留、授权校验、任务级上下文包和项目交付场景验证。


### 专题 05：企业运行认知基础设施试点实施方案

**企业运行认知基础设施试点实施方案——以项目交付为例**

- [试点实施方案（Markdown）](docs/05-企业运行认知基础设施试点实施方案-以项目交付为例.md)
- [试点实施方案（HTML 阅读版）](docs/05-企业运行认知基础设施试点实施方案-以项目交付为例.html)

核心议题：样板项目选择、项目交付状态评审、权威数据源与协同线索、只读连接器、任务级上下文包、Agent 人工确认闭环、十周实施计划、业务指标、治理和 Go / No-Go。


### 专题 05 配套：试点执行模板

- [试点执行模板说明](pilot/README.md)
- [试点章程模板](pilot/试点章程模板.md)
- [数据源与权威字段矩阵（CSV）](pilot/数据源与权威字段矩阵模板.csv)
- [基线与验收指标采集表（CSV）](pilot/基线与验收指标采集模板.csv)
- [Agent 输出人工核验记录（CSV）](pilot/Agent输出人工核验记录模板.csv)


### 专题 06：企业运行认知引擎与企业 Agent 协同执行体系

**企业运行认知引擎与企业 Agent 协同执行体系设计**

- [协同执行体系设计（Markdown）](docs/06-企业运行认知引擎与企业Agent协同执行体系设计.md)
- [协同执行体系设计（HTML 阅读版）](docs/06-企业运行认知引擎与企业Agent协同执行体系设计.html)
- [Agent Task Envelope JSON Schema](schemas/ads-agent-task-envelope-v0.1.schema.json)
- [项目交付 Agent 委派示例](examples/ads-agent-project-delivery-review.json)
- [Agent 协同运行评估模板（CSV）](pilot/Agent协同运行评估模板.csv)

核心议题：ADS Context Plane、Agent Control Plane、Agent Execution Plane、Governance & Observability、Orchestrator、专业 Agent、任务契约、工具网关、动作风险分级、审批绑定、运行状态机、Trace、评测和分阶段实施。


### 专题 07：企业 Agent 能力资产化与跨业务复用

**企业 Agent 能力资产化、任务经验沉淀与跨业务复用机制研究**

- [研究报告（Markdown）](docs/07-企业Agent能力资产化与跨业务复用机制研究.md)
- [交互式 HTML 阅读版](docs/07-企业Agent能力资产化与跨业务复用机制研究.html)
- [Capability Asset JSON Schema](schemas/ads-capability-asset-v0.1.schema.json)
- [项目风险初筛能力样例](examples/ads-capability-project-risk-triage-v0.1.json)
- [跨人跨岗位复用评估模板（CSV）](pilot/能力资产跨人跨岗位复用评估模板.csv)
- [Capability Registry 目录与治理说明](capabilities/README.md)
- [Capability Manifest 合同测试](prototype/test_capability_asset_schema.py)

核心议题：Capability Asset、个人经验授权与抽象、Skill / Rule / Playbook / Workflow 边界、Capability Manifest、Registry、能力生命周期、P0—P5 跨人跨岗位复用验证、对照评测、迁移损失、能力运营和反馈治理。


### 专题 08：企业工作本体与事件驱动的个人—企业—领域协同

**企业工作本体与事件驱动的个人—企业—领域协同标准研究**

- [研究报告（Markdown）](docs/08-企业工作本体与事件驱动的个人企业领域协同标准研究.md)
- [交互式 HTML 阅读版](docs/08-企业工作本体与事件驱动的个人企业领域协同标准研究.html)
- [Work Ontology Manifest JSON Schema](schemas/ads-work-ontology-v0.1.schema.json)
- [Work Ontology Catalog](ontologies/ads-work-ontology-v0.1.json)
- [Personal Context Event JSON Schema](schemas/ads-personal-context-event-v0.1.schema.json)
- [个人事件到企业事件投影样例](examples/ads-personal-to-enterprise-event-projection-v0.1.json)
- [工作本体映射与事件质量评估模板（CSV）](pilot/工作本体与事件映射评估模板.csv)
- [本体与投影合同测试](prototype/test_work_ontology_contracts.py)

核心议题：五层工作本体、个人工作与生活上下文、企业工作本体、领域本体、事件语义、身份解析、语义映射、个人到企业最小必要投影、授权与撤回、Ontology Registry、版本兼容和项目交付试点。


### 专题 09：个人数智底座的持续记忆、事件账本与自主智能体

**个人数智底座的持续记忆、事件账本与自主智能体架构研究**

- [研究报告（Markdown）](docs/09-个人数智底座的持续记忆事件账本与自主智能体架构研究.md)
- [交互式 HTML 阅读版](docs/09-个人数智底座的持续记忆事件账本与自主智能体架构研究.html)
- [个人事件账本 JSON Schema](schemas/ads-personal-event-ledger-v0.1.schema.json)
- [个人持续记忆 JSON Schema](schemas/ads-personal-memory-item-v0.1.schema.json)
- [个人目标与承诺 JSON Schema](schemas/ads-personal-intent-object-v0.1.schema.json)
- [Personal Agent 动作与审批 JSON Schema](schemas/ads-personal-agent-action-v0.1.schema.json)
- [个人事件—记忆—Agent 端到端示例](examples/ads-personal-memory-loop-v0.1.json)
- [Personal Memory Engine 参考原型](prototype/personal_memory_engine.py)
- [个人记忆与 Agent 合同测试](prototype/test_personal_memory_contracts.py)

核心议题：个人事件账本、持续记忆、情景/语义/程序/偏好记忆、个人目标与承诺、任务级 Context Package、Personal Agent 风险分级、动作审批、执行核验、记忆纠错与删除传播、本地优先和多端同步。


### 专题 10：个人数智底座的产品形态、多终端感知入口与个人助理 OS

**个人数智底座的产品形态、多终端感知入口与个人助理 OS 交互架构研究**

- [产品与交互架构研究报告（Markdown）](docs/10-个人数智底座的产品形态多终端感知入口与个人助理OS交互架构研究.md)
- [交互式 HTML 阅读版](docs/10-个人数智底座的产品形态多终端感知入口与个人助理OS交互架构研究.html)
- [个人助理 OS Daily Brief JSON Schema](schemas/ads-personal-assistant-daily-brief-v0.1.schema.json)
- [个人助理 OS 每日首页示例数据](examples/ads-personal-assistant-os-daily-brief-v0.1.json)
- [每日首页产品契约测试](prototype/test_personal_assistant_os_contracts.py)

核心议题：Personal Assistant OS 产品定位、五个核心工作空间、全局快速入口、多终端协同、自然感知、主动服务、记忆纠错、渐进式授权、低打扰通知和 Personal Agent 审批体验。


## 研究主线

本仓库的连续研究主线是：

**多源工作感知 → 个人工作记忆 → 授权与语义映射 → 企业数智资产 → 企业工作上下文 → 统一数据模型与运行认知引擎 → 标准数据契约与上下文服务 → 企业 Agent 协同 → 能力资产化与跨人跨岗位复用验证 → 工作本体与事件驱动协同 → 个人持续记忆与事件账本 → 个人运行模型与受约束 Agent → Personal Assistant OS 产品体验与多端协同 → 可交互原型与产品验收 → 主动智能与长期目标推进 → 个人、企业与领域数智底座安全协同。**

其中，个人数智底座负责个人工作信息的自主沉淀；企业数智底座融合企业既有业务系统、知识和经授权的协同信息，并形成标准业务数据、运行上下文和能力资产；业务领域中心数智底座通过共同语义、联邦资产目录、授权协调和跨域治理提供支撑。工作上下文基础设施与运行认知引擎是企业数智底座内部的能力体系，不是新增的第四级底座，也不是员工持续监控系统。

## 工程验证路线

1. 先评审 JSON Schema、事件目录、权威字段和授权模型。
2. 在本地运行 Python 原型，验证事件接入、幂等、状态重建、冲突处理和上下文包生成。
3. 使用一个真实项目交付流程开展只读试点。
4. 建立人工确认、纠错、授权撤回和质量反馈闭环。
5. 在第二个项目或团队中独立验证复用价值，再评估受控写回与规模化。
6. 将经过授权和独立验证的任务方法沉淀为 Capability Asset，开展跨人员、跨团队、跨岗位的对照评测。
7. 建立共同核心、个人、企业和领域本体，验证个人工作事件到企业业务事件的最小必要投影。
8. 建立个人事件账本、持续记忆、目标承诺和 Personal Agent 动作契约，先验证可追溯、可纠错和用户控制，再逐步增加 Agent 自主程度。
9. 设计面向普通用户的 Personal Assistant OS，验证自然感知、自动理解、持续记忆、主动服务和受控执行的产品闭环。

## 架构基线

- ADS-12：三级数智底座矩阵架构，V0.3。
- ADS-19：三级数智底座统一数据模型与资产目录，V0.4。
- ARCH-ADS-001：AI Native 数智基础设施总体架构，V1.0-Review。

## 研究边界

本仓库中的研究文件属于架构研究、工程规范草案和逻辑验证原型，不等同于已批准的生产部署规格、法律意见或生产级安全能力。涉及个人信息、员工工作记录、第三方信息和企业数据的采集、处理与共享，须另行通过组织制度、安全和适用法律审查。


### 专题 10.1：Personal Assistant OS 可交互原型与研发验收

**个人助理 OS 可交互原型与研发验收规范**

- [交互式原型入口](prototype/personal-assistant-os/index.html)
- [原型使用说明](prototype/personal-assistant-os/README.md)
- [交互与研发验收规范](docs/10.1-个人助理OS可交互原型与研发验收规范.md)
- [30 天虚构演示数据](examples/ads-personal-assistant-os-demo-v0.1.json)
- [演示数据 JSON Schema](schemas/ads-personal-assistant-os-demo-v0.1.schema.json)
- [设计 Token](prototype/personal-assistant-os/design-tokens.json)
- [交互领域逻辑与 Node 测试](prototype/personal-assistant-os/core.js)
- [30 天试点评估模板](pilot/个人助理OS30天试点评估模板.csv)
- [用户访谈提纲](pilot/个人助理OS用户访谈提纲.md)

核心议题：五大工作空间交互原型、30 天个人上下文旅程、快速记录—事件—记忆—承诺—提醒—Agent 审批闭环、记忆纠错与撤回、来源权限、隐私和自动化控制。原型只使用虚构数据，不连接真实系统、不执行外部动作。


### 专题 11：PDKS 与 ADS 个人数智底座融合

**PDKS 与 ADS 个人数智底座融合架构**

- [融合架构研究报告（Markdown）](docs/11-PDKS与ADS个人数智底座融合架构.md)
- [融合架构交互式 HTML 阅读版](docs/11-PDKS与ADS个人数智底座融合架构.html)
- [PDKS → ADS 互操作映射规范](schemas/ads-pdks-interoperability-mapping-v0.1.json)
- [PDKS → ADS 投影示例](examples/pdks-ads-bridge-projection-v0.1.json)

核心议题：PDKS 个人数据统一表达、ADS-WORK-08 语义与授权桥接、ADS-WORK-09 个人事件账本/持续记忆/Intent 运行时、ADS-WORK-10 Personal Assistant OS。PDKS Action 映射为 Intent，不自动生成 Agent Action Proposal；个人侧默认 personal_only，企业投影须独立授权。

### 专题 12：AI 原生事件智能基础设施与个人多源采集运行时

**Event Intelligence Lab：事件本体、PALOS 适配与 Connector Runtime**

- [V0.3.2 研发进展](docs/12-AI原生事件智能基础设施V0.3.2研发进展.md)
- [PALOS 只读 Adapter 集成契约](docs/13-PALOS只读Adapter集成契约V0.1.md)
- [Connector Worker 运行与调度机制](docs/14-ConnectorWorker运行与调度机制V0.3.2.md)
- [PDKS 多源个人采集运行时路线图](docs/15-PDKS多源个人采集运行时V0.3路线图.md)
- [PALOS Adapter Profile Schema](schemas/palos-adapter-profile-v0.1.schema.json)
- [PALOS Adapter Profile 模板](examples/palos-adapter-profile.template.json)

本专题以 Event Ontology V0.1 为事件语义基线，逐步打通个人多源采集、证据定位、事件理解、持续记忆、状态重建和 Agent 上下文。V0.3.2 当前仅实现 PALOS SQLite 只读结构适配预览和单机 Connector Worker；未连接真实 PALOS 数据库，钉钉 DWS CLI 仍待实际版本、帮助信息和脱敏输出核验。



### 专题 12.1：来源生命周期与证据依赖感知删除（V0.3.3 Alpha）

- [V0.3.3 研发进展](docs/16-AI原生事件智能基础设施V0.3.3研发进展.md)
- [Source Lifecycle 与 Evidence-aware Purge 规范](docs/17-SourceLifecycle与证据依赖感知删除规范.md)
- [PALOS / 钉钉 DWS 真实集成资料清单](docs/18-PALOS与钉钉DWS真实集成资料清单.md)

V0.3.3 增加来源删除预览、显式确认、跨来源事件保留、专属事件与证据清理、RDF 投影失效、状态快照失效和上下文包撤销。删除范围仅覆盖 EIL 本地数据库与受控文件目录，不代表远端提供方删除、备份擦除或法律合规认证。当前 PALOS 仍未连接真实数据库，DingTalk DWS CLI 仍处于 blocked 状态。

### 专题 13：Personal Data Runtime V0.4.0 Alpha

**从个人多源事件采集走向可治理的事件融合与多 Agent 协同**

- [V0.4.0 研发进展](docs/19-PersonalDataRuntimeV0.4.0研发进展.md)
- [Event Fusion Candidate 规范](docs/20-EventFusionCandidate规范V0.1.md)
- [Agent Event Runtime 契约](docs/21-AgentEventRuntime契约V0.1.md)
- [PALOS / DWS 集成边界](docs/22-PALOS与DWS集成边界V0.4.md)
- [交互式架构总览](docs/23-PersonalDataRuntime架构总览V0.4.html)
- [Agent Subscription JSON Schema](schemas/agent-subscription-v0.1.schema.json)
- [Event Fusion Decision JSON Schema](schemas/event-fusion-decision-v0.1.schema.json)

V0.4.0 增加跨来源事件融合候选和本地 Pull-only Agent Runtime。融合分数仅用于候选排序，必须人工裁决；确认后只建立 EventRelation，不自动合并 Event。Agent 仅能在用途、敏感度和有效期约束下拉取已确认的个人域事件。PALOS 真实 Schema 与钉钉官方 DWS CLI 仍未接入；个人数据不自动投影到企业域。


### 专题 14：Personal Cognitive Runtime V0.5.0 Alpha

**从个人事件账本走向持续记忆、状态与意图运行时**

- [V0.5.0 研发进展](docs/24-PersonalCognitiveRuntimeV0.5.0研发进展.md)
- [Event / Memory / State / Intent 语义边界](docs/25-EventMemoryStateIntent语义边界V0.1.md)
- [PALOS / DWS / Agent 集成边界](docs/26-PALOS-DWS-Agent集成边界V0.5.md)
- [交互式架构总览](docs/27-PersonalCognitiveRuntime架构总览V0.5.html)
- [Memory / Intent / Agent API 示例](docs/28-PersonalCognitiveRuntimeAPI示例V0.5.md)
- [V0.5 测试报告](docs/29-PersonalCognitiveRuntime测试报告V0.5.md)
- [Personal Memory Item Schema](schemas/ads-personal-memory-item-v0.2.schema.json)
- [Personal Intent Object Schema](schemas/ads-personal-intent-object-v0.2.schema.json)
- [Intent Transition Schema](schemas/ads-personal-intent-transition-v0.1.schema.json)
- [Reflection Run Schema](schemas/ads-personal-reflection-run-v0.1.schema.json)
- [Personal Runtime 增量迁移](migrations/005_v050_personal_memory_intent_runtime.sql)
- [Agent Personal Context 客户端示例](examples/agent-personal-context-client-v0.5.py)

V0.5 增加 Memory、State、Intent、Reflection 四个个人认知运行时引擎。Reflection 仅从已确认的个人域事件生成待审核候选；Memory 可追溯来源、有效时间和修订历史；Intent 默认 proposed，只有用户显式激活后才进入 Agent 上下文；Agent 只读访问授权范围内的记忆、意图和状态。来源失效会触发派生对象复核，不自动推断人格、心理状态或执行外部动作。

验证：96 automated tests passed；fresh ZIP extraction test 96 passed；Python compileall passed；UI JavaScript node --check passed；FastAPI OpenAPI 55 paths。完整 Python MVP 作为独立研发 ZIP 交付，不在本 PR 中提交全部运行时代码。
