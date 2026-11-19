"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("./core.js");

function fixture() {
  return {
    memories: [
      { memory_id: "m1", type: "preference", statement: "旧偏好", status: "candidate", confidence: 0.7, source_event_refs: ["e1"], updated_at: "2026-11-01T00:00:00+08:00", scope: "personal_only", rationale: "推断" }
    ],
    intents: [
      { intent_id: "i1", type: "commitment", title: "整理风险清单", status: "proposed", confirmation_status: "inferred_candidate", owner: "待确认" }
    ],
    actions: [
      { action_id: "a1", risk_tier: "L2", approval_required: true, approval_status: "pending", execution_status: "not_started" },
      { action_id: "a2", risk_tier: "L3", approval_required: true, approval_status: "pending", execution_status: "not_started" }
    ],
    sources: [
      { source_id: "s1", status: "connected", permission: "read_only" }
    ]
  };
}

test("capture turns user input into a traceable observed event", () => {
  const event = core.captureToEvent({ title: "临时想法", content: "记录一条新想法", source_id: "src-voice" }, {
    eventId: "e-new", timestamp: "2026-11-19T09:00:00+08:00", date: "2026-11-19"
  });
  assert.equal(event.event_id, "e-new");
  assert.equal(event.assertion_status, "observed");
  assert.equal(event.summary, "记录一条新想法");
  assert.equal(event.source_id, "src-voice");
});

test("capture rejects empty content", () => {
  assert.throws(() => core.captureToEvent({ content: " " }), /不能为空/);
});

test("candidate memory can be confirmed by the owner", () => {
  const f = fixture();
  const result = core.confirmMemory(f.memories, "m1", "2026-11-19T09:00:00+08:00");
  assert.equal(result.status, "confirmed");
  assert.equal(f.memories[0].status, "confirmed");
});

test("memory correction preserves old version and creates a confirmed replacement", () => {
  const f = fixture();
  const replacement = core.correctMemory(f.memories, "m1", "正确的新偏好", "2026-11-19T09:00:00+08:00");
  assert.equal(f.memories[0].status, "superseded");
  assert.equal(replacement.status, "confirmed");
  assert.equal(replacement.statement, "正确的新偏好");
  assert.equal(replacement.supersedes, "m1");
});

test("withdrawn memory cannot be silently re-confirmed", () => {
  const f = fixture();
  core.withdrawMemory(f.memories, "m1", "2026-11-19T09:00:00+08:00");
  assert.throws(() => core.confirmMemory(f.memories, "m1"), /不允许直接确认/);
});

test("inferred commitment only becomes active after explicit owner confirmation", () => {
  const f = fixture();
  const result = core.confirmIntent(f.intents, "i1", true, "2026-11-19T09:00:00+08:00");
  assert.equal(result.status, "active");
  assert.equal(result.confirmation_status, "user_confirmed");
});

test("user can reject an inferred commitment without assigning it", () => {
  const f = fixture();
  const result = core.confirmIntent(f.intents, "i1", false, "2026-11-19T09:00:00+08:00");
  assert.equal(result.status, "cancelled");
  assert.equal(result.owner, "非本人 / 已排除");
});

test("L2/L3 action approval is explicit and never executes external effects", () => {
  const f = fixture();
  const result = core.approveAction(f.actions, "a2", true, "2026-11-19T09:00:00+08:00");
  assert.equal(result.approval_status, "approved");
  assert.equal(result.execution_status, "not_started");
  assert.match(result.execution_note, /没有执行真实写入/);
});

test("L2/L3 actions cannot be approved when the approval gate is disabled", () => {
  const f = fixture();
  f.actions[0].approval_required = false;
  assert.throws(() => core.approveAction(f.actions, "a1", true), /必须要求明确审批/);
});

test("revoked source cannot be resumed without a new authorization", () => {
  const f = fixture();
  core.changeSourceState(f.sources, "s1", "revoke");
  assert.throws(() => core.changeSourceState(f.sources, "s1", "resume"), /需要重新授权/);
});
