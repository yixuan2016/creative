# PDKS-STD-01-002：Ontology 与关系模型规范

Baseline: Ontology 0.2.1  
Status: Existing baseline; semantic governance draft

## 本体职责
Ontology 定义个人世界中的对象类型、属性、关系和约束。它不等同于数据库表结构，也不负责规定某个 Agent 的提示词。

## 核心概念族
Actor：Person、Organization、Agent。  
Context：Project、Area、Location、TimeContext。  
Occurrence：Event、Interaction、Meeting、LifeEvent。  
Intent & Execution：Goal、Action、Task、Commitment。  
Knowledge：Assertion、Decision、KnowledgeAsset、Preference。  
Evidence：SourceAsset、EvidenceSegment、Artifact。  
Governance：ConsentGrant、SensitivityLabel、RetentionPolicy、AuditEvent。

以上为概念族建议。与 Ontology 0.2.1 已有类名不一致时，必须通过映射表解释，不得直接改写冻结基线。

## 关系规范
关系采用有向、具名、可校验谓词，例如 participated_in(Person, Event)、belongs_to(Event, Project)、assigned_to(Action, Person)、supported_by(Assertion, Evidence)、derived_from(KnowledgeAsset, SourceAsset)。

关系记录应包含 subject、predicate、object、provenance，以及适用时的 valid_time 和 confidence。

## 事件中心原则
Event 关联同一事项在聊天、会议、日历、待办、邮件和文件中的不同表现。合并事件必须保留各自 Source Asset / Evidence，不得丢失来源差异。

## 本体治理
新增类或谓词需提供定义、正反例、domain/range、必要属性、来源映射、迁移规则和验证用例。
