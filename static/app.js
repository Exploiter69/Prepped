const $ = (selector) => document.querySelector(selector);
const views = ["home-view", "practice-view", "feedback-view", "history-view", "learning-view"];
let scenario = null;
let activeSession = null;
let activeFeedback = null;
let busy = false;
let profileConfigured = false;

function setStatus(message, isError = false) {
  const element = $("#global-status");
  element.textContent = message || "";
  element.classList.toggle("error", isError);
}

function showView(viewId) {
  if (viewId !== "practice-view") window.PreppedVoice?.stopAll();
  for (const id of views) $("#" + id).classList.toggle("hidden", id !== viewId);
  $("#learning-toggle")?.setAttribute("aria-expanded", String(viewId === "learning-view"));
  setStatus("");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : "The request could not be completed.";
    throw new Error(detail);
  }
  return payload;
}

function buttonBusy(value) {
  busy = value;
  for (const selector of ["#start-button", "#submit-button", "#skip-button", "#cancel-button", "#retry-button", "#delete-session-button"]) {
    const button = $(selector);
    if (button) button.disabled = value;
  }
  window.PreppedVoice?.setBusy(value);
}

async function loadStarterData() {
  try {
    const results = await Promise.all([api("/api/health"), api("/api/scenarios/project-explanation")]);
    const health = results[0];
    scenario = results[1];
    $("#system-status").textContent = health.status === "ok" ? "Local app ready" : "App status unknown";
    $("#scenario-description").textContent = scenario.description;
    $("#scenario-role").textContent = scenario.role;
    $("#scenario-length").textContent = Number.isFinite(scenario.estimated_minutes) ? "About " + scenario.estimated_minutes + " minutes" : "Not specified";
    $("#scenario-version").textContent = scenario.version;
    const list = $("#question-list");
    list.replaceChildren();
    for (const question of scenario.questions) {
      const item = document.createElement("li");
      item.textContent = question.prompt;
      list.append(item);
    }
    $("#start-button").disabled = false;
    setStatus("Ready. Start when you are comfortable.");
  } catch (error) {
    $("#system-status").textContent = "Could not load local app";
    $("#system-status").classList.add("error");
    setStatus(error.message, true);
  }
}

const goalLabels = {
  english_fluency: "English fluency",
  placement_interviews: "Placement interviews",
  technical_interviews: "Technical interviews",
  project_communication: "Explaining projects",
  professional_communication: "Professional communication",
};

const areaLabels = {
  speaking_fluency: "speaking fluency",
  grammar: "grammar and sentence construction",
  vocabulary: "vocabulary",
  pronunciation: "pronunciation and listening",
  project_explanation: "project explanation",
  technical_interviews: "technical interviews",
  hr_interviews: "HR and behavioural interviews",
  professional_communication: "professional communication",
  confidence: "speaking confidence",
};

function renderProfile(result) {
  profileConfigured = result.configured;
  const profile = result.profile;
  if (!profile) {
    $("#profile-summary").textContent = "Not set up yet. Add a few details to help Prepped organise relevant practice. You can skip this and start practising.";
    $("#profile-edit-toggle").textContent = "Set up profile";
    setProfileFormOpen(false);
    return;
  }

  $("#profile-name").value = profile.display_name || "";
  $("#profile-year").value = profile.study_year == null ? "" : String(profile.study_year);
  $("#profile-branch").value = profile.branch || "";
  $("#profile-role").value = profile.target_role || "";
  $("#profile-goal").value = profile.primary_goal;
  $("#profile-confidence").value = profile.confidence_level;
  for (const checkbox of document.querySelectorAll('input[name="improvement_areas"]')) {
    checkbox.checked = profile.improvement_areas.includes(checkbox.value);
  }

  const details = [
    goalLabels[profile.primary_goal] || profile.primary_goal,
    profile.study_year ? "Year " + profile.study_year : null,
    profile.branch || null,
    profile.target_role ? "Target: " + profile.target_role : null,
  ].filter(Boolean);
  const focus = profile.improvement_areas.map((area) => areaLabels[area]).filter(Boolean);
  $("#profile-summary").textContent = details.join(" · ") + (focus.length ? ". Focus: " + focus.join(", ") + "." : ".");
  $("#profile-edit-toggle").textContent = "Edit profile";
  setProfileFormOpen(false);
}

function setProfileFormOpen(open) {
  const form = $("#profile-form");
  const toggle = $("#profile-edit-toggle");
  form.classList.toggle("hidden", !open);
  toggle.setAttribute("aria-expanded", String(open));
  toggle.textContent = open ? "Close profile" : (profileConfigured ? "Edit profile" : "Set up profile");
  if (open) $("#profile-name").focus();
}

async function loadProfile() {
  try {
    const result = await api("/api/profile");
    renderProfile(result);
    $("#profile-save-status").textContent = result.configured ? "Saved locally" : "Not set up";
  } catch (error) {
    $("#profile-save-status").textContent = "Could not load profile";
    $("#profile-error").textContent = error.message;
  }
}

async function saveProfile(event) {
  event.preventDefault();
  const submit = $("#profile-form button[type='submit']");
  submit.disabled = true;
  $("#profile-error").textContent = "";
  const studyYear = $("#profile-year").value;
  const payload = {
    display_name: $("#profile-name").value,
    study_year: studyYear ? Number(studyYear) : null,
    branch: $("#profile-branch").value,
    target_role: $("#profile-role").value,
    primary_goal: $("#profile-goal").value,
    confidence_level: $("#profile-confidence").value,
    improvement_areas: Array.from(document.querySelectorAll('input[name="improvement_areas"]:checked')).map((item) => item.value),
  };
  try {
    const result = await api("/api/profile", { method: "PUT", body: JSON.stringify(payload) });
    renderProfile(result);
    $("#profile-save-status").textContent = "Saved locally";
    setStatus("Your learning profile has been saved on this device.");
  } catch (error) {
    $("#profile-error").textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}

function renderQuestion(session) {
  activeSession = session;
  const current = session.current_question;
  $("#answer-error").textContent = "";
  $("#answer-input").value = "";
  $("#answer-count").textContent = "0 / 6000";
  $("#practice-progress").textContent = "Question " + Math.min(session.answered_count + 1, session.question_count) + " of " + session.question_count;
  $("#progress-bar").style.width = ((session.answered_count / session.question_count) * 100) + "%";
  if (!current) {
    $("#practice-title").textContent = "All questions complete";
    $("#question-prompt").textContent = "Preparing your review…";
    $("#answer-form").classList.add("hidden");
    window.PreppedVoice?.setQuestion("");
    return;
  }
  $("#answer-form").classList.remove("hidden");
  $("#practice-title").textContent = "Question " + (session.answered_count + 1);
  $("#question-prompt").textContent = current.prompt;
  window.PreppedVoice?.setQuestion(current.prompt);
}

async function startPractice() {
  if (busy) return;
  buttonBusy(true);
  try {
    const session = await api("/api/sessions", { method: "POST" });
    renderQuestion(session);
    showView("practice-view");
    $("#answer-input").focus();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    buttonBusy(false);
  }
}

async function submitCurrentAnswer(answerText) {
  if (busy || !activeSession || !activeSession.current_question) return;
  window.PreppedVoice?.stopAll();
  buttonBusy(true);
  $("#answer-error").textContent = "";
  try {
    const session = await api("/api/sessions/" + encodeURIComponent(activeSession.id) + "/answers", {
      method: "POST",
      body: JSON.stringify({ question_id: activeSession.current_question.id, answer_text: answerText }),
    });
    renderQuestion(session);
    if (session.status === "completed") await showFeedback(session.id);
    else $("#answer-input").focus();
  } catch (error) {
    $("#answer-error").textContent = error.message;
  } finally {
    buttonBusy(false);
  }
}

function makeFeedbackCard(title, status, message, evidence, nextAction, meta = "") {
  const card = document.createElement("article");
  card.className = "feedback-card";
  const heading = document.createElement("div");
  heading.className = "feedback-heading";
  const h = document.createElement("h4");
  h.textContent = title;
  const badge = document.createElement("span");
  badge.className = "feedback-status " + status;
  badge.textContent = status.replaceAll("_", " ");
  heading.append(h, badge);
  card.append(heading);
  if (meta) {
    const detail = document.createElement("p");
    detail.className = "section-help";
    detail.textContent = meta;
    card.append(detail);
  }
  const explanation = document.createElement("p");
  explanation.textContent = message;
  card.append(explanation);
  const quote = document.createElement("p");
  quote.className = "evidence";
  quote.textContent = evidence ? "Evidence: “" + evidence + "”" : "Evidence: not enough text to quote.";
  card.append(quote);
  const next = document.createElement("p");
  next.className = "next-action";
  next.textContent = "Next action: " + nextAction;
  card.append(next);
  const save = document.createElement("button");
  save.type = "button";
  save.className = "button button-quiet memory-save-suggestion";
  save.textContent = "Save a learning note…";
  save.addEventListener("click", () => {
    document.dispatchEvent(new CustomEvent("prepped:memory-save", { detail: {
      item_type: "correction",
      front: evidence || title,
      back: [message, "Next action: " + nextAction].filter(Boolean).join("\n\n"),
      source_type: "practice",
      source_id: activeSession?.id || "",
      source_title: "Project explanation · Attempt " + (activeFeedback?.attempt_number || ""),
      source_excerpt: evidence || "",
    }}));
  });
  card.append(save);
  return card;
}

function renderFeedback(feedback) {
  activeFeedback = feedback;
  $("#attempt-label").textContent = "Attempt " + feedback.attempt_number;
  $("#feedback-summary").textContent = feedback.answered_questions + " of " + feedback.total_questions + " questions had non-empty answers. " + feedback.total_words + " words submitted. There is no overall score.";
  const limitations = $("#feedback-limitations");
  limitations.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = "Read this honestly";
  limitations.append(title);
  const list = document.createElement("ul");
  for (const item of feedback.limitations) {
    const li = document.createElement("li");
    li.textContent = item;
    list.append(li);
  }
  limitations.append(list);

  const questionTarget = $("#question-feedback");
  questionTarget.replaceChildren();
  for (const item of feedback.question_feedback) {
    questionTarget.append(makeFeedbackCard(item.prompt, item.status, item.message, item.evidence, item.next_action, item.word_count + " words"));
  }
  const rubricTarget = $("#rubric-feedback");
  rubricTarget.replaceChildren();
  for (const item of feedback.rubric_feedback) {
    rubricTarget.append(makeFeedbackCard(item.label, item.status, item.message, item.evidence, item.next_action, item.question));
  }
}

async function renderComparison(feedback) {
  const section = $("#comparison-section");
  const history = await api("/api/sessions");
  const groupId = activeSession ? activeSession.attempt_group_id : feedback.session_id;
  const previous = history.sessions
    .filter((item) => item.attempt_group_id === groupId && item.status === "completed" && item.attempt_number < feedback.attempt_number)
    .sort((a, b) => b.attempt_number - a.attempt_number)[0];
  if (!previous) {
    section.classList.add("hidden");
    return;
  }
  const priorFeedback = await api("/api/sessions/" + encodeURIComponent(previous.id) + "/feedback");
  section.classList.remove("hidden");
  $("#comparison-note").textContent = "Attempt " + previous.attempt_number + " compared with attempt " + feedback.attempt_number + ". Status labels describe checklist signals, not a validated measure of improvement.";
  const oldMap = new Map(priorFeedback.rubric_feedback.map((item) => [item.criterion_id, item]));
  const table = document.createElement("table");
  table.className = "comparison-table";
  const thead = document.createElement("thead");
  const header = document.createElement("tr");
  for (const label of ["Checklist", "Attempt " + previous.attempt_number, "Attempt " + feedback.attempt_number]) {
    const th = document.createElement("th");
    th.textContent = label;
    header.append(th);
  }
  thead.append(header);
  const tbody = document.createElement("tbody");
  for (const current of feedback.rubric_feedback) {
    const old = oldMap.get(current.criterion_id);
    const tr = document.createElement("tr");
    for (const value of [current.label, old ? old.status.replaceAll("_", " ") : "—", current.status.replaceAll("_", " ")]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    tbody.append(tr);
  }
  table.append(thead, tbody);
  $("#comparison-content").replaceChildren(table);
}

async function showFeedback(sessionId) {
  try {
    const feedback = await api("/api/sessions/" + encodeURIComponent(sessionId) + "/feedback");
    activeSession = await api("/api/sessions/" + encodeURIComponent(sessionId));
    renderFeedback(feedback);
    await renderComparison(feedback);
    showView("feedback-view");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function cancelPractice() {
  if (!activeSession || busy) return;
  if (!window.confirm("End this session? Your saved answers will remain in local history.")) return;
  buttonBusy(true);
  try {
    await api("/api/sessions/" + encodeURIComponent(activeSession.id) + "/cancel", { method: "POST" });
    activeSession = null;
    showView("home-view");
    setStatus("Session ended. Its saved answers remain in local history.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    buttonBusy(false);
  }
}

async function retryPractice() {
  if (!activeSession || busy) return;
  buttonBusy(true);
  try {
    const session = await api("/api/sessions/" + encodeURIComponent(activeSession.id) + "/retry", { method: "POST" });
    renderQuestion(session);
    showView("practice-view");
    $("#answer-form").classList.remove("hidden");
    $("#answer-input").focus();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    buttonBusy(false);
  }
}

async function deleteSession(sessionId) {
  if (!window.confirm("Permanently delete this session and its saved answers from this local database? This cannot be undone.")) return;
  try {
    await api("/api/sessions/" + encodeURIComponent(sessionId), { method: "DELETE" });
    activeSession = null;
    showView("history-view");
    await loadHistory();
    setStatus("Session and its answers were deleted from local storage.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function loadHistory() {
  const target = $("#history-list");
  target.replaceChildren();
  try {
    const result = await api("/api/sessions");
    if (!result.sessions.length) {
      const empty = document.createElement("p");
      empty.className = "history-empty";
      empty.textContent = "No saved practice sessions yet. Start the first one when you are ready.";
      target.append(empty);
      return;
    }
    for (const session of result.sessions) {
      const item = document.createElement("article");
      item.className = "history-item";
      const detail = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = session.scenario_id.replaceAll("-", " ") + " · attempt " + session.attempt_number;
      const meta = document.createElement("p");
      meta.textContent = session.status.replaceAll("_", " ") + " · " + new Date(session.created_at).toLocaleString() + " · scenario " + session.scenario_version;
      detail.append(title, meta);
      const actions = document.createElement("div");
      actions.className = "history-actions";
      if (session.status === "completed") {
        const open = document.createElement("button");
        open.type = "button";
        open.className = "button button-secondary";
        open.textContent = "Review";
        open.addEventListener("click", () => showFeedback(session.id));
        actions.append(open);
      } else if (session.status === "in_progress") {
        const resume = document.createElement("button");
        resume.type = "button";
        resume.className = "button button-secondary";
        resume.textContent = "Resume";
        resume.addEventListener("click", async () => {
          try {
            const loaded = await api("/api/sessions/" + encodeURIComponent(session.id));
            renderQuestion(loaded);
            showView("practice-view");
          } catch (error) { setStatus(error.message, true); }
        });
        actions.append(resume);
      }
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "button button-quiet";
      remove.textContent = "Delete";
      remove.addEventListener("click", () => deleteSession(session.id));
      actions.append(remove);
      item.append(detail, actions);
      target.append(item);
    }
  } catch (error) {
    setStatus(error.message, true);
  }
}

$("#profile-edit-toggle").addEventListener("click", () => {
  setProfileFormOpen($("#profile-form").classList.contains("hidden"));
});
$("#profile-cancel").addEventListener("click", async () => {
  if (profileConfigured) await loadProfile();
  else $("#profile-form").classList.add("hidden");
});
$("#profile-form").addEventListener("submit", saveProfile);
$("#start-button").addEventListener("click", startPractice);
$("#answer-form").addEventListener("submit", (event) => {
  event.preventDefault();
  submitCurrentAnswer($("#answer-input").value);
});
$("#skip-button").addEventListener("click", () => submitCurrentAnswer(""));
$("#cancel-button").addEventListener("click", cancelPractice);
$("#retry-button").addEventListener("click", retryPractice);
$("#delete-session-button").addEventListener("click", () => { if (activeSession) deleteSession(activeSession.id); });
$("#back-home-button").addEventListener("click", () => { activeSession = null; showView("home-view"); });
$("#history-toggle").addEventListener("click", async () => { await loadHistory(); showView("history-view"); });
$("#history-home-button").addEventListener("click", () => showView("home-view"));
$("#answer-input").addEventListener("input", () => { $("#answer-count").textContent = $("#answer-input").value.length + " / 6000"; });

window.PreppedVoice?.init();
loadStarterData();
loadProfile();
