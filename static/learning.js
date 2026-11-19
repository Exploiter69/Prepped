(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const state = { catalog: null, progress: null, attempt: null, busy: false, voiceStatus: null,
    recorder: null, stream: null, chunks: [], recordTimer: null, discardRecording: false, listeningAudio: null, audioUrl: null };
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
    stopLearningRecording(true);
    stopListeningAudio();
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "learning-view");
    $("#global-status")?.classList.add("hidden");
    $("#learning-view").classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
    loadWorkspace();
  }

  function showHome() {
    stopLearningRecording(true);
    stopListeningAudio();
    $("#learning-view").classList.add("hidden");
    $("#global-status")?.classList.remove("hidden");
    for (const id of viewIds) $("#" + id)?.classList.toggle("hidden", id !== "home-view");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function makeButton(label, lessonId, className = "button button-secondary", disabled = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.dataset.lessonId = lessonId;
    button.disabled = disabled;
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

  function renderTracks(tracks, progress) {
    const container = $("#learning-track-list");
    const completed = new Set(progress.completed_lesson_ids || []);
    const titles = Object.fromEntries(tracks.flatMap((track) => track.lessons.map((lesson) => [lesson.id, lesson.title])));
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
        meta.textContent = (completed.has(lesson.id) ? "COMPLETED · " : "") + lesson.exercise_count + " EXERCISES · " + lesson.estimated_minutes + " MIN";
        const missing = (lesson.prerequisites || []).filter((id) => !completed.has(id));
        const prerequisite = document.createElement("p");
        prerequisite.className = "learning-prerequisite";
        prerequisite.textContent = missing.length
          ? "Complete first: " + missing.map((id) => titles[id] || id.replaceAll("-", " ")).join(", ")
          : (completed.has(lesson.id) ? "You can repeat this lesson at any time." : "Ready to start.");
        card.append(meta, title, summary, prerequisite,
          makeButton(completed.has(lesson.id) ? "Practise again" : "Open lesson", lesson.id, "button button-secondary", missing.length > 0));
        list.append(card);
      }
      section.append(heading, description, list);
      container.append(section);
    }
  }

  function renderSkills(skills) {
    const container = $("#learning-skill-list");
    container.replaceChildren();
    for (const skill of skills) {
      const card = document.createElement("article");
      card.className = "learning-skill";
      const heading = document.createElement("h4");
      heading.textContent = skill.title;
      const status = document.createElement("span");
      status.className = "learning-skill-status " + skill.status;
      status.textContent = skill.status;
      const description = document.createElement("p");
      description.textContent = skill.description;
      const progress = document.createElement("p");
      progress.className = "meta-label";
      progress.textContent = skill.completed_lessons + " completed lesson attempts · " + skill.available_lessons + " available lessons";
      card.append(heading, status, description, progress);
      if (skill.outcomes?.length) {
        const list = document.createElement("ul");
        for (const outcome of skill.outcomes) {
          const item = document.createElement("li");
          item.textContent = outcome;
          list.append(item);
        }
        card.append(list);
      }
      container.append(card);
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
      state.voiceStatus = await request("/api/voice/status").catch(() => null);
      state.catalog = catalog;
      state.progress = progress;
      renderRecommendations(catalog.recommendations);
      renderTracks(catalog.tracks, progress);
      renderSkills(progress.skills);
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
    if (exercise.context) {
      const context = document.createElement("p");
      context.className = "learning-context";
      context.textContent = exercise.context;
      $("#learning-exercise").append(context);
    }
    if (exercise.type === "listening") {
      const controls = document.createElement("div");
      controls.className = "learning-listening-controls";
      const play = document.createElement("button");
      play.type = "button";
      play.className = "button button-secondary";
      play.textContent = "Play spoken message";
      play.addEventListener("click", () => playListeningAudio(exercise.audio_text));
      const reveal = document.createElement("button");
      reveal.type = "button";
      reveal.className = "button button-quiet";
      reveal.textContent = "Show text alternative";
      const transcript = document.createElement("p");
      transcript.className = "learning-transcript hidden";
      transcript.textContent = exercise.transcript || exercise.audio_text;
      reveal.setAttribute("aria-expanded", "false");
      reveal.addEventListener("click", () => {
        const open = transcript.classList.toggle("hidden") === false;
        reveal.setAttribute("aria-expanded", String(open));
        reveal.textContent = open ? "Hide text alternative" : "Show text alternative";
      });
      const status = document.createElement("p");
      status.className = "section-help";
      status.textContent = "Audio uses the configured local text-to-speech engine when available. The text alternative is always available.";
      controls.append(play, reveal, transcript, status);
      $("#learning-exercise").append(controls);
    }

    if (["choice", "vocabulary", "listening"].includes(exercise.type)) {
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
      const voice = document.createElement("div");
      voice.className = "learning-voice-controls";
      const privacy = document.createElement("p");
      privacy.className = "section-help";
      const record = document.createElement("button");
      record.type = "button";
      record.className = "button button-secondary";
      record.textContent = "Record spoken response";
      const stop = document.createElement("button");
      stop.type = "button";
      stop.className = "button button-quiet";
      stop.textContent = "Stop recording";
      stop.disabled = true;
      const status = document.createElement("p");
      status.id = "learning-voice-status";
      status.className = "voice-status";
      const available = Boolean(state.voiceStatus?.stt?.available) &&
        Boolean(navigator.mediaDevices?.getUserMedia) && typeof MediaRecorder !== "undefined";
      record.disabled = !available;
      privacy.textContent = state.voiceStatus?.stt?.engine === "groq-whisper"
        ? "Optional voice input sends the recording to Groq for transcription. Prepped does not save raw audio. Review and edit the transcript before submitting."
        : "Optional voice input is transcribed by the configured speech engine. Prepped does not save raw audio. Review and edit the transcript before submitting.";
      status.textContent = available
        ? "You can type or record. Text input always remains available."
        : "Voice input is unavailable in this browser or configuration. Type your response instead.";
      record.addEventListener("click", startLearningRecording);
      stop.addEventListener("click", () => stopLearningRecording(false));
      voice.append(privacy, record, stop, status);
      $("#learning-exercise").append(voice);
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
      } else if (["choice", "vocabulary", "listening"].includes(item.type)) {
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

  async function playListeningAudio(text) {
    stopListeningAudio();
    const controls = $("#learning-exercise");
    const status = controls.querySelector(".learning-listening-controls .section-help");
    try {
      status.textContent = "Preparing spoken message…";
      const response = await fetch("/api/voice/tts", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Local speech playback is unavailable.");
      }
      const blob = await response.blob();
      state.audioUrl = URL.createObjectURL(blob);
      state.listeningAudio = new Audio(state.audioUrl);
      state.listeningAudio.addEventListener("ended", stopListeningAudio, { once: true });
      await state.listeningAudio.play();
      status.textContent = "Playing the spoken message.";
    } catch (error) {
      status.textContent = error.message + " Use the text alternative.";
    }
  }

  function stopListeningAudio() {
    if (state.listeningAudio) {
      state.listeningAudio.pause();
      state.listeningAudio = null;
    }
    if (state.audioUrl) {
      URL.revokeObjectURL(state.audioUrl);
      state.audioUrl = null;
    }
  }

  async function startLearningRecording() {
    if (state.recorder || !state.voiceStatus?.stt?.available) return;
    const status = $("#learning-voice-status");
    const record = $("#learning-exercise button");
    try {
      status.textContent = "Requesting microphone permission…";
      state.stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      state.recorder = new MediaRecorder(state.stream);
      state.chunks = [];
      state.discardRecording = false;
      state.recorder.addEventListener("dataavailable", (event) => {
        if (event.data?.size) state.chunks.push(event.data);
      });
      state.recorder.addEventListener("stop", async () => {
        const recorder = state.recorder;
        state.recorder = null;
        for (const track of state.stream?.getTracks() || []) track.stop();
        state.stream = null;
        if (state.recordTimer) window.clearTimeout(state.recordTimer);
        state.recordTimer = null;
        const blob = new Blob(state.chunks, { type: recorder?.mimeType || "audio/webm" });
        state.chunks = [];
        if (state.discardRecording) {
          state.discardRecording = false;
          return;
        }
        if (!blob.size) {
          status.textContent = "No audio was captured. Type your response instead.";
          return;
        }
        status.textContent = state.voiceStatus?.stt?.engine === "groq-whisper"
          ? "Sending recording to Groq for transcription…"
          : "Transcribing locally…";
        try {
          const response = await fetch("/api/voice/transcribe", {
            method: "POST", headers: { "Content-Type": blob.type || "application/octet-stream" }, body: blob,
          });
          const payload = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(payload.detail || "Speech transcription failed.");
          const textarea = $("#learning-reflection");
          if (textarea) textarea.value = String(payload.text || "");
          status.textContent = textarea?.value
            ? "Transcript added. Edit recognition errors before submitting."
            : "No speech was recognised. Type your response instead.";
        } catch (error) {
          status.textContent = error.message + " You can type your response instead.";
        }
        const stopButton = $("#learning-exercise button:nth-of-type(2)");
        if (stopButton) stopButton.disabled = true;
      });
      state.recorder.start();
      status.textContent = "Recording… press Stop recording when finished (60-second limit).";
      const stopButton = $("#learning-exercise button:nth-of-type(2)");
      if (stopButton) stopButton.disabled = false;
      state.recordTimer = window.setTimeout(() => stopLearningRecording(false), 60000);
    } catch (error) {
      for (const track of state.stream?.getTracks() || []) track.stop();
      state.stream = null;
      state.recorder = null;
      status.textContent = "Microphone unavailable: " + error.message + ". Type your response instead.";
    }
  }

  function stopLearningRecording(discard = false) {
    state.discardRecording = discard;
    if (state.recordTimer) window.clearTimeout(state.recordTimer);
    state.recordTimer = null;
    for (const track of state.stream?.getTracks() || []) track.stop();
    if (state.recorder && state.recorder.state !== "inactive") {
      state.recorder.stop();
    } else {
      state.recorder = null;
      state.stream = null;
      state.chunks = [];
      state.discardRecording = false;
    }
    const stopButton = $("#learning-exercise button:nth-of-type(2)");
    if (stopButton) stopButton.disabled = true;
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
    stopLearningRecording(true);
    stopListeningAudio();
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
    window.addEventListener("beforeunload", () => {
      stopLearningRecording(true);
      stopListeningAudio();
    });
  });
})();
