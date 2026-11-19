# Agent Event Runtime 契约 V0.1

## 1. 目标

为多个个人 Agent 提供统一、最小化、可撤销的事件订阅机制。Agent 通过 Pull 获取已确认事件；本服务不调用 Agent，也不执行外部动作。

## 2. 订阅授权

每条订阅绑定 workspace_id、agent_id、purpose_scopes、可选 event_types、max_sensitivity 和 expires_at。用途沿用个人用途白名单：personal_knowledge、personal_assistant、project_context、task_support、personal_search。

## 3. Token

创建订阅时生成一次性 URL-safe Token，只在创建响应返回。服务端仅存 SHA-256 摘要。Agent 请求通过 X-Agent-Token Header 认证。撤销时清空 Token 摘要。该凭据是本地原型机制，不替代 OAuth 或企业 IAM。

## 4. 事件可见性

仅允许 owner_scope=personal、epistemic_status=confirmed、verification_status 为 human_reviewed/source_verified 的事件；用途必须相交，敏感级别不得超过订阅上限，事件类型必须命中订阅过滤。每次 Inbox / Context 读取重新检查。

## 5. Delivery 生命周期

pending → acked；订阅撤销、来源删除或事件授权变化时转为 revoked。以 subscription_id + event_id 唯一约束实现幂等；Ack 可重复调用。

## 6. 数据最小化

Inbox 返回 delivery_id、event_id、类型、标题、发生时间、认识状态、置信度和敏感级别。Context Endpoint 可额外返回事件描述，但不返回来源正文、原始证据、文件路径或其他 Agent 的订阅信息。

## 7. API

- POST /v1/agents/subscriptions
- GET /v1/agents/subscriptions
- POST /v1/agents/dispatch
- GET /v1/agents/subscriptions/{id}/inbox
- GET /v1/agents/subscriptions/{id}/events/{event_id}
- POST /v1/agents/subscriptions/{id}/deliveries/{delivery_id}/ack
- POST /v1/agents/subscriptions/{id}/revoke

## 8. 撤权边界

Token 立即失效，Pending Delivery 撤销。Source Purge 会使相关 Pending/Acked Delivery 标记 revoked。已经被 Agent 拉取并复制到外部记忆的数据，无法由本地运行时自动擦除；后续需要 PALOS Memory Revocation Hook 和删除回执。

Agent 不得创建或确认 Event，不得修改 Assertion/Source，不得调用其他 Agent，不得触发消息、日历或任务等外部副作用。