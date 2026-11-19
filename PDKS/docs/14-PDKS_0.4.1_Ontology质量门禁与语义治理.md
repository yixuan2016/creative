# PDKS 0.4.1：Ontology 质量门禁与语义治理引擎

> PDKS Runtime：0.4.1  
> PDKS Ontology：0.2.1  
> Record Schema：0.1.x（保持兼容）  
> Agent Skill：0.3.1  
> 日期：2026-11-19  
> 关联：PDKS 0.4.0 / ADS-WORK-08 / ADS-WORK-09 / ADS-WORK-10

## 0. 本阶段目标

PDKS 0.4.0 已经具备 Ontology-aware Runtime，但本体资源还缺少自动化质量门禁。本阶段将 Ontology 从“可以加载和映射”推进到“每次修改都能检查、比较、验证、追溯”。

**0.4.1 的核心不是增加更多概念，而是建立语义变更的安全机制。**

五项能力：
1. SHACL 运行时校验接口与 CI 强制门禁。
2. Runtime 术语、受控词汇、Event Taxonomy 和 JSON-LD Context 覆盖检查。
3. Ontology 版本差异、历史术语桥接和属性约束兼容性分析。
4. JSON-LD / RDF 图同构往返测试。
5. Ontology 资源 SHA-256 Manifest 与 GitHub Actions CI。

## 1. 版本策略

| 部件 | 0.4.0 | 0.4.1 | 兼容策略 |
|---|---|---|---|
| Runtime | 0.4.0 | 0.4.1 | 增加治理 CLI 与 SHACL 执行接口 |
| Ontology | 0.2.0 | 0.2.1 | 只增加历史映射、约束和质量元数据 |
| Record Schema | 0.1.x | 0.1.x | 不改写历史 JSON |
| Skill | 0.3.0 | 0.3.1 | 增加 CI、治理与 Manifest 工具 |

Ontology 0.2.0 作为历史版本保留，不原位覆盖。0.2.1 使用独立目录 `assets/ontology/0.2.1/`，但继续沿用稳定术语空间 `urn:pdks:ontology#` 和受控词汇空间 `urn:pdks:vocabulary:0.2#`。版本 IRI 为 `urn:pdks:ontology:0.2.1`。

## 2. 本阶段发现并修复的兼容性缺口

0.4.0 的旧版桥接检查只覆盖了部分核心类和属性。对 0.1 基线本体做完整扫描后，发现旧版本声明的 71 个 OWL 类和属性中，37 个缺少显式 `owl:equivalentClass` / `owl:equivalentProperty` 桥接。

0.4.1 补齐所有桥接：

- 旧版类：26/26 有显式映射。
- 旧版对象属性与数据属性：45/45 有显式映射。
- 旧版受控词汇概念：34/34 通过稳定 notation 建立 `skos:exactMatch`。
- 事件 Taxonomy 继续保持独立版本，不将事件代码误当成 OWL 类。

这保证旧 RDF 数据在新版本中仍然能够被解析、定位和迁移，而不是只保证 JSON 字段仍然存在。

## 3. Ontology 质量门禁分层

| 门禁 | 检查内容 | 失败后果 |
|---|---|---|
| G0 Manifest | 文件存在、字节数和 SHA-256 一致 | 阻止发布 |
| G1 Syntax | Turtle、JSON、JSON-LD Context 可解析 | 阻止发布 |
| G2 Term Coverage | Runtime 引用术语必须在 Ontology 声明 | 阻止发布 |
| G3 Vocabulary | Runtime 受控值必须在 SKOS Vocabulary 中 | 阻止发布 |
| G4 Taxonomy | 事件类型必须来自 Event Taxonomy | 阻止发布 |
| G5 Compatibility | 旧术语必须有等价桥接；不能新增破坏性约束 | 阻止发布 |
| G6 SHACL | 数据图必须符合图结构约束 | 阻止该数据包入库/发布 |
| G7 Round-trip | JSON-LD 导出再解析必须与原 RDF 图同构 | 阻止发布 |
| G8 Runtime Regression | SQLite、Owner 隔离、版本、SPARQL 和投影重建测试 | 阻止发布 |

## 4. SHACL 运行时校验

新增 `OntologyRuntime.validate_shacl(data_graph)`：

1. 复制待校验 Owner RDF 投影。
2. 合并只读受控词汇图和 Event Taxonomy 图，避免远程导入依赖。
3. 加载版本化 SHACL Shapes。
4. 使用 pySHACL 执行 RDFS inference、SHACL Advanced/SPARQL Constraints 和 Meta-SHACL 检查。
5. 返回 conformant / non_conformant / unavailable 状态、结果数量、焦点节点、属性路径、严重级别和消息。

本体 Shape 增加以下约束：
- 每条个人记录必须有且只有一个 Owner、敏感级别和访问范围。
- Event 类型必须属于指定 Event Taxonomy。
- Assertion 认知状态必须来自核心受控词汇。
- Evidence Segment 必须链接 Source Asset。
- Personal Context 必须有主体、类型和核验状态。
- Source Asset 的设备采集/连接器同步必须有授权引用。
- Agent Action Proposal 必须有提案 Agent、审批状态和必要的批准/执行主体。
- ActionSpecification 不得同时标记为 AgentActionProposal。
- 个人记录之间不得出现未授权的跨 Owner 数据引用。
- QualifiedRelationship 的谓词必须来自白名单。

注意：Ontology 描述授权语义，但 SHACL 只能检查图中是否存在授权引用，不能证明授权真实有效。真实授权仍须由宿主 Consent / Policy Service 验证。

## 5. 术语覆盖检查

`pdks_ontology_governance.py` 自动扫描：
- Runtime 源码中所有 `PDKS.term` 引用；
- Ontology 中声明的稳定术语；
- Runtime 受控值与 SKOS notation 的覆盖；
- Event Taxonomy 是否为空、事件代码是否可用；
- JSON-LD Context 中 `pdks:` 别名是否指向已声明术语。

当前结果：Runtime 引用 98 个 PDKS 术语，98/98 已声明；54 个 Runtime 必需受控值全部可解析；Event Taxonomy 有 72 个事件类型。

## 6. 版本差异与兼容性分类

兼容性检查不简单比较 Turtle 文件文本，而是比较 OWL 语义声明：

- `breaking`：旧术语缺少显式桥接；新增更严格的 domain/range 约束；旧属性被替换但无迁移路径。
- `compatible_with_review`：旧约束被放宽，历史数据仍可读，但语义边界变宽，需要本体负责人审查。
- `compatible`：所有历史术语都有桥接，且没有待审查的语义约束变化。

0.4.1 相对 0.1 基线：71/71 个类和属性桥接完整；0 个破坏性变化；14 项 domain/range 放宽进入人工审查清单。放宽不等于自动正确，必须由语义负责人确认是否为有意的泛化。

## 7. JSON-LD / RDF 往返一致性

原有测试只比较导出前后的三元组数量，这不足以证明图一致。0.4.1 改为 RDF 图同构测试：

`Graph -> JSON-LD -> Graph` 必须通过 `rdflib.compare.isomorphic`。

同时从 JSON-LD Context 中删除没有对应本体声明的 envelope-only alias，避免产生不存在的 `pdks:payload`、`pdks:governance` 等伪语义属性。

## 8. Ontology Manifest

每个 Ontology 发布目录包含 `ontology-manifest.json`，登记：
- Ontology Version IRI；
- 稳定术语、词汇和事件分类命名空间；
- Record Schema 兼容范围；
- Core、Governance、Agent Runtime、Vocabulary、SHACL、JSON-LD Context、Mapping 和 Migration 文件的字节数与 SHA-256。

发布前必须执行：

```bash
python skills/pdks-personal-knowledge/scripts/build_ontology_manifest.py --check
```

修改 Ontology 资源后，先执行不带 `--check` 的构建命令，再提交更新后的 Manifest。

## 9. CI 使用方法

安装完整开发依赖（包括 pySHACL）：

```bash
python -m pip install -r requirements-dev.txt
```

运行质量门禁：

```bash
python prototype/pdks_ontology_cli.py ontology-check
python prototype/pdks_ontology_cli.py validate \
  --records-dir skills/pdks-personal-knowledge/examples/scenarios \
  --strict-refs --shacl \
  --trusted-consent-ref urn:pdks:consent:example:daily-work \
  --trusted-consent-ref urn:pdks:consent:example:research \
  --trusted-consent-ref urn:pdks:consent:example:voice-meeting
python -m unittest discover -s tests -v
```

`--shacl` 是强制执行模式：如果 pySHACL 不可用，命令返回非零状态，不允许把“跳过”报告成通过。

GitHub Actions 工作流：`.github/workflows/pdks-ontology-ci.yml`。PR 和目标分支变更时自动执行 Manifest、Ontology 治理、SHACL 和单元测试门禁。

## 10. 本地验证结果与限制

| 项目 | 本地结果 |
|---|---|
| 自动化测试 | 27 项：26 通过、1 项因 pySHACL 缺失跳过 |
| Ontology Governance CLI | valid |
| Runtime 术语覆盖 | 98/98 |
| 0.1 → 0.2.1 类/属性桥接 | 71/71 |
| 0.1 → 0.2.1 Vocabulary 桥接 | 34/34 |
| 破坏性语义变化 | 0 |
| 待审查的约束放宽 | 14 |
| Ontology Manifest | 8/8 文件哈希通过 |
| 示例记录 | 29 条、3 个 Owner，严格引用与授权门禁通过 |
| SHACL 真实运行时校验 | 当前执行环境无法联网安装 pySHACL，尚待 GitHub Actions runner 执行 |

本地没有 pySHACL 时，Runtime 返回 `unavailable`，不会伪装为 conformant。CI 配置会安装 pySHACL 并执行真实 SHACL 校验；在看到成功的 Actions Run 前，不把 SHACL 运行时门禁宣称为已通过。

## 11. 下一阶段

### 0.4.2：语义治理工作台
- 14 项放宽约束逐项给出理由、风险和批准人。
- 自动生成 Ontology diff HTML。
- 术语生命周期：proposed / accepted / deprecated / retired。
- 维护 ontology decision record（ODR）。

### 0.5：真实数据接入
- 用户主动导出的钉钉、语音转写和文档。
- 证据定位、来源去重、增量同步和撤回传播。
- 真实授权服务接入，不复用示例 Consent Reference。

### 0.6：个人数智底座服务化
- Personal Data API、个人上下文服务和 Agent Adapter。
- 加密、多端同步、身份与权限服务。

## 最终判断

PDKS 0.4.0 解决“数据如何按统一语义组织和运行”；PDKS 0.4.1 解决“这套语义如何安全演进、如何证明没有破坏历史兼容性”。

**没有质量门禁的 Ontology 只是文档；具备版本、兼容性、约束、哈希和 CI 的 Ontology，才开始成为可治理的基础设施标准。**
