# PALOS / DingTalk DWS 集成边界 V0.4

## PALOS

继续复用 SQLite Read-only Adapter：结构指纹、Profile 字段映射、Schema mismatch fail-closed、只读统计预览。真实 PALOS Schema 尚未提供，因此不声明物理兼容、不生成生产 Migration、不执行双向同步。

生产集成优先通过 PALOS Repository / Service API，而不是由 EIL 直接写 PALOS 生产数据库。需要确认本体 URI/版本、主键、用户/Workspace/Tenant 边界、事件与证据关系、保留删除策略和 Agent Memory 撤权接口。

## 钉钉 DWS CLI

连接器继续 blocked。启用前必须取得官方 CLI 准确名称、来源、版本、平台、完整帮助输出、只读查询命令帮助、脱敏 JSON 样例、分页/游标/限流/请求 ID、官方授权范围和可执行文件路径。

执行时使用 argv 数组而非 shell 字符串；只允许审核过的白名单只读子命令；必须设置超时、输出大小限制、stderr 脱敏、审计和 checkpoint 测试。不得猜测命令或要求用户提交 Token/Cookie。

## 当前未完成

无真实 PALOS 连接、无真实 DWS 命令执行、无邮件/日历/录音连接器、无外部 Agent SDK、无企业域投影、无多机 Worker。