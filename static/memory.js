(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const state = { items: [], queue: [], editingId: null, revealed: false };
  const typeLabels = { word: "Word", phrase: "Phrase", correction: "Correction", concept: "Concept", example: "Example" };

  async function request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    if (response.status === 204) return null;
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = body.detail;
      const message = typeof detail === "string" ? detail : detail?.message || "The request could not be completed.";
      throw new Error(message);
    }
    return body;
  }

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function setStatus(message, isError = false) {
    const status = $("#memory-status");
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("error", isError);
  }

  async function load() {
    try {
      const [items, queue, stats] = await Promise.all([
        request("/api/memory/items?status=all"),
        request("/api/memory/review/queue"),
        request("/api/memory/stats"),
      ]);
      state.items = items.items;
      state.queue = queue.items;
      renderStats(stats);
      renderItems();
      renderQueue();
      setStatus("Stored locally");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function renderStats(stats) {
    const target = $("#memory-stats");
    target.replaceChildren();
    [
      [stats.active, "Active cards"],
      [stats.due, "Due to review"],
      [stats.suspended, "Paused"],
      [stats.reviews_completed, "Reviews completed"],
    ].forEach(([value, label]) => {
      const item = node("div", undefined, "learning-progress-item");
      item.append(node("strong", String(value)), node("span", label));
      target.append(item);
    });
  }

  function resetForm() {
    state.editingId = null;
    $("#memory-form").reset();
    $("#memory-form-title").textContent = "Save something worth remembering";
    $("#memory-form-submit").textContent = "Save to memory";
    $("#memory-form-cancel").classList.add("hidden");
    $("#memory-source-note").textContent = "Manual items stay local. Lesson items keep a link to their source context.";
  }

  function renderItems() {
    const target = $("#memory-items");
    target.replaceChildren();
    if (!state.items.length) {
      target.append(node("p", "No saved items yet. Save a useful word, phrase, correction, or concept when you choose to keep it.", "history-empty"));
      return;
    }
    for (const item of state.items) {
      const card = node("article", undefined, "memory-item");
      const header = node("div", undefined, "memory-item-heading");
      header.append(node("span", typeLabels[item.item_type] || item.item_type, "meta-label"));
      header.append(node("span", item.status === "suspended" ? "Paused" : "Active", "status"));
      card.append(header, node("h4", item.front), node("p", item.back));
      if (item.source_title || item.source_excerpt) {
        const source = node("p", [item.source_title, item.source_excerpt].filter(Boolean).join(" · "), "section-help");
        card.append(source);
      }
      const due = item.status === "active"
        ? "Next review: " + new Date(item.due_at).toLocaleDateString()
        : "Reviews paused until resumed";
      card.append(node("p", due, "section-help"));
      const actions = node("div", undefined, "memory-actions");
      const edit = node("button", "Edit", "button button-quiet");
      edit.type = "button";
      edit.addEventListener("click", () => editItem(item));
      const pause = node("button", item.status === "active" ? "Suspend" : "Resume", "button button-quiet");
      pause.type = "button";
      pause.addEventListener("click", () => changeStatus(item, item.status === "active" ? "suspended" : "active"));
      const history = node("button", "Review history", "button button-quiet");
      history.type = "button";
      history.addEventListener("click", async () => {
        const existing = card.querySelector(".memory-history");
        if (existing) { existing.remove(); return; }
        try {
          const result = await request("/api/memory/items/" + encodeURIComponent(item.id) + "/reviews");
          const list = node("div", undefined, "memory-history");
          list.append(node("strong", "Review history (" + result.count + ")"));
          if (!result.reviews.length) list.append(node("p", "No reviews yet.", "section-help"));
          result.reviews.forEach((review) => {
            list.append(node("p", review.rating.toUpperCase() + " · " +
              new Date(review.reviewed_at).toLocaleString() + " · next: " +
              new Date(review.next_due_at).toLocaleDateString(), "section-help"));
          });
          card.append(list);
        } catch (error) { setStatus(error.message, true); }
      });
      const remove = node("button", "Delete", "button button-quiet");
      remove.type = "button";
      remove.addEventListener("click", () => deleteItem(item));
      actions.append(edit, pause, history, remove);
      card.append(actions);
      target.append(card);
    }
  }

  function editItem(item) {
    state.editingId = item.id;
    $("#memory-type").value = item.item_type;
    $("#memory-front").value = item.front;
    $("#memory-back").value = item.back;
    $("#memory-form-title").textContent = "Edit saved item";
    $("#memory-form-submit").textContent = "Save changes";
    $("#memory-form-cancel").classList.remove("hidden");
    $("#memory-source-note").textContent = "Editing preserves the original source and review history.";
    $("#memory-front").focus();
    $("#memory-form").scrollIntoView({ behavior: "smooth", block: "center" });
  }

  async function changeStatus(item, status) {
    try {
      await request("/api/memory/items/" + encodeURIComponent(item.id) + "/status?status=" + status, { method: "PATCH" });
      await load();
    } catch (error) { setStatus(error.message, true); }
  }

  async function deleteItem(item) {
    if (!window.confirm("Delete this saved item and its review history? This cannot be undone.")) return;
    try {
      await request("/api/memory/items/" + encodeURIComponent(item.id), { method: "DELETE" });
      if (state.editingId === item.id) resetForm();
      await load();
    } catch (error) { setStatus(error.message, true); }
  }

  function renderQueue() {
    const target = $("#memory-review");
    target.replaceChildren();
    if (!state.queue.length) {
      target.append(node("p", "You're clear for now. Saved active cards will appear here when their review date arrives.", "history-empty"));
      return;
    }
    const item = state.queue[0];
    const card = node("article", undefined, "memory-review-card");
    card.append(node("span", "CARD 1 OF " + state.queue.length, "meta-label"));
    card.append(node("h3", item.front));
    if (!state.revealed) {
      const reveal = node("button", "Show answer", "button button-secondary");
      reveal.type = "button";
      reveal.addEventListener("click", () => { state.revealed = true; renderQueue(); });
      card.append(reveal);
    } else {
      card.append(node("p", item.back, "memory-review-answer"));
      const prompt = node("p", "How well did you recall it?", "section-help");
      card.append(prompt);
      const ratings = node("div", undefined, "memory-ratings");
      [["again", "Again · forgot"], ["hard", "Hard"], ["good", "Good"], ["easy", "Easy"]].forEach(([rating, label]) => {
        const button = node("button", label, "button button-secondary");
        button.type = "button";
        button.addEventListener("click", () => submitReview(item, rating));
        ratings.append(button);
      });
      card.append(ratings);
    }
    target.append(card);
  }

  async function submitReview(item, rating) {
    try {
      const result = await request("/api/memory/items/" + encodeURIComponent(item.id) + "/review", {
        method: "POST", body: JSON.stringify({ rating }),
      });
      state.revealed = false;
      await load();
      setStatus(result.schedule_note);
    } catch (error) { setStatus(error.message, true); }
  }

  $("#memory-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      item_type: $("#memory-type").value,
      front: $("#memory-front").value,
      back: $("#memory-back").value,
    };
    try {
      if (state.editingId) {
        await request("/api/memory/items/" + encodeURIComponent(state.editingId), {
          method: "PUT", body: JSON.stringify(payload),
        });
        setStatus("Saved changes. Existing review history was kept.");
      } else {
        await request("/api/memory/items", {
          method: "POST",
          body: JSON.stringify({
            ...payload,
            source_type: $("#memory-source-type").value || "manual",
            source_id: $("#memory-source-id").value || null,
            source_title: $("#memory-source-title").value || null,
            source_excerpt: $("#memory-source-excerpt").value || null,
          }),
        });
        setStatus("Saved locally. Your first review is due now.");
      }
      resetForm();
      await load();
    } catch (error) { setStatus(error.message, true); }
  });

  $("#memory-form-cancel").addEventListener("click", resetForm);
  $("#memory-refresh").addEventListener("click", load);
  document.addEventListener("prepped:memory-save", (event) => {
    const detail = event.detail || {};
    resetForm();
    $("#memory-type").value = detail.item_type || "correction";
    $("#memory-front").value = detail.front || "";
    $("#memory-back").value = detail.back || "";
    $("#memory-source-type").value = detail.source_type || "lesson";
    $("#memory-source-id").value = detail.source_id || "";
    $("#memory-source-title").value = detail.source_title || "";
    $("#memory-source-excerpt").value = detail.source_excerpt || "";
    $("#memory-source-note").textContent = "Review this suggestion, edit it, then choose Save to memory. Nothing is saved until you submit.";
    $("#memory-form").scrollIntoView({ behavior: "smooth", block: "center" });
    $("#memory-front").focus();
  });

  document.addEventListener("DOMContentLoaded", () => {
    if ($("#memory-view")) load();
    $("#learning-toggle")?.addEventListener("click", () => {
      if (!$("#learning-view")?.classList.contains("hidden")) load();
    });
  });
})();
