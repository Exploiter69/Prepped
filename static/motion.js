/* Prepped Motion System v1 — Tactile Paper & Calm Breath
   FLIP sliding tab thumbs, spatial workspace/stage transitions, living SVG owl,
   editorial completion seals, Memory deck choreography, KPI counter ease-in,
   validation nudges, transcript arrival wash, and optional Web Audio cues. */
(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* -----------------------------------------------------------------------
     1. Optional Web Audio Subtle Sound Engine (Default: OFF, persisted)
     ----------------------------------------------------------------------- */
  const SOUND_KEY = "prepped:sound_enabled_v1";
  let soundEnabled = false;
  let audioCtx = null;

  try {
    soundEnabled = localStorage.getItem(SOUND_KEY) === "1";
  } catch {}

  function getAudioContext() {
    if (!soundEnabled) return null;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    if (!audioCtx) audioCtx = new Ctx();
    if (audioCtx.state === "suspended") audioCtx.resume().catch(() => {});
    return audioCtx;
  }

  function playTone(freq, duration = 0.07, gainPeak = 0.04, type = "sine", delay = 0) {
    const ctx = getAudioContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime + delay;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, now);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(gainPeak, now + 0.012);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + duration + 0.02);
    } catch {}
  }

  const Sound = {
    tick: () => playTone(520, 0.045, 0.028, "triangle"),
    flip: () => playTone(410, 0.06, 0.025, "sine"),
    recordStart: () => playTone(440, 0.09, 0.035, "sine"),
    recordStop: () => playTone(350, 0.08, 0.03, "sine"),
    success: () => {
      playTone(523.25, 0.14, 0.04, "sine", 0);
      playTone(659.25, 0.18, 0.04, "sine", 0.09);
      playTone(783.99, 0.24, 0.035, "sine", 0.18);
    },
  };
  window.PreppedSound = Sound;

  function syncSoundToggleButton() {
    const btn = $("#sound-toggle-btn");
    if (!btn) return;
    btn.setAttribute("aria-pressed", String(soundEnabled));
    const label = btn.querySelector("span");
    if (label) label.textContent = soundEnabled ? "Sound on" : "Sound off";
  }

  const soundBtn = $("#sound-toggle-btn");
  if (soundBtn) {
    syncSoundToggleButton();
    soundBtn.addEventListener("click", () => {
      soundEnabled = !soundEnabled;
      try { localStorage.setItem(SOUND_KEY, soundEnabled ? "1" : "0"); } catch {}
      syncSoundToggleButton();
      if (soundEnabled) Sound.tick();
    });
  }

  /* -----------------------------------------------------------------------
     2. FLIP Sliding Segmented Tab Thumb (.seg-tabs)
     ----------------------------------------------------------------------- */
  function positionThumb(bar, instant = false) {
    if (!bar) return;
    const active = bar.querySelector(".seg-tab.is-active");
    let thumb = bar.querySelector(":scope > .seg-thumb");
    if (!active || active.offsetWidth === 0) {
      if (thumb) thumb.style.opacity = "0";
      return;
    }
    if (!thumb) {
      thumb = document.createElement("span");
      thumb.className = "seg-thumb";
      thumb.setAttribute("aria-hidden", "true");
      bar.prepend(thumb);
      bar.classList.add("has-thumb");
      instant = true;
    }
    const barRect = bar.getBoundingClientRect();
    const tabRect = active.getBoundingClientRect();
    const left = tabRect.left - barRect.left;
    const top = tabRect.top - barRect.top;
    if (instant || reduceMotion()) {
      const prev = thumb.style.transition;
      thumb.style.transition = "none";
      thumb.style.width = tabRect.width + "px";
      thumb.style.height = tabRect.height + "px";
      thumb.style.transform = `translate3d(${left}px, ${top}px, 0)`;
      thumb.style.opacity = "1";
      thumb.offsetHeight; // force flush
      thumb.style.transition = prev;
    } else {
      thumb.style.width = tabRect.width + "px";
      thumb.style.height = tabRect.height + "px";
      thumb.style.transform = `translate3d(${left}px, ${top}px, 0)`;
      thumb.style.opacity = "1";
    }
  }

  function attachSlidingTabBar(bar) {
    if (!bar || bar.dataset.motionTabsAttached === "1") return;
    bar.dataset.motionTabsAttached = "1";
    bar.addEventListener("click", (e) => {
      if (e.target.closest(".seg-tab")) {
        window.requestAnimationFrame(() => positionThumb(bar, false));
        Sound.tick();
      }
    });
    const mo = new MutationObserver(() => {
      window.requestAnimationFrame(() => positionThumb(bar, false));
    });
    mo.observe(bar, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] });
    window.requestAnimationFrame(() => positionThumb(bar, true));
  }

  function syncAllTabBars(instant = false) {
    for (const bar of $$(".seg-tabs")) {
      attachSlidingTabBar(bar);
      positionThumb(bar, instant);
    }
  }

  /* -----------------------------------------------------------------------
     3. Living Inline SVG Owl Hydrator (Preserves static .svg assets untouched)
     ----------------------------------------------------------------------- */
  function hydrateLivingOwl() {
    const wrap = $(".dashboard-mascot-wrap");
    const img = wrap?.querySelector("img.dashboard-mascot");
    if (!wrap || !img || wrap.querySelector(".living-owl")) return;

    const svgNS = "http://www.w3.org/2000/svg";
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `<svg class="living-owl" xmlns="${svgNS}" viewBox="0 0 184 184" role="img" aria-label="Prepped owl mascot">
      <defs>
        <linearGradient id="preppedOwlBody" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#4F9671"/>
          <stop offset="1" stop-color="#245B45"/>
        </linearGradient>
      </defs>
      <ellipse class="owl-shadow" cx="92" cy="165" rx="54" ry="9" fill="#0B2522" opacity=".2"/>
      <g class="owl-body-group">
        <path class="owl-wing-left" d="M43 77 Q24 61 33 37 Q55 42 66 58" fill="#B8E4C9" stroke="#245B45" stroke-width="4" stroke-linejoin="round"/>
        <path class="owl-wing-right" d="M118 58 Q132 40 153 37 Q160 61 141 78" fill="#B8E4C9" stroke="#245B45" stroke-width="4" stroke-linejoin="round"/>
        <path d="M47 91 Q42 53 69 37 Q91 22 115 37 Q143 53 137 91 L132 137 Q127 160 92 161 Q57 160 52 137z" fill="url(#preppedOwlBody)" stroke="#173D32" stroke-width="4"/>
        <path d="M55 100 Q58 69 91 65 Q124 69 129 100 Q130 139 92 145 Q54 139 55 100" fill="#F6F2E8"/>
        <path d="M74 43 Q90 27 106 43" fill="none" stroke="#F5B942" stroke-width="8" stroke-linecap="round"/>
        <g class="owl-eyes-group">
          <circle cx="70" cy="83" r="19" fill="#FFFDF6"/>
          <circle cx="114" cy="83" r="19" fill="#FFFDF6"/>
          <circle cx="70" cy="83" r="7" fill="#173D32"/>
          <circle cx="114" cy="83" r="7" fill="#173D32"/>
          <circle cx="73" cy="80" r="2.2" fill="#FFFFFF"/>
          <circle cx="117" cy="80" r="2.2" fill="#FFFFFF"/>
          <path d="M60 76 Q70 64 80 76 M104 76 Q114 64 124 76" fill="none" stroke="#173D32" stroke-width="4" stroke-linecap="round"/>
        </g>
        <path d="M87 96 L97 96 L92 105z" fill="#D98A5C"/>
        <path d="M88 94 Q96 101 104 94" fill="none" stroke="#C46F52" stroke-width="4" stroke-linecap="round"/>
        <path d="M60 142 Q47 151 43 164 M124 142 Q137 151 141 164" stroke="#D6A45E" stroke-width="7" stroke-linecap="round"/>
        <path d="M72 158 Q92 165 112 158" fill="none" stroke="#173D32" stroke-width="4" stroke-linecap="round"/>
      </g>
    </svg>`;
    const svgEl = wrapper.firstElementChild;
    img.classList.add("hidden");
    img.after(svgEl);
  }

  /* -----------------------------------------------------------------------
     4. Editorial Animated Completion Seal (Lesson & Career Complete)
     ----------------------------------------------------------------------- */
  function buildCompletionSeal(titleText, subtitleText) {
    const wrap = document.createElement("div");
    wrap.className = "motion-seal-wrap";
    wrap.innerHTML = `<svg class="motion-seal" viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <g class="seal-ticks" stroke="#F5B942" stroke-width="2.4" stroke-linecap="round">
        <line x1="32" y1="3" x2="32" y2="8"/>
        <line x1="32" y1="56" x2="32" y2="61"/>
        <line x1="3" y1="32" x2="8" y2="32"/>
        <line x1="56" y1="32" x2="61" y2="32"/>
        <line x1="11.5" y1="11.5" x2="15" y2="15"/>
        <line x1="49" y1="49" x2="52.5" y2="52.5"/>
      </g>
      <circle class="seal-ring" cx="32" cy="32" r="24" fill="#DCEFEA" stroke="#0F766E" stroke-width="2.8"/>
      <path class="seal-check" d="M21.5 32.5L28.5 39.5L43 24.5" stroke="#0F5C57" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div class="motion-seal-copy"><strong></strong><span></span></div>`;
    wrap.querySelector("strong").textContent = titleText;
    wrap.querySelector("span").textContent = subtitleText;
    return wrap;
  }

  /* -----------------------------------------------------------------------
     5. Workspace View, Career Stage, Lesson Step & Memory Deck Observers
     ----------------------------------------------------------------------- */
  function replayClass(el, className) {
    if (!el || reduceMotion()) return;
    el.classList.remove(className);
    void el.offsetWidth;
    el.classList.add(className);
  }

  window.addEventListener("prepped:viewchange", (e) => {
    const viewId = e.detail?.view;
    if (viewId) {
      const viewEl = document.getElementById(viewId);
      replayClass(viewEl, "motion-view-enter");
    }
    window.requestAnimationFrame(() => syncAllTabBars(true));
  });

  // Career directional transitions + Completion Seal
  const careerView = $("#career-view");
  const careerOrder = { studios: 0, setup: 1, session: 2, review: 3, history: 0 };
  let lastCareerStage = careerView?.dataset.careerStage || "studios";
  if (careerView) {
    new MutationObserver(() => {
      const next = careerView.dataset.careerStage || "studios";
      if (next === lastCareerStage) return;
      const forward = (careerOrder[next] ?? 0) >= (careerOrder[lastCareerStage] ?? 0);
      lastCareerStage = next;
      const panelMap = {
        studios: "#career-catalog-stage",
        setup: "#career-setup",
        session: "#career-active",
        review: "#career-review",
        history: "#career-history-stage",
      };
      const panel = $(panelMap[next]);
      replayClass(panel, forward ? "motion-slide-forward" : "motion-slide-back");
      if (next === "review") {
        const reviewIntro = $("#career-review .career-review-intro");
        if (reviewIntro && !reviewIntro.querySelector(".motion-seal-wrap")) {
          reviewIntro.prepend(buildCompletionSeal("Round completed", "Review your answers line by line below."));
        }
        Sound.success();
      } else {
        Sound.tick();
      }
      window.requestAnimationFrame(() => syncAllTabBars(false));
    }).observe(careerView, { attributes: true, attributeFilter: ["data-career-stage"] });
  }

  // Lesson step cross-slide & Completion Seal
  const learningExercise = $("#learning-exercise");
  if (learningExercise) {
    new MutationObserver(() => {
      if (learningExercise.children.length > 0) {
        replayClass(learningExercise, "motion-step-enter");
      }
    }).observe(learningExercise, { childList: true });
  }

  const learningFeedback = $("#learning-feedback");
  if (learningFeedback) {
    new MutationObserver(() => {
      const visible = !learningFeedback.classList.contains("hidden") && learningFeedback.children.length > 0;
      if (visible && !learningFeedback.querySelector(".motion-seal-wrap")) {
        learningFeedback.prepend(buildCompletionSeal("Lesson complete", "Your responses and progress are saved locally."));
        Sound.success();
      }
    }).observe(learningFeedback, { attributes: true, childList: true, attributeFilter: ["class"] });
  }

  // Memory flashcard rise & reveal chime
  const memoryReview = $("#memory-review");
  if (memoryReview) {
    new MutationObserver(() => {
      const card = memoryReview.querySelector(".memory-review-card");
      if (card) {
        replayClass(card, "motion-card-enter");
        if (card.querySelector(".memory-review-answer")) Sound.flip();
      }
    }).observe(memoryReview, { childList: true });
  }

  // Transcript arrival wash + sound cues
  window.addEventListener("prepped:transcript-inserted", () => {
    const input = $("#answer-input");
    if (input) replayClass(input, "motion-transcript-flash");
    Sound.tick();
  });

  // Gentle error shake when inline validation message appears
  for (const errEl of $$(".inline-error")) {
    new MutationObserver(() => {
      if (errEl.textContent.trim()) replayClass(errEl, "motion-shake");
    }).observe(errEl, { childList: true, characterData: true, subtree: true });
  }

  // Smooth integer counter roll-up on Today stats
  function observeCounter(id) {
    const el = document.getElementById(id);
    if (!el) return;
    let lastVal = null;
    new MutationObserver(() => {
      if (reduceMotion() || el.dataset.counting === "1") return;
      const num = parseInt(el.textContent.trim(), 10);
      if (!Number.isFinite(num) || num <= 0 || num === lastVal) {
        lastVal = Number.isFinite(num) ? num : lastVal;
        return;
      }
      const from = Number.isFinite(lastVal) ? lastVal : 0;
      lastVal = num;
      el.dataset.counting = "1";
      const start = performance.now();
      const duration = 360;
      const tick = (now) => {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = String(Math.round(from + (num - from) * eased));
        if (t < 1) window.requestAnimationFrame(tick);
        else {
          el.textContent = String(num);
          delete el.dataset.counting;
        }
      };
      window.requestAnimationFrame(tick);
    }).observe(el, { childList: true, characterData: true, subtree: true });
  }

  ["dashboard-lessons-completed", "dashboard-skills-active", "dashboard-reviews-due"].forEach(observeCounter);

  // Sync sliding tab thumbs on viewport resize
  let resizeTimer = null;
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => syncAllTabBars(true), 80);
  });

  // Initialize once DOM is ready
  hydrateLivingOwl();
  syncAllTabBars(true);

  window.PreppedMotion = {
    syncTabs: syncAllTabBars,
    sound: Sound,
  };
})();
