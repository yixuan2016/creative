# PDKS-STD-00-001：标准体系总则

Version: 1.0.0-draft  
Status: Candidate Draft  
Applies to: PDKS Standard、Runtime、Skills、Connectors、Agent Adapters

## 1. 目的
定义个人知识资产的统一表达、沉淀、治理、存储、交换和验证规则，使数据不依赖单一 Agent、数据库或应用而长期可读、可迁移和可复用。

## 2. 架构分层
- 语义层：Ontology、Event Taxonomy、关系与类型。
- 结构层：Record Schema、字段字典、约束。
- 证据层：Source Asset、Evidence、Provenance。
- 知识层：Knowledge Asset、质量、审核与生命周期。
- 存储层：Markdown、JSON/JSONL、原始附件、可重建索引。
- 交互层：Agent Tool Contract、MCP、CLI、用户确认。
- 治理层：Identity、Consent、Sensitivity、Retention、Audit。

## 3. 符合性原则
实现必须声明支持的标准版本；保留稳定 pdks_id/object_id；保留来源引用和采集时间；区分来源事实、用户陈述、Agent 推断和人工确认；执行授权与访问控制；支持开放格式导出；不得静默覆盖用户编辑或原始证据。

## 4. 版本策略
MAJOR 表示破坏性变化；MINOR 表示兼容扩展；PATCH 表示纠错。Draft、Candidate、Frozen、Deprecated、Retired 是不同状态。Frozen 仅代表兼容基线稳定，不等于生产安全认证。

## 5. 冲突优先级
法律与组织政策 > 用户明确授权 > 原始来源证据 > 人工确认知识 > Agent 推断 > 自动摘要。发生冲突时保留双方证据，不允许模型自行抹平。
