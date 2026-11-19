# PDKS 0.4.2 — 过渡阶段 Skill 工程版

> **当前研发定位：过渡阶段的 Agent Skill 开发与验证。** 本版本不是最终版个人数智底座，不是生产级个人数据平台，也不是企业/中心 Ontology 的已实现版本。

- Runtime development track: 0.4.2
- Agent Skill: 0.3.2 (Experimental / Preview)
- PDKS Standard: 0.1.0 (frozen)
- JSON Record Schema: 0.1.x (frozen)
- Ontology: 0.2.1 (frozen)
- Event Taxonomy: 0.1.0 (frozen)

## 先读这些文件

1. [STAGE.md](STAGE.md) — 当前阶段和能力边界
2. [docs/15-PDKS_0.4.2_过渡阶段Skill工程定位与演进边界.md](docs/15-PDKS_0.4.2_过渡阶段Skill工程定位与演进边界.md) — 详细研发说明
3. [ROADMAP.md](ROADMAP.md) — 从 Skill 到个人数智底座的演进路线
4. [skill-development/0.3.2-transition/README.md](skill-development/0.3.2-transition/README.md) — 本分支跟踪的阶段治理覆盖文件

## 本轮主要变化

- Skill 0.3.2 显式声明 transitional-skill-development / experimental / preview。
- 增加机器可读开发阶段与能力矩阵。
- 增加阶段声明校验脚本和回归测试。
- 将个人—企业—中心 Ontology 关系标记为 research proposal only。
- 冻结 Ontology 0.2.1，不在本轮新增正式术语。

## 重要限制

后台持续采集、原生钉钉连接器、录音设备集成、生产级授权服务、密钥管理、云端长期记忆和多端同步均未在本版本实现。SQLite / RDF 是本地参考原型。
