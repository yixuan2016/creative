# PDKS 0.4.2 — 过渡阶段 Skill 工程版

**当前研发定位：过渡阶段的 Agent Skill 开发与验证。** 本版本不是最终版个人数智底座，不是生产级个人数据平台，也不是企业/中心 Ontology 的已实现版本。

| 项目 | 版本 | 本轮策略 |
|---|---:|---|
| Runtime 研发轨道 | 0.4.2 | 过渡阶段 Skill 工程与边界治理 |
| Agent Skill | 0.3.2 | Experimental / Preview |
| PDKS 标准 | 0.1.0 | 冻结 |
| JSON Record Schema | 0.1.x | 冻结 |
| Ontology | 0.2.1 | 冻结，不新增正式类/属性 |
| Event Taxonomy | 0.1.0 | 冻结 |

## 当前是什么

可移植的 Agent Skill、机器可读契约和本地参考原型，用于验证日常材料理解、事件抽取、知识沉淀、个人上下文、语义映射、质量校验和导出流程。

## 当前不是什么

- 不是已经完成的个人数智底座产品或企业级平台。
- 不是自动录音、后台监听或原生钉钉连接器。
- 不是云端长期记忆或多端同步服务。
- 不是生产级身份、授权、密钥管理或加密系统。
- 不是个人数据自动流向企业/中心的数据共享系统。

能力状态必须区分：available_in_skill、prototype_local、prototype_partial、host_dependent、not_implemented、future_research。

## 快速验证

运行阶段配置校验脚本：python skill-development/0.3.2-transition/scripts/validate_skill_stage.py --json

运行阶段契约测试：python -m unittest discover -s tests -p test_transition_stage_contract.py -v

SHACL 依赖不可用时必须报告 unavailable / skipped，不能记为通过。请勿将真实个人录音、敏感原始文件或生产数据库提交到公开仓库。
