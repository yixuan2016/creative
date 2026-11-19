# PDKS 0.4.0：Ontology 优先的个人数智底座架构

> Runtime 0.4.0 · Ontology 0.2.0 · Record Schema 0.1.x · 2026-11-19

## 核心判断

**Ontology 定义数据意义；Taxonomy 定义受控概念；JSON Schema 定义记录结构；SHACL 定义图关系约束；SQLite 负责事务与持久化；RDF 是可重建的语义投影；Agent 负责理解和使用数据。**

0.4 不替换 SQLite，也不把 RDF 图谱作为唯一事实源。规范 PDKS JSON 记录是 canonical record；SQLite 是本地权威存储；RDF 图谱是可重建、可查询、可交换的语义视图。

## 架构

```text
多源输入：钉钉导出 / 语音转写 / 文档 / 邮件 / 日历 / 手工输入
                              |
                              v
                    Canonical PDKS JSON
                              |
                              v
          JSON Schema -> SKOS Taxonomy -> OWL -> SHACL
                              |
                              v
                  Ontology-aware Runtime
                  ID / 时间 / 来源 / 关系 / 治理
                              |
                  +-----------+-----------+
                  |                       |
                  v                       v
             SQLite Store           RDF Projection
        规范记录 / 历史版本         Owner Named Graph
        revision / audit            Turtle / JSON-LD / SPARQL
                  |                       |
                  +-----------+-----------+
                              v
               Personal Assistant OS / Agents
```

## 本体模块

| 模块 | 核心语义 |
|---|---|
| Core | Person、Organization、Event、Assertion、Knowledge、Context、Action、Relationship |
| Event | 工作、学习、思考、生活事件分类 |
| Knowledge | 方法、经验、洞察、原则、案例 |
| Personal Context | 角色、能力、目标、责任、偏好 |
| Temporal | 发生、采集、记录、有效、截止时间 |
| Provenance | 来源、证据、表达者、创建者、处理活动 |
| Governance | Consent、Access、Retention、Deletion |
| Agent Runtime | Intent、AgentActionProposal、审批、执行 |

复用 OWL/RDFS、SKOS、PROV-O、OWL-Time、SHACL。

## 版本策略

- Ontology Version IRI：`urn:pdks:ontology:0.2`
- 稳定术语命名空间：`urn:pdks:ontology#`
- 受控词汇：`urn:pdks:vocabulary:0.2#`
- Event Taxonomy：沿用 `urn:pdks:taxonomy:event:0.1#`
- Record Schema：保持 0.1.x，历史 JSON 不强制重写。

旧 `urn:pdks:ontology:0.1#` 术语通过 `owl:equivalentClass` / `owl:equivalentProperty` 桥接。迁移时保留原始记录、ID、来源和证据，在新本体版本下重新投影。

## 关键语义边界

1. Event 不等于 Assertion：某人表达一个观点，不证明所描述的事件已经发生。
2. Evidence 不等于 Knowledge：证据是来源，知识是经过提炼的可复用资产。
3. AI 推断的 Personal Context 默认是候选，不自动升级为本人确认。
4. Intent / ActionSpecification 不等于 AgentActionProposal，不自动获得外部执行权限。
5. Owner、Record Creator、Assertion Speaker、Processing Agent 是不同角色。
6. 事件发生时间、来源采集时间、记录时间和有效时间不得混用。
7. 不确定身份使用 `possibleIdentityMatch`，不滥用 `owl:sameAs`。
8. OWL 采用开放世界假设；缺少三元组不等于事实为假。

## SQLite 设计

| 表 | 责任 |
|---|---|
| pdks_ontology_registry | 本体版本、IRI、manifest hash |
| pdks_owner_state | owner revision、并发控制 |
| pdks_objects | canonical JSON 当前版本 |
| pdks_object_versions | 不可变历史快照 |
| pdks_triples | owner-scoped RDF 投影 |
| pdks_audit_log | 最小化操作审计 |
| pdks_schema_migrations | 数据库结构升级 |

原始录音和文档独立存储；SQLite 保存 locator、hash 和证据定位。RDF 是物化视图，可从 canonical JSON 重建。

## 0.4 原型实现

- `prototype/pdks_ontology_runtime.py`：Ontology 加载、JSON Schema / Taxonomy 校验、RDF 投影。
- `prototype/pdks_ontology_sqlite.py`：规范记录、版本、Owner 分区、RDF triples、审计。
- `prototype/pdks_ontology_cli.py`：validate、init、import、export、SPARQL、rebuild。
- Skill 0.3.0 同步携带运行时脚本与 Ontology 资源。

设备采集和连接器同步必须提供可信 Consent Service 返回的 active reference；模型不能自行编造。示例包中的 consent reference 是合成测试值。

## 验证结果

- 自动化测试：**20/20 通过**。
- 3 个场景、29 条示例记录，严格引用校验通过。
- 9 个 Turtle 文件、2,187 triples 语法解析通过。
- 72 个事件类型代码、67 个受控词汇代码。
- SQLite 导入、重启恢复、幂等、并发冲突、Owner 隔离、Turtle / JSON-LD 导出、SPARQL 和 RDF 重建测试通过。

**SHACL 边界：** 当前环境未安装 pySHACL；本次完成 SHACL 文件语法解析和内置语义 profile 校验，未执行 SHACL 运行时 conformance。

## 尚未生产化

数据库加密、密钥管理、Owner 身份认证、正式 Consent / Policy Service、真实钉钉/录音连接器、多端同步、原始文件物理删除传播和生产级防篡改审计尚未实现。SPARQL 当前在单个 Owner 的内存图上执行，不是生产图数据库。

## 下一步

- 0.4.1：pySHACL CI、Ontology term coverage、semantic diff、JSON-LD round-trip。
- 0.5：钉钉主动导出和录音转写的只读接入、增量同步、去重和来源撤回。
- 0.6：Personal Assistant OS、个人上下文服务、加密同步和删除闭环。
