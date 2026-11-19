# 企业运行认知引擎与企业 Agent 协同执行体系设计

> ADS-WORK-06：在统一企业运行上下文之上，构建可治理、可观测、可评估的 Agent 协同执行体系，使企业从“理解正在发生什么”走向“安全地推进下一步工作”。

| 项目 | 内容 |
|---|---|
| 文档编号 | ADS-WORK-06 |
| 版本 | V0.1-Architecture & Engineering Proposal |
| 日期 | 2026-11-19 |
| 文档性质 | 企业 Agent 协同架构研究与工程设计建议稿 |
| 上游专题 | ADS-WORK-01 至 ADS-WORK-05 |
| 目标领域 | 项目交付与跨角色协同，后续可扩展至其他业务领域 |
| 核心对象 | Agent、AgentTask、Plan、Delegation、ToolCall、Approval、Run、Trace、Artifact |
| 当前状态 | 研究与设计建议，待 ADS 架构、业务、安全、数据治理和工程团队评审 |

---

## 摘要：从企业运行认知走向企业协同执行

ADS-WORK-01 至 ADS-WORK-05 已经形成一条连续路径：从多源工作感知和个人—企业数智资产协同出发，建立企业工作上下文基础设施，设计统一数据模型和运行认知引擎，定义数据契约与最小原型，并提出以项目交付为例的真实业务试点方案。

当企业运行认知引擎能够持续回答“发生了什么、当前状态是什么、依据是什么、哪里存在冲突和未知”之后，下一步自然出现一个问题：

**如何让 AI 不只是解释企业状态，而是能够在业务规则、授权边界和人工责任之内，协调多个专业 Agent 完成复杂工作？**

本专题提出：在企业运行认知引擎之上增加企业 Agent 协同执行体系。该体系不是让多个模型自由聊天，也不是简单地把多个 Agent 放进一个群组，而是以统一任务协议、任务级上下文包、能力注册、编排控制、工具网关、审批机制、执行账本和评测体系为基础，让不同专业 Agent 按明确的任务契约协作。

### 核心判断

1. **企业运行认知引擎是 Agent 的共同事实基础。** Agent 不应各自建立互相矛盾的企业事实副本，而应通过授权后的 Context Package 获取同一套可追溯、可版本化的运行上下文。
2. **Agent 是受约束的任务执行单元，不是拥有无限权限的数字员工。** 每个 Agent 必须有明确的角色、任务范围、能力清单、数据范围、动作等级、预算和退出条件。
3. **协同应以任务契约为中心，而不是以自由对话为中心。** Agent 之间通过结构化任务委派、结果契约和证据引用交换工作成果；对话仅作为内部推理方式，不作为正式业务记录。
4. **编排控制与专业执行分离。** Orchestrator 负责拆解、分派、汇总、超时和流程状态；领域 Agent 负责专业分析；Policy / Tool Gateway 负责权限和动作执行；人类责任人保留业务决策权。
5. **认知状态与执行状态必须分开。** 运行认知引擎表达企业业务状态；Agent Runtime 表达任务和执行状态。Agent 执行成功不能自动意味着业务事实已改变。
6. **先只读、再草拟、后受控执行。** 先验证多 Agent 对复杂任务的协同质量，再在明确的业务收益、审批、幂等、回滚和审计条件下开放有限写入。
7. **能力复用优先于 Agent 数量增长。** 可复用的领域能力、工具、规则、上下文服务和评测集，比不断增加 Agent 角色更重要。

### 本专题要形成的交付物

- 企业 Agent 协同参考架构与核心组件边界；
- Agent、任务、委派、执行、审批和结果的统一概念模型；
- Agent Task Envelope 与 Result Contract 数据契约；
- 项目交付多 Agent 协同工作流；
- Orchestrator、专业 Agent、Verifier、Policy Service 和 Tool Gateway 的职责设计；
- Agent 生命周期、任务状态机和风险分级动作模型；
- 权限、审计、上下文版本、失败恢复和人工确认机制；
- 评测指标、验收测试集和分阶段实施路线。

> **一句话定位：ADS 提供企业运行认知，Agent Runtime 负责组织受约束的智能执行，业务系统仍然是正式业务状态和交易结果的权威载体。**

---

## 1. 目标、范围与非目标

### 1.1 设计目标

本体系应使企业能够：

- 让 Agent 使用统一、最新、经授权的企业运行上下文；
- 将复杂业务任务拆分为可分派、可追踪、可验收的子任务；
- 根据任务类型选择合适的专业 Agent、工具和确定性服务；
- 支持串行、并行、监督式和事件驱动式协作；
- 在每个委派边界传递明确的目标、输入、输出、约束和截止时间；
- 对工具调用、外部动作和高影响操作执行独立策略校验；
- 将审批绑定到具体动作内容、对象、参数和有效期；
- 在失败、超时、重复调用和部分成功时保持可恢复性；
- 记录 Agent 运行、委派、工具调用、审批、结果和人工反馈；
- 通过离线评测、影子运行和真实任务数据持续验证质量。

### 1.2 本专题范围

第一阶段以 ADS-WORK-05 的项目交付场景为主，重点覆盖：

- 项目状态评审准备；
- 风险和问题识别；
- 任务依赖分析；
- 决策与证据核验；
- 会议后行动项整理；
- 项目经理确认后的内部跟进草稿。

后续可以扩展到客户服务、产品研发、运营管理、售前方案和内部知识服务，但必须由各业务领域定义自己的领域本体、权威字段、动作策略和评测集。

### 1.3 非目标

本专题不主张：

- 建设不受约束的 Agent Swarm，让 Agent 任意创建 Agent、无限递归委派；
- 让 Agent 之间直接共享全部记忆、全部工具或全部企业数据；
- 让一个通用大模型替代 ERP、CRM、项目管理、OA 或审批系统；
- 让 Orchestrator 代替业务负责人批准决策、合同、费用、验收或客户承诺；
- 通过模型置信度推断授权、审批或业务事实；
- 在第一阶段开放自动外部沟通、不可逆交易或高影响写入；
- 把模型的内部推理链作为审计记录或正式业务依据；
- 用 Agent 数量、对话轮数或 Token 消耗衡量企业智能化成熟度。

### 1.4 与前五份专题的关系

| 专题 | 已解决的问题 | 本专题继承的能力 |
|---|---|---|
| ADS-WORK-01 | 工作信息如何感知、沉淀并在授权下转化为企业资产 | 来源、授权、个人—企业责任边界 |
| ADS-WORK-02 | 企业需要理解哪些工作上下文 | 业务活动、对象、决策、任务、风险和依赖语义 |
| ADS-WORK-03 | 如何建立统一数据模型和运行认知引擎 | WorkEvent、BusinessObject、StateAssertion、EvidenceRef、ContextPackage |
| ADS-WORK-04 | 如何把模型落实为数据契约和原型 | Schema、API、幂等、状态重建、上下文生成 |
| ADS-WORK-05 | 如何在真实项目中验证上下文能力 | 项目交付场景、基线、人工确认、治理与 Go / No-Go |
| ADS-WORK-06 | 如何基于可信上下文协调多个 Agent 完成工作 | Agent Runtime、任务编排、动作治理、执行验证 |

---

## 2. 设计原则：先定义协作边界，再讨论智能程度

| 编号 | 原则 | 设计要求 |
|---|---|---|
| AP-01 | Context First | Agent 先获取任务所需的 Context Package，不直接任意检索全企业数据 |
| AP-02 | Contract First | Agent 委派必须使用结构化任务契约和明确结果契约 |
| AP-03 | Least Privilege | Agent、用户、工具和委派链均按最小权限授权 |
| AP-04 | Separate Cognition and Execution | 业务状态、认知判断和执行状态分别建模 |
| AP-05 | Human Accountability | 高影响业务决策由明确的人类责任人承担 |
| AP-06 | Deterministic Guardrails | 权限、金额、状态迁移、幂等和审批使用确定性服务，不依赖提示词 |
| AP-07 | Evidence Before Assertion | 重要结论必须带证据引用、来源和时间 |
| AP-08 | Bounded Autonomy | 每个运行有步骤、时间、成本、工具调用和委派深度上限 |
| AP-09 | Observable by Design | 所有运行、委派、工具调用和审批均有统一 Trace |
| AP-10 | Recoverable Execution | 超时、重试、部分成功、撤销和补偿动作必须可设计 |
| AP-11 | Reusable Capability | 优先沉淀能力、工具、任务模板和评测集，而非堆叠 Agent |
| AP-12 | Versioned Change | Agent 配置、Prompt、工具、Schema、策略和模型版本均可追溯 |

### 2.1 Agent、Skill、Tool 和 Workflow 的边界

这些概念不能混用：

| 概念 | 定义 | 示例 | 是否自主推理 |
|---|---|---|---|
| Agent | 有明确角色、目标、上下文和能力边界的任务执行单元 | 项目风险分析 Agent | 可以，但受约束 |
| Skill / Capability | 可复用的专业能力封装，可能由代码、规则或模型实现 | 依赖路径分析、证据核验 | 不一定 |
| Tool | Agent 可调用的外部接口或系统动作 | 查询项目状态、读取风险台账 | 通常不负责规划 |
| Workflow | 明确步骤、条件、审批和异常分支的流程定义 | 项目状态评审流程 | 通常由流程控制 |
| Orchestrator | 负责任务规划、委派、调度、汇总和生命周期管理的控制组件 | Project Review Coordinator | 可以使用模型规划，但关键控制确定性执行 |

**架构建议：** 把确定性规则、计算和系统操作优先做成 Skill / Tool；只有需要理解语义、处理非结构化信息、提出候选解释或动态拆解任务时，才引入 Agent。不要把每个 API 都包装成一个 Agent。

---

## 3. 总体架构：四个平面与一个受控闭环

### 3.1 四个平面

**A. 企业运行上下文平面（ADS Context Plane）**

承接 ADS-WORK-03 / 04 的运行认知引擎，负责对象、事件、状态、关系、证据、授权和 Context Package。它提供企业共同事实基础，不承担 Agent 的自主编排。

**B. Agent 控制平面（Agent Control Plane）**

负责 Agent Registry、Capability Registry、任务模板、Orchestrator、计划校验、委派路由、预算、生命周期和版本管理。

**C. Agent 执行平面（Agent Execution Plane）**

承载具体 Agent Runtime、模型调用、Skill 执行、工具请求、结果校验和运行隔离。Agent 只获得当前任务需要的上下文和能力。

**D. 治理与观测平面（Governance & Observability Plane）**

负责身份、策略、审批、审计、风险分级、运行追踪、质量评估、成本管理、异常检测和紧急停止。

### 3.2 参考架构

~~~mermaid
flowchart TB
  U[业务人员 / 业务系统事件 / 定时任务]
  subgraph ADS[ADS 企业运行认知平面]
    C1[统一数据模型]
    C2[运行认知引擎]
    C3[Context Package API]
    C1 --> C2 --> C3
  end
  subgraph CTRL[Agent 控制平面]
    R[Agent Registry / Capability Registry]
    O[Orchestrator]
    P[Plan Validator / Task Scheduler]
    R --> O --> P
  end
  subgraph EXEC[Agent 执行平面]
    A1[项目上下文 Agent]
    A2[风险分析 Agent]
    A3[依赖分析 Agent]
    A4[证据核验 Agent]
    A5[结果汇总 Agent]
    V[Verifier Agent / Deterministic Validator]
  end
  subgraph TOOLS[受控工具与业务系统]
    TG[Tool Gateway]
    T1[项目 / 任务查询]
    T2[风险 / 决策查询]
    T3[文档 / 证据引用]
    T4[内部草稿 / 待办服务]
  end
  subgraph GOV[治理与观测平面]
    IAM[Identity & Policy]
    AP[Approval Service]
    AUD[Audit / Trace / Evaluation]
    KILL[Budget / Rate Limit / Kill Switch]
  end
  U --> O
  O --> C3
  O --> R
  P --> A1
  P --> A2
  P --> A3
  P --> A4
  A1 --> V
  A2 --> V
  A3 --> V
  A4 --> V
  V --> O
  A1 --> TG
  A2 --> TG
  A3 --> TG
  A4 --> TG
  TG --> T1
  TG --> T2
  TG --> T3
  TG --> T4
  IAM -.-> O
  IAM -.-> TG
  AP -.-> TG
  AUD -.-> O
  AUD -.-> EXEC
  KILL -.-> O
  KILL -.-> EXEC
~~~

### 3.3 核心数据流

1. 用户或业务事件提出一个有明确目的的任务。
2. Orchestrator 识别任务类型，读取任务模板和 Agent Registry。
3. ADS Context API 按调用主体、用途、对象、时间和字段范围生成 Context Package。
4. Orchestrator 生成执行计划，并通过确定性规则校验计划是否超出权限、预算和动作边界。
5. 任务被委派给一个或多个专业 Agent。
6. 专业 Agent 仅通过 Task Envelope 获取输入，通过 Tool Gateway 调用允许的工具。
7. Agent 返回符合 Result Contract 的结果，并附证据引用、未知项和限制说明。
8. Verifier 对结构、证据、权限、冲突和业务规则进行独立检查。
9. Orchestrator 汇总结果；需要业务判断或高影响动作时，进入人工审批。
10. 获批的动作由正式业务系统或受控执行服务完成，执行结果以事件回流 ADS。
11. 评测和审计记录整个过程，形成可复盘、可改进的能力资产。

---

## 4. 核心组件与职责边界

| 组件 | 核心职责 | 不应承担的职责 |
|---|---|---|
| Agent Registry | 登记 Agent 身份、版本、角色、能力、模型、所有者和运行限制 | 不直接授权访问任意业务数据 |
| Capability Registry | 登记 Skill / Tool 的输入输出、风险等级、依赖和版本 | 不替代业务权限策略 |
| Orchestrator | 接收目标、规划、拆解、委派、汇总、超时和终止 | 不绕过 Policy Service 执行高风险动作 |
| Plan Validator | 校验计划结构、动作等级、预算、权限和循环风险 | 不依赖 LLM 自我声明“安全” |
| Agent Runtime | 运行单个 Agent，装载任务上下文、调用模型和能力 | 不自行扩大授权范围 |
| Task Broker | 任务排队、路由、并发控制、重试和状态更新 | 不改变任务业务含义 |
| Context Adapter | 向 Agent 提供任务所需 Context Package 或引用 | 不提供全量企业上下文 |
| Tool Gateway | 统一执行工具鉴权、参数校验、限流、幂等、审计和结果封装 | 不让 Agent 直接持有系统凭证 |
| Policy Service | 对主体、用途、对象、字段、动作和环境进行策略决策 | 不由模型提示词替代 |
| Approval Service | 绑定具体动作摘要、参数、审批人、有效期和审批结果 | 不把一次审批扩展成永久授权 |
| Verifier | 检查结果结构、证据、矛盾、约束和验收标准 | 不对无证据内容做主观背书 |
| Run Ledger / Trace | 记录运行、任务、委派、工具、审批和结果关联 | 不记录不必要的模型私有推理链 |
| Evaluation Service | 执行离线、影子、在线和人工评测 | 不把单次成功等同于长期可靠 |

### 4.1 控制组件与模型组件分离

Orchestrator 可以使用模型提出任务分解建议，但任务创建、委派、授权、预算扣减、状态转换和动作提交必须由可测试的控制逻辑执行。模型输出是候选计划，不是系统命令。

### 4.2 Agent Registry 的最小登记项

每个 Agent 至少登记：

- agent_id、display_name、domain、owner；
- role_description、supported_task_types；
- input_contract、output_contract；
- allowed_capabilities、denied_capabilities；
- allowed_context_types、data_classification_ceiling；
- max_risk_tier、max_delegation_depth；
- model_profile、prompt_version、runtime_version；
- timeout、max_steps、max_tool_calls、token_budget；
- evaluation_profile、lifecycle_status。

Agent 配置应版本化。停用 Agent 时应阻止新任务，并为运行中的任务定义完成、迁移或取消策略。

---

## 5. Agent 协作模型：以任务契约组织专业分工

### 5.1 项目交付 Agent 团队

首个业务场景建议采用一个协调 Agent 加多个专业 Agent 的模式：

| Agent | 主要任务 | 典型输入 | 典型输出 |
|---|---|---|---|
| Project Coordinator | 理解用户目标、拆解任务、分派和汇总 | 任务目标、项目 Context Package | 执行计划、汇总报告、待确认事项 |
| Project Context Agent | 提取项目状态、里程碑和关键变化 | 项目状态、时间线、任务数据 | 项目运行摘要和状态证据 |
| Risk Analysis Agent | 识别风险、影响和触发条件 | 风险台账、事件、状态和证据 | 候选风险、影响对象、证据和未知 |
| Dependency Analysis Agent | 分析任务依赖和阻塞传播 | Task、Relation、Milestone | 依赖路径、阻塞链和影响范围 |
| Decision & Evidence Agent | 核验决策状态、交付物和证据版本 | Decision、EvidenceRef、审批记录 | 决策状态、证据有效性和缺口 |
| Action Drafting Agent | 将已确认的问题转成行动项草稿 | 已核验问题、责任人候选和期限规则 | 行动项草稿，不直接写回 |
| Verifier Agent | 检查结果是否有证据、是否冲突、是否越权 | 各 Agent 的 Result Contract | 通过、拒绝、要求补充或人工复核 |

### 5.2 任务契约

每次 Agent 委派都必须明确：

- **目标：** 这次子任务要解决什么问题；
- **范围：** 哪些业务对象、时间范围和字段可使用；
- **上下文：** Context Package 的 ID、版本、完整性摘要和过期时间；
- **输入：** 结构化任务输入，不传递无关对话历史；
- **能力：** 允许调用的 Capability / Tool；
- **禁止事项：** 不允许的动作、数据和推断；
- **输出：** 结果 Schema、证据要求和验收标准；
- **资源限制：** 截止时间、最大步骤、工具次数、Token / 成本预算；
- **委派规则：** 是否允许继续委派、最大深度和可委派 Agent 范围；
- **失败策略：** 超时、部分结果、重试、取消和人工升级方式。

任务契约不是给模型看的提示词而已，它是 Runtime、Policy Service、Task Broker 和审计系统共同执行的控制对象。

### 5.3 Task Envelope 示例

~~~json
{
  "envelope_id": "env-2026-014-003",
  "tenant_id": "tenant-demo",
  "trace_id": "trace-review-014",
  "run_id": "run-review-014",
  "parent_task_id": "task-review-014",
  "task_id": "task-dependency-014",
  "task_type": "analyze_project_dependencies",
  "task_version": "0.1",
  "requester": {
    "subject_type": "agent",
    "subject_id": "agent-project-coordinator",
    "on_behalf_of": "user-project-manager"
  },
  "recipient": {
    "agent_id": "agent-dependency-analysis",
    "agent_version": "0.1"
  },
  "purpose": "prepare_project_status_review",
  "scope": {
    "object_refs": ["obj-project-014"],
    "time_window": {
      "from": "2026-11-17T00:00:00+08:00",
      "to": "2026-11-20T00:00:00+08:00"
    }
  },
  "context_package_ref": {
    "context_id": "ctx-project-review-014",
    "integrity_hash": "sha256:example-digest",
    "expires_at": "2026-11-19T10:30:00+08:00"
  },
  "input": {
    "focus": ["blocked_tasks", "critical_dependencies", "milestone_impact"]
  },
  "allowed_capabilities": ["context.read", "dependency.graph.read"],
  "prohibited_actions": ["project.write", "task.reassign", "customer.send"],
  "risk_tier": "L0",
  "constraints": {
    "evidence_required": true,
    "preserve_unknowns": true,
    "do_not_infer_approval": true,
    "max_steps": 8,
    "max_tool_calls": 10,
    "max_delegation_depth": 0
  },
  "expected_output": {
    "schema_ref": "ads-agent-result-v0.1",
    "required_sections": ["dependency_paths", "affected_objects", "evidence_refs", "unknowns"]
  },
  "idempotency_key": "tenant-demo:task-dependency-014:v1",
  "policy_version": "agent-policy-0.1",
  "created_at": "2026-11-19T10:00:00+08:00",
  "expires_at": "2026-11-19T10:15:00+08:00"
}
~~~

以上为示例结构，生产环境需使用经过评审的 JSON Schema、身份体系和策略服务；示例 ID、时间和摘要均为虚构。

### 5.4 Result Contract 示例

专业 Agent 的输出应包括：

- task_id、agent_id、agent_version、run_id；
- status：completed / partial / failed / needs_human_review；
- summary：简短结果；
- findings：结构化发现；
- evidence_refs：支持每个重要发现的来源；
- conflicts：相互矛盾的来源或状态；
- unknowns：无法确认的信息；
- assumptions：显式假设；
- recommended_next_steps：建议的下一步；
- action_proposals：如有动作建议，必须是提议而非执行结果；
- limitations：数据缺口、过期信息和适用范围；
- metrics：耗时、调用次数和成本；
- output_schema_version。

Verifier 应拒绝缺少必要证据、超出任务范围、把推断写成正式事实或违反输出 Schema 的结果。

---

## 6. 协作模式：何时串行、并行、监督或事件驱动

### 6.1 四种标准模式

**模式 A：串行流水线**

适合前一步输出是下一步必要输入的任务。例如：获取项目上下文 → 识别风险 → 生成行动项草稿 → 核验。

**模式 B：并行分工与汇总**

适合可以独立分析的子任务。例如：项目状态、风险、依赖、决策证据可以并行分析，最后由 Coordinator 汇总。并行前必须共享相同的 Context Package 版本或明确各自上下文差异。

**模式 C：监督式委派**

适合复杂目标。Coordinator 根据任务契约委派专业 Agent，并控制最大委派深度、并发数、预算和截止时间。专业 Agent 默认不能无限创建子 Agent。

**模式 D：事件驱动协作**

适合项目状态变化、风险升级、交付物更新等事件触发的工作。事件只创建候选任务；是否执行仍需检查策略、重复任务、业务时间窗和责任人配置。

### 6.2 推荐采用混合式编排

企业场景建议采用**中心化控制 + 专业化执行 + 确定性工具服务**：

- 中心化控制：确保权限、预算、状态和责任链一致；
- 专业化执行：让领域 Agent 专注明确的子任务；
- 确定性工具服务：负责查询、计算、状态迁移和系统操作；
- 人工审批：承接高影响判断和例外情况。

不建议把“Agent 互相自由聊天、互相评价、无限递归委派”作为默认架构。它会导致责任边界模糊、成本失控、结果难以复现和权限传播困难。

### 6.3 项目状态评审的协作时序

~~~mermaid
sequenceDiagram
  participant U as 项目经理
  participant O as Coordinator
  participant C as ADS Context
  participant R as Task Broker
  participant S as 专业 Agents
  participant V as Verifier
  participant H as 审批 / 人工确认
  participant T as Tool Gateway
  U->>O: 请求准备项目状态评审
  O->>C: 请求指定项目的 Context Package
  C-->>O: 返回上下文、证据、冲突、未知和有效期
  O->>R: 提交经过校验的执行计划
  par 并行专业分析
    R->>S: 项目状态分析任务
    R->>S: 风险分析任务
    R->>S: 依赖分析任务
    R->>S: 决策与证据核验任务
  end
  S-->>O: 返回结构化结果和证据引用
  O->>V: 提交汇总结果进行核验
  V-->>O: 通过 / 补充 / 人工复核
  O-->>U: 展示评审材料和待确认事项
  U->>H: 确认或修正
  H-->>O: 返回人工确认结果
  O->>T: 如获授权，提交限定的后续动作
  T-->>O: 返回执行结果和业务系统引用
  O-->>U: 返回完成状态与审计引用
~~~

### 6.4 并行协作的约束

- 并行 Agent 必须使用同一 Context Package，或在任务中显式记录各自的 Context ID 和版本。
- 同一业务对象的写入任务默认串行化，不能由多个 Agent 竞争修改。
- 结果汇总时保留不同 Agent 的分歧，不通过投票把事实冲突变成确定结论。
- 超时任务可以返回 partial，但必须标注未完成的子任务。
- 并行数量受租户、业务域、任务类型和成本预算共同限制。

---

## 7. 运行生命周期与任务状态机

### 7.1 Run 与 Task 分离

- **Run** 是一次用户目标或事件触发的完整执行实例。
- **Task** 是 Run 中可独立分派、追踪和验收的工作单元。
- **Delegation** 记录父任务向子 Agent 的正式委派关系。
- **ToolCall** 记录一次工具调用及其策略决策和结果。
- **Approval** 记录某个具体动作是否获批。
- **Artifact** 是任务产生的可交付结果，例如报告、草稿、结构化清单或证据索引。

一个 Run 可以包含多个 Task；Task 可以包含有限的 Delegation；所有子任务必须能回溯到发起 Run 和业务主体。

### 7.2 建议生命周期

~~~mermaid
stateDiagram-v2
  [*] --> requested
  requested --> authorized
  requested --> rejected
  authorized --> planned
  planned --> running
  planned --> awaiting_approval
  awaiting_approval --> running: approved
  awaiting_approval --> rejected: denied
  running --> waiting: delegated_or_async
  waiting --> running: result_received
  running --> completed
  running --> partial
  running --> failed
  running --> cancelled
  running --> expired
  partial --> running: resume_if_allowed
  partial --> completed: accepted_as_partial
  failed --> retryable
  retryable --> running
  completed --> [*]
  rejected --> [*]
  cancelled --> [*]
  expired --> [*]
~~~

### 7.3 状态定义

| 状态 | 含义 | 关键控制 |
|---|---|---|
| requested | 已收到任务请求 | 校验请求结构和身份 |
| authorized | 主体、用途和范围通过初始授权 | 记录策略版本和授权引用 |
| planned | 计划已生成并通过结构、预算和风险校验 | 计划不可无痕修改 |
| awaiting_approval | 需要人工批准具体动作或计划 | 审批绑定动作摘要和有效期 |
| running | 正在执行 | 限制步骤、时间、工具和成本 |
| waiting | 等待委派、工具或异步事件 | 保留超时与取消机制 |
| partial | 部分子任务完成 | 标记缺失结果和不可用结论 |
| completed | 达到任务验收条件 | 结果和证据已归档 |
| failed | 执行失败 | 记录失败阶段和可否重试 |
| cancelled | 由用户、策略或系统取消 | 停止后续调用并清理可撤销资源 |
| expired | 超过有效期 | 拒绝使用过期上下文继续执行 |
| rejected | 授权或审批拒绝 | 记录拒绝原因，不继续执行 |

业务状态变更必须由正式业务系统或责任人确认；Agent Run 的 completed 仅代表该 Agent 任务满足其执行契约。

---

## 8. 工具调用与动作风险治理

### 8.1 Tool Gateway 是唯一工具执行入口

Agent 不应直接持有 ERP、CRM、OA、项目系统或文档平台的长期凭证。所有工具调用经过 Tool Gateway，由 Gateway 执行：

1. 解析 Agent、用户和代表关系；
2. 检查任务目的、对象范围、字段范围和数据分类；
3. 校验工具是否在该 Agent 的能力清单内；
4. 校验参数 Schema、业务规则和速率限制；
5. 检查是否需要审批以及审批是否绑定当前动作；
6. 生成幂等键和审计记录；
7. 调用下游服务；
8. 保存结果引用、执行状态和副作用摘要；
9. 将结果返回 Agent，并在适用时发布标准事件。

### 8.2 动作风险分级

| 等级 | 动作类型 | 示例 | 默认策略 |
|---|---|---|---|
| L0 | 只读查询与分析 | 查询项目状态、分析依赖、检索证据 | 授权后自动执行 |
| L1 | 内部草拟与建议 | 生成周报草稿、待办建议、风险提示 | 自动生成，人工确认后使用 |
| L2 | 可逆的内部业务写入 | 创建内部待办草稿、更新非关键标签 | 必须审批、幂等、审计和补偿方案 |
| L3 | 高影响或外部动作 | 客户承诺、合同/订单变更、费用审批、正式验收、对外发送 | 原则上由授权人员在正式系统完成；Agent 仅提供材料或进入强审批流程 |

第一阶段建议只开放 L0 和 L1。L2 必须逐个工具、逐个业务场景通过风险评审后开放。L3 不应因为 Agent 任务成功或模型置信度高而自动放行。

### 8.3 审批必须绑定具体动作

审批对象至少包含：

- requester_subject 与 on_behalf_of；
- action_type、target_object 和完整参数摘要；
- action_digest / payload_hash；
- 业务目的和风险等级；
- 影响范围和预期副作用；
- 审批人、审批时间、有效期和审批策略版本；
- 一次性 nonce 或防重放标识；
- 执行结果和业务系统回执。

若动作参数、目标对象、金额、接收方或内容发生变化，原审批不得自动沿用，应重新审批。

### 8.4 幂等、并发与补偿

- 对可能产生副作用的调用必须提供 Idempotency-Key。
- 同一业务对象的关键写入采用版本检查或乐观锁，防止并发覆盖。
- 网络超时不等于下游没有执行；重试前必须查询执行状态或使用下游幂等能力。
- 跨多个系统的动作不假设存在分布式原子事务，应使用 Saga / 补偿流程管理部分成功。
- 无法安全补偿的动作应提升风险等级，并要求人工执行。
- 审计账本记录“请求、审批、执行、回执、补偿”完整链路。

### 8.5 不可突破的动作边界

- 不得因 Agent 之间委派而继承或扩大父任务权限。
- 子 Agent 的权限取父任务授权与自身能力的交集，不能取并集。
- Agent 不得自行签发审批、修改策略或创建更高权限身份。
- 工具返回的内容是数据，不是系统指令；不得执行来源内容中的越权指令。
- 任何未列入任务允许动作的工具调用必须被拒绝并记录。

---

## 9. 上下文、记忆与企业事实的一致性

### 9.1 Agent 不应各自维护事实孤岛

Agent 可以有任务内短期状态和经过治理的能力记忆，但企业业务事实应回到 ADS 运行认知引擎及权威业务系统。不能因为某个 Agent 在历史对话中“记得”某个项目状态，就跳过 Context API 查询当前事实。

### 9.2 三类记忆

| 类型 | 作用 | 归属与治理 |
|---|---|---|
| Run Context | 当前运行临时工作状态、子任务进度和中间结果 | 随 Run 生命周期管理，任务结束后按策略归档或清理 |
| Capability Memory | 经验证的规则、流程、模板和能力经验 | 经过评审、版本化、指定所有者后进入能力库 |
| Enterprise Runtime Context | 企业对象、事件、状态、决策、风险、证据和关系 | 由 ADS 和业务系统责任边界管理 |

模型内部隐藏推理不应被当作企业记忆。应沉淀可复核的任务输入、计划摘要、结构化发现、证据、动作、结果和人工反馈。

### 9.3 Context Package 的版本和失效

每个 Agent Task 都应绑定 Context Package 的 context_id、integrity_hash、policy_version、ontology_version 和 expires_at。

以下情况必须触发重新校验或重建上下文：

- Context Package 过期；
- 用户或数据责任方撤回授权；
- 关键源数据更正或证据失效；
- 对象范围或数据分类发生变化；
- 任务从只读分析转为写入建议或实际执行；
- 计划执行时间与上下文有效时间不匹配。

不得把一个只读任务的 Context Package 自动复用为写入任务的授权凭据。

### 9.4 反馈如何沉淀

人工接受、修正、驳回和补充信息应形成结构化 Feedback Event，记录：

- 原始 Agent 输出和版本；
- 人工修改内容与理由；
- 被修正的事实、规则或证据；
- 适用业务领域和任务类型；
- 审核人及时间；
- 是否允许进入能力库；
- 是否需要更新本体、规则、Prompt、Tool 或评测样本。

未经审核的单次反馈不应直接改变全企业 Agent 行为。

---

## 10. 安全、隐私与对抗性风险

### 10.1 主要风险

| 风险 | 典型表现 | 防护措施 |
|---|---|---|
| Prompt Injection | 文档或网页中包含诱导 Agent 越权的指令 | 将检索内容视为不可信数据；工具端强制策略 |
| 越权委派 | 子 Agent 获得父任务之外的数据和工具 | 权限取交集；每次委派重新做 Policy Check |
| 数据外泄 | Agent 将敏感内容写入不允许的外部工具 | 数据分类、出口控制、字段脱敏和工具白名单 |
| 工具滥用 | 错误参数、重复提交或异常高频调用 | Schema 校验、限流、幂等和预算 |
| 结果串线 | 多项目或多租户上下文混用 | Tenant / Object Scope 隔离和上下文完整性校验 |
| 伪造证据 | Agent 生成不存在的来源或引用 | EvidenceRef 必须由系统解析验证 |
| 循环委派 | Agent 反复创建子任务 | 最大深度、最大任务数、循环检测和超时 |
| 计划漂移 | 执行过程中改变目标或扩大范围 | 计划版本化；范围变更重新授权 |
| 多 Agent 共识幻觉 | 多个 Agent 重复同一错误信息 | 证据独立性检查，不用多数票替代来源核验 |
| 成本失控 | 长时间运行、无效重试和过度并行 | Token / 时间 / 工具 / 并发预算和 Kill Switch |

### 10.2 信任边界

- Agent 输出默认属于候选结果，不自动成为业务事实。
- 外部文档、邮件、网页、会议内容和工具返回值均属于不可信输入。
- Prompt 中的角色说明不能替代服务端授权。
- 不能让 Agent 自行判断自己拥有某项权限。
- 不能将用户可见的摘要、模型内部推理和正式审计记录混为一体。
- 所有跨责任域访问必须经过 ADS 授权协调和各责任域策略检查。

### 10.3 紧急停止机制

平台至少提供以下控制：

- 按租户、业务域、Agent、Tool 和 Run 维度暂停；
- 撤销指定 Agent 的新任务接收权限；
- 取消尚未执行的委派和排队任务；
- 禁止高风险工具调用；
- 使指定 Context Package 和授权引用失效；
- 导出指定 Trace、审批和动作记录供调查；
- 在恢复前执行回归测试和审批。

---

## 11. 可观测性、审计与运行指标

### 11.1 统一 Trace 关联

一次复杂协作至少关联：

- tenant_id、request_id、trace_id、run_id；
- parent_run_id、task_id、parent_task_id；
- agent_id、agent_version、model_profile；
- context_id、context_integrity_hash、policy_version；
- delegation_id、tool_call_id、approval_id；
- artifact_id、result_schema_version；
- started_at、completed_at、status、error_code。

日志应记录足以重建系统行为的元数据、输入引用、输出摘要、策略结果和副作用，不应无必要保存完整敏感上下文或模型隐藏推理链。

### 11.2 指标体系

| 维度 | 指标 | 定义 |
|---|---|---|
| 任务质量 | Task Success Rate | 满足任务验收标准的 Run / 已完成评测 Run |
| 结果质量 | Evidence Coverage | 有效证据支持的关键发现 / 全部关键发现 |
| 结果质量 | Unsupported Claim Rate | 无有效证据或超范围的关键结论占比 |
| 协作效率 | Delegation Completion Rate | 按契约完成的委派任务 / 全部委派任务 |
| 协作效率 | Rework Rate | 因结果不合格而返工的任务占比 |
| 稳定性 | Timeout / Failure Rate | 超时或失败的任务占比 |
| 治理 | Policy Denial Rate | 被策略拒绝的请求占比，需结合原因分析 |
| 治理 | Approval Compliance | 需要审批的动作中正确完成审批的比例 |
| 安全 | Unauthorized Action Success | 未授权动作成功次数，目标为 0 |
| 运行成本 | Cost per Accepted Task | 每个被业务接受任务的平均成本 |
| 业务价值 | Cycle Time Reduction | 同类业务任务周期相对基线的变化 |
| 用户体验 | Human Correction Rate | 人工修正的关键结论 / 人工审核的关键结论 |

不能单独以 Task Success Rate 作为上线依据。必须同时检查证据质量、权限安全、人工修改率、业务收益和失败恢复能力。

### 11.3 建议的初始验收阈值

以下为试点设计目标，不代表已经达到或已经获得企业批准：

- 任务输出 Schema 合规率：≥ 99%；
- 关键结论证据可追溯率：≥ 95%；
- 关键事实与人工裁定一致率：≥ 95%；
- 委派任务状态可追踪率：100%；
- 需要审批的动作审批绑定率：100%；
- 未授权动作成功次数：0；
- 高风险工具绕过 Gateway 次数：0；
- 运行 Trace 关联完整率：≥ 99%；
- 影子运行阶段不触发真实业务写入；
- 业务任务周期改善：在基线可比的前提下争取 ≥ 20%，以实际测量为准。

阈值需在试点前由业务、工程、安全和评估负责人冻结。低频高影响风险不能仅用平均准确率衡量，必须单独做边界测试和人工复核。

---

## 12. 评测体系：从单 Agent 测试到协同系统验收

### 12.1 四层评测

**第一层：组件评测**

验证单个 Agent 的任务理解、结构化输出、证据引用和工具参数质量。

**第二层：协作评测**

验证任务拆解是否合理、委派是否正确、上下文是否一致、并行结果是否冲突、汇总是否遗漏。

**第三层：系统评测**

验证授权、审批、超时、幂等、重试、取消、部分成功、Trace、成本和 Kill Switch。

**第四层：业务评测**

验证团队是否减少重复查找和确认，是否更快发现阻塞，是否提升行动项闭环率，是否愿意持续使用。

### 12.2 必测场景

| 编号 | 测试场景 | 预期结果 |
|---|---|---|
| AG-01 | 单 Agent 只读查询 | 仅访问任务范围内对象和字段 |
| AG-02 | 多 Agent 并行分析 | 所有子任务绑定相同上下文版本或显式差异 |
| AG-03 | 子 Agent 尝试越权工具 | Gateway 拒绝并产生审计记录 |
| AG-04 | 子 Agent 继续委派 | 默认拒绝，或仅在明确允许的最大深度内执行 |
| AG-05 | 两个 Agent 结果冲突 | 保留冲突，Verifier 要求证据或人工判断 |
| AG-06 | Context Package 过期 | 阻断执行并要求重建上下文 |
| AG-07 | 审批后修改动作参数 | 原审批失效，要求重新审批 |
| AG-08 | 工具调用超时但下游已执行 | 通过幂等键或状态查询避免重复副作用 |
| AG-09 | 部分子任务失败 | 返回 partial，明确缺失内容，不伪装完整 |
| AG-10 | 运行超预算或进入循环 | Runtime 自动停止或降级 |
| AG-11 | 外部文档 Prompt Injection | 内容作为数据处理，不能改变策略或工具权限 |
| AG-12 | 跨项目 / 跨租户对象引用 | Policy Service 拒绝越界读取 |
| AG-13 | 人工修正 Agent 结果 | 原结果、修正、人员和时间均可追溯 |
| AG-14 | Kill Switch 触发 | 停止新调用，取消可取消任务，保留审计 |
| AG-15 | Agent 版本升级 | 旧版和新版使用同一评测集比较，版本可回滚 |
| AG-16 | 业务系统回执与 Agent 预期不同 | 以业务系统回执为准，标记执行结果差异 |

### 12.3 评测样本构建

- 使用脱敏、合成或经批准的真实业务样本；
- 为关键事实建立人工裁定和证据基准；
- 覆盖正常、边界、冲突、缺失、过期和恶意输入；
- 保留任务难度、项目复杂度和业务阶段标签；
- 每次 Agent、Prompt、模型、Tool 或策略升级后执行回归；
- 线上人工修正样本经审核后进入评测集，避免未经验证的反馈污染标准答案。

---

## 13. 项目交付场景的端到端协同示例

### 13.1 用户目标

项目经理提出：“请基于截至今天的授权项目上下文，准备本周项目状态评审材料，重点说明延期风险、关键依赖、待确认决策和建议跟进动作。”

### 13.2 执行过程

1. Coordinator 识别任务为 project_status_review。
2. Policy Service 校验项目经理身份、项目范围和用途。
3. ADS Context Engine 生成指定项目和时间窗的 Context Package。
4. Plan Validator 检查任务分解、Agent 清单、预算、时间和允许动作。
5. Project Context Agent 汇总当前状态、里程碑和变化。
6. Risk Analysis Agent 分析候选风险和影响。
7. Dependency Analysis Agent 分析阻塞链和关键路径。
8. Decision & Evidence Agent 核验决策审批状态、交付物版本和证据引用。
9. Verifier 检查各结果的来源、时效、冲突、未知和范围。
10. Coordinator 汇总评审材料，明确哪些是事实、推断、冲突和未知。
11. Action Drafting Agent 根据已核验问题生成内部行动项草稿。
12. 项目经理接受、修正或驳回建议；正式任务创建仍走原业务系统授权流程。
13. 如果后续开放受控 L2 动作，必须对每项动作独立审批、校验幂等并由 Tool Gateway 执行。
14. 业务系统返回回执，ADS 接收结果事件，Run Ledger 归档执行链路。

### 13.3 最终交付格式

每次评审至少包含：

- 项目概览与评审时间范围；
- 正式业务状态和认知状态的区分；
- 本期变化及来源；
- 关键里程碑和延期影响；
- 风险、问题和依赖链；
- 决策状态与证据缺口；
- 待确认事项；
- 行动项草稿及负责人候选；
- 结论证据索引；
- 未完成子任务、限制和数据新鲜度；
- 人工确认记录。

### 13.4 业务价值验证

与 ADS-WORK-05 的基线对齐，比较：

- 一次评审准备的总耗时；
- 跨系统查找和人工确认次数；
- 风险发现到责任人确认的周期；
- 会后行动项形成和录入耗时；
- 关键事实遗漏、日期错误和证据缺失；
- Agent 输出人工修改比例；
- 团队持续使用意愿。

不要将 Agent 执行任务数量当作业务价值。只有在质量和治理约束下真正减少工作成本或改善结果，才算有效。

---

## 14. 运行成本、性能与可靠性设计

### 14.1 运行预算

每个 Run 应配置：

- 最大总耗时和单任务超时；
- 最大 Agent 步骤数；
- 最大委派深度和子任务数；
- 最大并发数；
- 最大工具调用次数；
- Token / 模型成本预算；
- 最大重试次数；
- 允许的模型档位和降级策略。

预算由控制平面强制执行，Agent 不可自行提高预算。

### 14.2 模型路由

- 简单分类、格式校验和确定性计算优先使用规则或轻量模型。
- 复杂语义理解、冲突解释和任务规划使用适当能力模型。
- 高影响任务应优先选择更稳定的模型配置并增加验证步骤。
- 模型降级不能绕过原有权限和证据要求。
- 模型版本变化需要评测集回归，不应只比较速度或价格。

### 14.3 缓存与上下文复用

- 可缓存不含敏感数据且仍在有效期内的通用能力结果。
- 任务级 Context Package 必须检查授权、版本、完整性和 TTL。
- 不得跨租户或跨权限主体复用缓存。
- 业务状态变化、授权撤回、证据失效和策略升级应触发缓存失效。
- 不应将旧任务的 Agent 结果当作当前项目状态。

### 14.4 可靠性原则

- 任务队列支持持久化和状态恢复；
- 事件与工具调用支持幂等；
- 外部服务故障时返回明确的 partial / unavailable；
- 重试采用退避策略，并设置上限；
- 重要操作先查询后执行，避免超时导致重复副作用；
- 子任务失败不应隐藏在汇总文本中；
- 具备按 Agent、Tool、租户和业务域的熔断与降级能力。

---

## 15. 分阶段实施路线

本专题不是要求一次建设完整 Agent 平台。建议依照 ADS-WORK-05 的项目交付试点成果，按以下阶段逐步增加协同复杂度。

| 阶段 | 周期建议 | 建设重点 | 放行条件 |
|---|---|---|---|
| P0：契约与治理准备 | 1—2 周 | Agent Registry、Task Envelope、Result Contract、风险等级、策略边界 | 业务、安全、架构评审通过 |
| P1：单 Agent 只读 | 3—4 周 | 一个项目 Agent 消费 Context Package，完成状态评审摘要 | 证据、范围和结果质量达标 |
| P2：多 Agent 影子协同 | 5—6 周 | Coordinator + 2—4 个专业 Agent，先并行分析、不写回 | 委派可追踪，冲突和部分失败可处理 |
| P3：人工确认闭环 | 7—8 周 | Verifier、人工接受/修正/驳回、行动项草稿 | 业务团队完成真实任务验证 |
| P4：受控动作评估 | 9—10 周 | 对单个低风险内部动作做 L2 可行性评估和沙箱验证 | 幂等、审批、补偿、审计、安全测试通过 |
| P5：扩展与复用 | 后续 | 多项目、多团队、领域能力目录和运营机制 | 有可重复业务收益和明确运维责任 |

**重要边界：** P4 仅是评估和沙箱验证阶段，不代表默认进入真实生产写入。任何真实 L2 写入必须单独立项、单独授权和审批。L3 外部或高影响动作仍应由授权人员在正式业务系统完成。

### 15.1 首批工程最小集

建议先实现：

1. Agent Registry（静态配置起步）；
2. Task Envelope / Result Contract Schema；
3. Orchestrator（有限状态机）；
4. Task Broker（可先用单队列）；
5. Context Adapter（复用 ADS Context API）；
6. Tool Gateway（先只读）；
7. Verifier（Schema + 证据 + 规则检查）；
8. Run Ledger / Trace；
9. Human Review UI 或现有工作台入口；
10. Evaluation Dataset 与回归测试。

首期不需要先做 Agent 市场、可视化拖拽编排、无限自我规划或复杂自治系统。

---

## 16. 组织职责与运营机制

| 角色 | 主要职责 |
|---|---|
| 业务发起人 | 定义业务目标、风险容忍度和价值指标 |
| 业务流程负责人 | 确认流程、人工责任、审批节点和例外处理 |
| ADS 架构负责人 | 维护上下文模型、服务接口和跨层边界 |
| Agent Platform Owner | 维护 Agent Runtime、Orchestrator、Registry 和任务协议 |
| Domain Agent Owner | 对专业 Agent 的任务定义、结果质量和版本负责 |
| Tool Owner | 对工具参数、权限、下游副作用和 SLA 负责 |
| Policy / Security Owner | 对身份、授权、动作策略、审计和应急机制负责 |
| Evaluation Owner | 对评测集、验收口径、回归和业务收益评估负责 |
| Human Approver | 对具体业务决策和高影响动作承担正式责任 |

### 16.1 运营节奏

- 每周：检查失败任务、人工修正、策略拒绝、成本异常和用户反馈；
- 每次版本发布：执行离线评测和安全回归；
- 每月：复核 Agent 能力、工具权限、模型版本、成本和业务价值；
- 每季度或重大变更时：复核领域本体、权威字段、数据用途和授权范围；
- 发生重大安全事件：触发 Kill Switch、审计调查和恢复审批。

---

## 17. 架构决策记录（ADR）

| 编号 | 决策 | 推荐选择 | 原因 |
|---|---|---|---|
| ADR-01 | Agent 协作模式 | 中心化 Orchestrator + 专业 Agent | 权限、预算、状态和责任更易控制 |
| ADR-02 | Agent 间通信 | 结构化 Task Envelope / Result Contract | 可验证、可追踪、可复现 |
| ADR-03 | 共同事实来源 | ADS Context Package + 权威业务系统 | 避免 Agent 各自维护事实副本 |
| ADR-04 | 工具访问 | 统一 Tool Gateway | 集中鉴权、审计、幂等和限流 |
| ADR-05 | 高风险动作 | 独立 Approval Service + 人工责任 | 避免模型自行批准自己的计划 |
| ADR-06 | 任务状态 | 显式 Run / Task 状态机 | 处理部分成功、超时、取消和恢复 |
| ADR-07 | 记忆策略 | Run Context、Capability Memory、Enterprise Context 分离 | 防止记忆污染和越权共享 |
| ADR-08 | 质量评估 | 离线 + 影子 + 人工确认 + 业务基线 | 不以演示成功代替业务验证 |

以上是建议决策，须由正式架构评审确认。不同规模或业务域可以选择不同部署形态，但不能破坏任务契约、权限、审计和责任边界。

---

## 18. 关键待决策事项

立项前需要确认：

1. ADS 当前是否已有可复用的 Context API、授权服务和审计能力？
2. Agent Runtime 由 ADS 平台团队建设，还是复用已有 Agent 平台？
3. 首个 Agent 运行入口放在项目管理系统、企业工作台还是独立服务？
4. Agent 身份与人员身份如何绑定，如何表达 on_behalf_of？
5. Tool Gateway 是否有现成 API Gateway / IAM / Policy Engine 可以复用？
6. 哪些模型服务允许处理试点数据，部署和数据出域边界是什么？
7. 首批项目 Agent 的业务 Owner、Tool Owner 和人工审批人是谁？
8. 评测样本由谁维护，如何建立人工裁定基准？
9. 运行 Trace 和 Agent 产物的保留周期如何确定？
10. 未来允许哪些 L2 动作进入沙箱验证，谁有最终放行权？

---

## 19. 立项与验收清单

### 19.1 立项前

- [ ] 业务目标和首批任务类型明确；
- [ ] 业务流程负责人和 Agent Owner 明确；
- [ ] Agent、Tool、Skill 的边界已确认；
- [ ] Context Package 和权限模型可复用；
- [ ] Task Envelope 与 Result Contract 已版本化；
- [ ] Tool Gateway 的身份、策略和审计设计通过评审；
- [ ] L0—L3 动作等级和审批规则明确；
- [ ] 预算、并发、委派深度和 Kill Switch 已定义；
- [ ] 评测样本和基线口径明确；
- [ ] 真实数据处理范围获得批准。

### 19.2 上线前

- [ ] 单 Agent 任务验收通过；
- [ ] 多 Agent 并行、串行和部分失败场景通过；
- [ ] 子 Agent 越权测试通过；
- [ ] Context 过期、撤回和版本变化测试通过；
- [ ] 工具调用幂等、超时和重试测试通过；
- [ ] 审批与动作参数绑定测试通过；
- [ ] Trace 关联和审计完整性通过；
- [ ] 成本和运行预算强制限制通过；
- [ ] Prompt Injection 和跨项目隔离测试通过；
- [ ] 业务团队确认人工责任和例外处理方式。

### 19.3 扩大前

- [ ] 多项目任务成功率和证据质量达到冻结阈值；
- [ ] 业务周期或质量指标出现可重复改善；
- [ ] 人工修正率和返工原因可解释；
- [ ] 失败恢复和 Kill Switch 演练完成；
- [ ] Agent / Tool 版本和权限有持续维护人；
- [ ] 单项目成功已在其他项目中独立复现；
- [ ] 安全、业务和架构负责人共同作出 Go / No-Go 决策。

---

## 20. 结论：ADS 不只是让 Agent 知道企业发生了什么，更要让 Agent 在边界内推进工作

企业 Agent 协同不是在聊天界面里增加几个角色，也不是让多个模型互相讨论后直接操作业务系统。真正的企业级 Agent 协同，必须建立在统一运行上下文、明确任务契约、最小权限、受控工具、人工责任、执行审计和持续评测之上。

ADS 的独特价值可以进一步概括为：

- **ADS Context：** 让 Agent 知道企业正在发生什么，以及信息从哪里来；
- **ADS Ontology：** 让 Agent 理解业务对象、关系、事件和规则是什么意思；
- **ADS Policy：** 让 Agent 知道什么可以访问、什么可以做、什么必须审批；
- **Agent Runtime：** 让多个专业 Agent 按任务契约协同完成工作；
- **ADS Feedback：** 让执行结果、人工修正和业务验证回流，形成持续改进。

最终要形成的不是一群各自为政的 Agent，而是一套**共享可信企业上下文、遵守统一策略、按专业任务协作、由人承担业务责任、执行过程可验证和可追溯的企业智能执行体系**。

### 研究主线的下一步

ADS-WORK-07 可以继续研究：

**《企业 Agent 能力资产化、任务经验沉淀与跨业务复用机制研究》**

重点回答：一次 Agent 协同任务中，哪些经验可以沉淀为 Skill，哪些规则应该进入领域本体，哪些反馈可以优化任务模板，哪些结果可以成为企业能力资产，以及如何验证这些能力在不同项目、团队和岗位之间真正可复用。

---

## 附录 A：Machine-readable Task Envelope

- [Task Envelope JSON Schema](../schemas/ads-agent-task-envelope-v0.1.schema.json)
- [项目交付 Agent 委派示例](../examples/ads-agent-project-delivery-review.json)

## 附录 B：协同运行评估模板

- [Agent 协同运行评估表（CSV）](../pilot/Agent协同运行评估模板.csv)

> 本文件是架构与工程建议稿。Agent 角色、模型、指标阈值、权限策略、部署方式和动作开放范围均须根据 ADS 实际系统能力、业务流程和安全治理要求评审确认。示例中的租户、项目、Agent、用户和事件均为虚构。
