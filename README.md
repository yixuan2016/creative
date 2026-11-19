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

## 研究主线

本仓库的连续研究主线是：

**多源工作感知 → 个人工作记忆 → 授权与语义映射 → 企业数智资产 → 企业工作上下文 → 统一数据模型与运行认知引擎 → 标准数据契约与上下文服务 → 企业 Agent 协同 → 能力资产化与跨人跨岗位复用验证 → 工作本体与事件驱动协同 → 个人、企业与领域数智底座语义互操作。**

其中，个人数智底座负责个人工作信息的自主沉淀；企业数智底座融合企业既有业务系统、知识和经授权的协同信息，并形成标准业务数据、运行上下文和能力资产；业务领域中心数智底座通过共同语义、联邦资产目录、授权协调和跨域治理提供支撑。工作上下文基础设施与运行认知引擎是企业数智底座内部的能力体系，不是新增的第四级底座，也不是员工持续监控系统。

## 工程验证路线

1. 先评审 JSON Schema、事件目录、权威字段和授权模型。
2. 在本地运行 Python 原型，验证事件接入、幂等、状态重建、冲突处理和上下文包生成。
3. 使用一个真实项目交付流程开展只读试点。
4. 建立人工确认、纠错、授权撤回和质量反馈闭环。
5. 在第二个项目或团队中独立验证复用价值，再评估受控写回与规模化。
6. 将经过授权和独立验证的任务方法沉淀为 Capability Asset，开展跨人员、跨团队、跨岗位的对照评测。
7. 建立共同核心、个人、企业和领域本体，验证个人工作事件到企业业务事件的最小必要投影。

## 架构基线

- ADS-12：三级数智底座矩阵架构，V0.3。
- ADS-19：三级数智底座统一数据模型与资产目录，V0.4。
- ARCH-ADS-001：AI Native 数智基础设施总体架构，V1.0-Review。

## 研究边界

本仓库中的研究文件属于架构研究、工程规范草案和逻辑验证原型，不等同于已批准的生产部署规格、法律意见或生产级安全能力。涉及个人信息、员工工作记录、第三方信息和企业数据的采集、处理与共享，须另行通过组织制度、安全和适用法律审查。
