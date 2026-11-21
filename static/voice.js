/* Local voice controls: push-to-talk recording, transcript insertion, and TTS. */
(() => {
  "use strict";

  const MAX_ANSWER_CHARS = 6000;
  const state = {
    status: null,
    questionText: "",
    busy: false,
    recording: false,
    transcribing: false,
    permissionPending: false,
    discardRecording: false,
    recorder: null,
    stream: null,
    chunks: [],
    timerId: null,
    startedAt: 0,
    audioUrl: null,
    promptAudioCache: new Map(),
    generation: 0,
    transcriptionController: null,
    ttsController: null,
    audioContext: null,
    analyser: null,
    visualizerSource: null,
    visualizerFrame: null,
  };

  const ui = {};

  function cacheUi() {
    ui.record = document.getElementById("record-button");
    ui.stopRecord = document.getElementById("stop-recording-button");
    ui.recordStatus = document.getElementById("record-status");
    ui.voiceError = document.getElementById("voice-error");
    ui.ttsPlay = document.getElementById("tts-play-button");
    ui.ttsStop = document.getElementById("tts-stop-button");
    ui.ttsReplay = document.getElementById("tts-replay-button");
    ui.ttsStatus = document.getElementById("tts-status");
    ui.audio = document.getElementById("tts-audio");
    ui.answer = document.getElementById("answer-input");
    ui.privacyNote = document.getElementById("privacy-note");
    ui.privacySummary = document.getElementById("privacy-summary");
    ui.visualizer = document.getElementById("recording-visualizer");
    ui.recordingClock = document.getElementById("recording-clock");
    ui.draftState = document.getElementById("response-draft-state");
  }

  function setRecordStatus(message, tone = "") {
    if (!ui.recordStatus) return;
    ui.recordStatus.textContent = message || "";
    ui.recordStatus.classList.toggle("error", tone === "error");
    ui.recordStatus.classList.toggle("recording", tone === "recording");
  }

  function setTtsStatus(message, tone = "") {
    if (!ui.ttsStatus) return;
    ui.ttsStatus.textContent = message || "";
    ui.ttsStatus.classList.toggle("error", tone === "error");
  }

  function setVoiceError(message) {
    if (ui.voiceError) ui.voiceError.textContent = message || "";
  }

  function supportsRecording() {
    return Boolean(
      window.MediaRecorder &&
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === "function"
    );
  }

  function recordingLimitSeconds() {
    return state.status?.limits?.max_recording_seconds || 60;
  }

  function formatClock(seconds) {
    const safe = Math.max(0, Math.floor(seconds));
    return String(Math.floor(safe / 60)).padStart(2, "0") + ":" + String(safe % 60).padStart(2, "0");
  }

  function stopVisualizer() {
    if (state.visualizerFrame !== null) {
      window.cancelAnimationFrame(state.visualizerFrame);
      state.visualizerFrame = null;
    }
    try { state.visualizerSource?.disconnect(); } catch (error) {}
    state.visualizerSource = null;
    state.analyser = null;
    const context = state.audioContext;
    state.audioContext = null;
    if (context && context.state !== "closed") context.close().catch(() => {});
    if (ui.visualizer) {
      ui.visualizer.classList.remove("is-active", "is-fallback");
      for (const bar of ui.visualizer.querySelectorAll("span")) bar.style.height = "7px";
    }
  }

  function startVisualizer(stream) {
    if (!ui.visualizer) return;
    stopVisualizer();
    ui.visualizer.classList.add("is-active");
    const bars = Array.from(ui.visualizer.querySelectorAll("span"));
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      ui.visualizer.classList.add("is-fallback");
      return;
    }
    try {
      const context = new AudioContextClass();
      state.audioContext = context;
      const analyser = context.createAnalyser();
      analyser.fftSize = 128;
      const source = context.createMediaStreamSource(stream);
      source.connect(analyser);
      state.analyser = analyser;
      state.visualizerSource = source;
      const samples = new Uint8Array(analyser.fftSize);
      context.resume().catch(() => {});
      const draw = () => {
        if (!state.recording || state.analyser !== analyser) return;
        if (context.state !== "running") {
          ui.visualizer.classList.add("is-fallback");
        } else {
          ui.visualizer.classList.remove("is-fallback");
          analyser.getByteTimeDomainData(samples);
          const windowSize = Math.max(1, Math.floor(samples.length / Math.max(1, bars.length)));
          bars.forEach((bar, index) => {
            let energy = 0;
            const first = index * windowSize;
            for (let sample = first; sample < Math.min(samples.length, first + windowSize); sample += 1) {
              const amplitude = (samples[sample] - 128) / 128;
              energy += amplitude * amplitude;
            }
            const rms = Math.sqrt(energy / windowSize);
            bar.style.height = (7 + Math.min(31, rms * 72)) + "px";
          });
        }
        state.visualizerFrame = window.requestAnimationFrame(draw);
      };
      state.visualizerFrame = window.requestAnimationFrame(draw);
    } catch (error) {
      stopVisualizer();
      ui.visualizer.classList.add("is-active", "is-fallback");
    }
  }

  function updateControls() {
    if (!ui.record) return;
    const sttReady = supportsRecording() && Boolean(state.status?.stt?.available);
    const ttsReady = Boolean(state.status?.tts?.available && state.questionText);
    const recordingOrTranscribing = state.recording || state.transcribing || state.permissionPending;

    ui.record.disabled = state.busy || !sttReady || recordingOrTranscribing;
    ui.record.textContent = state.recording ? "Recording…" : "Start recording";
    ui.record.classList.toggle("recording", state.recording);
    ui.visualizer?.classList.toggle("is-active", state.recording);
    ui.stopRecord.disabled = state.busy || !state.recording;
    ui.stopRecord.textContent = state.transcribing ? "Transcribing…" : "Stop recording";

    ui.ttsPlay.disabled = state.busy || !ttsReady || recordingOrTranscribing;
    ui.ttsReplay.disabled = state.busy || !ttsReady || recordingOrTranscribing;
    ui.ttsStop.disabled = state.busy || !state.audioUrl;
  }

  function refreshRecordHint() {
    if (state.recording || state.transcribing) return;
    if (!supportsRecording()) {
      setRecordStatus(
        "This browser cannot record audio here. Type your answer instead.",
        "error"
      );
      return;
    }
    if (!state.status) return;
    if (state.status.stt?.available) {
      if (state.status.stt?.engine === "groq-whisper") {
        setRecordStatus("Ready to record. Your audio will be sent to Groq for transcription.");
      } else {
        setRecordStatus("Ready to record locally. Audio is not sent to a provider or saved.");
      }
    } else {
      setRecordStatus(
        state.status.stt?.detail ||
          "Speech-to-text is not available. Type your answer instead.",
        "error"
      );
    }
  }

  function refreshTtsHint() {
    if (!state.status) return;
    if (!state.questionText) {
      setTtsStatus("");
    } else if (state.status.tts?.available) {
      setTtsStatus("Press Play question aloud to hear this prompt.");
    } else {
      setTtsStatus(
        state.status.tts?.detail ||
          "Local spoken prompts are unavailable. Read the question on screen.",
        "error"
      );
    }
  }

  async function refreshStatus() {
    try {
      const response = await fetch("/api/voice/status", {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Local voice status could not be loaded.");
      state.status = await response.json();
    } catch (error) {
      state.status = null;
      setRecordStatus(
        "Speech-provider status is unavailable. Text input still works.",
        "error"
      );
      setTtsStatus(
        "Local spoken prompts are unavailable. Read the question on screen.",
        "error"
      );
    }
    refreshPrivacyCopy();
    refreshRecordHint();
    refreshTtsHint();
    updateControls();
  }

  function refreshPrivacyCopy() {
    const remoteStt = state.status?.stt?.engine === "groq-whisper";
    const remoteTts = state.status?.tts?.engine === "groq-orpheus";
    const remote = remoteStt || remoteTts;
    const localText = "Answers are saved in the local SQLite database. Raw microphone audio is processed for transcription and is not stored by Prepped.";
    const remoteText = "Answers are saved in the local SQLite database. " + (remoteStt ? "Your microphone audio is sent to Groq Whisper for transcription. " : "") + (remoteTts ? "Groq Orpheus sends prompt text for speech generation. " : "") + "Prepped does not store raw audio. Use only content you are comfortable sending to the provider.";
    const unavailableText = "Answers are saved locally. Speech-provider details could not be loaded; check voice status before recording. Prepped does not store raw audio.";
    const detail = state.status ? (remote ? remoteText : localText) : unavailableText;
    if (ui.privacyNote) ui.privacyNote.textContent = detail;
    if (ui.privacySummary) {
      ui.privacySummary.textContent = !state.status
        ? "Answers stay in the local app. Speech-provider details are unavailable until status can be checked."
        : remote
          ? "Answers stay in the local app. " + (remoteStt ? "Your microphone audio is sent to Groq Whisper for STT. " : "") + (remoteTts ? "Groq receives prompt text for TTS. " : "") + "Prepped does not store raw audio."
          : "Answers stay in the local app. Vosk and local spoken prompts run locally; Prepped does not store raw audio.";
    }
  }

  function stopSpeech(updateStatus = false) {
    state.ttsController?.abort();
    state.ttsController = null;
    if (ui.audio) {
      ui.audio.pause();
      ui.audio.onended = null;
      ui.audio.onerror = null;
      ui.audio.currentTime = 0;
      ui.audio.removeAttribute("src");
      ui.audio.load();
    }
    if (state.audioUrl) {
      URL.revokeObjectURL(state.audioUrl);
      state.audioUrl = null;
    }
    if (updateStatus) setTtsStatus("Question audio stopped.");
    updateControls();
  }

  function stopQuestion() {
    stopSpeech(true);
  }

  async function playQuestion() {
    if (!state.questionText || state.busy || state.recording || state.transcribing) return;
    stopSpeech();
    const requestGeneration = state.generation;
    const controller = new AbortController();
    state.ttsController = controller;
    const cacheKey = state.questionText;
    const cachedBlob = state.promptAudioCache.get(cacheKey);
    setTtsStatus(cachedBlob ? "Loading saved question audio…" : "Preparing question audio…");
    try {
      let blob = cachedBlob;
      if (!blob) {
      const response = await fetch("/api/voice/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: state.questionText }),
        signal: controller.signal,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : "Local spoken prompts are unavailable."
        );
      }
      blob = await response.blob();
      if (requestGeneration !== state.generation || controller.signal.aborted) return;
      if (blob.size <= 2 * 1024 * 1024) state.promptAudioCache.set(cacheKey, blob);
      while (state.promptAudioCache.size > 4) {
        state.promptAudioCache.delete(state.promptAudioCache.keys().next().value);
      }
      }
      if (requestGeneration !== state.generation || controller.signal.aborted) return;
      state.audioUrl = URL.createObjectURL(blob);
      ui.audio.src = state.audioUrl;
      ui.audio.onended = () => {
        setTtsStatus("Question finished. Use Replay to hear it again.");
        updateControls();
      };
      ui.audio.onerror = () => {
        setTtsStatus("The local audio could not be played. Read the question on screen.", "error");
      };
      await ui.audio.play();
      if (requestGeneration !== state.generation || controller.signal.aborted) return;
      setTtsStatus("Playing question audio. Use Stop to interrupt.");
    } catch (error) {
      if (error.name !== "AbortError" && requestGeneration === state.generation) {
        setTtsStatus(
          (error.message || "Local spoken prompts are unavailable.") +
            " Read the question on screen.",
          "error"
        );
      }
    } finally {
      if (state.ttsController === controller) state.ttsController = null;
      updateControls();
    }
  }

  async function replayQuestion() {
    if (!state.questionText || state.busy) return;
    if (state.audioUrl && ui.audio.src) {
      const generation = state.generation;
      const audio = ui.audio;
      try {
        audio.currentTime = 0;
        await audio.play();
        if (generation === state.generation && audio === ui.audio && audio.src) {
          setTtsStatus("Replaying question audio. Use Stop to interrupt.");
        }
      } catch (error) {
        if (generation === state.generation) {
          setTtsStatus("The local audio could not be replayed. Press Play question aloud.", "error");
        }
      }
    } else {
      await playQuestion();
    }
    updateControls();
  }

  function chosenMimeType() {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/ogg;codecs=opus",
      "audio/webm",
      "audio/mp4",
    ];
    if (typeof MediaRecorder.isTypeSupported !== "function") return "";
    return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || "";
  }

  function microphoneError(error) {
    switch (error?.name) {
      case "NotAllowedError":
      case "PermissionDeniedError":
        return "Microphone permission was denied. Allow access in the browser or type your answer instead.";
      case "NotFoundError":
      case "DevicesNotFoundError":
        return "No microphone was found. Connect one or type your answer instead.";
      case "NotReadableError":
      case "TrackStartError":
        return "The microphone is busy or could not start. Close other apps using it or type your answer instead.";
      case "OverconstrainedError":
        return "The microphone does not support the requested settings. Try another microphone or type your answer instead.";
      case "SecurityError":
        return "Microphone access is blocked. Open Prepped at http://127.0.0.1:8000 or type your answer instead.";
      default:
        return "The microphone could not start. Type your answer instead.";
    }
  }

  function releaseStream() {
    if (state.stream) {
      for (const track of state.stream.getTracks()) track.stop();
      state.stream = null;
    }
  }

  function clearTimer() {
    if (state.timerId) {
      window.clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  function updateRecordingTimer() {
    if (!state.recording) return;
    const limit = recordingLimitSeconds();
    const elapsed = Math.min(Math.floor((Date.now() - state.startedAt) / 1000), limit);
    setRecordStatus(
      `Recording… ${elapsed}s / ${limit}s. Press Stop recording when finished.`,
      "recording"
    );
    if (ui.recordingClock) ui.recordingClock.textContent = formatClock(elapsed) + " / " + formatClock(limit);
    if (elapsed >= limit) {
      stopRecording(false, `Recording reached the ${limit}-second limit; transcribing now.`);
    }
  }

  async function startRecording() {
    if (state.busy || state.recording || state.transcribing) return;
    setVoiceError("");
    if (!state.status?.stt?.available) {
      setRecordStatus(
        state.status?.stt?.detail ||
          "Speech-to-text is not available. Type your answer instead.",
        "error"
      );
      return;
    }
    if (!supportsRecording()) {
      setRecordStatus("This browser cannot record audio here. Type your answer instead.", "error");
      return;
    }

    stopSpeech();
    const requestGeneration = state.generation;
    state.permissionPending = true;
    setRecordStatus("Requesting microphone permission…");
    updateControls();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      // Question/session may have changed while the browser permission prompt
      // was open. Never let that stale request start a recording.
      if (requestGeneration !== state.generation) {
        for (const track of stream.getTracks()) track.stop();
        return;
      }
      state.stream = stream;
    } catch (error) {
      if (requestGeneration === state.generation) {
        setRecordStatus(microphoneError(error), "error");
      }
      return;
    } finally {
      if (requestGeneration === state.generation) {
        state.permissionPending = false;
        updateControls();
      }
    }

    if (requestGeneration !== state.generation) {
      releaseStream();
      return;
    }

    try {
      const mimeType = chosenMimeType();
      state.recorder = mimeType
        ? new MediaRecorder(state.stream, { mimeType })
        : new MediaRecorder(state.stream);
    } catch (error) {
      releaseStream();
      setRecordStatus("This browser could not start recording. Type your answer instead.", "error");
      return;
    }

    state.chunks = [];
    state.discardRecording = false;
    state.recorder.addEventListener("dataavailable", (event) => {
      if (event.data && event.data.size > 0) state.chunks.push(event.data);
    });
    state.recorder.addEventListener("stop", () => {
      finishRecording();
    });
    state.recorder.addEventListener("error", () => {
      setRecordStatus("Recording failed. Try again or type your answer instead.", "error");
      stopRecording(true);
    });

    state.recording = true;
    state.startedAt = Date.now();
    try {
      state.recorder.start();
    } catch (error) {
      state.recording = false;
      state.recorder = null;
      state.chunks = [];
      releaseStream();
      setRecordStatus("This browser could not begin recording. Try again or type your answer instead.", "error");
      updateControls();
      return;
    }
    startVisualizer(state.stream);
    if (ui.recordingClock) ui.recordingClock.textContent = "00:00 / " + formatClock(recordingLimitSeconds());
    state.timerId = window.setInterval(updateRecordingTimer, 250);
    setRecordStatus(`Recording… 0s / ${recordingLimitSeconds()}s. Press Stop recording when finished.`, "recording");
    updateControls();
  }

  function stopRecording(discard = false, message = "") {
    if (!state.recording && !state.recorder) return;
    state.discardRecording = discard;
    clearTimer();
    stopVisualizer();
    releaseStream();
    const recorder = state.recorder;
    state.recording = false;
    if (recorder && recorder.state !== "inactive") {
      try {
        recorder.stop();
      } catch (error) {
        // The stop event may already be queued; nothing else to do here.
      }
    }
    if (discard) {
      setRecordStatus(message || "Recording discarded.");
    } else if (message) {
      setRecordStatus(message);
    }
    updateControls();
  }

  async function finishRecording() {
    clearTimer();
    stopVisualizer();
    releaseStream();
    const recorder = state.recorder;
    state.recorder = null;
    state.recording = false;

    if (state.discardRecording) {
      state.discardRecording = false;
      state.chunks = [];
      updateControls();
      return;
    }

    const mimeType = recorder?.mimeType || "audio/webm";
    const blob = new Blob(state.chunks, { type: mimeType });
    state.chunks = [];
    if (!blob.size) {
      setRecordStatus("No audio was captured. Try again or type your answer instead.", "error");
      updateControls();
      return;
    }

    const generation = state.generation;
    const controller = new AbortController();
    state.transcriptionController = controller;
    state.transcribing = true;
    setRecordStatus(
      state.status?.stt?.engine === "groq-whisper"
        ? "Sending recording to Groq for transcription… Prepped does not store the raw audio."
        : "Transcribing locally… Prepped does not store the raw audio."
    );
    updateControls();
    try {
      const response = await fetch("/api/voice/transcribe", {
        method: "POST",
        headers: { "Content-Type": blob.type || "application/octet-stream" },
        body: blob,
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => ({}));
      if (generation !== state.generation) return;
      if (!response.ok) {
        throw new Error(
          typeof payload.detail === "string"
            ? payload.detail
            : "Speech-to-text failed."
        );
      }
      const text = String(payload.text || "").trim();
      if (!text) {
        setRecordStatus("No speech was recognised. Try again or type your answer.", "error");
        return;
      }
      insertTranscript(text);
    } catch (error) {
      if (error.name !== "AbortError" && generation === state.generation) {
        setRecordStatus(
          (error.message || "Speech-to-text failed.") + " You can type your answer instead.",
          "error"
        );
      }
    } finally {
      if (state.transcriptionController === controller) state.transcriptionController = null;
      if (generation === state.generation) {
        state.transcribing = false;
        updateControls();
      }
    }
  }

  function insertTranscript(text) {
    if (!ui.answer) return;
    const existing = ui.answer.value.trim();
    let next = existing ? `${existing}\n${text}` : text;
    let truncated = false;
    if (next.length > MAX_ANSWER_CHARS) {
      next = next.slice(0, MAX_ANSWER_CHARS);
      truncated = true;
    }
    ui.answer.value = next;
    ui.answer.dispatchEvent(new Event("input", { bubbles: true }));
    ui.answer.focus();
    ui.answer.setSelectionRange(ui.answer.value.length, ui.answer.value.length);
    if (ui.draftState) ui.draftState.textContent = "Transcript added · review before saving";
    setRecordStatus(
      truncated
        ? "Transcript added, but it was cut at the 6,000-character limit. Edit before saving."
        : "Transcript added. Edit any recognition errors before saving.",
      truncated ? "error" : ""
    );
  }

  function stopAll() {
    state.generation += 1;
    state.permissionPending = false;
    state.transcriptionController?.abort();
    state.transcriptionController = null;
    state.transcribing = false;
    stopSpeech();
    if (state.recording || state.recorder) {
      stopRecording(true);
    }
    clearTimer();
    stopVisualizer();
    releaseStream();
    setVoiceError("");
    updateControls();
  }

  function setQuestion(text) {
    stopAll();
    state.questionText = typeof text === "string" ? text.trim() : "";
    if (ui.recordingClock) ui.recordingClock.textContent = "00:00 / " + formatClock(recordingLimitSeconds());
    setVoiceError("");
    setRecordStatus("");
    setTtsStatus("");
    refreshRecordHint();
    refreshTtsHint();
    updateControls();
  }

  function setBusy(value) {
    state.busy = Boolean(value);
    updateControls();
  }

  function init() {
    cacheUi();
    if (!ui.record) return;

    ui.record.addEventListener("click", startRecording);
    ui.stopRecord.addEventListener("click", () => stopRecording(false));
    ui.ttsPlay.addEventListener("click", playQuestion);
    ui.ttsStop.addEventListener("click", stopQuestion);
    ui.ttsReplay.addEventListener("click", replayQuestion);
    window.addEventListener("beforeunload", () => stopAll());

    setRecordStatus("Checking microphone and speech provider…");
    setTtsStatus("Checking speech providers…");
    updateControls();
    refreshStatus();
  }

  window.PreppedVoice = { init, setQuestion, stopAll, setBusy };
})();
