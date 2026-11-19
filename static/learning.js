(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const state = { catalog: null, progress: null, attempt: null, busy: false };
  const viewIds = ["home-view", "practice-view", "feedback-view", "history-view", "learning-view"];

  async function request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The learning request failed.");
    return body;
  }

  function showLearning() {
    window.PreppedVoice?.stopAll();
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "learning-view");
    $("#global-status")?.classList.add("hidden");
    $("#learning-view").classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
    loadWorkspace();
  }

  function showHome() {
    $("#learning-view").classList.add("hidden");
    $("#global-status")?.classList.remove("hidden");
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "home-view");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function makeButton(label, lessonId, className = "button button-secondary") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.dataset.lessonId = lessonId;
    button.addEventListener("click", () => startLesson(lessonId));
    return button;
  }

  function renderRecommendations(recommendations) {
    $("#learning-route-title").textContent = recommendations.track_title;
    $("#learning-route-goal").textContent = recommendations.goal.replaceAll("_", " ");
    $("#learning-route-description").textContent = recommendations.track_description;
    $("#learning-route-note").textContent = recommendations.note;
    const container = $("#learning-recommendations");
    container.replaceChildren();
    for (const item of recommendations.items) {
      const card = document.createElement("article");
      card.className = "learning-card";
      const heading = document.createElement("h4");
      heading.textContent = item.title;
      const description = document.createElement("p");
      description.textContent = item.summary;
      const why = document.createElement("p");
      why.className = "learning-why";
      why.textContent = item.why;
      const meta = document.createElement("span");
      meta.className = "meta-label";
      meta.textContent = "ABOUT " + item.estimated_minutes + " MINUTES";
      card.append(meta, heading, description, why, makeButton("Start lesson →", item.lesson_id, "button button-primary"));
      container.append(card);
    }
  }

  function renderTracks(tracks) {
    const container = $("#learning-track-list");
    container.replaceChildren();
    for (const track of tracks) {
      const section = document.createElement("section");
      section.className = "learning-track";
      const heading = document.createElement("h4");
      heading.textContent = track.title;
      const description = document.createElement("p");
      description.textContent = track.description;
      const list = document.createElement("div");
      list.className = "learning-card-list";
      for (const lesson of track.lessons) {
        const card = document.createElement("article");
        card.className = "learning-card compact";
        const title = document.createElement("h5");
        title.textContent = lesson.title;
        const summary = document.createElement("p");
        summary.textContent = lesson.summary;
        const meta = document.createElement("span");
        meta.className = "meta-label";
        meta.textContent = lesson.exercise_count + " EXERCISES · " + lesson.estimated_minutes + " MIN";
        card.append(meta, title, summary, makeButton("Open lesson", lesson.id));
        list.append(card);
      }
      section.append(heading, description, list);
      container.append(section);
    }
  }

  function renderProgress(progress) {
    $("#learning-progress").replaceChildren();
    const facts = [
      ["Lessons completed", progress.lessons_completed],
      ["Attempts started", progress.attempts_started],
      ["Recorded events", progress.learning_events],
    ];
    for (const [label, value] of facts) {
      const item = document.createElement("div");
      item.className = "learning-progress-item";
      const strong = document.createElement("strong");
      strong.textContent = String(value);
      const span = document.createElement("span");
      span.textContent = label;
      item.append(strong, span);
      $("#learning-progress").append(item);
    }
    $("#learning-progress-note").textContent = progress.note;
    const resume = $("#learning-resume-list");
    resume.replaceChildren();
    const active = progress.recent_attempts.filter((item) => item.status === "in_progress");
    if (active.length) {
      const heading = document.createElement("h4");
      heading.textContent = "Continue an unfinished lesson";
      resume.append(heading);
      for (const item of active) {
        const lesson = progress.lesson_titles?.[item.lesson_id] || item.lesson_id.replaceAll("-", " ");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "button button-secondary";
        button.textContent = "Resume: " + lesson;
        button.addEventListener("click", () => resumeAttempt(item.id));
        resume.append(button);
      }
    }
  }

  async function loadWorkspace() {
    $("#learning-status").textContent = "Loading curriculum…";
    try {
      const [catalog, progress] = await Promise.all([
        request("/api/learning/catalog"),
        request("/api/learning/progress"),
      ]);
      state.catalog = catalog;
      state.progress = progress;
      renderRecommendations(catalog.recommendations);
      renderTracks(catalog.tracks);
      const titles = {};
      for (const track of catalog.tracks) for (const lesson of track.lessons) titles[lesson.id] = lesson.title;
      progress.lesson_titles = titles;
      renderProgress(progress);
      $("#learning-status").textContent = catalog.skills.length + " skills · " + catalog.tracks.length + " paths";
    } catch (error) {
      $("#learning-status").textContent = "Could not load curriculum";
      $("#learning-route-note").textContent = error.message;
    }
  }

  function renderExample(lesson) {
    const target = $("#learning-example");
    target.replaceChildren();
    if (!lesson.example) return;
    const title = document.createElement("strong");
    title.textContent = lesson.example.label || "Example";
    const before = document.createElement("p");
    before.textContent = "Before: " + lesson.example.before;
    const after = document.createElement("p");
    after.textContent = "After: " + lesson.example.after;
    const explanation = document.createElement("p");
    explanation.textContent = lesson.example.explanation;
    target.append(title, before, after, explanation);
  }

  function renderExercise(exercise, index, total) {
    $("#learning-exercise-count").textContent = "Exercise " + (index + 1) + " of " + total;
    $("#learning-exercise-error").textContent = "";
    $("#learning-exercise").replaceChildren();
    const prompt = document.createElement("h4");
    prompt.textContent = exercise.prompt;
    $("#learning-exercise").append(prompt);

    if (exercise.type === "choice") {
      const group = document.createElement("fieldset");
      group.className = "learning-choice-list";
      const legend = document.createElement("legend");
      legend.textContent = "Choose one answer";
      group.append(legend);
      for (const option of exercise.options) {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "radio";
        input.name = "learning-choice";
        input.value = option.id;
        label.append(input, document.createTextNode(option.label));
        group.append(label);
      }
      $("#learning-exercise").append(group);
    } else if (exercise.type === "ordering") {
      const group = document.createElement("div");
      group.className = "learning-order-list";
      const hint = document.createElement("p");
      hint.textContent = "Choose the item for each position. Use every item once.";
      group.append(hint);
      for (let i = 0; i < exercise.tokens.length; i += 1) {
        const label = document.createElement("label");
        label.textContent = "Position " + (i + 1);
        const select = document.createElement("select");
        select.className = "learning-order-select";
        select.required = true;
        select.dataset.position = String(i);
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "Choose an item";
        select.append(empty);
        for (const token of exercise.tokens) {
          const option = document.createElement("option");
          option.value = token.id;
          option.textContent = token.label;
          select.append(option);
        }
        label.append(select);
        group.append(label);
      }
      $("#learning-exercise").append(group);
    } else {
      const label = document.createElement("label");
      label.textContent = "Your response";
      const textarea = document.createElement("textarea");
      textarea.id = "learning-reflection";
      textarea.rows = 5;
      textarea.maxLength = 6000;
      textarea.placeholder = exercise.placeholder || "Write your response…";
      label.append(textarea);
      const guidance = document.createElement("p");
      guidance.className = "section-help";
      guidance.textContent = exercise.guidance;
      $("#learning-exercise").append(label, guidance);
    }
    $("#learning-submit").disabled = false;
    $("#learning-submit").textContent = "Check and continue →";
  }

  function renderFeedback(items) {
    const container = $("#learning-feedback");
    container.replaceChildren();
    const heading = document.createElement("h4");
    heading.textContent = "Lesson review";
    const note = document.createElement("p");
    note.textContent = "These notes relate to your submitted answers. Open responses are saved for your own review and are not automatically graded.";
    container.append(heading, note);
    for (const item of items) {
      const card = document.createElement("article");
      card.className = "feedback-card";
      const title = document.createElement("h5");
      title.textContent = item.prompt;
      const status = document.createElement("span");
      status.className = "feedback-status " + item.status;
      status.textContent = item.status.replaceAll("_", " ");
      card.append(title, status);
      const detail = document.createElement("p");
      if (item.type === "reflection") {
        detail.textContent = "Your response: " + (item.original_response || "(empty)");
      } else if (item.type === "choice") {
        detail.textContent = "Your choice: " + item.selected + ". Suggested answer: " + item.correct_answer + ". " + item.explanation;
      } else {
        detail.textContent = "Your order: " + item.your_order.join(" → ") + ". Suggested order: " + item.suggested_order.join(" → ") + ". " + item.explanation;
      }
      card.append(detail);
      if (item.guidance) {
        const guidance = document.createElement("p");
        guidance.textContent = item.guidance;
        card.append(guidance);
      }
      container.append(card);
    }
    const back = document.createElement("button");
    back.type = "button";
    back.className = "button button-secondary";
    back.textContent = "Back to lesson list";
    back.addEventListener("click", exitLesson);
    container.append(back);
    container.classList.remove("hidden");
  }

  function renderAttempt(attempt) {
    state.attempt = attempt;
    $("#learning-runner").classList.remove("hidden");
    $("#learning-runner-title").textContent = attempt.lesson.title;
    $("#learning-runner-intro").textContent = attempt.lesson.introduction;
    renderExample(attempt.lesson);
    $("#learning-feedback").classList.add("hidden");
    if (attempt.status === "completed") {
      $("#learning-exercise").replaceChildren();
      $("#learning-exercise-count").textContent = "Completed";
      $("#learning-submit").disabled = true;
      $("#learning-submit").textContent = "Lesson completed";
      renderFeedback(attempt.feedback);
    } else {
      renderExercise(attempt.current_exercise, attempt.response_count, attempt.exercise_count);
    }
    $("#learning-runner").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function startLesson(lessonId) {
    if (state.busy) return;
    state.busy = true;
    try {
      const attempt = await request("/api/learning/attempts", {
        method: "POST", body: JSON.stringify({ lesson_id: lessonId }),
      });
      renderAttempt(attempt);
    } catch (error) {
      $("#learning-status").textContent = error.message;
    } finally {
      state.busy = false;
    }
  }

  async function resumeAttempt(attemptId) {
    try {
      const attempt = await request("/api/learning/attempts/" + encodeURIComponent(attemptId));
      renderAttempt(attempt);
    } catch (error) {
      $("#learning-status").textContent = error.message;
    }
  }

  async function submitCurrent() {
    if (!state.attempt || state.attempt.status !== "in_progress" || state.busy) return;
    const exercise = state.attempt.current_exercise;
    let answer;
    if (exercise.type === "choice") {
      answer = $('input[name="learning-choice"]:checked', $("#learning-exercise"))?.value || "";
    } else if (exercise.type === "ordering") {
      answer = Array.from(document.querySelectorAll(".learning-order-select")).map((select) => select.value);
      if (answer.some((value) => !value) || new Set(answer).size !== answer.length) {
        $("#learning-exercise-error").textContent = "Choose every item once, without duplicates.";
        return;
      }
    } else {
      answer = $("#learning-reflection")?.value || "";
    }
    if (!answer || (typeof answer === "string" && !answer.trim())) {
      $("#learning-exercise-error").textContent = "Add your answer before continuing.";
      return;
    }
    state.busy = true;
    $("#learning-submit").disabled = true;
    $("#learning-exercise-error").textContent = "";
    try {
      const attempt = await request("/api/learning/attempts/" + encodeURIComponent(state.attempt.id) + "/responses", {
        method: "POST", body: JSON.stringify({ exercise_id: exercise.id, answer }),
      });
      renderAttempt(attempt);
      if (attempt.status === "completed") {
        await loadWorkspace();
        $("#learning-feedback").classList.remove("hidden");
      }
    } catch (error) {
      $("#learning-exercise-error").textContent = error.message;
      $("#learning-submit").disabled = false;
    } finally {
      state.busy = false;
    }
  }

  function exitLesson() {
    $("#learning-runner").classList.add("hidden");
    state.attempt = null;
    loadWorkspace();
    $("#learning-title").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("#learning-toggle")?.addEventListener("click", showLearning);
    $("#learning-home")?.addEventListener("click", showHome);
    $("#learning-exit")?.addEventListener("click", exitLesson);
    $("#learning-submit")?.addEventListener("click", submitCurrent);
  });
})();
