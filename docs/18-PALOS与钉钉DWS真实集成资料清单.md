# PALOS 与钉钉 DWS 真实集成资料清单

当前原型不会猜测 PALOS 物理 Schema，也不会猜测钉钉官方 DWS CLI 命令。

## A. PALOS 输入

优先提供脱敏 SQLite 数据库副本（保留 Schema，可删除业务行）；也可提供全部相关 Migration 或 Schema Inspector JSON。

建议覆盖：
- ontology_entities / entities
- ontology_relations / relations
- sources
- evidence
- observations
- life_events / event_occurrences
- assertions
- event_relations
- event_review_queue
- state_snapshots
- context_bundle_runs
- jobs / audit_events

需要同时说明 Schema 版本、主键语义、外键关系、租户/用户边界、权限模型。不要提供生产凭据、会议正文、录音或真实个人身份信息。

## B. 钉钉官方 DWS CLI 输入

请提供：
1. 官方 CLI 准确名称、来源、版本、操作系统和 CPU 架构；
2. 完整帮助输出及相关查询命令帮助（脱敏）；
3. 一份真实结构但已脱敏的 JSON 输出样例；
4. 分页字段、增量游标、时间格式和请求 ID 的说明；
5. 官方授权方式及最小只读权限；
6. CLI 可执行文件绝对路径。

不要提供 Token、Cookie、企业密钥或员工真实数据。不要为了配合原型而执行未经确认的未知命令。

## C. 集成验收

- PALOS 字段映射经责任人审核；
- 主键、关系、语义、租户和权限边界明确；
- DWS CLI 命令与输出可复现；
- 只读权限、游标恢复、幂等、限流、撤权和删除测试通过；
- 个人生活数据不自动投影到企业域。
