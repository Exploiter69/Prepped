(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const viewIds = ["home-view", "practice-view", "feedback-view", "history-view", "learning-view", "career-view", "progress-view"];
  const state = { overview: null, editingGoalId: null, archivedVisible: false, dismissedVisible: false, dismissedCount: 0 };

  async function request(url, options = {}) {
    const response = await fetch(url, options);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The request could not be completed.");
    return body;
  }

  function showProgress() {
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "progress-view");
    window.dispatchEvent(new CustomEvent("prepped:viewchange", { detail: { view: "progress-view" } }));
    $("#progress-toggle")?.setAttribute("aria-expanded", "true");
    $("#learning-toggle")?.setAttribute("aria-expanded", "false");
    $("#career-toggle")?.setAttribute("aria-expanded", "false");
    window.PreppedVoice?.stopAll();
    window.scrollTo({ top: 0, behavior: "smooth" });
    load();
  }

  async function waitForElement(selector, matches) {
    for (let frame = 0; frame < 300; frame += 1) {
      const found = [...document.querySelectorAll(selector)].find(matches);
      if (found) return found;
      await new Promise(resolve => requestAnimationFrame(resolve));
    }
    return null;
  }

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);
    return element;
  }

  function renderSummary(summary) {
    const total = ["lessons_completed", "practice_sessions_completed", "interviews_completed", "memory_reviews_completed"].reduce((sum, key) => sum + Math.max(0, Number(summary[key]) || 0), 0);
    const note = $("#progress-insight-note");
    if (note) note.textContent = total === 0 ? "Your starting point is simple: complete one small activity and it will appear here. Nothing is scored or ranked." : "You have saved " + total + " completed learning and practice activities across this workspace. These records show what you did—not how capable you are.";
    const target = $("#progress-summary");
    target.replaceChildren();
    const stats = [
      [summary.lessons_completed, "Lessons completed"],
      [summary.practice_sessions_completed, "Project sessions"],
      [summary.interviews_completed, "Interviews completed"],
      [summary.memory_reviews_completed, "Memory reviews"],
      [summary.due_memory_items, "Notes due"],
      [summary.active_goals, "Active goals"],
    ];
    for (const [value, label] of stats) {
      const card = node("div", "progress-stat");
      card.append(node("strong", "", value), node("span", "", label));
      target.append(card);
    }
  }

  function renderSkills(skills) {
    const target = $("#progress-skills");
    target.replaceChildren();
    for (const skill of skills) {
      const card = node("article", "progress-skill");
      const title = node("h4", "", skill.title);
      const stateLabel = node("span", "progress-skill-state", skill.completed_lessons > 0 ? "Lesson evidence recorded" : "Evidence not yet recorded");
      const description = node("p", "", skill.description);
      const count = node("p", "", skill.completed_lessons + " of " + skill.available_lessons + " linked lessons completed");
      const track = node("div", "progress-track-small");
      track.setAttribute("role", "progressbar");
      track.setAttribute("aria-label", skill.title + " lesson coverage");
      track.setAttribute("aria-valuemin", "0");
      track.setAttribute("aria-valuemax", "100");
      track.setAttribute("aria-valuenow", String(skill.completion_percent));
      const fill = node("span");
      fill.style.width = skill.completion_percent + "%";
      track.append(fill);
      const evidence = node("p", "progress-skill-evidence", skill.evidence.length
        ? "Completed lesson evidence: " + skill.evidence.map(item => item.title).join(", ")
        : "No completed lesson evidence yet. Try a linked lesson to begin a record.");
      card.append(stateLabel, title, description, count, track, evidence);
      target.append(card);
    }
  }

  function renderWeek(days) {
    const weekTotal = days.reduce((sum, item) => sum + Math.max(0, Number(item.count) || 0), 0);
    const weekSummary = $("#progress-week-summary");
    if (weekSummary) weekSummary.textContent = weekTotal === 0 ? "No completed activities are recorded in this seven-day window yet. Your earlier work remains in history." : weekTotal + " completed " + (weekTotal === 1 ? "activity" : "activities") + " recorded in the last seven days. This is activity, not a streak or learning-gain measure.";
    const target = $("#progress-week");
    target.replaceChildren();
    const max = Math.max(1, ...days.map(item => item.count));
    for (const day of days) {
      const cell = node("div", "progress-day");
      cell.setAttribute("role", "img");
      cell.setAttribute("aria-label", day.date + ": " + day.count + " completed activities");
      const bar = node("div", "progress-day-bar");
      bar.setAttribute("aria-hidden", "true");
      const fill = node("span");
      fill.style.height = (day.count ? Math.max(8, (day.count / max) * 100) : 0) + "%";
      bar.append(fill);
      const label = node("small", "", new Date(day.date + "T12:00:00").toLocaleDateString(undefined, { weekday: "short" }));
      label.title = day.date + " · " + day.count + " completed activities";
      cell.append(bar, label);
      target.append(cell);
    }
  }

  function renderGoals(goals, archived = []) {
    const target = $("#progress-goals");
    target.replaceChildren();
    const archivedTarget = $("#progress-archived-goals");
    archivedTarget.replaceChildren();
    archivedTarget.classList.toggle("hidden", !state.archivedVisible);
    $("#goal-archive-toggle").textContent = state.archivedVisible ? "Hide archived goals" : "Show archived goals";
    $("#goal-archive-toggle").setAttribute("aria-expanded", String(state.archivedVisible));
    $("#goal-count").textContent = goals.length + " active";
    if (!goals.length) {
      target.append(node("p", "progress-empty", "No active goals yet. Add a small target above; it will count saved activity, not estimate ability."));
    }
    for (const goal of goals) {
      const row = node("article", "progress-row");
      const details = node("div");
      details.append(node("strong", "", goal.title));
      const type = goal.goal_type.replaceAll("_", " ");
      details.append(node("p", "", goal.current_count + " / " + goal.target_count + " " + type +
        (goal.reached_target ? " · target reached" : " · " + goal.remaining + " to go") +
        (goal.due_date ? " · target date " + goal.due_date : "")));
      if (goal.description) details.append(node("p", "", goal.description));
      const actions = node("div", "progress-row-actions");
      const edit = node("button", "button button-quiet", "Edit");
      edit.type = "button";
      edit.addEventListener("click", () => {
        state.editingGoalId = goal.id;
        $("#goal-title").value = goal.title;
        $("#goal-description").value = goal.description || "";
        $("#goal-type").value = goal.goal_type;
        $("#goal-target").value = String(goal.target_count);
        $("#goal-date").value = goal.due_date || "";
        $("#goal-form button[type='submit']").textContent = "Save goal";
        $("#goal-cancel-edit").classList.remove("hidden");
        $("#goal-title").focus();
      });
      const archive = node("button", "button button-quiet", "Archive");
      archive.type = "button";
      archive.addEventListener("click", async () => {
        try { await request("/api/goals/" + encodeURIComponent(goal.id) + "/archive", { method: "POST" }); await load(); }
        catch (error) { setStatus(error.message, true); }
      });
      const remove = node("button", "button button-quiet", "Delete");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!window.confirm("Permanently delete this goal? Activity records will not be deleted.")) return;
        try { await request("/api/goals/" + encodeURIComponent(goal.id), { method: "DELETE" }); await load(); }
        catch (error) { setStatus(error.message, true); }
      });
      actions.append(edit, archive, remove);
      row.append(details, actions);
      target.append(row);
    }
    for (const goal of archived) {
      const row = node("article", "progress-row");
      const details = node("div");
      details.append(node("strong", "", goal.title), node("p", "", "Archived · " + goal.current_count + " / " + goal.target_count + " " + goal.goal_type.replaceAll("_", " ")));
      const actions = node("div", "progress-row-actions");
      const restore = node("button", "button button-secondary", "Restore");
      restore.type = "button";
      restore.addEventListener("click", async () => {
        try { await request("/api/goals/" + encodeURIComponent(goal.id) + "/restore", { method: "POST" }); await load(); }
        catch (error) { setStatus(error.message, true); }
      });
      const remove = node("button", "button button-quiet", "Delete");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!window.confirm("Permanently delete this archived goal? Activity records will not be deleted.")) return;
        try { await request("/api/goals/" + encodeURIComponent(goal.id), { method: "DELETE" }); await load(); }
        catch (error) { setStatus(error.message, true); }
      });
      actions.append(restore, remove);
      row.append(details, actions);
      archivedTarget.append(row);
    }
    if (!archived.length) archivedTarget.append(node("p", "progress-empty", "No archived goals."));
  }

  function renderActivity(items) {
    const target = $("#progress-activity");
    target.replaceChildren();
    if (!items.length) {
      target.append(node("p", "progress-empty", "Your completed lessons, practice, interviews and memory reviews will appear here."));
      return;
    }
    for (const item of items) {
      const row = node("div", "progress-row");
      const date = item.occurred_at ? new Date(item.occurred_at).toLocaleString() : "Date unavailable";
      row.append(node("strong", "", item.title), node("p", "", date));
      target.append(row);
    }
  }

  async function openRecommendation(item) {
    if (item.kind === "goal" || item.kind === "choose_goal") {
      $("#goal-title").focus();
      return;
    }
    if (item.kind === "resume_practice") {
      $("#history-toggle").click();
      const button = await waitForElement("#history-list button[data-session-id]", el => el.dataset.sessionId === item.target_id);
      if (button) button.click();
      return;
    }
    if (item.kind === "resume_interview") {
      $("#career-toggle").click();
      const button = await waitForElement("#career-history-list button[data-session-id]", el => el.dataset.sessionId === item.target_id);
      if (button) button.click();
      return;
    }
    if (item.kind === "resume_lesson" || item.kind === "lesson" || item.kind === "review_memory") {
      $("#learning-toggle").click();
      if (item.kind === "resume_lesson") {
        const button = await waitForElement("#learning-resume-list button[data-attempt-id]", el => el.dataset.attemptId === item.target_id);
        if (button) button.click();
      } else if (item.kind === "lesson") {
        const button = await waitForElement("[data-lesson-id]", el => el.dataset.lessonId === item.target_id);
        if (button) button.click();
      } else {
        $("#memory-view")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      return;
    }
    if (item.kind === "practice") $("#start-button")?.click();
    if (item.kind === "career") $("#career-toggle")?.click();
  }

  function renderRecommendations(items, dismissed) {
    const target = $("#progress-recommendations");
    target.replaceChildren();
    for (const item of items) {
      const row = node("div", "progress-row");
      const details = node("div");
      details.append(node("strong", "", item.title), node("p", "", item.reason));
      const actions = node("div", "progress-row-actions");
      const action = node("button", "button button-secondary", "Open");
      action.type = "button";
      action.addEventListener("click", () => openRecommendation(item));
      const dismiss = node("button", "button button-quiet", "Dismiss");
      dismiss.type = "button";
      dismiss.addEventListener("click", async () => {
        try {
          await request("/api/progress/recommendations/dismiss", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item),
          });
          await load();
        } catch (error) { setStatus(error.message, true); }
      });
      actions.append(action, dismiss);
      row.append(details, actions);
      target.append(row);
    }
    if (!items.length) target.append(node("p", "progress-empty", "No suggested next steps right now. Your saved work remains available from Learning, Career, and History."));
    const dismissedTarget = $("#progress-dismissed-recommendations");
    state.dismissedCount = dismissed.length;
    dismissedTarget.replaceChildren();
    dismissedTarget.classList.toggle("hidden", !state.dismissedVisible);
    $("#progress-dismissed-toggle").textContent = (state.dismissedVisible ? "Hide dismissed suggestions (" : "Show dismissed suggestions (") + dismissed.length + ")";
    $("#progress-dismissed-toggle").setAttribute("aria-expanded", String(state.dismissedVisible));
    for (const item of dismissed) {
      const row = node("div", "progress-row");
      const details = node("div");
      details.append(node("strong", "", item.title), node("p", "", item.reason));
      const restore = node("button", "button button-secondary", "Restore suggestion");
      restore.type = "button";
      restore.addEventListener("click", async () => {
        try {
          await request("/api/progress/recommendations/restore", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ kind: item.kind, target_id: item.target_id }),
          });
          await load();
        } catch (error) { setStatus(error.message, true); }
      });
      row.append(details, restore);
      dismissedTarget.append(row);
    }
    if (!dismissed.length) dismissedTarget.append(node("p", "progress-empty", "No dismissed suggestions."));
  }

  function setStatus(message, isError = false) {
    $("#progress-status").textContent = message;
    $("#progress-status").classList.toggle("error", isError);
  }

  async function load() {
    setStatus("Updating saved activity…");
    try {
      const [overview, goals, dismissed] = await Promise.all([
        request("/api/progress/overview"),
        request("/api/goals?include_archived=true"),
        request("/api/progress/recommendations/dismissed"),
      ]);
      state.overview = overview;
      renderSummary(overview.summary);
      renderSkills(overview.skills);
      renderWeek(overview.weekly_activity);
      renderGoals(goals.goals.filter(goal => goal.status === "active"),
        goals.goals.filter(goal => goal.status === "archived"));
      renderActivity(overview.recent_activity);
      renderRecommendations(overview.recommendations, dismissed.recommendations);
      setStatus("Updated " + new Date(overview.generated_at).toLocaleTimeString());
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function createGoal(event) {
    event.preventDefault();
    const submit = $("#goal-form button[type='submit']");
    submit.disabled = true;
    $("#goal-error").textContent = "";
    try {
      await request(state.editingGoalId ? "/api/goals/" + encodeURIComponent(state.editingGoalId) : "/api/goals", {
        method: state.editingGoalId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: $("#goal-title").value,
          description: $("#goal-description").value,
          goal_type: $("#goal-type").value,
          target_count: Number($("#goal-target").value),
          due_date: $("#goal-date").value || null,
        }),
      });
      $("#goal-form").reset();
      $("#goal-target").value = "3";
      state.editingGoalId = null;
      $("#goal-form button[type='submit']").textContent = "Add my goal";
      $("#goal-cancel-edit").classList.add("hidden");
      await load();
    } catch (error) {
      $("#goal-error").textContent = error.message;
    } finally {
      submit.disabled = false;
    }
  }

  async function exportBackup() {
    const button = $("#data-export");
    button.disabled = true;
    $("#data-status").textContent = "Preparing a local backup…";
    try {
      const response = await fetch("/api/data/export");
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Backup export failed.");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "prepped-backup-" + new Date().toISOString().replaceAll(":", "-").slice(0, 19) + ".json";
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1500);
      $("#data-status").textContent = "Backup downloaded. Keep it private: it contains your saved answers and learning notes.";
    } catch (error) {
      $("#data-status").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }

  async function importBackup(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = "";
    if (file.size > 25 * 1024 * 1024) {
      $("#data-status").textContent = "This file exceeds the 25 MB restore limit.";
      return;
    }
    if (!window.confirm("Restore this Prepped backup? This replaces ALL current local profile, practice, lesson, memory, interview and goal data. Export a backup of the current database first if you may need it.")) return;
    $("#data-status").textContent = "Validating backup before replacing local data…";
    try {
      const backup = JSON.parse(await file.text());
      backup.confirm_replace = true;
      const result = await request("/api/data/restore", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(backup),
      });
      $("#data-status").textContent = "Restored " + result.records_restored + " records. Reloading Prepped…";
      window.setTimeout(() => window.location.reload(), 700);
    } catch (error) {
      $("#data-status").textContent = error instanceof SyntaxError ? "The selected file is not valid JSON." : error.message;
    }
  }

  $("#progress-toggle")?.addEventListener("click", showProgress);
  $("#progress-refresh")?.addEventListener("click", load);
  $("#progress-dismissed-toggle")?.addEventListener("click", () => {
    state.dismissedVisible = !state.dismissedVisible;
    const target = $("#progress-dismissed-recommendations");
    const toggle = $("#progress-dismissed-toggle");
    target?.classList.toggle("hidden", !state.dismissedVisible);
    toggle?.setAttribute("aria-expanded", String(state.dismissedVisible));
    toggle.textContent = (state.dismissedVisible ? "Hide dismissed suggestions (" : "Show dismissed suggestions (") + state.dismissedCount + ")";
    if (state.overview) load();
  });
  $("#progress-home")?.addEventListener("click", () => { for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "home-view"); $("#progress-toggle")?.setAttribute("aria-expanded", "false"); });
  $("#goal-form")?.addEventListener("submit", createGoal);
  $("#goal-cancel-edit")?.addEventListener("click", () => {
    state.editingGoalId = null;
    $("#goal-form").reset();
    $("#goal-target").value = "3";
    $("#goal-form button[type='submit']").textContent = "Add my goal";
    $("#goal-cancel-edit").classList.add("hidden");
    $("#goal-error").textContent = "";
  });
  $("#goal-archive-toggle")?.addEventListener("click", () => {
    state.archivedVisible = !state.archivedVisible;
    if (state.overview) load();
  });
  $("#data-export")?.addEventListener("click", exportBackup);
  $("#data-import")?.addEventListener("change", importBackup);
  document.addEventListener("DOMContentLoaded", () => {
    if ($("#progress-view")) {
      $("#progress-view").addEventListener("focusin", () => {});
    }
  });
})();
