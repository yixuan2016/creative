# ADS Capability Registry（能力资产目录）

本目录用于维护企业能力资产目录的治理约定、索引和发布说明。它不是 Prompt 文件夹，也不是未经审核的经验收集区。

## 目录原则

1. 只登记具有明确业务任务、Owner、版本和适用边界的能力资产。
2. 候选资产、沙箱资产和正式发布资产必须明确区分。
3. 每项资产必须引用机器可读 Manifest；生产调用必须锁定版本及依赖。
4. 资产的适用范围、不适用条件、证据要求和评测结果必须可见。
5. 语义检索只用于发现候选能力，实际调用必须经过适用条件和 Policy 检查。
6. 个人工作记忆、原始录音、个人 Prompt 和未经授权的客户资料不得直接登记为企业能力资产。
7. 正式资产必须有 Capability Owner、复核日期、暂停和退役机制。

## 目录结构建议

```text
capabilities/
  README.md
  <domain>/
    <capability-id>/
      manifest.json
      README.md
      versions/
      tests/
      evaluation/
      changelog.md
```

首期可先用 Git 版本化目录实现；后续根据 ADS 平台能力演进为 Registry 服务。不要为了“建设能力市场”提前引入复杂平台。

## 生命周期

- candidate：经验已抽象，尚未完成评审。
- in_review：业务、数据和治理责任方评审中。
- sandbox：仅在隔离环境或指定评测任务中测试。
- validated：通过定义好的评测门槛，但尚未必然获得广泛发布资格。
- published：在明确的团队、领域和任务范围内正式可调用。
- suspended：因质量、安全、权限或依赖问题暂停。
- deprecated：不再推荐新任务使用，保留迁移窗口。
- retired：停止调用，保留必要的审计和历史引用。
- rejected：评审未通过。

## 跨人、跨岗位复用声明

能力目录必须记录 P0—P5 验证等级及其证据范围：

| 等级 | 验证范围 |
|---|---|
| P0 | 原作者、原任务类型 |
| P1 | 同岗位、不同人员 |
| P2 | 同岗位、不同团队 |
| P3 | 相邻岗位、相同业务流程 |
| P4 | 不同岗位、相同任务家族 |
| P5 | 不同业务领域 |

不得把“已在某个团队验证”描述为“全企业通用”。样本不足时应标记为 exploratory，并明确未验证范围。

## 首批候选能力

| Capability ID | 名称 | 类型 | 当前状态 | 复用声明 |
|---|---|---|---|---|
| ads.project.risk-triage | 项目风险初筛 | Skill | candidate | 尚未验证 |
| 后续补充 | 项目状态归纳 | Skill + Template | 未创建 | 待验证 |
| 后续补充 | 任务依赖分析 | Skill + Rule | 未创建 | 待验证 |
| 后续补充 | 决策证据核验 | Skill + Evidence Standard | 未创建 | 待验证 |

## 本仓库参考文件

- [Capability Asset JSON Schema](../schemas/ads-capability-asset-v0.1.schema.json)
- [项目风险初筛能力样例](../examples/ads-capability-project-risk-triage-v0.1.json)
- [跨人跨岗位复用评估模板](../pilot/能力资产跨人跨岗位复用评估模板.csv)
- [ADS-WORK-07 研究报告](../docs/07-企业Agent能力资产化与跨业务复用机制研究.md)

## 重要说明

当前样例是研究和工程讨论用的候选资产，不代表已经通过真实业务验证、授权审批或生产发布。正式使用前必须由业务 Owner、数据治理、信息安全和知识产权责任方评审。
