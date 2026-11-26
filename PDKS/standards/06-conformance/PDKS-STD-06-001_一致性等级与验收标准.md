# PDKS-STD-06-001：一致性等级与验收标准

| 等级 | 名称 | 要求 |
|---|---|---|
| C0 | Documented | 声明支持版本并提供文档 |
| C1 | Structural | Schema、Frontmatter、Manifest 校验 |
| C2 | Semantic | Ontology、关系、事件分类测试 |
| C3 | Operational | 幂等、断点、冲突、撤销、恢复测试 |
| C4 | Interoperable | 至少两个 Agent 和两个查看工具互操作 |
| C5 | Secure Production | 加密、权限、审计、威胁建模和真实环境验收 |

等级累进；单元测试通过不代表 C5。

## 必测场景
Schema 错误；Ontology domain/range；时间精度；来源证据追溯；重复采集和断点；Markdown 编辑冲突；Consent 缺失/过期/撤销；Agent 越权；Vault 迁移与索引重建；跨平台路径与权限。

## 发布声明
每次发布必须说明测试环境、数据类型、通过/失败/跳过数、未执行项目和限制。未完成真实环境验收的能力标记 not_verified。
