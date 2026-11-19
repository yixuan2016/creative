# V0.5 PALOS / DWS / Agent 集成边界

## PALOS
V0.5 Personal Runtime 是 Event Intelligence Lab 的本地实验服务，不是 PALOS Memory API 的替代品。尚未取得真实 PALOS Schema、Migration、Repository / Service 契约和 Memory Revocation API，因此不声明 PALOS 物理 Schema 兼容、不写入 PALOS 生产数据库、不做双向同步，也不把 EIL 本地 Memory 表定义为 PALOS 最终标准。

生产接入优先使用 PALOS Repository / Service API。需要确认个人主体 ID、Workspace/Tenant 边界、Memory / Intent / State 主键、版本、有效时间、审计、撤回和删除协议。

## DingTalk DWS CLI
仍保持 disabled / blocked。启用前需要用户实际安装的官方 CLI 名称、来源、版本、平台、完整帮助输出、只读命令帮助和脱敏 JSON 样例。不得猜测命令、参数或返回结构。

## Agent 平台
V0.5 提供本地 HTTP Pull API 和 Python 示例客户端，不包含 Codex、WorkBuddy、钉钉 Agent 等外部平台 SDK。Agent 只能读取订阅授权范围内的已确认记忆、用户激活意图和受限状态投影。不能写 Memory、修改 Intent、执行任务或调用其他 Agent。

## 外部记忆撤回
本地撤权可以阻止后续 API 读取、撤销 Token 和隐藏失效对象，但不能擦除 Agent 已经复制到其外部向量库、文件或模型上下文缓存的数据。生产化前必须设计稳定引用、消费回执、撤回通知、删除/失效确认回执、失败重试和审计。

## 个人—企业投影
V0.5 不提供个人 Memory / Intent 自动进入企业域的功能。即使个人意图关联企业项目，也必须独立确认业务用途、主体授权、最小必要字段、企业权威来源和撤回机制。共享本体不等于共享数据权限。
