# Connector Worker 运行与调度机制 V0.3.2

## 1. 进程模型

API Server 与 Connector Worker 分开运行：

```bash
# 终端 A
python -m event_intelligence_lab

# 终端 B
python -m event_intelligence_lab.worker --poll-seconds 5
```

API Server 不在启动时隐式启动调度线程，避免多 Uvicorn Worker 重复调度。

## 2. Schedule 数据

每个 Connector Instance 最多一条 Schedule，记录：

- enabled；
- interval_seconds；
- max_items；
- next_run_at；
- last_run_at / last_status；
- consecutive_failures；
- lease_owner / lease_until。

自动同步最小间隔 300 秒，最大 86400 秒；每批最多 100 条。

## 3. 双层租约

### Schedule Lease

Worker 在 `BEGIN IMMEDIATE` 事务中领取最早到期且未被租约占用的 Schedule。事务确保多个 Worker 不会同时领取同一条 Schedule。

### Sync Lease

每个连接器有独立 Sync Lease，防止手动同步和 Worker 同步并发执行。租约当前为 15 分钟；长任务心跳续租尚未实现，因此只对当前本地文件连接器开放自动调度。

## 4. 交付与重试语义

系统采用 **at-least-once + idempotent ingestion**，不承诺 exactly-once。

- Source 幂等键防止重放产生重复来源；
- 每个成功处理的 ConnectorItem 后推进 checkpoint；
- 进程崩溃后租约过期可重新领取；
- 失败按 interval × 2^failure_count 退避，上限 24 小时；
- partial 分页约 30 秒后继续；
- 若手动同步占有 Sync Lease，Worker 将本次任务视为 busy 并短间隔延期，而不是记为失败。

## 5. 暂停、恢复与撤权

- Pause Instance：停止未来同步并禁用 Schedule；
- Resume Instance：恢复实例状态，但不自动恢复 Schedule；
- Pause Schedule：仅暂停计划，不撤回数据授权；
- Revoke：撤回 Grant、禁用 Schedule、阻止未来读取；
- 已经开始的同步任务不会被强制中断，当前版本没有中途取消令牌；
- 历史原始文件、Evidence、FTS、RDF、缓存和备份的清理尚未自动化。

## 6. 运维 API

- `POST /v1/connectors/instances/{id}/schedule`
- `GET /v1/connectors/schedules`
- `POST /v1/connectors/instances/{id}/schedule/pause`
- `POST /v1/connectors/instances/{id}/pause`
- `POST /v1/connectors/instances/{id}/resume`

每次执行仍重新验证有效 Grant、用途、敏感级别和模型处理权限。

## 7. 扩展前提

若要支持长时运行的钉钉、邮件、日历等远程连接器，必须先增加：

- Lease Heartbeat / renewal；
- connector-level rate limit；
- retry-after 与 provider quota；
- cancellation token；
- cursor versioning；
- dead-letter / quarantine；
- secret store；
- source deletion and derived-data purge workflow；
- worker health / readiness / liveness；
- 多机队列或可靠的分布式锁。

当前 SQLite Worker 只适合单机个人原型，不可直接横向扩展为多机集群。
