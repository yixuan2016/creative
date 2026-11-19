(function (root) {
  "use strict";

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function findById(items, key, id) {
    const item = items.find((entry) => entry[key] === id);
    if (!item) throw new Error("未找到对象：" + id);
    return item;
  }

  function confirmMemory(memories, memoryId, timestamp) {
    const memory = findById(memories, "memory_id", memoryId);
    if (["withdrawn", "superseded", "stale"].includes(memory.status)) {
      throw new Error("当前记忆状态不允许直接确认。");
    }
    memory.status = "confirmed";
    memory.updated_at = timestamp || new Date().toISOString();
    return clone(memory);
  }

  function correctMemory(memories, memoryId, statement, timestamp) {
    if (!statement || !statement.trim()) throw new Error("纠正内容不能为空。");
    const old = findById(memories, "memory_id", memoryId);
    if (old.status === "withdrawn") throw new Error("已撤回的记忆不能被静默恢复。");
    const now = timestamp || new Date().toISOString();
    old.status = "superseded";
    old.updated_at = now;
    const replacement = {
      ...clone(old),
      memory_id: memoryId + "-corrected",
      statement: statement.trim(),
      status: "confirmed",
      confidence: 1,
      updated_at: now,
      rationale: "由用户主动纠正；原记忆保留为历史，不再作为当前事实使用。",
      supersedes: memoryId
    };
    memories.push(replacement);
    return clone(replacement);
  }

  function withdrawMemory(memories, memoryId, timestamp) {
    const memory = findById(memories, "memory_id", memoryId);
    memory.status = "withdrawn";
    memory.updated_at = timestamp || new Date().toISOString();
    return clone(memory);
  }

  function captureToEvent(item, options) {
    if (!item || !item.content || !item.content.trim()) {
      throw new Error("记录内容不能为空。");
    }
    const opts = options || {};
    const now = opts.timestamp || new Date().toISOString();
    const date = opts.date || now.slice(0, 10);
    return {
      event_id: opts.eventId || "evt-session-" + Date.now(),
      occurred_at: date + "T" + now.slice(11, 19) + "+08:00",
      category: opts.category || "work",
      title: item.title || item.content.trim().slice(0, 28),
      summary: item.content.trim(),
      source_id: item.source_id || "src-voice",
      assertion_status: "observed",
      confidence: 0.9,
      tags: ["快速记录", "待复核"],
      project: "个人记录",
      day_index: 30,
      session_created: true
    };
  }

  function confirmIntent(intents, intentId, ownerConfirmed, timestamp) {
    const intent = findById(intents, "intent_id", intentId);
    if (intent.confirmation_status !== "inferred_candidate" && intent.status !== "proposed") {
      throw new Error("该事项不是待确认候选。");
    }
    if (ownerConfirmed) {
      intent.status = "active";
      intent.confirmation_status = "user_confirmed";
      intent.owner = "本人";
    } else {
      intent.status = "cancelled";
      intent.confirmation_status = "unknown";
      intent.owner = "非本人 / 已排除";
    }
    intent.updated_at = timestamp || new Date().toISOString();
    return clone(intent);
  }

  function approveAction(actions, actionId, approved, timestamp) {
    const action = findById(actions, "action_id", actionId);
    if (["L2", "L3"].includes(action.risk_tier) && !action.approval_required) {
      throw new Error("L2/L3 动作必须要求明确审批。");
    }
    if (!action.approval_required) {
      throw new Error("该动作不需要审批；请查看草稿，不应伪造审批。");
    }
    if (action.approval_status !== "pending") {
      throw new Error("该动作已处理或审批已失效。");
    }
    action.approval_status = approved ? "approved" : "rejected";
    action.approved_at = timestamp || new Date().toISOString();
    // This local prototype never performs an external write or communication.
    action.execution_status = "not_started";
    action.execution_note = approved
      ? "演示审批已记录；没有连接外部系统，也没有执行真实写入。"
      : "用户拒绝了该动作；没有产生外部副作用。";
    return clone(action);
  }

  function changeSourceState(sources, sourceId, operation) {
    const source = findById(sources, "source_id", sourceId);
    if (operation === "pause") {
      if (source.status === "revoked") throw new Error("已撤销的来源不能暂停或恢复。");
      source.status = "paused";
    } else if (operation === "resume") {
      if (source.status === "revoked") throw new Error("已撤销的授权不能直接恢复，需要重新授权。");
      source.status = "connected";
    } else if (operation === "revoke") {
      source.status = "revoked";
      source.permission = "revoked";
    } else {
      throw new Error("未知的来源操作。");
    }
    return clone(source);
  }

  const api = {
    clone,
    confirmMemory,
    correctMemory,
    withdrawMemory,
    captureToEvent,
    confirmIntent,
    approveAction,
    changeSourceState
  };

  root.ADSCore = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
