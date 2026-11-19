# PDKS 0.4.1：Ontology 质量门禁与语义治理引擎

> Runtime 0.4.1 · Ontology 0.2.1 · Record Schema 0.1.x · Skill 0.3.1

## 本阶段目标

PDKS 0.4.0 已具备 Ontology-aware Runtime；0.4.1 将它推进为可持续演进、可验证、可审计的语义基础设施。核心不是堆叠更多概念，而是建立本体变更的质量门禁。

## 五项增量

1. **SHACL 运行时校验**：通过 pySHACL 执行 SHACL Core、Advanced/SPARQL Constraints 与 Meta-SHACL。缺少依赖时返回 `unavailable`，绝不冒充通过。
2. **术语覆盖检查**：扫描 Runtime 的 PDKS 术语、受控词汇、Event Taxonomy 和 JSON-LD Context。
3. **语义版本差异**：比较 OWL 类/属性桥接，以及 `rdfs:domain` / `rdfs:range` 变化。
4. **JSON-LD 往返一致性**：由三元组数量比较升级为 RDF graph isomorphism。
5. **资源完整性与 CI**：8 个 Ontology 资源文件登记 SHA-256，并加入 GitHub Actions 门禁。

## 版本策略

| 部件 | 版本 | 说明 |
|---|---|---|
| Runtime | 0.4.1 | 增加语义治理 CLI 和 SHACL API |
| Ontology | 0.2.1 | 历史桥接补齐、增强图约束 |
| Record Schema | 0.1.x | 保持兼容，不强制重写历史 JSON |
| Skill | 0.3.1 | 增加治理脚本和 Manifest |

Ontology 0.2.0 保留为历史版本；0.2.1 使用独立目录，不覆盖旧资源。稳定术语命名空间仍为 `urn:pdks:ontology#`，版本 IRI 为 `urn:pdks:ontology:0.2.1`。

## 历史兼容性修复

完整扫描 0.1 基线后发现，旧版 71 个 OWL 类/属性中有 37 个缺少显式等价桥接。0.2.1 已补齐：

- OWL Class：26/26；
- Object / Datatype Property：45/45；
- 历史 SKOS 概念：34/34 通过稳定 notation 和 `skos:exactMatch` 映射。

语义差异检查结果：**0 个 breaking change**；14 项 domain/range 放宽进入人工审查清单。约束放宽不等于自动正确，仍需 Ontology Owner 确认。

## 九道质量门禁

| Gate | 检查 |
|---|---|
| G0 | Ontology Manifest、SHA-256 |
| G1 | Turtle / JSON / Context 语法 |
| G2 | Runtime 术语覆盖 |
| G3 | SKOS 受控词汇覆盖 |
| G4 | Event Taxonomy 覆盖 |
| G5 | 历史桥接和语义兼容性 |
| G6 | SHACL 图约束 |
| G7 | JSON-LD / RDF 图同构 |
| G8 | SQLite、Owner 隔离、SPARQL、投影重建回归 |

SHACL 约束包括 Owner 唯一性、敏感度和访问范围、事件类型、Assertion 认知状态、证据来源、个人上下文主体、设备采集授权引用、Agent Action Proposal 审批语义、跨 Owner 关系以及 QualifiedRelationship 谓词白名单。

注意：SHACL 只能检查授权引用是否存在，不能证明授权真实有效。实际授权必须由可信 Consent / Policy Service 执行。

## 本地验证结果

- 自动化测试：27 项，26 通过、1 项因本地未安装 pySHACL 而跳过；
- Runtime 术语覆盖：98/98；
- 旧版 OWL 类/属性桥接：71/71；
- 旧版 SKOS 概念桥接：34/34；
- 破坏性语义变化：0；
- 约束放宽待审查：14；
- Ontology Manifest：8/8 文件 SHA-256 通过；
- 示例数据：29 条、3 个 Owner，严格引用和授权门禁通过。

本地环境无法联网安装 pySHACL，因此**没有宣称 SHACL 运行时已通过**。完整交付包中的 GitHub Actions 工作流会安装 pySHACL 并执行真实校验；应以成功的 Actions Run 为准。

## 运行命令

```bash
python -m pip install -r requirements-dev.txt
python prototype/pdks_ontology_cli.py ontology-check
python prototype/pdks_ontology_cli.py validate \
  --records-dir skills/pdks-personal-knowledge/examples/scenarios \
  --strict-refs --shacl \
  --trusted-consent-ref urn:pdks:consent:example:daily-work \
  --trusted-consent-ref urn:pdks:consent:example:research \
  --trusted-consent-ref urn:pdks:consent:example:voice-meeting
python -m unittest discover -s tests -v
```

示例 Consent Reference 是合成测试值，只用于示例；真实导入必须使用可信授权服务返回的 active reference。

## 下一阶段

0.4.2 建立 Ontology Decision Record、逐项审查 14 个语义放宽、自动生成版本差异报告和术语生命周期；0.5 再接入用户主动导出的钉钉、语音转写和文档，形成真实数据闭环。
