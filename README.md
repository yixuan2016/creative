# PDKS 0.4.3 — 过渡阶段 Skill 工程版

> **当前研发定位：过渡阶段 Agent Skill 开发与验证。** 不是最终版个人数智底座，也不是生产级平台。

- Runtime track: 0.4.3
- Agent Skill: 0.3.3 (Experimental / Preview)
- PDKS Standard: 0.1.0 (frozen)
- JSON Record Schema: 0.1.x (frozen)
- Ontology: 0.2.1 (frozen)
- Event Taxonomy: 0.1.0 (frozen)

## 本轮目标

建立跨宿主 Agent Skill 可用性与真实工作流验证体系：12 个合成场景、统一输出契约、结构性评估器、人工评分标准、宿主运行矩阵和 CI。

**测试协议已准备，真实跨 Agent 实测尚未执行。** 需要至少两个真实宿主各执行 12 案例 × 3 次（至少 72 次运行），并完成人工复核，才能声称跨宿主验证通过。

## 重点文档

- [阶段定位](STAGE.md)
- [演进路线](ROADMAP.md)
- [0.4.3 跨 Agent 验证设计](docs/16-PDKS_0.4.3_跨Agent_Skill可用性与工作流验证.md)
- [测试协议](benchmarks/CROSS_AGENT_TEST_PROTOCOL.md)
- [评分标准](benchmarks/EVALUATION_RUBRIC.md)
- [输出契约](benchmarks/OUTPUT_CONTRACT.md)
- [本地验证报告](reports/CROSS_AGENT_VALIDATION_STATUS_0.4.3.md)

## 能力边界

后台持续采集、原生钉钉连接器、录音设备集成、生产级授权服务、密钥管理、云端长期记忆和多端同步均未在本版本实现。SQLite / RDF 仍为本地参考原型。
