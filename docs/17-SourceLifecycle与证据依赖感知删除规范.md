# Source Lifecycle 与 Evidence-aware Purge 规范 V0.1

## 1. 目标

把授权撤回、来源删除、证据清理、事件保留、派生状态失效和 Agent 上下文撤销纳入统一生命周期。

## 2. 核心原则

1. Source 是采集来源记录；Evidence 是可定位证据；Event 是被证据支持的现实事件表达，三者不能混为一谈。
2. 删除一个 Source 不意味着必须删除所有相关 Event。
3. Event 仍有其他 Source / Evidence 支持时，应保留 Event。
4. 不再有其他来源支持的 Event，应连同断言、参与人、关系、检索索引和投影删除。
5. 任何受影响的 State Snapshot 必须失效；任何包含受影响 Event 的 Context Bundle 必须撤销。
6. 共享内容寻址文件在仍被其他 Source 引用时不得删除。
7. 删除必须可预览、显式确认、审计，且不可逆。

## 3. API 契约

### Preview

`GET /v1/sources/{source_id}/deletion-preview`

返回来源 ID、来源类型、连接器、受影响证据/事件数量、跨来源保留数量、专属事件删除数量、共享 Blob 标记。不得返回来源正文或绝对路径。

### Purge

`POST /v1/sources/{source_id}/purge`

请求：

```json
{
  "confirm": true,
  "actor_id": "local-user",
  "reason": "用户请求删除该来源"
}
```

缺少 confirm=true 或删除原因不合法时拒绝执行。

## 4. 依赖处理顺序

1. 识别 Source、Evidence、Event 依赖图；
2. 移除该 Source 的 Assertions 与 Participants；
3. 移除 EventEvidence 和 EventSource；
4. 判断 Event 是否仍有其他来源支持；
5. 删除无支持 Event 及其 EventRelation / Review / FTS；
6. 使 RDF 投影失效；
7. 删除引用受影响事件的 State Snapshot；
8. 撤销 Context Bundle；
9. 删除 ModelInvocation、PipelineRun、Observation、Evidence、Source；
10. 删除未被其他 Source 引用的内容寻址文件；
11. 写入最小删除回执和审计。

## 5. 当前实现边界

V0.3.3 Alpha 只覆盖 EIL 本地数据库及受控目录。远端提供方删除、备份/快照擦除、用户导出副本清理、删除任务重试队列和法律保留策略仍需独立设计。该能力不构成合规认证。
