(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const state = { studios: [], selected: null, session: null, recorder: null, stream: null, chunks: [], timer: null, audioUrl: null, audio: null, stt: null };
  const viewIds = ["home-view", "practice-view", "feedback-view", "history-view", "learning-view", "career-view"];
  async function api(url, options = {}) {
    const response = await fetch(url, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
    if (response.status === 204) return null;
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Career request failed.");
    return body;
  }
  function status(message, error = false) {
    $("#career-status").textContent = message;
    $("#career-status").classList.toggle("error", error);
  }
  function showCareer() {
    stopRecording(true);
    window.PreppedVoice?.stopAll();
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "career-view");
    $("#career-toggle")?.setAttribute("aria-expanded", "true");
    $("#learning-toggle")?.setAttribute("aria-expanded", "false");
    window.scrollTo({ top: 0, behavior: "smooth" });
    loadWorkspace();
  }
  function showHome() {
    stopRecording(true);
    if (state.audio) state.audio.pause();
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "home-view");
    $("#career-toggle")?.setAttribute("aria-expanded", "false");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function make(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined && text !== null) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  async function loadWorkspace() {
    try {
      const [catalog, history] = await Promise.all([api("/api/career/studios"), api("/api/career/sessions")]);
      state.studios = catalog.studios;
      renderStudios();
      renderHistory(history.sessions);
      status("Three interview studios · local practice");
    } catch (error) { status(error.message, true); }
  }
  function renderStudios() {
    const list = $("#career-studio-list");
    list.replaceChildren();
    for (const studio of state.studios) {
      const card = make("article", null, "career-studio-card");
      card.append(make("span", studio.category.toUpperCase(), "meta-label"));
      card.append(make("h3", studio.title));
      card.append(make("p", studio.description, "section-help"));
      const meta = make("p", studio.estimated_minutes + " min · " + studio.question_count + " main questions", "career-studio-meta");
      card.append(meta);
      const skills = make("p", studio.skills.join(" · "), "career-studio-skills");
      card.append(skills);
      const button = make("button", "Choose studio →", "button button-secondary");
      button.type = "button";
      button.addEventListener("click", () => selectStudio(studio));
      card.append(button);
      list.append(card);
    }
  }
  function selectStudio(studio) {
    state.selected = studio;
    $("#career-selected-title").textContent = studio.title;
    $("#career-selected-description").textContent = studio.description;
    $("#career-setup").classList.remove("hidden");
    $("#career-active").classList.add("hidden");
    $("#career-review").classList.add("hidden");
    $("#career-setup").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  async function startInterview() {
    if (!state.selected) return;
    try {
      state.session = await api("/api/career/sessions", { method: "POST", body: JSON.stringify({ studio_id: state.selected.id, difficulty: $("#career-difficulty").value }) });
      $("#career-setup").classList.add("hidden");
      $("#career-review").classList.add("hidden");
      $("#career-active").classList.remove("hidden");
      renderPrompt();
      status("Interview in progress");
    } catch (error) { status(error.message, true); }
  }
  function renderPrompt() {
    const prompt = state.session?.current_prompt;
    if (!prompt) return;
    stopRecording(true);
    if (state.audio) state.audio.pause();
    $("#career-prompt-title").textContent = prompt.prompt;
    const primary = prompt.turn_type === "primary";
    const current = state.session.answered_primary_count + (primary ? 1 : 0);
    $("#career-turn-label").textContent = primary ? "MAIN QUESTION " + current : "FOLLOW-UP · QUESTION " + state.session.answered_primary_count;
    $("#career-progress").textContent = "Main question " + Math.min(current, state.session.primary_question_count) + " of " + state.session.primary_question_count;
    $("#career-answer").value = "";
    $("#career-answer-error").textContent = "";
    $("#career-voice-status").textContent = "Speak or type. Review and edit any transcript before submitting.";
    $("#career-answer").focus();
  }
  async function submitAnswer() {
    const answer = $("#career-answer").value.trim();
    if (!answer) { $("#career-answer-error").textContent = "Write or transcribe an answer before continuing."; return; }
    $("#career-submit").disabled = true;
    try {
      state.session = await api("/api/career/sessions/" + state.session.id + "/answers", { method: "POST", body: JSON.stringify({ answer_text: answer }) });
      if (state.session.status === "completed") {
        const feedback = await api("/api/career/sessions/" + state.session.id + "/feedback");
        renderReview(feedback);
        $("#career-active").classList.add("hidden");
        $("#career-review").classList.remove("hidden");
        await loadHistory();
      } else renderPrompt();
    } catch (error) { $("#career-answer-error").textContent = error.message; }
    finally { $("#career-submit").disabled = false; }
  }
  function renderReview(feedback) {
    $("#career-review-disclaimer").textContent = feedback.disclaimer;
    const notes = $("#career-review-notes");
    notes.replaceChildren();
    for (const note of feedback.notes) {
      const card = make("article", null, "career-review-card");
      card.append(make("span", note.turn_type === "primary" ? "MAIN QUESTION" : "FOLLOW-UP", "meta-label"));
      card.append(make("h4", note.prompt));
      card.append(make("blockquote", "“" + note.answer + "”", "career-answer-quote"));
      for (const check of note.checks) {
        const item = make("div", null, "career-check");
        const heading = make("strong", check.criterion + (check.observed ? " · signal found" : " · consider reviewing"));
        item.append(heading);
        if (check.evidence) item.append(make("p", "Evidence: " + check.evidence, "career-evidence"));
        item.append(make("p", check.guidance, "section-help"));
        card.append(item);
      }
      const save = make("button", "Save answer to learning memory", "button button-quiet");
      save.type = "button";
      save.addEventListener("click", () => {
        document.dispatchEvent(new CustomEvent("prepped:memory-save", { detail: {
          item_type: "example",
          front: note.prompt,
          back: note.answer.slice(0, 2000),
          source_type: "career_interview",
          source_id: state.session?.id || "",
          source_title: state.session?.studio_title || "Career interview",
          source_excerpt: note.answer,
        }}));
      });
      card.append(save);
      notes.append(card);
    }
    const steps = $("#career-next-steps");
    steps.replaceChildren(make("strong", "Suggested next steps"));
    const list = make("ul");
    for (const step of feedback.next_steps) list.append(make("li", step));
    steps.append(list);
  }
  async function loadHistory() {
    const result = await api("/api/career/sessions");
    renderHistory(result.sessions);
  }
  function renderHistory(sessions) {
    const list = $("#career-history-list");
    list.replaceChildren();
    if (!sessions.length) { list.append(make("p", "No interview sessions yet. Start with any studio above.", "section-help")); return; }
    for (const session of sessions.slice(0, 12)) {
      const row = make("div", null, "career-history-row");
      const info = make("div");
      info.append(make("strong", session.studio_title));
      info.append(make("p", new Date(session.created_at).toLocaleString() + " · " + session.status.replace("_", " ") + " · attempt " + session.attempt_number, "section-help"));
      row.append(info);
      const open = make("button", "Open", "button button-quiet");
      open.type = "button";
      open.addEventListener("click", () => openSession(session.id));
      row.append(open);
      const remove = make("button", "Delete", "button button-quiet");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!window.confirm("Delete this interview and its answers from this device?")) return;
        try { await api("/api/career/sessions/" + session.id, { method: "DELETE" }); await loadHistory(); }
        catch (error) { status(error.message, true); }
      });
      row.append(remove);
      list.append(row);
    }
  }
  async function openSession(id) {
    try {
      const session = await api("/api/career/sessions/" + id);
      state.session = session;
      state.selected = state.studios.find(item => item.id === session.studio_id) || null;
      $("#career-setup").classList.add("hidden");
      if (session.status === "completed") {
        renderReview(await api("/api/career/sessions/" + id + "/feedback"));
        $("#career-review").classList.remove("hidden");
        $("#career-active").classList.add("hidden");
        $("#career-retry").classList.remove("hidden");
      } else if (session.status === "in_progress") {
        $("#career-active").classList.remove("hidden");
        $("#career-review").classList.add("hidden");
        renderPrompt();
      } else status("This interview was cancelled.");
      $("#career-active").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) { status(error.message, true); }
  }
  async function retryInterview() {
    if (!state.session) return;
    try {
      state.session = await api("/api/career/sessions/" + state.session.id + "/retry", { method: "POST" });
      $("#career-review").classList.add("hidden");
      $("#career-active").classList.remove("hidden");
      renderPrompt();
      await loadHistory();
    } catch (error) { status(error.message, true); }
  }
  function stopPrompt() {
    if (state.audio) {
      state.audio.pause();
      state.audio.currentTime = 0;
    }
    $("#career-voice-status").textContent = "Prompt playback stopped.";
  }
  async function playPrompt() {
    const text = $("#career-prompt-title").textContent;
    try {
      const response = await fetch("/api/voice/tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || "Local speech playback is unavailable. Read the prompt instead."); }
      const blob = await response.blob();
      if (state.audioUrl) URL.revokeObjectURL(state.audioUrl);
      state.audioUrl = URL.createObjectURL(blob);
      state.audio = new Audio(state.audioUrl);
      state.audio.play().catch(() => { $("#career-voice-status").textContent = "Playback could not start. Read the prompt instead."; });
      $("#career-voice-status").textContent = "Playing the prompt using the configured local voice engine.";
    } catch (error) { $("#career-voice-status").textContent = error.message; }
  }
  async function startRecording() {
    if (state.stt?.engine === "groq-whisper") {
      $("#career-voice-status").textContent = "Remote transcription is enabled: after recording, audio is sent to Groq Whisper. Prepped does not retain the raw recording. Continue only with a non-sensitive answer; text entry is available instead.";
    } else {
      $("#career-voice-status").textContent = "Local speech transcription is selected. Prepped does not retain the raw recording. Text entry is available instead.";
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      $("#career-voice-status").textContent = "Microphone recording is unavailable in this browser. Type your answer instead.";
      return;
    }
    try {
      state.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = {};
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) options.mimeType = "audio/webm;codecs=opus";
      state.recorder = new MediaRecorder(state.stream, options);
      state.chunks = [];
      state.recorder.ondataavailable = event => { if (event.data.size) state.chunks.push(event.data); };
      state.recorder.onstop = transcribeRecording;
      state.recorder.start();
      $("#career-record").disabled = true;
      $("#career-stop-record").disabled = false;
      $("#career-voice-status").textContent = "Recording… up to 60 seconds. Stop when you are ready. Raw audio is not saved by Prepped.";
      state.timer = window.setTimeout(() => stopRecording(false), 60000);
    } catch (error) { releaseStream(); $("#career-voice-status").textContent = (error.message || "Microphone permission was not available.") + " You can type instead."; }
  }
  function releaseStream() {
    if (state.stream) state.stream.getTracks().forEach(track => track.stop());
    state.stream = null;
  }
  function stopRecording(discard = false) {
    if (state.timer) clearTimeout(state.timer);
    state.timer = null;
    if (!state.recorder) { releaseStream(); return; }
    const recorder = state.recorder;
    state.recorder = null;
    releaseStream();
    if (discard) { state.chunks = []; recorder.onstop = null; }
    if (recorder.state !== "inactive") recorder.stop();
    $("#career-record").disabled = false;
    $("#career-stop-record").disabled = true;
  }
  async function transcribeRecording() {
    const chunks = state.chunks;
    state.chunks = [];
    const blob = new Blob(chunks, { type: chunks[0]?.type || "audio/webm" });
    if (!blob.size) { $("#career-voice-status").textContent = "No audio captured. Type your answer instead."; return; }
    $("#career-voice-status").textContent = "Transcribing… review and edit the text before submitting.";
    try {
      const response = await fetch("/api/voice/transcribe", { method: "POST", headers: { "Content-Type": blob.type }, body: blob });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || "Transcription failed.");
      const field = $("#career-answer");
      field.value = (field.value.trim() ? field.value.trim() + "\n" : "") + String(body.text || "").trim();
      $("#career-voice-status").textContent = "Transcript added. Edit recognition errors before submitting.";
    } catch (error) { $("#career-voice-status").textContent = error.message + " You can type your answer instead."; }
  }
  async function refreshVoiceStatus() {
    try {
      const result = await api("/api/voice/status");
      state.stt = result.stt || null;
      const detail = result.stt?.detail || "Text answers are available.";
      $("#career-voice-status").textContent = detail + " Transcript text can be edited before submission.";
    } catch (_) { /* text entry remains available */ }
  }
  function init() {
    $("#career-toggle").addEventListener("click", showCareer);
    $("#career-home").addEventListener("click", showHome);
    $("#career-start").addEventListener("click", startInterview);
    $("#career-submit").addEventListener("click", submitAnswer);
    $("#career-speak").addEventListener("click", playPrompt);
    $("#career-replay").addEventListener("click", playPrompt);
    $("#career-stop-speak").addEventListener("click", stopPrompt);
    $("#career-record").addEventListener("click", startRecording);
    $("#career-stop-record").addEventListener("click", () => stopRecording(false));
    $("#career-exit").addEventListener("click", async () => {
      if (state.session?.status === "in_progress" && window.confirm("Leave this interview? Your saved answers remain in history and you can resume later.")) {
        stopRecording(true); $("#career-active").classList.add("hidden"); status("Interview saved. Resume it from Recent interview practice.");
        await loadHistory();
      }
    });
    $("#career-back").addEventListener("click", () => {
      $("#career-review").classList.add("hidden"); $("#career-setup").classList.remove("hidden"); $("#career-studio-list").scrollIntoView({ behavior: "smooth" });
    });
    $("#career-retry").addEventListener("click", retryInterview);
    $("#career-refresh").addEventListener("click", loadHistory);
    window.addEventListener("beforeunload", () => { stopRecording(true); if (state.audio) state.audio.pause(); if (state.audioUrl) URL.revokeObjectURL(state.audioUrl); });
    refreshVoiceStatus();
  }
  document.addEventListener("DOMContentLoaded", init);
})();