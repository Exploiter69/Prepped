(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const state = { overview: null, plan: null, week: null, dismissed: [], catalog: null, loading: false };

  async function request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The adaptive learning request failed.");
    return body;
  }

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined && text !== null) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  }

  function localDate(value = new Date()) {
    const offset = value.getTimezoneOffset();
    return new Date(value.getTime() - offset * 60_000).toISOString().slice(0, 10);
  }

  function mondayOf(value) {
    const date = new Date(value + "T12:00:00");
    date.setDate(date.getDate() - date.getDay() + (date.getDay() === 0 ? -6 : 1));
    return localDate(date);
  }

  function setStatus(message, error = false) {
    const target = $("#intelligence-status");
    if (!target) return;
    target.textContent = message;
    target.classList.toggle("error", error);
  }

  function renderSummary(summary) {
    const target = $("#intelligence-summary");
    target.replaceChildren();
    [
      [summary.skills_with_activity + " / " + summary.skill_count, "Skills with saved activity"],
      [summary.closed_exercise_responses, "Skill-linked closed responses"],
      [summary.review_needed_responses, "Responses marked for review"],
      [summary.due_memory_items, "Revision items due"],
    ].forEach(([value, label]) => {
      const card = node("div", undefined, "progress-stat");
      card.append(node("strong", value), node("span", label));
      target.append(card);
    });
  }

  function renderSkills(skills) {
    const target = $("#intelligence-skills");
    target.replaceChildren();
    for (const skill of skills) {
      const card = node("article", undefined, "intelligence-skill");
      card.append(node("h5", skill.title));
      card.append(node("p", skill.description));
      const meta = node("div", undefined, "intelligence-skill-meta");
      meta.append(
        node("span", skill.state_label),
        node("span", skill.freshness === "unknown" ? "No dated evidence" :
          skill.freshness + (skill.evidence_age_days === null ? "" : " · " + skill.evidence_age_days + "d ago")),
        node("span", skill.activity_count + " activity records"),
        node("span", skill.closed_response_count + " closed responses"),
      );
      card.append(meta);
      const counts = node("p", "Correct responses observed: " + skill.correct_response_count +
        " · Responses needing review: " + skill.review_needed_count);
      card.append(counts);
      if (skill.repeated_mistakes.length) {
        card.append(node("p", "Repeated review prompts: " + skill.repeated_mistakes
          .map(item => item.exercise_id + " (" + item.review_needed_responses + ")").join(", ")));
      }
      const details = node("details", undefined, "intelligence-evidence");
      details.append(node("summary", "Inspect evidence (" + skill.evidence.length + " recent records)"));
      const list = node("ul");
      for (const item of skill.evidence) {
        const dateLabel = item.occurred_at ? new Date(item.occurred_at).toLocaleString() : "Date unavailable";
        list.append(node("li", item.title + " · " + item.kind.replaceAll("_", " ") +
          " · " + item.outcome + " · " + dateLabel + ". " + item.note));
      }
      if (!skill.evidence.length) list.append(node("li", "No linked saved activity yet."));
      details.append(list);
      card.append(details);
      card.append(node("p", skill.limitations));
      target.append(card);
    }
  }

  function renderRecommendations(items) {
    const target = $("#intelligence-recommendations");
    target.replaceChildren();
    if (!items.length) {
      target.append(node("p", "No urgent next step is identified from current evidence. You can still choose any lesson or practice studio."));
      return;
    }
    for (const item of items) {
      const row = node("article", undefined, "intelligence-recommendation");
      row.append(node("strong", item.title));
      row.append(node("p", item.reason));
      row.append(node("p", item.estimated_minutes + " min · " + item.source.replaceAll("_", " ")));
      const actions = node("div", undefined, "intelligence-plan-item-actions");
      if (["lesson", "career_practice", "project_practice"].includes(item.kind)) {
        const add = node("button", "Add to today's plan", "button button-secondary");
        add.type = "button";
        add.addEventListener("click", () => addToPlan(item.kind, item.target_id));
        actions.append(add);
      } else if (item.kind === "review_memory") {
        const open = node("button", "Open revision queue", "button button-secondary");
        open.type = "button";
        open.addEventListener("click", openLearning);
        actions.append(open);
      }
      const dismiss = node("button", "Dismiss", "button button-quiet");
      dismiss.type = "button";
      dismiss.addEventListener("click", () => dismissRecommendation(item));
      actions.append(dismiss);
      row.append(actions);
      target.append(row);
    }
  }

  function renderDismissed(items) {
    const target = $("#intelligence-dismissed");
    target.replaceChildren();
    for (const item of items) {
      const row = node("article", undefined, "intelligence-recommendation");
      row.append(node("strong", item.title), node("p", item.reason || "Dismissed suggestion"));
      const restore = node("button", "Restore", "button button-quiet");
      restore.type = "button";
      restore.addEventListener("click", async () => {
        try {
          await request("/api/intelligence/recommendations/restore", {
            method: "POST", body: JSON.stringify({
              kind: item.kind, target_id: item.target_id, title: item.title, reason: item.reason || "",
            }),
          });
          await load();
        } catch (error) { setStatus(error.message, true); }
      });
      row.append(restore);
      target.append(row);
    }
    if (!items.length) target.append(node("p", "No dismissed adaptive suggestions."));
  }

  function renderPlan(plan) {
    const target = $("#intelligence-plan-items");
    target.replaceChildren();
    const dateLabel = $("#intelligence-plan-date-label");
    dateLabel.textContent = plan ? plan.plan_date + " · " + plan.estimated_minutes + " planned min" : "No plan for this date";
    if (!plan) {
      target.append(node("p", "Build a daily plan to combine due revision, a suitable lesson, and optional interview practice."));
      return;
    }
    if (!plan.items.length) target.append(node("p", "No activities fit this plan yet. Add a lesson or practice activity below."));
    plan.items.forEach((item, index) => {
      const row = node("article", undefined, "intelligence-plan-item");
      const details = node("div");
      details.append(node("strong", (index + 1) + ". " + item.title));
      details.append(node("p", item.reason));
      details.append(node("p", item.estimated_minutes + " min · " + item.status +
        (item.status === "completed" ? " · confirmed by saved activity" : "")));
      const actions = node("div", undefined, "intelligence-plan-item-actions");
      const open = node("button", item.item_type === "memory_review" ? "Open revision" :
        item.item_type === "lesson" ? "Open lesson" : "Open practice", "button button-secondary");
      open.type = "button";
      open.disabled = item.status === "skipped";
      open.addEventListener("click", () => openPlanItem(item));
      actions.append(open);
      if (item.status !== "completed") {
        const skip = node("button", item.status === "skipped" ? "Restore" : "Skip", "button button-quiet");
        skip.type = "button";
        skip.addEventListener("click", () => updatePlanItem(item.id, { skipped: item.status !== "skipped" }));
        actions.append(skip);
      }
      const up = node("button", "Move up", "button button-quiet");
      up.type = "button";
      up.disabled = index === 0;
      up.addEventListener("click", () => updatePlanItem(item.id, { position: Math.max(0, index - 1) }));
      const down = node("button", "Move down", "button button-quiet");
      down.type = "button";
      down.disabled = index === plan.items.length - 1;
      down.addEventListener("click", () => updatePlanItem(item.id, { position: index + 1 }));
      actions.append(up, down);
      row.append(details, actions);
      target.append(row);
    });

  }

  function renderWeek(week) {
    const target = $("#intelligence-week");
    target.replaceChildren();
    week.days.forEach(day => {
      const card = node("button", undefined, "intelligence-week-day");
      card.type = "button";
      card.append(node("strong", new Date(day.plan_date + "T12:00:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })));
      card.append(node("span", day.items.length + " activities"));
      card.append(node("span", day.completed_count + " complete · " + day.estimated_minutes + " min"));
      card.addEventListener("click", async () => {
        $("#intelligence-plan-date").value = day.plan_date;
        try { await loadPlan(day.plan_date); }
        catch (error) { setStatus(error.message, true); }
      });
      target.append(card);
    });
  }

  function renderActivity(days) {
    const target = $("#intelligence-activity");
    target.replaceChildren();
    const max = Math.max(1, ...days.map(item => item.count));
    for (const day of days) {
      const cell = node("div", undefined, "progress-day");
      cell.setAttribute("role", "img");
      cell.setAttribute("aria-label", day.date + ": " + day.count + " saved events and reviews");
      const bar = node("div", undefined, "progress-day-bar");
      const fill = node("span");
      fill.style.height = (day.count ? Math.max(8, day.count / max * 100) : 0) + "%";
      bar.append(fill);
      cell.append(bar, node("small", new Date(day.date + "T12:00:00").toLocaleDateString(undefined, { weekday: "short" })));
      target.append(cell);
    }
  }

  function renderAddActivityOptions() {
    const type = $("#intelligence-add-type");
    const target = $("#intelligence-add-target");
    if (!type || !target || !state.catalog) return;
    target.replaceChildren();
    const values = type.value === "lesson" ? state.catalog.lessons :
      type.value === "career_practice" ? state.catalog.career_studios : [state.catalog.project_practice];
    for (const item of values) {
      const option = node("option", item.title);
      option.value = item.id;
      target.append(option);
    }
  }

  async function loadPlan(targetDate = $("#intelligence-plan-date").value) {
    const planDate = targetDate || localDate();
    const result = await request("/api/intelligence/plan?plan_date=" + encodeURIComponent(planDate));
    state.plan = result.plan;
    renderPlan(state.plan);
  }

  async function loadWeek(start = mondayOf($("#intelligence-plan-date").value || localDate())) {
    state.week = await request("/api/intelligence/plan/week?week_start=" + encodeURIComponent(start));
    renderWeek(state.week);
  }

  async function load() {
    if (state.loading) return;
    state.loading = true;
    setStatus("Updating evidence…");
    try {
      const [overview, dismissed, catalog] = await Promise.all([
        request("/api/intelligence/overview"),
        request("/api/progress/recommendations/dismissed"),
        request("/api/intelligence/catalog"),
      ]);
      state.overview = overview;
      state.catalog = catalog;
      renderAddActivityOptions();
      state.dismissed = dismissed.recommendations.filter(item =>
        ["lesson", "review_memory", "career_practice", "project_practice"].includes(item.kind));
      renderSummary(overview.summary);
      renderSkills(overview.skills);
      renderRecommendations(overview.recommendations);
      renderDismissed(state.dismissed);
      renderActivity(overview.activity_30_days);
      const planDate = $("#intelligence-plan-date").value || localDate();
      $("#intelligence-plan-date").value = planDate;
      await Promise.all([loadPlan(planDate), loadWeek(mondayOf(planDate))]);
      setStatus("Evidence updated · " + new Date(overview.generated_at).toLocaleTimeString());
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      state.loading = false;
    }
  }

  async function generateDay() {
    const button = $("#intelligence-generate-day");
    button.disabled = true;
    try {
      const result = await request("/api/intelligence/plan/generate", {
        method: "POST",
        body: JSON.stringify({
          plan_date: $("#intelligence-plan-date").value || localDate(),
          available_minutes: Number($("#intelligence-plan-minutes").value),
          regenerate: true,
        }),
      });
      state.plan = result.plan;
      renderPlan(state.plan);
      await loadWeek(mondayOf(state.plan.plan_date));
      setStatus("Daily plan updated.");
    } catch (error) { setStatus(error.message, true); }
    finally { button.disabled = false; }
  }

  async function generateWeek() {
    const button = $("#intelligence-generate-week");
    button.disabled = true;
    try {
      const start = mondayOf($("#intelligence-plan-date").value || localDate());
      const result = await request("/api/intelligence/plan/week/generate", {
        method: "POST",
        body: JSON.stringify({
          week_start: start,
          available_minutes_per_day: Number($("#intelligence-plan-minutes").value),
        }),
      });
      state.week = { week_start: result.week_start, days: result.days };
      renderWeek(state.week);
      const selected = result.days.find(item => item.plan_date === ($("#intelligence-plan-date").value || localDate())) || result.days[0];
      state.plan = selected;
      renderPlan(state.plan);
      setStatus("Seven-day plan created.");
    } catch (error) { setStatus(error.message, true); }
    finally { button.disabled = false; }
  }

  async function addToPlan(itemType, targetId) {
    const planDate = $("#intelligence-plan-date").value || localDate();
    try {
      const current = await request("/api/intelligence/plan?plan_date=" + encodeURIComponent(planDate));
      if (!current.plan) {
        await request("/api/intelligence/plan/generate", {
          method: "POST", body: JSON.stringify({
            plan_date: planDate, available_minutes: Number($("#intelligence-plan-minutes").value), regenerate: false,
          }),
        });
      }
      await addPlanItem(itemType, targetId);
    } catch (error) { setStatus(error.message, true); }
  }

  async function addPlanItem(itemType, targetId) {
    const planDate = $("#intelligence-plan-date").value || localDate();
    try {
      const result = await request("/api/intelligence/plan/items", {
        method: "POST", body: JSON.stringify({ plan_date: planDate, item_type: itemType, target_id: targetId }),
      });
      state.plan = result.plan;
      renderPlan(state.plan);
      await loadWeek(mondayOf(planDate));
      setStatus("Activity added to your plan.");
    } catch (error) { setStatus(error.message, true); }
  }

  async function updatePlanItem(itemId, patch) {
    try {
      const result = await request("/api/intelligence/plan/items/" + encodeURIComponent(itemId), {
        method: "PATCH", body: JSON.stringify(patch),
      });
      state.plan = result.plan;
      renderPlan(state.plan);
      await loadWeek(mondayOf(state.plan.plan_date));
    } catch (error) { setStatus(error.message, true); }
  }

  async function dismissRecommendation(item) {
    try {
      await request("/api/intelligence/recommendations/dismiss", {
        method: "POST", body: JSON.stringify({
          kind: item.kind, target_id: item.target_id, title: item.title, reason: item.reason,
        }),
      });
      await load();
    } catch (error) { setStatus(error.message, true); }
  }

  async function openPlanItem(item) {
    if (item.item_type === "memory_review") {
      openLearning();
      return;
    }
    if (item.item_type === "project_practice") {
      window.dispatchEvent(new CustomEvent("prepped:open-practice"));
      return;
    }
    if (item.item_type === "career_practice") {
      $("#career-toggle")?.click();
      const studioTitle = item.target_id.replaceAll("-", " ").toLowerCase();
      const card = await waitFor(() => [...document.querySelectorAll(".career-studio-card")].find(
        element => element.textContent.toLowerCase().includes(studioTitle)
      ));
      card?.querySelector("button")?.click();
      return;
    }
    openLearning();
    const found = await waitFor(() => [...document.querySelectorAll("[data-lesson-id]")].find(
      element => element.dataset.lessonId === item.target_id
    ));
    found?.click();
  }

  function openLearning() {
    $("#learning-toggle")?.click();
    window.setTimeout(() => $("#memory-view")?.scrollIntoView({ behavior: "smooth", block: "start" }), 250);
  }

  async function waitFor(callback) {
    for (let index = 0; index < 180; index += 1) {
      const element = callback();
      if (element) return element;
      await new Promise(resolve => requestAnimationFrame(resolve));
    }
    return null;
  }

  $("#intelligence-add-type")?.addEventListener("change", renderAddActivityOptions);
  $("#intelligence-add-activity")?.addEventListener("click", () => {
    const type = $("#intelligence-add-type").value;
    const target = $("#intelligence-add-target").value;
    if (type && target) addToPlan(type, target);
  });
  $("#intelligence-generate-day")?.addEventListener("click", generateDay);
  $("#intelligence-generate-week")?.addEventListener("click", generateWeek);
  $("#intelligence-plan-date")?.addEventListener("change", async () => {
    try {
      await Promise.all([
        loadPlan($("#intelligence-plan-date").value),
        loadWeek(mondayOf($("#intelligence-plan-date").value)),
      ]);
    } catch (error) { setStatus(error.message, true); }
  });
  $("#intelligence-dismissed-toggle")?.addEventListener("click", () => {
    const target = $("#intelligence-dismissed");
    const opening = target.classList.contains("hidden");
    target.classList.toggle("hidden", !opening);
    $("#intelligence-dismissed-toggle").setAttribute("aria-expanded", String(opening));
  });
  window.addEventListener("prepped:viewchange", event => {
    if (event.detail?.view === "progress-view") load();
  });
})();
