/* Prepped Packs A–D Controller */
(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  async function api(url, options = {}) {
    const res = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    if (res.status === 204) return null;
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(typeof body.detail === "string" ? body.detail : "The request could not be completed.");
    }
    return body;
  }

  /* 1. Pack B3 & B5: Local Preferences */
  const prefs = { ttsSpeed: 1.0, theme: "light", textSize: "normal", ephemeralAudioReplay: true };
  window.PreppedPrefs = prefs;

  function applyPreferencesToDocument() {
    const root = document.documentElement;
    let effectiveTheme = prefs.theme;
    if (effectiveTheme === "system") {
      effectiveTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    root.dataset.theme = effectiveTheme;
    root.dataset.textSize = prefs.textSize;
    if ($("#pref-tts-speed")) $("#pref-tts-speed").value = String(prefs.ttsSpeed);
    if ($("#pref-tts-speed-label")) $("#pref-tts-speed-label").textContent = Number(prefs.ttsSpeed).toFixed(2).replace(/0$/, "") + "×";
    if ($("#pref-theme")) $("#pref-theme").value = prefs.theme;
    if ($("#pref-text-size")) $("#pref-text-size").value = prefs.textSize;
    if ($("#pref-ephemeral-replay")) $("#pref-ephemeral-replay").checked = prefs.ephemeralAudioReplay;
  }

  async function loadPreferences() {
    try {
      const data = await api("/api/preferences");
      const p = data.preferences || {};
      prefs.ttsSpeed = Number(p.tts_speed || 1.0);
      prefs.theme = p.theme || "light";
      prefs.textSize = p.text_size || "normal";
      prefs.ephemeralAudioReplay = p.ephemeral_audio_replay !== false;
      applyPreferencesToDocument();
    } catch {
      applyPreferencesToDocument();
    }
  }

  $("#pref-tts-speed")?.addEventListener("input", (e) => {
    const val = Number(e.target.value || 1.0);
    if ($("#pref-tts-speed-label")) $("#pref-tts-speed-label").textContent = val.toFixed(2).replace(/0$/, "") + "×";
  });

  $("#preferences-save-btn")?.addEventListener("click", async () => {
    const status = $("#preferences-status");
    const payload = {
      tts_speed: Number($("#pref-tts-speed")?.value || 1.0),
      theme: $("#pref-theme")?.value || "light",
      text_size: $("#pref-text-size")?.value || "normal",
      ephemeral_audio_replay: Boolean($("#pref-ephemeral-replay")?.checked),
    };
    try {
      const data = await api("/api/preferences", { method: "PUT", body: JSON.stringify(payload) });
      const p = data.preferences;
      prefs.ttsSpeed = Number(p.tts_speed);
      prefs.theme = p.theme;
      prefs.textSize = p.text_size;
      prefs.ephemeralAudioReplay = p.ephemeral_audio_replay;
      applyPreferencesToDocument();
      if (!prefs.ephemeralAudioReplay) window.PreppedVoice?.clearEphemeralReplay?.();
      if (status) { status.textContent = "Preferences saved locally"; status.classList.remove("error"); }
      window.PreppedToast?.("Preferences saved on this device.");
    } catch (err) {
      if (status) { status.textContent = err.message; status.classList.add("error"); }
    }
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => {
    if (prefs.theme === "system") applyPreferencesToDocument();
  });

  /* 2. Pack B2: Safe Keyboard Shortcuts */
  $("#shortcuts-open-btn")?.addEventListener("click", (e) => {
    window.PreppedUI?.openModal?.("shortcuts-modal", e.currentTarget);
  });

  let gPrefixUntil = 0;
  function isEditableTarget(el) {
    if (!el) return false;
    const tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
  }

  document.addEventListener("keydown", (e) => {
    const anyModalOpen = Boolean($(".modal-backdrop:not(.hidden)"));
    const typing = isEditableTarget(document.activeElement);

    if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && !anyModalOpen) {
      if (!$("#practice-view")?.classList.contains("hidden")) { e.preventDefault(); $("#submit-button")?.click(); return; }
      if (!$("#learning-runner")?.classList.contains("hidden") && !$("#learning-view")?.classList.contains("hidden")) { e.preventDefault(); $("#learning-submit")?.click(); return; }
      if (!$("#mock-active-panel")?.classList.contains("hidden") && !$("#career-view")?.classList.contains("hidden")) { e.preventDefault(); $("#mock-submit-answer-btn")?.click(); return; }
    }

    if (e.altKey && !e.ctrlKey && !e.metaKey && e.key.toLowerCase() === "r" && !anyModalOpen) {
      if (!$("#practice-view")?.classList.contains("hidden")) {
        e.preventDefault();
        const stopBtn = $("#stop-recording-button");
        const recBtn = $("#record-button");
        if (stopBtn && !stopBtn.disabled) stopBtn.click();
        else if (recBtn && !recBtn.disabled) recBtn.click();
        return;
      }
    }

    if (typing || anyModalOpen || e.ctrlKey || e.metaKey || e.altKey) return;

    if (e.key === "?") {
      e.preventDefault();
      window.PreppedUI?.openModal?.("shortcuts-modal", $("#shortcuts-open-btn"));
      return;
    }

    const now = Date.now();
    const k = e.key.toLowerCase();
    if (k === "g") { gPrefixUntil = now + 900; return; }
    if (now <= gPrefixUntil) {
      gPrefixUntil = 0;
      const map = { t: "#home-toggle", p: "#practice-toggle", l: "#learning-toggle", c: "#career-toggle", m: "#memory-toggle", r: "#progress-toggle", h: "#history-toggle" };
      if (map[k]) { e.preventDefault(); $(map[k])?.click(); return; }
    }

    if (!$("#memory-view")?.classList.contains("hidden")) {
      if (e.key === " ") {
        const showBtn = Array.from($$("#memory-review button")).find((b) => b.textContent.trim() === "Show answer");
        if (showBtn) { e.preventDefault(); showBtn.click(); return; }
      }
      if (["1", "2", "3", "4"].includes(e.key)) {
        const ratingBtns = $$("#memory-review .memory-ratings button");
        const idx = Number(e.key) - 1;
        if (ratingBtns[idx]) { e.preventDefault(); ratingBtns[idx].click(); }
      }
    }
  });

  /* 3. Pack D: Optional Cloud AI Settings & Consent Modal */
  let aiConfig = null;
  let pendingAiTask = null;

  async function loadAiConfig() {
    try {
      const data = await api("/api/ai/config");
      aiConfig = data.ai;
      if ($("#ai-enabled-toggle")) $("#ai-enabled-toggle").checked = Boolean(aiConfig.enabled);
      if ($("#ai-provider-select")) $("#ai-provider-select").value = aiConfig.provider || "none";
      if ($("#ai-model-input")) $("#ai-model-input").value = aiConfig.model || "";
      if ($("#ai-daily-limit")) $("#ai-daily-limit").value = String(aiConfig.daily_request_limit || 25);
      if ($("#ai-key-status")) {
        const p = aiConfig.provider;
        if (p === "none") $("#ai-key-status").textContent = "Offline mode active. Select Gemini or Groq to configure an optional key.";
        else if (aiConfig.has_api_key) $("#ai-key-status").textContent = "API key configured (" + aiConfig.key_source + "). Never displayed in frontend.";
        else $("#ai-key-status").textContent = "No API key found for " + p + ". Paste one above or set environment variable.";
      }
      if ($("#ai-config-status")) {
        $("#ai-config-status").textContent = aiConfig.enabled && aiConfig.provider !== "none"
          ? "Optional Cloud AI ready (" + aiConfig.provider + " · " + aiConfig.requests_today + "/" + aiConfig.daily_request_limit + " today)"
          : "Offline mode active";
      }
    } catch {}
  }

  $("#ai-provider-select")?.addEventListener("change", () => {
    const provider = $("#ai-provider-select").value;
    const defaultModel = aiConfig?.providers?.[provider]?.default_model || "";
    if ($("#ai-model-input") && defaultModel) $("#ai-model-input").value = defaultModel;
  });

  $("#ai-save-config-btn")?.addEventListener("click", async () => {
    const status = $("#ai-config-status");
    try {
      const payload = {
        enabled: Boolean($("#ai-enabled-toggle")?.checked),
        provider: $("#ai-provider-select")?.value || "none",
        model: ($("#ai-model-input")?.value || "").trim(),
        consent_acknowledged: true,
        daily_request_limit: Number($("#ai-daily-limit")?.value || 25),
      };
      await api("/api/ai/config", { method: "PUT", body: JSON.stringify(payload) });
      await loadAiConfig();
      window.PreppedToast?.("Cloud AI settings saved locally.");
    } catch (err) {
      if (status) { status.textContent = err.message; status.classList.add("error"); }
    }
  });

  $("#ai-save-key-btn")?.addEventListener("click", async () => {
    const provider = $("#ai-provider-select")?.value || "none";
    const keyInput = $("#ai-api-key-input");
    const status = $("#ai-key-status");
    if (!["gemini", "groq"].includes(provider)) {
      if (status) status.textContent = "Choose Gemini or Groq before saving an API key.";
      return;
    }
    try {
      const keyVal = keyInput?.value || "";
      await api("/api/ai/key", { method: "POST", body: JSON.stringify({ provider, api_key: keyVal }) });
      if (keyInput) keyInput.value = "";
      await loadAiConfig();
      window.PreppedToast?.(keyVal.trim() ? "API key stored privately on this device (0600)." : "Saved API key cleared.");
    } catch (err) {
      if (status) status.textContent = err.message;
    }
  });

  $("#ai-test-btn")?.addEventListener("click", async () => {
    const status = $("#ai-config-status");
    if (status) { status.textContent = "Testing connection…"; status.classList.remove("error"); }
    try {
      const res = await api("/api/ai/test", { method: "POST" });
      if (status) status.textContent = "Verified: " + res.provider + " (" + res.model + ")";
    } catch (err) {
      if (status) { status.textContent = err.message; status.classList.add("error"); }
    }
  });

  function openAiConsentModal({ task, content, context, outputEl, onSuccess }) {
    if (!aiConfig || !aiConfig.enabled || aiConfig.provider === "none") {
      window.PreppedToast?.("Optional Cloud AI is off. Enable it in Profile to use cloud coaching.");
      return;
    }
    pendingAiTask = { task, context, outputEl, onSuccess };
    const providerLabel = aiConfig.provider === "gemini" ? "Google Gemini" : "Groq";
    if ($("#ai-consent-provider-label")) {
      $("#ai-consent-provider-label").textContent = "Destination: " + providerLabel + " (" + (aiConfig.model || "default") + ")";
    }
    if ($("#ai-consent-preview")) $("#ai-consent-preview").value = String(content || "").slice(0, 6000);
    if ($("#ai-consent-checkbox")) $("#ai-consent-checkbox").checked = false;
    if ($("#ai-consent-error")) $("#ai-consent-error").textContent = "";
    window.PreppedUI?.openModal?.("ai-consent-modal");
  }
  window.PreppedRequestAiConsent = openAiConsentModal;

  $("#ai-consent-send-btn")?.addEventListener("click", async () => {
    const err = $("#ai-consent-error");
    if (!$("#ai-consent-checkbox")?.checked) {
      if (err) err.textContent = "Tick the consent box before sending text outside this device.";
      return;
    }
    const text = ($("#ai-consent-preview")?.value || "").trim();
    if (text.length < 5) {
      if (err) err.textContent = "Enter at least 5 characters to send.";
      return;
    }
    const btn = $("#ai-consent-send-btn");
    if (btn) { btn.disabled = true; btn.textContent = "Requesting…"; }
    if (err) err.textContent = "";
    try {
      const res = await api("/api/ai/assist", {
        method: "POST",
        body: JSON.stringify({
          task: pendingAiTask.task,
          content: text,
          context: pendingAiTask.context || "",
          consent_confirmed: true,
        }),
      });
      window.PreppedUI?.closeModal?.("ai-consent-modal");
      if (pendingAiTask.outputEl) {
        pendingAiTask.outputEl.textContent = `Cloud AI (${res.provider} · ${res.model})\n\n${res.response}\n\n— ${res.note}`;
        pendingAiTask.outputEl.classList.remove("hidden");
      }
      if (typeof pendingAiTask.onSuccess === "function") pendingAiTask.onSuccess(res);
      await loadAiConfig();
    } catch (error) {
      if (err) err.textContent = error.message;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Send with consent"; }
    }
  });

  $("#feedback-ai-assist")?.addEventListener("click", () => {
    const fb = window.PreppedApp?.getActiveFeedback?.();
    if (!fb) return;
    const combined = (fb.question_feedback || [])
      .filter((q) => (q.answer_text || "").trim())
      .map((q) => `Q: ${q.prompt}\nA: ${q.answer_text}`)
      .join("\n\n");
    if (!combined) { window.PreppedToast?.("Submit at least one non-empty answer first."); return; }
    openAiConsentModal({
      task: "transcript_feedback",
      content: combined,
      context: "Project explanation practice · Attempt " + fb.attempt_number,
      outputEl: $("#feedback-ai-output"),
    });
  });

  /* 4. Pack C: Project Studio, Resume Prep, Timed Mock, Debrief & Warm-up */
  let savedProjects = [];
  let extractedResumeQuestions = [];
  let activeMock = null;
  let mockTimerId = null;
  let mockStartedAt = 0;
  let mockRecorder = null;
  let mockStream = null;
  let mockChunks = [];
  let mockRecStart = 0;
  let mockLastSpeakingSec = null;
  let lastDebrief = null;

  function formatMmSs(totalSec) {
    const safe = Math.max(0, Math.floor(totalSec));
    return String(Math.floor(safe / 60)).padStart(2, "0") + ":" + String(safe % 60).padStart(2, "0");
  }

  function stopMockTimer() {
    if (mockTimerId) { window.clearInterval(mockTimerId); mockTimerId = null; }
  }

  function stopMockRecording(discard = true) {
    if (mockRecorder && mockRecorder.state !== "inactive") {
      if (discard) mockChunks = [];
      try { mockRecorder.stop(); } catch {}
    }
    if (mockStream) {
      for (const track of mockStream.getTracks()) track.stop();
      mockStream = null;
    }
    mockRecorder = null;
    if ($("#mock-record-btn")) $("#mock-record-btn").disabled = false;
    if ($("#mock-stop-record-btn")) $("#mock-stop-record-btn").disabled = true;
  }

  async function loadProjects() {
    const list = $("#project-studio-list");
    if (!list) return;
    try {
      const data = await api("/api/career/projects");
      savedProjects = data.projects || [];
      list.replaceChildren();
      if (!savedProjects.length) {
        const empty = document.createElement("p");
        empty.className = "section-help";
        empty.textContent = "No projects saved yet. Fill in the framework on the left to build your first personal project studio.";
        list.append(empty);
        return;
      }
      for (const proj of savedProjects) {
        const card = document.createElement("article");
        card.className = "career-project-item";
        const title = document.createElement("strong");
        title.textContent = proj.title;
        const meta = document.createElement("p");
        meta.className = "section-help";
        meta.textContent = [proj.personal_role, proj.tech_stack].filter(Boolean).join(" · ") || "Saved locally";
        const actions = document.createElement("div");
        actions.className = "career-project-actions";
        const practiceBtn = document.createElement("button");
        practiceBtn.type = "button";
        practiceBtn.className = "button button-primary";
        practiceBtn.textContent = "Practise project →";
        practiceBtn.addEventListener("click", () => startMockSession({ mode: "project_studio", project_id: proj.id, time_limit_seconds: 600 }));
        const editBtn = document.createElement("button");
        editBtn.type = "button";
        editBtn.className = "button button-secondary";
        editBtn.textContent = "Edit";
        editBtn.addEventListener("click", () => {
          $("#proj-edit-id").value = proj.id;
          $("#proj-title").value = proj.title || "";
          $("#proj-role").value = proj.personal_role || "";
          $("#proj-stack").value = proj.tech_stack || "";
          $("#proj-problem").value = proj.problem || "";
          $("#proj-approach").value = proj.approach || "";
          $("#proj-implementation").value = proj.implementation || "";
          $("#proj-decisions").value = proj.decisions_tradeoffs || "";
          $("#proj-outcome").value = proj.outcome || "";
          $("#proj-learning").value = proj.learning || "";
          $("#proj-title").focus();
        });
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "button button-quiet";
        delBtn.textContent = "Delete";
        delBtn.addEventListener("click", async () => {
          if (!window.confirm("Delete this project studio from this device?")) return;
          await api("/api/career/projects/" + encodeURIComponent(proj.id), { method: "DELETE" });
          await loadProjects();
        });
        actions.append(practiceBtn, editBtn, delBtn);
        card.append(title, meta, actions);
        list.append(card);
      }
    } catch (err) {
      list.textContent = err.message;
    }
  }

  $("#proj-reset-btn")?.addEventListener("click", () => {
    $("#project-studio-form")?.reset();
    if ($("#proj-edit-id")) $("#proj-edit-id").value = "";
  });

  $("#project-studio-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = $("#proj-status");
    const editId = ($("#proj-edit-id")?.value || "").trim();
    const payload = {
      title: $("#proj-title").value,
      personal_role: $("#proj-role").value,
      tech_stack: $("#proj-stack").value,
      problem: $("#proj-problem").value,
      approach: $("#proj-approach").value,
      implementation: $("#proj-implementation").value,
      decisions_tradeoffs: $("#proj-decisions").value,
      outcome: $("#proj-outcome").value,
      learning: $("#proj-learning").value,
      source_kind: "project",
    };
    try {
      if (editId) await api("/api/career/projects/" + encodeURIComponent(editId), { method: "PUT", body: JSON.stringify(payload) });
      else await api("/api/career/projects", { method: "POST", body: JSON.stringify(payload) });
      $("#project-studio-form").reset();
      if ($("#proj-edit-id")) $("#proj-edit-id").value = "";
      if (status) { status.textContent = "Project saved locally with tailored interview prompts."; status.classList.remove("error"); }
      await loadProjects();
    } catch (err) {
      if (status) { status.textContent = err.message; status.classList.add("error"); }
    }
  });

  $("#resume-file-input")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    const status = $("#resume-status");
    if (!file) return;
    if (!/\.(txt|md)$/i.test(file.name)) {
      if (status) { status.textContent = "Only plain text (.txt) and Markdown (.md) files are supported. You can paste text from a PDF below."; status.classList.add("error"); }
      e.target.value = "";
      return;
    }
    if (file.size > 100 * 1024) {
      if (status) { status.textContent = "File exceeds the 100 KB limit. Paste the relevant project bullets directly."; status.classList.add("error"); }
      e.target.value = "";
      return;
    }
    try {
      const text = await file.text();
      $("#resume-text-input").value = text.slice(0, 50000);
      if (status) { status.textContent = "Loaded " + file.name + " locally. Click Extract topics & questions."; status.classList.remove("error"); }
    } catch {
      if (status) { status.textContent = "Could not read the selected file."; status.classList.add("error"); }
    }
  });

  $("#resume-prep-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = $("#resume-status");
    try {
      const res = await api("/api/career/resume/parse", {
        method: "POST",
        body: JSON.stringify({
          resume_text: $("#resume-text-input").value,
          save_as_project: Boolean($("#resume-save-project")?.checked),
        }),
      });
      extractedResumeQuestions = res.questions || [];
      const chips = $("#resume-skills-chips");
      if (chips) {
        chips.replaceChildren();
        for (const skill of res.detected_skills || []) {
          const sp = document.createElement("span");
          sp.className = "chip t";
          sp.textContent = skill;
          chips.append(sp);
        }
      }
      const qList = $("#resume-questions-list");
      if (qList) {
        qList.replaceChildren();
        for (const q of extractedResumeQuestions) {
          const item = document.createElement("article");
          item.className = "career-project-item";
          const topic = document.createElement("span"); topic.className = "chip"; topic.textContent = q.topic;
          const p = document.createElement("strong"); p.textContent = q.prompt;
          const tip = document.createElement("small"); tip.className = "section-help"; tip.textContent = q.tip;
          item.append(topic, p, tip);
          qList.append(item);
        }
      }
      $("#resume-start-mock-btn")?.classList.toggle("hidden", !extractedResumeQuestions.length);
      $("#resume-ai-questions-btn")?.classList.toggle("hidden", !extractedResumeQuestions.length);
      if (status) { status.textContent = res.note; status.classList.remove("error"); }
      if (res.saved_project) await loadProjects();
    } catch (err) {
      if (status) { status.textContent = err.message; status.classList.add("error"); }
    }
  });

  $("#resume-start-mock-btn")?.addEventListener("click", () => {
    if (!extractedResumeQuestions.length) return;
    startMockSession({ mode: "resume_prep", title: "Resume Practice Round", custom_questions: extractedResumeQuestions, time_limit_seconds: 600 });
  });

  $("#resume-ai-questions-btn")?.addEventListener("click", () => {
    const content = ($("#resume-text-input")?.value || "").trim();
    if (!content) return;
    openAiConsentModal({
      task: "generate_questions",
      content,
      context: "Tailored placement interview questions",
      onSuccess: (res) => {
        const lines = String(res.response || "").split("\n").map((l) => l.replace(/^\s*\d+[\).\-\s]+/, "").trim()).filter((l) => l.length > 12);
        if (lines.length) {
          extractedResumeQuestions = lines.slice(0, 5).map((prompt, idx) => ({
            id: "ai_resume_" + (idx + 1), topic: "AI-assisted prompt", prompt, tip: "Answer with one real example from your work.",
          }));
          window.PreppedToast?.("Updated practice prompts with Cloud AI suggestions.");
        }
      },
    });
  });

  function showMockPanel(which) {
    $("#mock-setup-panel")?.classList.toggle("hidden", which !== "setup");
    $("#mock-active-panel")?.classList.toggle("hidden", which !== "active");
    $("#mock-debrief-panel")?.classList.toggle("hidden", which !== "debrief");
  }

  async function loadMockHistory() {
    const target = $("#mock-history-list");
    if (!target) return;
    try {
      const data = await api("/api/career/mocks");
      const mocks = data.mocks || [];
      target.replaceChildren();
      if (!mocks.length) {
        const p = document.createElement("p");
        p.className = "section-help";
        p.textContent = "No timed mocks or warm-ups yet.";
        target.append(p);
        return;
      }
      for (const m of mocks.slice(0, 8)) {
        const row = document.createElement("div");
        row.className = "career-project-item";
        const strong = document.createElement("strong");
        strong.textContent = m.title + " (" + m.answered_count + "/" + m.question_count + " answered)";
        const meta = document.createElement("p");
        meta.className = "section-help";
        meta.textContent = m.status.replace("_", " ") + " · " + formatMmSs(m.elapsed_seconds) + " used · " + new Date(m.created_at).toLocaleString();
        const actions = document.createElement("div");
        actions.className = "career-project-actions";
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "button button-secondary";
        openBtn.textContent = m.status === "completed" ? "View debrief" : "Resume";
        openBtn.addEventListener("click", async () => {
          if (m.status === "completed") {
            const d = await api("/api/career/mocks/" + encodeURIComponent(m.id) + "/debrief");
            renderMockDebrief(d.debrief);
          } else {
            activeMock = m;
            renderActiveMock();
          }
        });
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "button button-quiet";
        delBtn.textContent = "Delete";
        delBtn.addEventListener("click", async () => {
          await api("/api/career/mocks/" + encodeURIComponent(m.id), { method: "DELETE" });
          await loadMockHistory();
        });
        actions.append(openBtn, delBtn);
        row.append(strong, meta, actions);
        target.append(row);
      }
    } catch {}
  }

  function renderActiveMock() {
    if (!activeMock || !activeMock.current_question) return;
    stopMockTimer();
    stopMockRecording(true);
    mockLastSpeakingSec = null;
    showMockPanel("active");
    const q = activeMock.current_question;
    const qNum = activeMock.answered_count + 1;
    $("#mock-active-title").textContent = activeMock.title;
    $("#mock-active-progress").textContent = `Question ${qNum} of ${activeMock.question_count}`;
    $("#mock-question-topic").textContent = (q.topic || "PROMPT").toUpperCase();
    $("#mock-question-prompt").textContent = q.prompt;
    $("#mock-question-tip").textContent = q.tip || "";
    $("#mock-answer-input").value = "";
    $("#mock-error").textContent = "";
    $("#mock-submit-answer-btn").textContent = qNum >= activeMock.question_count ? "Finish & view debrief →" : "Next question →";

    mockStartedAt = Date.now() - (activeMock.elapsed_seconds || 0) * 1000;
    const updateClock = () => {
      const elapsed = Math.floor((Date.now() - mockStartedAt) / 1000);
      const clock = $("#mock-timer-clock");
      if (!clock) return;
      if (activeMock.time_limit_seconds) {
        const rem = Math.max(0, activeMock.time_limit_seconds - elapsed);
        clock.textContent = formatMmSs(rem) + " left";
      } else {
        clock.textContent = formatMmSs(elapsed) + " elapsed";
      }
    };
    updateClock();
    mockTimerId = window.setInterval(updateClock, 1000);
    $("#mock-answer-input").focus();
  }

  function renderMockDebrief(debrief) {
    lastDebrief = debrief;
    stopMockTimer();
    stopMockRecording(true);
    showMockPanel("debrief");
    $("#mock-debrief-title").textContent = debrief.title;
    $("#mock-debrief-disclaimer").textContent = debrief.disclaimer;
    const aiOut = $("#mock-debrief-ai-output");
    if (aiOut) { aiOut.textContent = ""; aiOut.classList.add("hidden"); }

    const metrics = $("#mock-debrief-metrics");
    metrics.replaceChildren();
    const d = debrief.delivery_summary || {};
    for (const [val, lbl] of [
      [debrief.responses_completed + " / " + debrief.total_questions, "Completed responses"],
      [formatMmSs(debrief.elapsed_seconds), "Time used"],
      [d.total_words ?? 0, "Total words"],
      [d.average_wpm != null ? d.average_wpm + " WPM" : "Typed", d.pace_label || "Pace"],
      [d.total_fillers ?? 0, "Detected fillers"],
    ]) {
      const card = document.createElement("div");
      card.className = "delivery-metric-card";
      const s = document.createElement("strong"); s.textContent = String(val);
      const sp = document.createElement("span"); sp.textContent = lbl;
      card.append(s, sp);
      metrics.append(card);
    }

    const fillList = (id, items) => {
      const ul = $(id);
      ul.replaceChildren();
      for (const text of items || []) {
        const li = document.createElement("li"); li.textContent = text; ul.append(li);
      }
    };
    fillList("#mock-debrief-strengths", debrief.strengths);
    fillList("#mock-debrief-improve", debrief.areas_to_improve);

    const qWrap = $("#mock-debrief-questions");
    qWrap.replaceChildren();
    for (const q of debrief.question_reviews || []) {
      const card = document.createElement("article");
      card.className = "feedback-card";
      const h4 = document.createElement("h4");
      h4.textContent = q.topic + " — " + q.prompt;
      card.append(h4);
      if (q.answer_text && window.PreppedRenderTranscriptEvidence) {
        card.append(window.PreppedRenderTranscriptEvidence(q.answer_text, q.speaking_analytics));
      } else {
        const p = document.createElement("p");
        p.className = "section-help";
        p.textContent = q.answer_text || "Skipped / no response submitted.";
        card.append(p);
      }
      qWrap.append(card);
    }
    loadMockHistory();
  }

  async function startMockSession(payload) {
    window.PreppedApp?.showView?.("career-view");
    window.PreppedCareerStage?.("mock");
    try {
      const res = await api("/api/career/mocks", { method: "POST", body: JSON.stringify(payload) });
      activeMock = res.mock;
      renderActiveMock();
    } catch (err) {
      window.PreppedToast?.(err.message);
    }
  }

  $("#mock-start-btn")?.addEventListener("click", () => {
    const limit = Number($("#mock-time-select")?.value || 600);
    startMockSession({ mode: "timed_mock", focus: $("#mock-focus-select")?.value || "mixed", question_count: 5, time_limit_seconds: limit > 0 ? limit : null });
  });
  $("#warmup-start-btn")?.addEventListener("click", () => startMockSession({ mode: "warmup", time_limit_seconds: 300 }));
  $("#dashboard-warmup-button")?.addEventListener("click", () => startMockSession({ mode: "warmup", time_limit_seconds: 300 }));

  $("#mock-submit-answer-btn")?.addEventListener("click", async () => {
    if (!activeMock?.current_question) return;
    stopMockRecording(true);
    const elapsed = Math.floor((Date.now() - mockStartedAt) / 1000);
    try {
      const res = await api("/api/career/mocks/" + encodeURIComponent(activeMock.id) + "/respond", {
        method: "POST",
        body: JSON.stringify({
          question_id: activeMock.current_question.id,
          answer_text: $("#mock-answer-input").value,
          elapsed_seconds: elapsed,
          speaking_duration_seconds: mockLastSpeakingSec,
        }),
      });
      activeMock = res.mock;
      if (res.debrief) renderMockDebrief(res.debrief);
      else renderActiveMock();
    } catch (err) {
      $("#mock-error").textContent = err.message;
    }
  });

  $("#mock-finish-early-btn")?.addEventListener("click", async () => {
    if (!activeMock) return;
    stopMockRecording(true);
    const elapsed = Math.floor((Date.now() - mockStartedAt) / 1000);
    try {
      const res = await api("/api/career/mocks/" + encodeURIComponent(activeMock.id) + "/finish", {
        method: "POST",
        body: JSON.stringify({ elapsed_seconds: elapsed }),
      });
      activeMock = res.mock;
      renderMockDebrief(res.debrief);
    } catch (err) {
      $("#mock-error").textContent = err.message;
    }
  });

  $("#mock-debrief-back-btn")?.addEventListener("click", () => { showMockPanel("setup"); loadMockHistory(); });
  $("#mock-debrief-print-btn")?.addEventListener("click", () => window.print());
  $("#mock-debrief-ai-btn")?.addEventListener("click", () => {
    if (!lastDebrief) return;
    const text = (lastDebrief.question_reviews || []).filter((q) => q.answer_text).map((q) => `Q: ${q.prompt}\nA: ${q.answer_text}`).join("\n\n");
    if (!text) { window.PreppedToast?.("No answers available to review."); return; }
    openAiConsentModal({ task: "interview_feedback", content: text, context: lastDebrief.title, outputEl: $("#mock-debrief-ai-output") });
  });

  $("#mock-tts-btn")?.addEventListener("click", async () => {
    const text = $("#mock-question-prompt")?.textContent?.trim();
    const status = $("#mock-voice-status");
    if (!text) return;
    try {
      const res = await fetch("/api/voice/tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text, speed: Number(prefs.ttsSpeed || 1.0) }) });
      if (!res.ok) throw new Error("Spoken prompt unavailable. Read on screen.");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    } catch (err) {
      if (status) status.textContent = err.message;
    }
  });

  $("#mock-record-btn")?.addEventListener("click", async () => {
    const status = $("#mock-voice-status");
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      if (status) status.textContent = "Recording unavailable in this browser. Type your answer below.";
      return;
    }
    try {
      mockStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mockChunks = [];
      mockRecorder = new MediaRecorder(mockStream);
      mockRecStart = Date.now();
      mockRecorder.ondataavailable = (ev) => { if (ev.data?.size) mockChunks.push(ev.data); };
      mockRecorder.onstop = async () => {
        const durSec = Number(((Date.now() - mockRecStart) / 1000).toFixed(1));
        const blob = new Blob(mockChunks, { type: mockRecorder?.mimeType || "audio/webm" });
        mockChunks = [];
        if (!blob.size) return;
        mockLastSpeakingSec = durSec >= 1 ? durSec : null;
        if (status) status.textContent = "Transcribing… raw audio is not stored.";
        try {
          const res = await fetch("/api/voice/transcribe", { method: "POST", headers: { "Content-Type": blob.type || "application/octet-stream" }, body: blob });
          const data = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(data.detail || "Transcription failed. Type your answer instead.");
          const ta = $("#mock-answer-input");
          if (ta && data.text) ta.value = ta.value.trim() ? ta.value.trim() + "\n" + data.text : data.text;
          if (status) status.textContent = "Transcript added. Edit before submitting.";
        } catch (err) {
          if (status) status.textContent = err.message;
        }
      };
      mockRecorder.start();
      $("#mock-record-btn").disabled = true;
      $("#mock-stop-record-btn").disabled = false;
      if (status) status.textContent = "Recording… click Stop recording when done.";
    } catch {
      if (status) status.textContent = "Microphone permission was denied. Type your answer instead.";
    }
  });

  $("#mock-stop-record-btn")?.addEventListener("click", () => stopMockRecording(false));

  window.addEventListener("prepped:career-stage", (e) => {
    const stage = e.detail?.stage;
    if (stage === "projects") loadProjects();
    if (stage === "mock") { showMockPanel("setup"); loadMockHistory(); }
    if (stage === "warmup") startMockSession({ mode: "warmup", time_limit_seconds: 300 });
  });

  window.addEventListener("prepped:viewchange", (e) => {
    if (e.detail?.view !== "career-view") { stopMockTimer(); stopMockRecording(true); }
    if (e.detail?.view === "profile-view") { loadPreferences(); loadAiConfig(); }
  });

  /* 5. Pack B6: Safe PWA Service Worker Registration */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    });
  }

  loadPreferences();
  loadAiConfig();
})();
