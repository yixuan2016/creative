# V0.5 Memory / Intent / Reflection API 示例

Base URL: http://127.0.0.1:8765。若配置 EIL_API_TOKEN，本地管理 API 还需 Authorization: Bearer。

## 手动创建记忆

POST /v1/memories

```json
{
  "workspace_id": "ws-lab",
  "memory_type": "preference",
  "title": "沟通偏好",
  "content": "偏好先给结论，再展开依据，并标注不确定性。",
  "sensitivity": "P1",
  "purpose_scopes": ["personal_assistant", "personal_knowledge"],
  "created_by": "local-user"
}
```

用户手动表达的内容直接作为用户主张记录；由 Reflection 从事件中提炼的内容必须经过人工确认。

## 预览与运行 Reflection

POST /v1/reflections/preview 只读预览。  
POST /v1/reflections/run 物化候选。

只扫描 personal 域、已确认、验证通过、P0/P1 事件。Memory 候选默认 proposed / inferred；Commitment Intent 默认 proposed / review_required。

## 确认 Memory

POST /v1/memories/{memory_id}/review

```json
{"action":"confirm","actor_id":"local-user","reason":"核对来源后确认内容准确"}
```

如果反思记忆失去有效证据支持，则不能直接确认。

## 创建并激活 Intent

POST /v1/intents 创建 proposed Intent。  
POST /v1/intents/{intent_id}/transition 显式激活：

```json
{"action":"activate","actor_id":"local-user","reason":"用户确认开始推进"}
```

## 编译个人状态

POST /v1/personal-state/compile?workspace_id=ws-lab  
GET /v1/personal-state/latest?workspace_id=ws-lab

快照包含 as_of、支持事件引用、记忆引用、意图引用和投影器版本。

## Agent 只读上下文

```bash
curl http://127.0.0.1:8765/v1/agents/subscriptions/<id>/memories -H 'X-Agent-Token: <token>'
curl http://127.0.0.1:8765/v1/agents/subscriptions/<id>/intents -H 'X-Agent-Token: <token>'
curl http://127.0.0.1:8765/v1/agents/subscriptions/<id>/state -H 'X-Agent-Token: <token>'
```

Agent 无权确认 Memory、激活 Intent 或执行外部动作。
