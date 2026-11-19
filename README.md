# PDKS 0.4.1 — Ontology-first Personal Data Runtime

**PDKS 0.4.1 = Ontology 0.2.1 + Ontology Governance CI + SHACL Runtime API + RDF Semantic Projection + Agent Skill 0.3.1**

PDKS 将 Ontology 从概念说明升级为可执行的个人数据语义契约，并通过质量门禁保证本体能够兼容演进。

## 版本关系

| 部件 | 版本 | 说明 |
|---|---|---|
| PDKS Runtime | 0.4.1 | 本体治理、SHACL API、语义差异分析 |
| PDKS Ontology | 0.2.1 | 完整历史术语桥接、增强 SHACL Shapes |
| PDKS JSON Record Schema | 0.1.x | 保持兼容，不强制改写历史记录 |
| Event Taxonomy | 0.1.0 | 独立事件分类体系 |
| PDKS Agent Skill | 0.3.1 | 增加治理与 CI 资源 |

## 本次关键增量

- **SHACL 运行时接口**：pySHACL 实际校验，不把未安装依赖时的跳过误报为通过。
- **术语覆盖**：检查 Runtime 的 98 个 PDKS 术语引用是否全部声明。
- **历史兼容**：0.1 基线的 71 个 OWL 类/属性全部显式等价桥接；34 个历史受控词汇概念建立 `skos:exactMatch`。
- **语义差异**：识别破坏性 domain/range 收紧，以及需要人工审查的约束放宽。
- **往返一致性**：JSON-LD -> RDF 采用图同构测试，而不只是三元组数量比较。
- **Ontology Manifest**：8 个核心资源文件登记 SHA-256。
- **GitHub Actions**：增加自动化质量门禁工作流。

## 目录

```text
PDKS_Ontology_First_0.4.1_完整综合版/
├── docs/
│   └── 14-PDKS_0.4.1_Ontology质量门禁与语义治理.md/.html/.docx
├── prototype/
│   ├── pdks_ontology_runtime.py
│   ├── pdks_ontology_sqlite.py
│   ├── pdks_ontology_cli.py
│   └── pdks_ontology_governance.py
├── skills/pdks-personal-knowledge/
│   ├── SKILL.md
│   ├── scripts/
│   └── assets/ontology/0.2.1/
├── tests/
└── .github/workflows/pdks-ontology-ci.yml
```

## 快速开始

```bash
python -m pip install -r requirements-dev.txt

# 检查 Ontology 术语覆盖、历史兼容和资源 Manifest
python prototype/pdks_ontology_cli.py ontology-check

# 校验示例记录（不执行 SHACL）
python prototype/pdks_ontology_cli.py validate \
  --records-dir skills/pdks-personal-knowledge/examples/scenarios \
  --strict-refs \
  --trusted-consent-ref urn:pdks:consent:example:daily-work \
  --trusted-consent-ref urn:pdks:consent:example:research \
  --trusted-consent-ref urn:pdks:consent:example:voice-meeting

# 强制执行 SHACL；未安装 pySHACL 会返回非零状态
python prototype/pdks_ontology_cli.py validate \
  --records-dir skills/pdks-personal-knowledge/examples/scenarios \
  --strict-refs --shacl \
  --trusted-consent-ref urn:pdks:consent:example:daily-work \
  --trusted-consent-ref urn:pdks:consent:example:research \
  --trusted-consent-ref urn:pdks:consent:example:voice-meeting

# 单元测试
python -m unittest discover -s tests -v

# 验证 Ontology 文件哈希
python skills/pdks-personal-knowledge/scripts/build_ontology_manifest.py --check
```

示例 Consent Reference 是合成测试值，只能用于示例；真实导入必须使用可信 Consent / Policy Service 返回的 active reference。

## 本地验证摘要

- 自动化测试：27 项，26 通过、1 项因本地环境未安装 pySHACL 而跳过。
- Ontology Governance CLI：valid。
- Runtime 术语覆盖：98/98。
- 历史 OWL 类/属性桥接：71/71。
- 历史受控词汇桥接：34/34。
- 破坏性语义变化：0；约束放宽待审查：14。
- Ontology Manifest：8/8 文件哈希通过。
- 示例数据：29 条、3 个 Owner，严格引用和授权门禁通过。
- SHACL 真实运行时结果：须以 GitHub Actions runner 安装 pySHACL 后的执行结果为准；本地网络受限，未宣称通过。

## 重要边界

仍是本地参考实现，不是生产级个人数据服务。数据库加密、密钥管理、Owner 身份认证、正式 Consent / Policy Service、真实钉钉/录音连接器、多端同步、原始文件物理删除传播尚未实现。不要将真实个人数据库、录音和敏感原始文件提交到 GitHub。