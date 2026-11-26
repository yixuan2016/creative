# PDKS Standards 1.0 — 标准体系建设基线

状态：Candidate Draft；不是生产级正式发布标准。研发阶段仍为 transitional_skill_development。

兼容基线：PDKS Standard 0.1.0、Record Schema 0.1.x、Ontology 0.2.1、Event Taxonomy 0.1.0、File-first Storage 0.1.0 Preview。

| 标准域 | 内容 | 当前成熟度 |
|---|---|---|
| STD-00 总则与治理 | 术语、版本、变更 | Candidate Draft |
| STD-01 核心数据 | Record、Ontology、Event、关系 | 现有基线整合 |
| STD-02 知识资产 | Source、Evidence、Knowledge Quality | 部分实现 / Draft |
| STD-03 存储交换 | Markdown、JSONL、附件、Agent Exchange | Preview / Draft |
| STD-04 采集连接器 | Capture、Connector、增量同步 | DWS Preview |
| STD-05 安全治理 | Identity、Consent、Sensitivity、Retention、Audit | 部分实现 / 待安全评审 |
| STD-06 一致性验证 | Schema、Ontology、Connector、Agent Conformance | 原型 / Draft |

## 核心原则
1. 数据标准稳定，技术实现可替换，Agent Skill 可替换。
2. 原始来源、证据、AI 推断和人工确认必须区分。
3. 文件优先、开放格式、可迁移；SQLite 不作为唯一知识资产。
4. Ontology 定义语义，Schema 约束结构，Taxonomy 管理分类。
5. 用户授权、最小化采集、来源可追溯、删除可执行。
6. 未验收能力必须标注 not_verified，不得虚报兼容。
