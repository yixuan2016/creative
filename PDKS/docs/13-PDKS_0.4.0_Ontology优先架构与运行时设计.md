# PDKS 0.4.0：Ontology 优先的个人数智底座架构与运行时设计

> 版本：PDKS Runtime 0.4.0  
> Ontology：0.2.0  
> Record Schema：0.1.x（保持兼容）  
> 日期：2026-11-19  
> 关联：PDKS Agent Skill 0.3.0 / ADS-WORK-08 / ADS-WORK-09 / ADS-WORK-10

## 0. 本阶段结论

PDKS 从“有一套记录格式”升级为“有一套可执行的个人数据语义契约”。

**Ontology 定义数据意义；Taxonomy 定义受控概念；JSON Schema 定义记录结构；SHACL 定义图关系约束；SQLite 负责事务与持久化；RDF 是可重建的语义投影；Agent 负责理解和使用数据。**

本阶段不替换 SQLite，也不把 RDF 图谱作为唯一事实源。采用本地优先、Ontology-aware 的混合架构：

- PDKS JSON 记录是规范化、可携带的 canonical record。
- 原始录音、文档、图片等二进制证据留在文件/对象存储；数据库只保留引用、定位符、哈希和治理元数据。
- SQLite 保存 canonical JSON、不可变记录版本、owner revision、Ontology Registry、审计元数据和 RDF 三元组投影。
- RDF 投影可以按指定 Ontology 版本重建、导出 Turtle / JSON-LD，并在单个 owner 的图上执行 SPARQL。
- PDKS Ontology 不直接授予访问权限；授权必须由运行时策略和可信 Consent Service 执行。

## 1. 为什么要从 Schema 走向 Ontology

Schema 解决“数据长什么样”，Ontology 解决“数据是什么意思，以及不同数据如何形成语义关系”。

例如，同一条会议录音可以产生：

- Source Asset：原始录音；
- Evidence Segment：录音中的某段转写；
- Event：实际发生的会议；
- Assertion：某位参与者表达的观点；
- Knowledge Asset：从会议与证据中提炼的经验；
- Personal Context：关于本人当前关注方向的候选理解；
- Action / Intent：会议中形成的任务或承诺；
- Qualified Relationship：知识、事件、人物、项目之间带证据的关系。

它们不能被压缩成一个“会议纪要”文本，也不能把 AI 推断直接升级为本人确认的事实。

## 2. 0.4 总体架构

~~~text
DingTalk export / voice transcript / documents / mail / calendar / manual input
                              |
                              v
                   PDKS Capture & Normalization
                              |
                              v
                    Canonical PDKS JSON Records
             Entity / Source / Evidence / Event / Assertion
             Knowledge / PersonalContext / Action / Relation
                              |
                              v
                  Ontology-aware Validation Layer
              JSON Schema -> Taxonomy -> OWL terms -> SHACL
                              |
                              v
                  Ontology-aware Data Runtime
          ID resolution / provenance / temporal / governance
          controlled vocabulary / relation qualification
                              |
                +-------------+-------------+
                |                           |
                v                           v
         SQLite Canonical Store       RDF Semantic Projection
         record + versions            named graph per owner
         revision + audit             Turtle / JSON-LD / SPARQL
                |                           |
                +-------------+-------------+
                              |
                              v
                Agent Adapter / Personal Assistant OS
                  retrieve / reason / plan / assist
~~~

## 3. 四层标准与运行职责

| 层 | 标准/技术 | 责任 | 不应承担的责任 |
|---|---|---|---|
| 语义层 | OWL / RDFS | 定义类、属性、继承和关系语义 | 不负责数据库事务 |
| 概念层 | SKOS / Taxonomy | 定义事件类型、领域、状态、敏感级别 | 不负责个人事实判断 |
| 结构层 | JSON Schema | 约束 JSON 记录结构和字段类型 | 不替代语义关系校验 |
| 图约束层 | SHACL | 约束 RDF 图中的必需关系、基数、类型 | 不替代授权策略 |
| 运行层 | Python Runtime | 映射、校验、版本、ID、查询、迁移 | 不自动获得连接器权限 |
| 持久层 | SQLite + 文件存储 | 事务、记录、版本、索引、原始证据引用 | 不负责本体推理 |
| 语义视图 | RDFLib / RDF | 图谱查询、语义导出、跨系统交换 | 不作为唯一事实源 |

## 4. 模块化 Ontology

| 模块 | 主要类/语义 | 说明 |
|---|---|---|
| Core Ontology | Person、Organization、DomainEntity、Event、Assertion、KnowledgeAsset、PersonalContextStatement、ActionSpecification、QualifiedRelationship | 个人数据核心概念 |
| Event Taxonomy | work、learning、thinking、life 等域及细分事件 | 事件类型是 SKOS Concept，不为每个事件代码创建 OWL Class |
| Knowledge Vocabulary | method、insight、principle、case、lesson 等 | 知识类型受控化 |
| Personal Context Vocabulary | role、goal、capability、responsibility、current_focus 等 | 上下文类型可扩展 |
| Temporal | OWL-Time Instant / Interval | 区分发生、采集、记录、有效、截止时间 |
| Provenance | PROV-O、SourceAsset、EvidenceSegment、ProcessingActivity | 来源、表达者、创建者、处理者不能混淆 |
| Governance | ConsentRecord、AccessGrant、RetentionPolicy、DeletionRequest | 描述授权与生命周期，但不替代执行策略 |
| Agent Runtime | Intent、AgentActionProposal、AgentExecution | 人的计划与 Agent 外部动作分离 |

## 5. 命名空间与版本策略

- Ontology Version IRI：`urn:pdks:ontology:0.2`
- 稳定术语命名空间：`urn:pdks:ontology#`
- 受控词汇：`urn:pdks:vocabulary:0.2#`
- 事件 Taxonomy：`urn:pdks:taxonomy:event:0.1#`
- JSON Record Schema：`0.1.x`
- Runtime：`0.4.0`

**不要把版本号简单塞进每个术语 IRI。** 本体版本可以升级，但类和属性的身份应尽可能稳定。0.2 本体提供从 `urn:pdks:ontology:0.1#` 到稳定术语空间的 `owl:equivalentClass` / `owl:equivalentProperty` 桥接。

历史 JSON 记录不因 Ontology 版本变化而自动改写。迁移策略是：保留原始记录和 ID，在目标 Ontology 版本下重新生成语义投影，并记录投影所用的本体版本和映射版本。

## 6. 关键语义约束

### 6.1 Event 与 Assertion 分离

- Event：发生过什么。
- Assertion：谁说了什么、系统推断了什么。
- Evidence：这个判断依据哪段原始材料。
- Assertion 的 `epistemic_status` 必须保留 reported / inferred / hypothesized / corroborated / disputed / retracted / unknown 等状态。

“某人说项目延期”是 Assertion；“项目延期”是否真实发生，还需要事件证据和状态核验。

### 6.2 Knowledge 与 Personal Context 分离

- KnowledgeAsset 是可复用的经验、方法、原则、案例和洞察。
- PersonalContextStatement 是关于某个人的角色、能力、目标、责任、偏好和当前关注的时间限定陈述。
- AI 推断的个人上下文默认 inferred / candidate，不能自动升级为 owner_confirmed。
- 个人上下文必须保留证据、置信程度、复核策略和有效时间。

### 6.3 Intent 与 Agent Action Proposal 分离

- ActionSpecification / Intent 描述人的计划、任务和承诺。
- AgentActionProposal 描述 Agent 准备执行的外部或状态变更动作。
- 人有一个任务，不代表 Agent 获得执行任务的权限。
- Agent Action 必须经过身份、权限、策略和必要的本人审批。

### 6.4 Provenance 角色分离

至少区分：
- `owner_ref`：个人数据分区的所有者；
- `provenance.created_by`：记录创建者；
- `payload.asserted_by_ref`：观点/主张的表达者；
- `processing_activity_ref`：AI 或系统处理活动；
- `source_refs`：原始来源；
- `evidence_refs`：支持具体主张的证据片段。

### 6.5 时间语义分离

不得混用：
- Event occurrence time：事件发生时间；
- Source capture time：来源采集时间；
- Record time：记录创建和更新时间；
- Assertion time：表达时间；
- Due time：行动截止时间；
- Valid time：知识或个人上下文有效时间。

时间区间映射到 OWL-Time Interval，单一时间点映射到 OWL-Time Instant，原始时区和精度保留在 JSON 记录。

### 6.6 关系建模

- 简单、稳定、已确认的关系可以投影为 RDF 直接边。
- 需要置信度、证据、状态、有效期或审核者的关系必须保留 QualifiedRelationship 记录。
- 关系谓词使用受控白名单，不从用户文本动态创建任意 RDF 属性。
- 不确定实体匹配使用 `possibleIdentityMatch`，未经确认不使用 `owl:sameAs`。

## 7. 数据库策略：SQLite 继续作为本地权威存储

0.4 不替换 SQLite。增加 Ontology-aware SQLite Extension：

| 表 | 内容 | 用途 |
|---|---|---|
| `pdks_ontology_registry` | Ontology 版本、IRI、manifest hash、active | 本体版本登记 |
| `pdks_owner_state` | owner_ref、revision | 个人分区与乐观并发 |
| `pdks_objects` | 最新 canonical JSON、hash、类型、版本 | 规范记录 |
| `pdks_object_versions` | 不可变历史版本 | 审计、纠错和回滚依据 |
| `pdks_triples` | owner named graph、subject、predicate、object N3、来源对象、Ontology 版本 | RDF 物化投影 |
| `pdks_audit_log` | 操作、actor、revision、计数、摘要 | 元数据审计 |
| `pdks_schema_migrations` | SQLite 表结构版本 | 数据库升级 |

RDF 图谱是可重建视图，不是第二个相互独立的事实库。原始录音和文件不直接塞进 RDF 三元组或 SQLite 大字段；本版本保留 source locator / hash / evidence locator，真实文件存储和删除闭环仍需单独开发。

## 8. 数据流与验证顺序

1. **JSON Schema**：检查字段、类型、必填和格式。
2. **Taxonomy / Controlled Vocabulary**：检查事件代码、领域、认知状态、敏感度和关系谓词。
3. **Ontology Mapping**：把对象类型映射为 OWL Class，把概念代码映射为 SKOS Concept。
4. **Reference Validation**：检查本包内 PDKS 引用；外部主体必须经身份注册或明确标记。
5. **SHACL**：检查图关系、基数、对象类型等约束。
6. **Runtime Policy**：检查 owner、授权、目的、访问范围、保留和动作审批。
7. **Persistence**：原子写入 canonical record、版本、RDF projection 和审计元数据。

OWL 采用开放世界假设。没有某条三元组，不等于事实为假；推理结果也不能直接当成本人确认的事实。

## 9. 0.4 原型实现

新增：
- `prototype/pdks_ontology_runtime.py`：加载模块化本体、JSON Schema 和 Taxonomy；校验记录；投影 RDF。
- `prototype/pdks_ontology_sqlite.py`：SQLite canonical record / version / triples / registry / audit。
- `prototype/pdks_ontology_cli.py`：命令行入口。
- Skill 内同步同一组脚本，支持独立携带。
- `assets/ontology/0.2.0/`：本体、治理本体、Agent 本体、词汇、SHACL、JSON-LD context、映射、迁移表。

命令示例：

~~~bash
# 依赖
python -m pip install -r requirements-dev.txt

# 本体与概念清单
python prototype/pdks_ontology_cli.py ontology-info

# 校验示例记录
python prototype/pdks_ontology_cli.py validate \\
  --records-dir skills/pdks-personal-knowledge/examples/scenarios \\
  --strict-refs

# 初始化本地数据库
python prototype/pdks_ontology_cli.py init \\
  --db ./data/personal.sqlite3 --owner <owner-ref>

# 导入一个 owner 的 PDKS 记录包
python prototype/pdks_ontology_cli.py import \\
  --db ./data/personal.sqlite3 --owner <owner-ref> \\
  --records-dir ./my-export/records --expected-revision 0 --strict-refs \
  --trusted-consent-ref <trusted-active-consent-ref>

# 导出语义图
python prototype/pdks_ontology_cli.py export \\
  --db ./data/personal.sqlite3 --owner <owner-ref> \\
  --format turtle --output ./exports/personal-graph.ttl

# 查询：查找某个人图谱中的 Event
python prototype/pdks_ontology_cli.py sparql \\
  --db ./data/personal.sqlite3 --owner <owner-ref> \\
  --query 'SELECT ?s WHERE { ?s a <urn:pdks:ontology#Event> . }'
~~~

`--allow-updates` 仅在明确审核后用于同一 object_id 的内容修订；默认冲突即拒绝。`expected_revision` 用于防止并发覆盖。`device_capture` / `connector_sync` 必须提供来自可信授权服务的 `--trusted-consent-ref`，否则运行时拒绝导入。示例数据中的 consent refs 是合成测试值，不能用于真实录音或连接器授权。

## 10. 验证结果

- 自动化测试：20/20 通过。
- 3 个示例场景：29 条记录，分属 3 个 owner，严格引用校验通过。
- 9 个 Turtle 文件语法解析通过，共 2,187 triples。
- Ontology Runtime：核心本体、治理本体、Agent Runtime 本体加载成功。
- Event Taxonomy：72 个事件类型概念。
- 受控词汇：67 个概念代码。
- SQLite：导入、重启恢复、幂等、owner 隔离、并发冲突、版本更新、RDF 导出、SPARQL 查询和投影重建测试通过。
- SHACL：当前环境未安装 pySHACL；本次只完成 SHACL 文件语法解析和内置语义 profile 校验，**不宣称 SHACL 运行时验证通过**。

## 11. 尚未生产化

| 能力 | 0.4 状态 | 下一步 |
|---|---|---|
| Ontology 版本与映射 | 原型完成 | 语义评审、兼容性测试 |
| JSON → RDF | 原型完成 | 更多真实数据与边界测试 |
| SQLite 本地持久化 | 原型完成 | 压力、恢复、加密 |
| SPARQL | owner 图加载到内存后查询 | 大规模图查询服务 |
| SHACL | 文件已提供，运行时未执行 | 安装 pySHACL 并建立 CI |
| 原始文件存储 | 只保留 locator/hash | 加密对象存储和删除回执 |
| 身份认证 | 未实现 | 宿主身份与 owner 认证 |
| 授权服务 | 仅保留 consent_ref | 正式 Consent / Policy Service |
| 物理删除 | 未实现 | 原始文件、派生数据、备份传播 |
| 多端同步 | 未实现 | 端到端加密与冲突解决 |
| 钉钉/录音连接器 | 未实现 | 先做只读、用户主动导出接入 |
| 企业投影 | 未实现 | ADS-WORK-08 授权映射与隔离 |

## 12. 下一步建议

### PDKS 0.4.1：SHACL 与 Ontology CI
- 在 CI 中执行 pySHACL。
- 增加 Ontology term coverage 检查，禁止代码引用未定义谓词。
- 增加 JSON-LD round-trip 和 RDF 重建一致性测试。
- 为 Ontology 变更建立 semantic diff 与兼容性门禁。

### PDKS 0.5：真实数据接入
- 先接入用户主动导出的钉钉记录和语音转写。
- 做 source/evidence locator 标准化。
- 做增量游标、去重、来源撤回和重新投影。
- 不直接开启全量后台采集。

### PDKS 0.6：Personal Assistant OS
- 个人上下文服务、证据检索、时序回顾和任务意图。
- Agent API 与访问策略。
- 加密、多设备同步和删除闭环。

## 最终架构判断

PDKS 是个人数据的统一语义标准；Ontology 是个人数据的语义骨架；SQLite 是当前本地权威存储；RDF 是跨系统语义表达和查询视图；ADS-WORK-08 负责语义与授权桥接；ADS-WORK-09 负责个人运行时；ADS-WORK-10 面向用户提供个人助理体验。

这套架构要实现的不是“让所有 Agent 都读一个数据库”，而是让所有 Agent 都能通过稳定的个人数据语义契约，理解同一个人的事件、知识、上下文、证据、目标和权限。
