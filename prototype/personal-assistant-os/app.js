(function () {
  "use strict";
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const initial = clone(window.ADS_DEMO_DATA);
  let state = clone(initial);
  let currentView = "today";
  let timelineDay = 30;
  let timelineFilter = "all";
  let timelineQuery = "";
  let myAiTab = "memory";

  const viewMeta = {
    today: ["今日", "把今天真正值得关注的事情放在一起。"],
    inbox: ["收集箱", "先把内容交给助理，分类和整理交给系统。"],
    timeline: ["时间线", "沿着时间理解工作、生活与学习的连续变化。"],
    goals: ["目标与承诺", "不只记住发生过什么，还要持续推进重要事情。"],
    myai: ["我的 AI", "查看 AI 记住了什么、连接了什么，以及它可以做什么。"]
  };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }
  function dateLabel(value, options) {
    if (!value) return "未设置";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return esc(value);
    return new Intl.DateTimeFormat("zh-CN", options || { month: "short", day: "numeric" }).format(d);
  }
  function timeLabel(value) {
    if (!value) return "";
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? "" : new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
  }
  function statusPill(status) {
    const map = {
      confirmed: ["已确认", "good"], active: ["进行中", "good"], candidate: ["待确认", "warn"],
      inferred_candidate: ["推断候选", "warn"], proposed: ["待确认", "warn"], needs_review: ["待整理", "warn"],
      processed: ["已整理", "good"], paused: ["已暂停", "muted"], revoked: ["已撤销", "danger"],
      connected: ["已连接", "good"], available: ["可使用", "muted"], pending: ["待审批", "warn"],
      approved: ["已批准", "good"], rejected: ["已拒绝", "muted"], completed: ["已完成", "good"],
      withdrawn: ["已撤回", "muted"], superseded: ["已被修正", "muted"], blocked: ["有阻塞", "danger"],
      on: ["运行中", "good"], off: ["已关闭", "muted"]
    };
    const pair = map[status] || [status || "未知", "muted"];
    return '<span class="status ' + pair[1] + '">' + esc(pair[0]) + "</span>";
  }
  function categoryLabel(category) {
    return ({ work: "工作", life: "生活", learning: "学习", goal: "目标", task: "任务", commitment: "承诺", routine: "习惯" })[category] || category || "其他";
  }
  function sourceName(sourceId) {
    const source = state.sources.find((x) => x.source_id === sourceId);
    return source ? source.name : "手动记录";
  }
  function eventSource(event) {
    return sourceName(event.source_id);
  }
  function eventCard(event, compact) {
    return '<article class="event-card ' + (compact ? "compact" : "") + '">' +
      '<div class="event-rail ' + esc(event.category) + '"></div><div class="event-content">' +
      '<div class="event-meta"><span>' + dateLabel(event.occurred_at) + " · " + timeLabel(event.occurred_at) + '</span><span class="dot">·</span><span>' + esc(eventSource(event)) + '</span><span class="spacer"></span>' + statusPill(event.assertion_status) + '</div>' +
      '<h3>' + esc(event.title) + '</h3><p>' + esc(event.summary) + '</p><div class="event-foot"><span>' + esc(categoryLabel(event.category)) + '</span><span>可信度 ' + Math.round((event.confidence || 0) * 100) + '%</span>' + (event.project ? '<span>' + esc(event.project) + '</span>' : "") + '</div></div></article>';
  }
  function emptyState(title, text) {
    return '<div class="empty-state"><div class="empty-icon">✳</div><strong>' + esc(title) + '</strong><p>' + esc(text) + "</p></div>";
  }
  function statCard(label, value, note, icon) {
    return '<div class="stat-card"><div class="stat-icon">' + icon + '</div><div><div class="stat-label">' + esc(label) + '</div><div class="stat-value">' + esc(value) + '</div><div class="stat-note">' + esc(note) + "</div></div></div>";
  }
  function panelTitle(title, note, right) {
    return '<div class="panel-title"><div><h2>' + title + '</h2>' + (note ? '<p>' + note + '</p>' : "") + '</div>' + (right || "") + "</div>";
  }
  function renderHeader() {
    const meta = viewMeta[currentView];
    $("#view-heading").innerHTML = '<div><div class="eyebrow">PERSONAL ASSISTANT OS / DEMO</div><h1>' + meta[0] + '</h1><p>' + meta[1] + '</p></div>';
    $$(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.view === currentView);
      item.setAttribute("aria-current", item.dataset.view === currentView ? "page" : "false");
    });
    $("#today-date").textContent = "2026 年 11 月 19 日 · 星期四";
    $("#profile-name").textContent = state.profile.display_name;
    $("#avatar").textContent = state.profile.avatar_text;
    const pending = state.inbox.filter((x) => x.status === "needs_review").length +
      state.intents.filter((x) => x.confirmation_status === "inferred_candidate" && x.status === "proposed").length;
    $("#inbox-count").textContent = pending;
    $("#inbox-count").classList.toggle("hidden", pending === 0);
  }

  function renderToday() {
    const pendingConfirmations = state.intents.filter((x) => x.confirmation_status === "inferred_candidate" && x.status === "proposed");
    const nextEvent = state.events.find((x) => x.event_id === "evt-030");
    const activeGoals = state.intents.filter((x) => ["goal", "project"].includes(x.type) && x.status === "active");
    const pendingActions = state.actions.filter((x) => x.approval_status === "pending");
    const actionsToShow = state.actions.filter((x) => x.approval_status === "pending" || x.execution_status === "draft_ready");
    const upcoming = state.events.filter((x) => x.occurred_at.slice(0, 10) === "2026-11-19").slice(-2);
    return '<div class="welcome-row"><div><div class="eyebrow">THURSDAY · 19 NOVEMBER 2026</div><h2>早上好，' + esc(state.profile.display_name) + '。</h2><p>今天有几件值得关注的事。其余信息已经为你整理好，不需要逐条处理。</p></div><div class="welcome-mark">✳</div></div>' +
      '<div class="stat-grid">' +
      statCard("正在推进的目标", activeGoals.length, "有明确下一步", "◎") +
      statCard("待确认事项", pendingConfirmations.length, "不确定的内容不会自动变成承诺", "◷") +
      statCard("待审批动作", pendingActions.length, "所有高影响动作都需要你确认", "⌁") +
      statCard("30 天连续上下文", state.journey.length + " 天", "事件与记忆按来源关联", "↗") +
      '</div>' +
      '<div class="content-grid main-aside"><div class="stack">' +
      '<section class="panel">' + panelTitle("今天的重点", "基于已授权来源整理，所有内容均可查看依据。", '<span class="subtle-chip">AI 整理 · 模拟</span>') +
      '<div class="focus-card primary"><div class="focus-symbol">◷</div><div class="focus-main"><div class="focus-meta">接下来 · 10:30</div><h3>个人助理 OS 产品评审</h3><p>建议提前查看上次评审中的 MVP 边界和待确认事项。</p><div class="source-line">来源：个人日历（模拟） · 关联：' + esc(nextEvent ? nextEvent.project : "Personal OS") + '</div></div><span class="priority high">优先关注</span></div>' +
      '<div class="focus-card"><div class="focus-symbol violet">✳</div><div class="focus-main"><div class="focus-meta">待确认 · 会议承诺候选</div><h3>周五前整理项目风险清单</h3><p>会议中出现了这句话，但目前不能确认由谁负责。AI 不会擅自把它分配给你。</p><div class="source-line">来源：11 月 18 日会议记录 · 置信度 82%</div></div><span class="priority normal">需要确认</span></div>' +
      '<div class="focus-card"><div class="focus-symbol teal">✓</div><div class="focus-main"><div class="focus-meta">已完成 · 自动汇总</div><h3>原型验收清单已整理成草稿</h3><p>交互、权限、记忆纠错和 Agent 审批四个部分已归并。</p><div class="source-line">来源：个人文档空间（模拟）</div></div><span class="priority low">供查看</span></div></section>' +
      '<section class="panel">' + panelTitle("接下来", "日程只读同步；这里不会替你修改真实日历。") +
      (upcoming.length ? upcoming.map((e) => '<div class="schedule-row"><div class="schedule-time">' + timeLabel(e.occurred_at) + '</div><div class="schedule-marker"></div><div class="schedule-info"><strong>' + esc(e.title) + '</strong><span>' + esc(e.summary) + '</span></div><span class="schedule-source">' + esc(eventSource(e)) + '</span></div>').join("") : emptyState("今天没有新的安排", "如果日历来源已授权，新的安排会自动出现在这里。")) +
      '</section>' +
      '<section class="panel">' + panelTitle("AI 正在准备什么", "审批只代表你允许进入下一步；本原型不会执行真实外部操作。", '<button class="text-button" data-action="go-myai-actions">查看全部 <span>→</span></button>') +
      renderActionCards(actionsToShow.slice(0, 3)) + '</section></div>' +
      '<aside class="stack">' +
      '<section class="panel compact-panel">' + panelTitle("快速记录", "想到什么，直接交给助理。") +
      '<textarea id="quick-capture" class="quick-input" rows="3" placeholder="例如：下周要和团队确认个人知识沉淀标准……"></textarea>' +
      '<div class="quick-actions"><button class="btn btn-primary" data-action="quick-capture">✚ 记录一下</button><button class="btn btn-ghost" data-action="voice-sample">◉ 语音示例</button></div><div class="micro-note">演示模式：语音按钮填入示例转写，不会调用麦克风。</div></section>' +
      '<section class="panel compact-panel">' + panelTitle("目标进展", "保持少量重点，持续向前。") +
      activeGoals.map((g) => '<div class="goal-mini"><div class="goal-mini-head"><strong>' + esc(g.title) + '</strong><span>' + Math.round(g.progress * 100) + '%</span></div><div class="progress"><i style="width:' + Math.round(g.progress * 100) + '%"></i></div><div class="micro-note">下一步：' + esc(g.next_action) + '</div></div>').join("") +
      '<button class="btn btn-ghost btn-full" data-view="goals">查看目标与承诺 →</button></section>' +
      '<section class="panel compact-panel">' + panelTitle("30 天理解进度", "从零散记录到持续上下文。") +
      '<div class="journey-mini"><div class="journey-ring"><strong>30</strong><span>天</span></div><div><strong>已形成连续记录</strong><p>30 条示例事件 · 4 条记忆 · 4 个目标或承诺</p><button class="text-button" data-view="timeline">探索 30 天时间线 →</button></div></div></section>' +
      '<section class="panel compact-panel trust-panel">' + panelTitle("你的数据，你做主") +
      '<div class="trust-line"><span>个人上下文默认范围</span><strong>仅个人</strong></div><div class="trust-line"><span>企业自动投影</span><strong>关闭</strong></div><div class="trust-line"><span>后台持续录音</span><strong>关闭</strong></div><div class="trust-foot">所有示例均为虚构数据，本页面不连接真实账户。</div></section></aside></div>';
  }

  function renderActionCards(actions) {
    if (!actions.length) return emptyState("目前没有待审批动作", "当 AI 准备执行需要授权的操作时，会先在这里向你说明。");
    return actions.map((a) => {
      const needsApproval = a.approval_required && a.approval_status === "pending";
      return '<div class="action-card"><div class="action-card-top"><span class="risk-tag ' + a.risk_tier.toLowerCase() + '">' + a.risk_tier + " · " + (a.risk_tier === "L3" ? "高影响" : a.risk_tier === "L2" ? "可逆写入" : "草稿") + '</span>' + statusPill(a.approval_status) + '</div><h3>' + esc(a.title) + '</h3><p>' + esc(a.summary) + '</p><div class="action-target">操作对象：' + esc(a.target) + '</div><div class="button-row"><button class="btn btn-primary btn-small" data-action="' + (needsApproval ? "review-action" : "view-action") + '" data-id="' + esc(a.action_id) + '">' + (needsApproval ? "查看并审批" : "查看草稿") + '</button>' + (needsApproval ? '<button class="btn btn-ghost btn-small" data-action="reject-action" data-id="' + esc(a.action_id) + '">拒绝</button>' : "") + '</div></div>';
    }).join("");
  }

  function renderInbox() {
    const pending = state.inbox.filter((x) => x.status === "needs_review");
    const done = state.inbox.filter((x) => x.status !== "needs_review");
    return '<section class="panel inbox-compose">' + panelTitle("把内容交给助理", "你不需要先决定它属于知识、任务、事件还是记忆。") +
      '<textarea id="inbox-capture" class="compose-input" rows="3" placeholder="写下一段想法、会议结论、待办或生活记录……"></textarea>' +
      '<div class="compose-footer"><div class="micro-note">支持文字、分享内容和用户主动提交的语音转写。</div><div class="button-row"><button class="btn btn-ghost" data-action="voice-sample-inbox">◉ 语音示例</button><button class="btn btn-primary" data-action="add-inbox">加入收集箱 <span>→</span></button></div></div></section>' +
      '<div class="section-heading"><div><h2>需要理解 <span class="count-badge">' + pending.length + '</span></h2><p>系统先整理候选内容；未经确认的推断不会变成正式事实。</p></div><span class="subtle-chip">自动理解 · 模拟</span></div>' +
      (pending.length ? '<div class="inbox-list">' + pending.map((x) => '<article class="inbox-card"><div class="inbox-card-top"><span class="inbox-source">◈ ' + esc(x.source_label) + '</span><span class="inbox-time">' + dateLabel(x.received_at) + " · " + timeLabel(x.received_at) + '</span></div><h3>' + esc(x.title) + '</h3><p>' + esc(x.content) + '</p><div class="inbox-ai"><span>AI 判断：' + esc(x.suggested_type) + '</span><span>置信度 ' + Math.round(x.confidence * 100) + '%</span></div><div class="button-row"><button class="btn btn-primary btn-small" data-action="process-inbox" data-id="' + esc(x.inbox_id) + '">理解并形成事件</button><button class="btn btn-ghost btn-small" data-action="dismiss-inbox" data-id="' + esc(x.inbox_id) + '">暂不处理</button></div></article>').join("") + '</div>' : emptyState("收集箱已经清空", "新的记录、分享内容和已授权来源会出现在这里。")) +
      '<section class="panel processed-panel">' + panelTitle("最近已整理", "已形成事件的内容可以继续沉淀为记忆。") +
      (done.length ? done.map((x) => '<div class="processed-row"><div class="processed-icon">✓</div><div class="processed-main"><strong>' + esc(x.title) + '</strong><span>' + esc(x.source_label) + ' · ' + (x.status === "processed" ? "已整理" : "已忽略") + '</span></div>' + (x.status === "processed" ? '<button class="text-button" data-action="save-inbox-memory" data-id="' + esc(x.inbox_id) + '">沉淀为记忆 →</button>' : "") + '</div>').join("") : emptyState("还没有已整理内容", "完成一条记录的理解后，它会出现在这里。")) + '</section>';
  }

  function renderTimeline() {
    const day = state.journey[timelineDay - 1];
    const filtered = state.events.filter((e) => {
      const dayMatch = e.occurred_at.slice(0, 10) === day.date;
      const categoryMatch = timelineFilter === "all" || e.category === timelineFilter;
      const q = timelineQuery.trim().toLowerCase();
      const queryMatch = !q || (e.title + e.summary + e.project + e.tags.join(" ")).toLowerCase().includes(q);
      return dayMatch && categoryMatch && queryMatch;
    });
    const dots = state.journey.map((d) => '<button class="day-dot ' + (d.day_index === timelineDay ? "selected" : "") + (d.event_refs.length ? " has-event" : "") + '" data-action="select-day" data-day="' + d.day_index + '" aria-label="第 ' + d.day_index + ' 天：' + d.date + '" title="' + d.date + '">' + d.day_index + '</button>').join("");
    return '<section class="panel journey-panel">' + panelTitle("连续 30 天", "不是把信息堆在一起，而是看见事情如何逐渐形成上下文。", '<span class="subtle-chip">30 天演示旅程</span>') +
      '<div class="journey-head"><div><div class="eyebrow">DAY ' + String(timelineDay).padStart(2, "0") + " / 30</div><h2>" + esc(day.headline) + '</h2><p>' + esc(day.summary) + '</p></div><div class="journey-date">' + dateLabel(day.date, { year: "numeric", month: "long", day: "numeric" }) + '</div></div>' +
      '<div class="day-dots">' + dots + '</div><div class="range-row"><span>10 月 21 日</span><input type="range" min="1" max="30" value="' + timelineDay + '" id="journey-range" aria-label="选择 30 天中的某一天"><span>11 月 19 日</span></div>' +
      (day.milestone ? '<div class="milestone-banner">✦ 阶段节点：' + esc(day.milestone) + '</div>' : "") + '</section>' +
      '<section class="panel">' + panelTitle("当天发生的事", "每条事件都保留来源、时间和确认状态。", '<span class="subtle-chip">' + filtered.length + " 条事件</span>") +
      '<div class="timeline-tools"><div class="filter-pills"><button class="' + (timelineFilter === "all" ? "selected" : "") + '" data-filter="all">全部</button><button class="' + (timelineFilter === "work" ? "selected" : "") + '" data-filter="work">工作</button><button class="' + (timelineFilter === "life" ? "selected" : "") + '" data-filter="life">生活</button><button class="' + (timelineFilter === "learning" ? "selected" : "") + '" data-filter="learning">学习</button></div><input id="timeline-search" class="search-input" value="' + esc(timelineQuery) + '" placeholder="搜索当天内容…" aria-label="搜索时间线"></div>' +
      (filtered.length ? '<div class="event-list">' + filtered.map((e) => eventCard(e, false)).join("") + '</div>' : emptyState("这一天没有匹配的事件", "可以切换日期、清除筛选，或查看其他类型的记录。")) +
      '</section><section class="panel">' + panelTitle("30 天中的阶段变化", "从快速记录到记忆、承诺和主动服务。") +
      '<div class="milestone-list">' + state.journey.filter((x) => x.milestone).map((x) => '<button class="milestone-item" data-action="select-day" data-day="' + x.day_index + '"><span class="milestone-day">DAY ' + x.day_index + '</span><span><strong>' + esc(x.milestone) + '</strong><small>' + esc(x.summary) + '</small></span><span class="arrow">→</span></button>').join("") + '</div></section>';
  }

  function renderGoals() {
    const goals = state.intents.filter((x) => ["goal", "project"].includes(x.type));
    const tasks = state.intents.filter((x) => ["task", "routine"].includes(x.type));
    const commitments = state.intents.filter((x) => x.type === "commitment");
    return '<div class="goal-overview"><div><div class="eyebrow">PERSONAL INTENT SPACE</div><h2>重要的事情，持续向前。</h2><p>目标、任务和承诺共用同一条上下文，但确认状态彼此独立。</p></div><div class="goal-overview-stat"><strong>' + state.intents.filter((x) => x.status === "active").length + '</strong><span>项进行中</span></div></div>' +
      '<section class="panel">' + panelTitle("长期目标", "只展示少量真正重要的目标。") +
      (goals.map((g) => '<article class="goal-card"><div class="goal-card-head"><div><span class="intent-type">' + esc(categoryLabel(g.type)) + '</span><h3>' + esc(g.title) + '</h3></div>' + statusPill(g.status) + '</div><p>' + esc(g.description) + '</p><div class="goal-progress-row"><div class="progress"><i style="width:' + Math.round(g.progress * 100) + '%"></i></div><strong>' + Math.round(g.progress * 100) + '%</strong></div><div class="goal-detail-row"><span>截止：' + dateLabel(g.due_at, { month: "short", day: "numeric" }) + '</span><span>下一步：' + esc(g.next_action) + '</span></div></article>').join("") || emptyState("还没有长期目标", "当你表达想持续推进的事情时，助理会帮助建立目标候选。")) + '</section>' +
      '<section class="panel">' + panelTitle("承诺与待办", "AI 识别到的承诺先作为候选；责任人必须由你确认。") +
      commitments.concat(tasks).map((x) => '<article class="intent-row"><div class="intent-icon ' + (x.confirmation_status === "inferred_candidate" ? "warn" : "") + '">' + (x.type === "commitment" ? "↗" : x.type === "routine" ? "◷" : "✓") + '</div><div class="intent-main"><div class="intent-meta">' + esc(categoryLabel(x.type)) + ' · 截止 ' + dateLabel(x.due_at, { month: "short", day: "numeric" }) + ' · ' + statusPill(x.confirmation_status === "inferred_candidate" ? "inferred_candidate" : x.status) + '</div><h3>' + esc(x.title) + '</h3><p>' + esc(x.description) + '</p><div class="intent-next">下一步：' + esc(x.next_action) + '</div>' +
      (x.confirmation_status === "inferred_candidate" && x.status === "proposed" ? '<div class="button-row"><button class="btn btn-primary btn-small" data-action="confirm-intent" data-id="' + esc(x.intent_id) + '">是我负责</button><button class="btn btn-ghost btn-small" data-action="reject-intent" data-id="' + esc(x.intent_id) + '">不是我负责</button></div>' :
      (x.status === "active" ? '<div class="button-row"><button class="btn btn-ghost btn-small" data-action="complete-intent" data-id="' + esc(x.intent_id) + '">标记完成</button><button class="btn btn-ghost btn-small" data-action="pause-intent" data-id="' + esc(x.intent_id) + '">暂时暂停</button></div>' : "")) +
      '</div></article>').join("") + '</section>';
  }

  function renderMemoryTab() {
    const active = state.memories.filter((x) => !["withdrawn", "superseded"].includes(x.status));
    const history = state.memories.filter((x) => ["withdrawn", "superseded"].includes(x.status));
    return '<div class="memory-summary"><div><strong>' + active.length + '</strong><span>当前记忆</span></div><div><strong>' + active.filter((x) => x.status === "candidate").length + '</strong><span>等待确认</span></div><div><strong>' + history.length + '</strong><span>历史版本</span></div></div>' +
      '<div class="memory-list">' + active.map((m) => '<article class="memory-card"><div class="memory-card-head"><span class="memory-type">' + esc(categoryLabel(m.type)) + '</span>' + statusPill(m.status) + '</div><h3>' + esc(m.statement) + '</h3><p>' + esc(m.rationale) + '</p><div class="memory-source"><span>来源：' + esc(m.source_event_refs.map((id) => { const e = state.events.find((x) => x.event_id === id); return e ? e.title : id; }).join("、")) + '</span><span>置信度 ' + Math.round(m.confidence * 100) + '%</span><span>仅个人</span></div><div class="button-row">' +
      (m.status === "candidate" ? '<button class="btn btn-primary btn-small" data-action="confirm-memory" data-id="' + esc(m.memory_id) + '">确认记忆</button>' : "") +
      '<button class="btn btn-ghost btn-small" data-action="correct-memory" data-id="' + esc(m.memory_id) + '">纠正</button><button class="btn btn-ghost btn-small danger-text" data-action="withdraw-memory" data-id="' + esc(m.memory_id) + '">不再使用</button></div></article>').join("") + '</div>' +
      (history.length ? '<details class="history-details"><summary>查看已撤回或被修正的历史版本（' + history.length + '）</summary>' + history.map((m) => '<div class="history-row"><span>' + esc(m.statement) + '</span>' + statusPill(m.status) + '</div>').join("") + '</details>' : "");
  }

  function renderSourcesTab() {
    return '<div class="source-intro"><div class="source-intro-icon">◈</div><div><strong>你选择连接什么，助理才可以理解什么。</strong><p>以下全部是模拟来源。暂停会停止后续同步；撤销后不能直接恢复，必须重新授权。</p></div></div>' +
      '<div class="source-list">' + state.sources.map((s) => '<article class="source-card"><div class="source-logo">' + ({ collaboration: "钉", calendar: "日", documents: "文", voice_capture: "◉" })[s.kind] + '</div><div class="source-main"><div class="source-head"><h3>' + esc(s.name) + '</h3>' + statusPill(s.status) + '</div><p>' + esc(s.scope) + '</p><div class="source-meta">权限：' + esc(s.permission) + ' · 最近同步：' + dateLabel(s.last_sync_at) + " " + timeLabel(s.last_sync_at) + '</div><small>' + esc(s.note) + '</small></div><div class="source-actions">' +
      (s.status === "revoked" ? '<span class="micro-note">需重新授权</span>' : (s.status === "paused" ? '<button class="btn btn-ghost btn-small" data-action="resume-source" data-id="' + esc(s.source_id) + '">恢复</button>' : '<button class="btn btn-ghost btn-small" data-action="pause-source" data-id="' + esc(s.source_id) + '">暂停</button>')) +
      (s.status !== "revoked" ? '<button class="text-button danger-text" data-action="revoke-source" data-id="' + esc(s.source_id) + '">撤销授权</button>' : "") +
      '</div></article>').join("") + '</div>';
  }

  function renderPrivacyTab() {
    const p = state.policy;
    const toggle = (key, title, desc, checked, disabled) => '<div class="setting-row"><div><strong>' + title + '</strong><p>' + desc + '</p></div><button class="switch ' + (checked ? "on" : "") + '" data-action="toggle-policy" data-key="' + key + '" aria-pressed="' + checked + '" ' + (disabled ? "disabled" : "") + '><span></span></button></div>';
    return '<div class="privacy-banner"><div class="privacy-shield">◇</div><div><strong>个人上下文默认只属于你。</strong><p>企业空间不会自动获得个人工作或生活记录。任何跨边界使用都必须单独说明目的、范围和授权。</p></div></div>' +
      '<section class="settings-group"><h3>个人数据边界</h3><div class="setting-row"><div><strong>默认使用范围</strong><p>个人事件、记忆和目标默认只在个人空间中使用。</p></div><span class="fixed-value">仅个人</span></div><div class="setting-row"><div><strong>企业自动投影</strong><p>需要独立业务目的、字段范围、接收方和授权；本原型不开放投影。</p></div><span class="fixed-value off">关闭</span></div><div class="setting-row"><div><strong>后台持续录音</strong><p>没有默认持续录音；语音入口必须由用户主动启动。</p></div><span class="fixed-value off">关闭</span></div></section>' +
      '<section class="settings-group"><h3>体验与通知偏好</h3>' +
      toggle("quiet_hours_enabled", "安静时段", "在你设定的专注时间内，合并非紧急提醒。", p.quiet_hours_enabled, false) +
      toggle("sensitive_content_hidden", "通知隐藏敏感内容", "锁屏或通知预览不直接展示私人内容。", p.sensitive_content_hidden, false) +
      '</section><div class="policy-note">数据保留周期由来源类型、用户选择、产品策略和适用规则分别确定。本演示没有真实采集、存储或删除你的个人数据。</div>';
  }

  function renderAutomationTab() {
    return '<div class="automation-intro"><strong>自动化应该减少重复劳动，而不是制造新的管理工作。</strong><p>每条自动化都可以暂停或关闭。触发条件、运行时间和通知方式应当清楚可见。</p></div>' +
      state.automations.map((a) => '<article class="automation-card"><div class="automation-icon">↻</div><div class="automation-main"><div class="automation-head"><h3>' + esc(a.title) + '</h3>' + statusPill(a.status) + '</div><p>' + esc(a.description) + '</p><div class="automation-meta">' + esc(a.cadence) + ' · 下一次：' + dateLabel(a.next_run) + ' ' + timeLabel(a.next_run) + ' · ' + (a.notification_mode === "digest" ? "摘要" : "应用内提醒") + '</div></div><button class="switch ' + (a.status === "on" ? "on" : "") + '" data-action="toggle-automation" data-id="' + esc(a.automation_id) + '" aria-pressed="' + (a.status === "on") + '"><span></span></button></article>').join("");
  }

  function renderMyAI() {
    const tabs = [["memory","AI 记住的"],["sources","数据来源"],["privacy","权限与隐私"],["automation","自动化"]];
    let content = myAiTab === "memory" ? renderMemoryTab() : myAiTab === "sources" ? renderSourcesTab() : myAiTab === "privacy" ? renderPrivacyTab() : renderAutomationTab();
    return '<section class="panel myai-panel">' + panelTitle("我的 AI", "不是让你每天维护记忆，而是让你随时知道 AI 了解什么、能做什么。") +
      '<div class="myai-tabs" role="tablist">' + tabs.map(([id,label]) => '<button role="tab" aria-selected="' + (myAiTab === id) + '" class="' + (myAiTab === id ? "selected" : "") + '" data-tab="' + id + '">' + label + '</button>').join("") + '</div><div class="myai-content">' + content + '</div></section>';
  }

  function render() {
    renderHeader();
    const root = $("#view-root");
    root.innerHTML = currentView === "today" ? renderToday() :
      currentView === "inbox" ? renderInbox() :
      currentView === "timeline" ? renderTimeline() :
      currentView === "goals" ? renderGoals() : renderMyAI();
    $("#view-root").focus({ preventScroll: true });
  }

  function showToast(message, kind) {
    const toast = $("#toast");
    toast.className = "toast show " + (kind || "");
    toast.textContent = message;
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => { toast.className = "toast"; }, 2600);
  }
  function openModal(title, body, footer) {
    $("#modal-title").textContent = title;
    $("#modal-body").innerHTML = body;
    $("#modal-footer").innerHTML = footer || '<button class="btn btn-ghost" data-action="close-modal">关闭</button>';
    $("#modal-backdrop").classList.add("open");
    $("#modal").setAttribute("aria-hidden", "false");
    const first = $("#modal-footer button") || $("#modal-body button");
    if (first) first.focus();
  }
  function closeModal() {
    $("#modal-backdrop").classList.remove("open");
    $("#modal").setAttribute("aria-hidden", "true");
  }

  function addInbox(content, sourceId, sourceLabel) {
    const text = (content || "").trim();
    if (!text) { showToast("先写下一点内容，再交给助理。", "warn"); return; }
    state.inbox.unshift({
      inbox_id: "inbox-session-" + Date.now(),
      source_id: sourceId || "src-voice",
      source_label: sourceLabel || "快速记录（本地演示）",
      received_at: "2026-11-19T09:00:00+08:00",
      type: "quick_note",
      title: text.length > 28 ? text.slice(0, 28) + "…" : text,
      content: text,
      status: "needs_review",
      suggested_type: /提醒|截止|负责|完成|任务/.test(text) ? "task_or_commitment_candidate" : "personal_note",
      confidence: 0.88,
      source_event_refs: []
    });
    showToast("已加入收集箱。接下来由你决定是否形成事件。", "success");
    currentView = "inbox";
    render();
  }

  function processInbox(id) {
    const item = state.inbox.find((x) => x.inbox_id === id);
    if (!item || item.status !== "needs_review") return;
    const event = window.ADSCore.captureToEvent(item, {
      eventId: "evt-session-" + Date.now(),
      timestamp: "2026-11-19T09:00:00+08:00",
      date: "2026-11-19",
      sourceId: item.source_id
    });
    state.events.push(event);
    item.status = "processed";
    item.source_event_refs = [event.event_id];
    item.created_event_ref = event.event_id;
    showToast("已形成事件，来源和原始内容仍然保留。", "success");
    render();
  }

  function saveInboxMemory(id) {
    const item = state.inbox.find((x) => x.inbox_id === id);
    if (!item || !item.source_event_refs || !item.source_event_refs.length) {
      showToast("请先理解内容并形成事件。", "warn"); return;
    }
    const memoryId = "mem-session-" + Date.now();
    state.memories.unshift({
      memory_id: memoryId,
      type: item.suggested_type === "preference" ? "preference" : "episodic",
      statement: item.content,
      status: "candidate",
      confidence: item.confidence,
      source_event_refs: item.source_event_refs,
      updated_at: "2026-11-19T09:00:00+08:00",
      scope: "personal_only",
      rationale: "由用户提交的内容形成候选记忆；确认前不会作为稳定个人事实使用。"
    });
    myAiTab = "memory";
    currentView = "myai";
    showToast("已加入记忆候选，请在「我的 AI」中确认。", "success");
    render();
  }

  function showActionReview(id, mode) {
    const action = state.actions.find((x) => x.action_id === id);
    if (!action) return;
    const approval = mode === "approve";
    openModal(approval ? "确认这项操作？" : "查看操作详情",
      '<div class="modal-risk"><span class="risk-tag ' + action.risk_tier.toLowerCase() + '">' + action.risk_tier + " · " + esc(action.action_class) + '</span><span class="modal-target">操作对象：' + esc(action.target) + '</span></div>' +
      '<h3>' + esc(action.title) + '</h3><p>' + esc(action.summary) + '</p><div class="preview-box"><div class="eyebrow">CONTENT PREVIEW</div><pre>' + esc(action.content_preview) + '</pre></div><div class="side-effect-box"><strong>可能产生的影响</strong><ul>' + action.side_effects.map((x) => "<li>" + esc(x) + "</li>").join("") + '</ul><strong>撤销说明</strong><p>' + esc(action.rollback) + '</p></div><div class="approval-check">✓ 已展示操作对象、内容预览、风险等级和可能的副作用。</div>' +
      '<p class="micro-note">演示环境只记录你的审批选择，不会连接外部系统，也不会发送消息或创建真实任务。</p>',
      approval ? '<button class="btn btn-ghost" data-action="close-modal">先不操作</button><button class="btn btn-primary" data-action="confirm-action-approval" data-id="' + esc(id) + '">我已了解，确认审批</button>' : '<button class="btn btn-ghost" data-action="close-modal">关闭</button>');
  }

  function handleClick(event) {
    const view = event.target.closest("[data-view]");
    if (view) { currentView = view.dataset.view; render(); return; }
    const nav = event.target.closest("[data-nav-view]");
    if (nav) { currentView = nav.dataset.navView; render(); return; }
    const tab = event.target.closest("[data-tab]");
    if (tab) { myAiTab = tab.dataset.tab; render(); return; }
    const filter = event.target.closest("[data-filter]");
    if (filter) { timelineFilter = filter.dataset.filter; render(); return; }
    const actionEl = event.target.closest("[data-action]");
    if (!actionEl) return;
    const action = actionEl.dataset.action;
    const id = actionEl.dataset.id;

    if (action === "close-modal") { closeModal(); return; }
    if (action === "quick-capture") { addInbox($("#quick-capture").value); return; }
    if (action === "voice-sample" || action === "voice-sample-inbox") {
      const sample = "一个产品原则：不要让用户成为 AI 的数据管理员。日常整理由系统自动完成，用户只处理关键确认和纠错。";
      if (action === "voice-sample") { addInbox(sample, "src-voice", "语音快速记录（模拟）"); }
      else { $("#inbox-capture").value = sample; showToast("已填入一段模拟语音转写，可检查后提交。"); }
      return;
    }
    if (action === "add-inbox") { addInbox($("#inbox-capture").value); return; }
    if (action === "process-inbox") { processInbox(id); return; }
    if (action === "dismiss-inbox") {
      const item = state.inbox.find((x) => x.inbox_id === id);
      if (item) item.status = "dismissed";
      showToast("已暂不处理；内容仍保留在本次演示会话中。");
      render(); return;
    }
    if (action === "save-inbox-memory") { saveInboxMemory(id); return; }
    if (action === "select-day") { timelineDay = Number(actionEl.dataset.day); render(); return; }
    if (action === "go-myai-actions") { currentView = "myai"; myAiTab = "automation"; render(); return; }
    if (action === "confirm-memory") {
      window.ADSCore.confirmMemory(state.memories, id, "2026-11-19T09:00:00+08:00");
      showToast("记忆已确认；后续建议可以使用这条已确认信息。", "success"); render(); return;
    }
    if (action === "correct-memory") {
      const memory = state.memories.find((x) => x.memory_id === id);
      openModal("纠正 AI 的记忆", '<p>当前记忆</p><div class="preview-box">' + esc(memory.statement) + '</div><label class="field-label" for="memory-correction">正确内容</label><textarea id="memory-correction" class="modal-textarea" rows="4">' + esc(memory.statement) + '</textarea><p class="micro-note">纠正会保留旧版本的历史记录，并创建一条新的已确认记忆。</p>',
        '<button class="btn btn-ghost" data-action="close-modal">取消</button><button class="btn btn-primary" data-action="save-memory-correction" data-id="' + esc(id) + '">保存纠正</button>'); return;
    }
    if (action === "save-memory-correction") {
      try {
        window.ADSCore.correctMemory(state.memories, id, $("#memory-correction").value, "2026-11-19T09:00:00+08:00");
        closeModal(); showToast("已更新记忆；旧版本保留为历史。", "success"); render();
      } catch (err) { showToast(err.message, "warn"); }
      return;
    }
    if (action === "withdraw-memory") {
      const m = state.memories.find((x) => x.memory_id === id);
      openModal("不再使用这条记忆？", '<p>这条记忆将从当前有效记忆中撤回，不再作为后续建议的依据。</p><div class="preview-box">' + esc(m.statement) + '</div><p class="micro-note">这是演示状态变更，不代表真实数据删除服务。</p>',
        '<button class="btn btn-ghost" data-action="close-modal">取消</button><button class="btn btn-danger" data-action="confirm-withdraw-memory" data-id="' + esc(id) + '">确认撤回</button>'); return;
    }
    if (action === "confirm-withdraw-memory") {
      window.ADSCore.withdrawMemory(state.memories, id, "2026-11-19T09:00:00+08:00");
      closeModal(); showToast("这条记忆已从当前有效记忆中撤回。", "success"); render(); return;
    }
    if (action === "confirm-intent" || action === "reject-intent") {
      window.ADSCore.confirmIntent(state.intents, id, action === "confirm-intent", "2026-11-19T09:00:00+08:00");
      showToast(action === "confirm-intent" ? "已确认由你负责，事项现在进入正式承诺。" : "已排除该责任，不会再以你的承诺提醒。", "success");
      render(); return;
    }
    if (action === "complete-intent" || action === "pause-intent") {
      const intent = state.intents.find((x) => x.intent_id === id);
      if (intent) intent.status = action === "complete-intent" ? "completed" : "paused";
      showToast(action === "complete-intent" ? "已标记完成。" : "已暂停，不再作为当前优先事项。", "success"); render(); return;
    }
    if (action === "review-action") { showActionReview(id, "approve"); return; }
    if (action === "view-action") { showActionReview(id, "details"); return;
    if (action === "reject-action") { showActionReview(id, "details"); openModal("拒绝这项操作？", $("#modal-body").innerHTML + '<p class="micro-note">拒绝后该动作不会执行。</p>', '<button class="btn btn-ghost" data-action="close-modal">返回</button><button class="btn btn-danger" data-action="confirm-action-rejection" data-id="' + esc(id) + '">确认拒绝</button>'); return; }
    if (action === "confirm-action-approval" || action === "confirm-action-rejection") {
      try {
        window.ADSCore.approveAction(state.actions, id, action === "confirm-action-approval", "2026-11-19T09:00:00+08:00");
        closeModal();
        showToast(action === "confirm-action-approval" ? "审批已记录；演示环境没有执行外部操作。" : "已拒绝；没有产生外部副作用。", "success");
        render();
      } catch (err) { showToast(err.message, "warn"); }
      return;
    }
    if (action === "pause-source" || action === "resume-source" || action === "revoke-source") {
      const operation = action.replace("-source", "");
      if (operation === "revoke") {
        const source = state.sources.find((x) => x.source_id === id);
        openModal("撤销这个数据来源？", '<p>撤销后将停止后续同步。重新连接必须重新授权。</p><div class="preview-box"><strong>' + esc(source.name) + '</strong><br>' + esc(source.scope) + '</div>',
          '<button class="btn btn-ghost" data-action="close-modal">取消</button><button class="btn btn-danger" data-action="confirm-revoke-source" data-id="' + esc(id) + '">确认撤销</button>');
      } else {
        window.ADSCore.changeSourceState(state.sources, id, operation);
        showToast(operation === "pause" ? "已暂停来源同步。" : "已恢复来源同步。", "success"); render();
      }
      return;
    }
    if (action === "confirm-revoke-source") {
      window.ADSCore.changeSourceState(state.sources, id, "revoke");
      closeModal(); showToast("授权已撤销；恢复需要重新授权。", "success"); render(); return;
    }
    if (action === "toggle-automation") {
      const automation = state.automations.find((x) => x.automation_id === id);
      if (automation) automation.status = automation.status === "on" ? "off" : "on";
      showToast(automation.status === "on" ? "自动化已开启。" : "自动化已关闭。", "success"); render(); return;
    }
    if (action === "toggle-policy") {
      const key = actionEl.dataset.key;
      state.policy[key] = !state.policy[key];
      showToast("偏好已在本次演示会话中更新。", "success"); render(); return;
    }
    if (action === "export-session") { exportSession(); return; }
    if (action === "reset-demo") { resetDemo(); return; }
    if (action === "open-command") { openCommand(); return; }
  }

  function openCommand() {
    openModal("告诉助理", '<p>用自然语言记录、查询或补充上下文。当前为本地模拟，不会调用外部 AI 服务。</p><textarea id="command-input" class="modal-textarea" rows="3" placeholder="例如：帮我记录一下，周五要回顾本周承诺……"></textarea>',
      '<button class="btn btn-ghost" data-action="close-modal">取消</button><button class="btn btn-primary" data-action="submit-command">交给助理</button>');
  }
  function exportSession() {
    const payload = { exported_at: new Date().toISOString(), mode: "synthetic_local_demo", notice: "This export contains demo data and session changes only; no real account data.", state };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "ads-personal-assistant-os-demo-session.json"; a.click();
    URL.revokeObjectURL(url);
    showToast("演示会话 JSON 已导出。", "success");
  }
  function resetDemo() {
    openModal("重置本次演示？", "<p>将恢复全部虚构样例数据，并清除本次页面中的临时修改。</p>",
      '<button class="btn btn-ghost" data-action="close-modal">取消</button><button class="btn btn-danger" data-action="confirm-reset">重置演示</button>');
  }

  document.addEventListener("click", handleClick);
  document.addEventListener("submit", (event) => {
    if (event.target.id === "capture-form") event.preventDefault();
  });
  document.addEventListener("change", (event) => {
    if (event.target.id === "journey-range") {
      timelineDay = Number(event.target.value);
      render();
    }
  });
  document.addEventListener("input", (event) => {
    if (event.target.id === "timeline-search") {
      timelineQuery = event.target.value;
      const pos = event.target.selectionStart;
      render();
      const input = $("#timeline-search");
      if (input) { input.focus(); input.setSelectionRange(pos, pos); }
    }
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest('[data-action="submit-command"]');
    if (button) {
      const value = $("#command-input").value;
      closeModal();
      addInbox(value, "src-voice", "全局快速入口（本地演示）");
      return;
    }
    const reset = event.target.closest('[data-action="confirm-reset"]');
    if (reset) {
      state = clone(initial); timelineDay = 30; timelineFilter = "all"; timelineQuery = ""; myAiTab = "memory";
      closeModal(); currentView = "today"; showToast("演示已重置。"); render();
    }
  });
  $("#modal-backdrop").addEventListener("click", (event) => {
    if (event.target.id === "modal-backdrop") closeModal();
  });
  $("#command-button").addEventListener("click", openCommand);
  $("#export-button").addEventListener("click", exportSession);
  $("#reset-button").addEventListener("click", resetDemo);
  $("#view-root").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && event.target.id === "quick-capture" && !event.shiftKey) {
      event.preventDefault(); addInbox(event.target.value);
    }
  });
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault(); openCommand();
    }
    if (event.key === "Escape") closeModal();
  });

  render();
})();
