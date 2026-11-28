/* Prepped UI Shell — Claude Design System v1 interactions
   Offline banner, Ctrl/Cmd+K search overlay, mobile bottom navigation & sheet,
   6-step guided onboarding backed by /api/profile, lesson focus mode & exit dialog,
   Career/Memory segmented filters, Help & Privacy modal, and accessible toasts. */
(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  /* --- Toast helper --- */
  let toastTimer = null;
  function showToast(message) {
    const el = $("#app-toast");
    if (!el || !message) return;
    el.textContent = message;
    el.classList.remove("hidden");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => el.classList.add("hidden"), 4500);
  }
  window.PreppedToast = showToast;

  /* --- Offline banner --- */
  function syncOnlineStatus() {
    const banner = $("#offline-banner");
    if (!banner) return;
    banner.classList.toggle("hidden", navigator.onLine !== false);
  }
  window.addEventListener("online", syncOnlineStatus);
  window.addEventListener("offline", syncOnlineStatus);
  syncOnlineStatus();

  /* --- Accessible Modal Manager --- */
  let lastTrigger = null;
  function modalFocusableElements(modal) {
    return Array.from(modal.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )).filter((element) =>
      !element.hidden &&
      element.getAttribute("aria-hidden") !== "true" &&
      element.getClientRects().length > 0
    );
  }

  function openModal(modalId, trigger = null) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    lastTrigger = trigger || document.activeElement;
    modal.classList.remove("hidden");
    modal.setAttribute("tabindex", "-1");
    const focusable = modalFocusableElements(modal);
    if (focusable.length) focusable[0].focus();
    else modal.focus();
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal || modal.classList.contains("hidden")) return;
    modal.classList.add("hidden");
    if (lastTrigger && typeof lastTrigger.focus === "function") {
      lastTrigger.focus();
      lastTrigger = null;
    }
  }

  function closeAllModals() {
    for (const el of $$(".modal-backdrop:not(.hidden)")) {
      el.classList.add("hidden");
    }
    if (lastTrigger && typeof lastTrigger.focus === "function") {
      lastTrigger.focus();
      lastTrigger = null;
    }
  }

  for (const btn of $$("[data-close-modal]")) {
    btn.addEventListener("click", () => closeModal(btn.dataset.closeModal));
  }
  for (const backdrop of $$(".modal-backdrop")) {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal(backdrop.id);
    });
  }
  document.addEventListener("keydown", (e) => {
    const openModals = $$(".modal-backdrop:not(.hidden)");
    const activeModal = openModals[openModals.length - 1];

    if (e.key === "Escape" && activeModal) {
      closeModal(activeModal.id);
      return;
    }

    if (e.key === "Tab" && activeModal) {
      const focusable = modalFocusableElements(activeModal);
      if (!focusable.length) {
        e.preventDefault();
        activeModal.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && (document.activeElement === first || !activeModal.contains(document.activeElement))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (document.activeElement === last || !activeModal.contains(document.activeElement))) {
        e.preventDefault();
        first.focus();
      }
      return;
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openModal("search-modal", $("#global-search-trigger"));
      loadSearchIndex();
    }
  });

  /* --- Topbar & Dashboard Quick Links --- */
  $("#global-search-trigger")?.addEventListener("click", (e) => {
    openModal("search-modal", e.currentTarget);
    loadSearchIndex();
  });
  $("#help-open-btn")?.addEventListener("click", (e) => openModal("help-modal", e.currentTarget));
  $("#onboarding-open-btn")?.addEventListener("click", (e) => openOnboarding(e.currentTarget));

  /* --- Profile & Memory quick actions --- */
  $("#dashboard-career-button")?.addEventListener("click", () => $("#career-toggle")?.click());
  $("#feedback-save-memory")?.addEventListener("click", () => {
    $("#memory-toggle")?.click();
    window.setTimeout(() => $("#memory-open-editor")?.click(), 120);
  });

  /* --- Mobile Bottom Navigation & More Sheet --- */
  const mobileBtns = $$(".mobile-nav-btn[data-mobile-target]");
  for (const btn of mobileBtns) {
    btn.addEventListener("click", () => {
      const target = document.getElementById(btn.dataset.mobileTarget);
      if (target) target.click();
    });
  }
  $("#mobile-more-trigger")?.addEventListener("click", (e) => openModal("mobile-more-sheet", e.currentTarget));
  for (const btn of $$("[data-sheet-target]")) {
    btn.addEventListener("click", () => {
      closeModal("mobile-more-sheet");
      document.getElementById(btn.dataset.sheetTarget)?.click();
    });
  }
  for (const btn of $$("[data-sheet-modal]")) {
    btn.addEventListener("click", () => {
      closeModal("mobile-more-sheet");
      openModal(btn.dataset.sheetModal);
      if (btn.dataset.sheetModal === "search-modal") loadSearchIndex();
    });
  }

  function syncMobileNav(activeView) {
    const viewToTarget = {
      "dashboard-view": "home-toggle",
      "learning-view": "learning-toggle",
      "memory-view": "memory-toggle",
      "home-view": "practice-toggle",
      "practice-view": "practice-toggle",
      "feedback-view": "practice-toggle",
    };
    const activeTarget = viewToTarget[activeView] || "";
    for (const btn of mobileBtns) {
      btn.classList.toggle("is-active", btn.dataset.mobileTarget === activeTarget);
    }
    const moreBtn = $("#mobile-more-trigger");
    if (moreBtn) {
      moreBtn.classList.toggle("is-active", ["career-view", "progress-view", "history-view", "profile-view"].includes(activeView));
    }
  }
  window.addEventListener("prepped:viewchange", (e) => syncMobileNav(e.detail?.view || "dashboard-view"));

  /* --- Global Search Overlay (Ctrl/Cmd+K) --- */
  let searchCache = null;
  async function loadSearchIndex() {
    if (searchCache) {
      renderSearchResults($("#global-search-input")?.value || "");
      return;
    }
    const status = $("#global-search-status");
    if (status) status.textContent = "Loading local curriculum, studios, and memory…";
    const items = [];
    try {
      const [catalogRes, studiosRes, memRes] = await Promise.allSettled([
        fetch("/api/learning/catalog").then((r) => (r.ok ? r.json() : null)),
        fetch("/api/career/studios").then((r) => (r.ok ? r.json() : null)),
        fetch("/api/memory/items?status=all").then((r) => (r.ok ? r.json() : null)),
      ]);
      if (catalogRes.status === "fulfilled" && catalogRes.value?.tracks) {
        for (const track of catalogRes.value.tracks) {
          for (const lesson of track.lessons || []) {
            items.push({
              group: "Lessons",
              title: lesson.title || lesson.id,
              meta: track.title || "Curriculum",
              action: () => {
                closeModal("search-modal");
                $("#learning-toggle")?.click();
                window.dispatchEvent(new CustomEvent("prepped:start-lesson", { detail: { lessonId: lesson.id } }));
              },
            });
          }
        }
      }
      if (studiosRes.status === "fulfilled" && Array.isArray(studiosRes.value?.studios)) {
        for (const studio of studiosRes.value.studios) {
          items.push({
            group: "Career Studios",
            title: studio.title || studio.id,
            meta: studio.description || "Interview studio",
            action: () => {
              closeModal("search-modal");
              $("#career-toggle")?.click();
            },
          });
        }
      }
      const memList = memRes.status === "fulfilled" ? (memRes.value?.items || memRes.value || []) : [];
      if (Array.isArray(memList)) {
        for (const mem of memList) {
          items.push({
            group: "Memory",
            title: mem.front || "Saved item",
            meta: (mem.item_type || "item") + " · " + (mem.back || "").slice(0, 72),
            action: () => {
              closeModal("search-modal");
              $("#memory-toggle")?.click();
            },
          });
        }
      }
      items.push({
        group: "Practice",
        title: "Explain your project to a placement interviewer",
        meta: "Project practice scenario",
        action: () => {
          closeModal("search-modal");
          $("#practice-toggle")?.click();
        },
      });
      items.push({
        group: "Help",
        title: "Privacy, local storage & feedback limits",
        meta: "Help & trust",
        action: () => {
          closeModal("search-modal");
          openModal("help-modal");
        },
      });
      searchCache = items;
      renderSearchResults($("#global-search-input")?.value || "");
    } catch {
      if (status) status.textContent = "Could not load local search index.";
    }
  }

  function renderSearchResults(rawQuery) {
    const container = $("#global-search-results");
    const status = $("#global-search-status");
    if (!container) return;
    const q = rawQuery.trim().toLowerCase();
    const list = (searchCache || []).filter((item) => {
      if (!q) return true;
      return (item.title + " " + item.meta + " " + item.group).toLowerCase().includes(q);
    });
    container.replaceChildren();
    if (!list.length) {
      if (status) status.textContent = 'No matches for "' + rawQuery.trim() + '".';
      return;
    }
    if (status) status.textContent = q ? list.length + " matching items" : "Showing " + Math.min(list.length, 12) + " quick destinations";
    for (const item of list.slice(0, 12)) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "search-result-item";
      const badge = document.createElement("span");
      badge.className = "chip t";
      badge.textContent = item.group;
      const body = document.createElement("span");
      body.className = "search-result-copy";
      const strong = document.createElement("strong");
      strong.textContent = item.title;
      const small = document.createElement("small");
      small.textContent = item.meta;
      body.append(strong, small);
      btn.append(badge, body);
      btn.addEventListener("click", item.action);
      container.append(btn);
    }
  }
  $("#global-search-input")?.addEventListener("input", (e) => renderSearchResults(e.target.value));

  /* --- Lesson Focus Mode & Exit Confirmation Dialog --- */
  const runner = $("#learning-runner");
  const learningViewEl = $("#learning-view");
  if (runner) {
    const syncLessonFocus = () => {
      const active = !runner.classList.contains("hidden") && !learningViewEl?.classList.contains("hidden");
      document.body.classList.toggle("lesson-focus-mode", active);
    };
    const focusObserver = new MutationObserver(syncLessonFocus);
    focusObserver.observe(runner, { attributes: true, attributeFilter: ["class"] });
    if (learningViewEl) focusObserver.observe(learningViewEl, { attributes: true, attributeFilter: ["class"] });
    window.addEventListener("prepped:viewchange", syncLessonFocus);
    syncLessonFocus();
  }
  $("#learning-focus-exit")?.addEventListener("click", (e) => {
    openModal("lesson-exit-dialog", e.currentTarget);
  });
  $("#lesson-exit-keep")?.addEventListener("click", () => closeModal("lesson-exit-dialog"));
  $("#lesson-exit-confirm")?.addEventListener("click", () => {
    closeModal("lesson-exit-dialog");
    $("#learning-exit")?.click();
  });

  /* --- Career Studios Category Filter --- */
  const careerFilterBar = $("#career-filter-bar");
  if (careerFilterBar) {
    careerFilterBar.addEventListener("click", (e) => {
      const tab = e.target.closest("[data-career-filter]");
      if (!tab) return;
      const filter = tab.dataset.careerFilter;
      for (const btn of careerFilterBar.querySelectorAll("[data-career-filter]")) {
        const on = btn === tab;
        btn.classList.toggle("is-active", on);
        btn.setAttribute("aria-selected", String(on));
      }
      for (const card of $$("#career-studio-list .career-studio-card")) {
        const group = (card.dataset.filterGroup || "").toLowerCase();
        const titleText = (card.querySelector("h3")?.textContent || "").toLowerCase();
        const catText = (card.dataset.studioCategory || "").toLowerCase();
        const show =
          filter === "all" ||
          group === filter ||
          (!group && (
            (filter === "project" && (titleText.includes("project") || catText.includes("project"))) ||
            (filter === "hr" && (titleText.includes("hr") || catText.includes("behaviour"))) ||
            (filter === "technical" && (titleText.includes("technical") || catText.includes("computer-science")))
          ));
        card.classList.toggle("hidden", !show);
      }
    });
  }

  /* --- Memory Segmented Filter --- */
  const memoryFilterBar = $("#memory-filter-bar");
  if (memoryFilterBar) {
    memoryFilterBar.addEventListener("click", (e) => {
      const tab = e.target.closest("[data-memory-filter]");
      if (!tab) return;
      const filter = tab.dataset.memoryFilter;
      for (const btn of memoryFilterBar.querySelectorAll("[data-memory-filter]")) {
        const on = btn === tab;
        btn.classList.toggle("is-active", on);
        btn.setAttribute("aria-selected", String(on));
      }
      const reviewSection = $(".memory-review-section");
      if (filter === "due" && reviewSection) {
        reviewSection.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      }
      for (const card of $$("#memory-items > *")) {
        const text = card.textContent.toLowerCase();
        const show = filter === "all" || filter === "due" || text.includes(filter);
        card.classList.toggle("hidden", !show);
      }
    });
  }

  /* --- Progress 4-Tab Workspace (Overview · Plan & Goals · Skills · Backup & Data) --- */
  function setProgressTab(tabKey) {
    const bar = $("#progress-tabs");
    if (!bar) return;
    for (const btn of bar.querySelectorAll("[data-progress-tab]")) {
      const on = btn.dataset.progressTab === tabKey;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", String(on));
    }
    for (const panel of $$("#progress-view [data-progress-panel]")) {
      panel.classList.toggle("hidden", panel.dataset.progressPanel !== tabKey);
    }
  }
  $("#progress-tabs")?.addEventListener("click", (e) => {
    const tab = e.target.closest("[data-progress-tab]");
    if (tab) setProgressTab(tab.dataset.progressTab);
  });

  /* --- History 2-Tab Workspace (All activity · Project sessions) --- */
  function setHistoryTab(tabKey) {
    const bar = $("#history-tabs");
    if (!bar) return;
    for (const btn of bar.querySelectorAll("[data-history-tab]")) {
      const on = btn.dataset.historyTab === tabKey;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", String(on));
    }
    for (const panel of $$("#history-view [data-history-panel]")) {
      panel.classList.toggle("hidden", panel.dataset.historyPanel !== tabKey);
    }
  }
  $("#history-tabs")?.addEventListener("click", (e) => {
    const tab = e.target.closest("[data-history-tab]");
    if (tab) setHistoryTab(tab.dataset.historyTab);
  });

  window.PreppedUI = { setProgressTab, setHistoryTab, openModal, closeModal };

  /* --- 6-Step Guided Onboarding Modal (backed by /api/profile + localStorage resume) --- */
  const ONBOARD_KEY = "prepped:onboarding_draft_v1";
  let onboardStep = 1;
  let onboardData = {
    goals: ["english_fluency", "placement_interviews"],
    confidence: "developing",
    dailyMinutes: 10,
    quickAnswer: "",
  };

  function saveOnboardDraft() {
    try {
      localStorage.setItem(ONBOARD_KEY, JSON.stringify({ step: onboardStep, data: onboardData }));
    } catch {}
  }

  function loadOnboardDraft() {
    try {
      const raw = localStorage.getItem(ONBOARD_KEY);
      if (!raw) return false;
      const parsed = JSON.parse(raw);
      if (parsed && parsed.step >= 2 && parsed.step <= 5) {
        onboardStep = parsed.step;
        onboardData = { ...onboardData, ...(parsed.data || {}) };
        return true;
      }
    } catch {}
    return false;
  }

  function openOnboarding(trigger) {
    const resumed = loadOnboardDraft();
    if (!resumed) onboardStep = 1;
    $("#onboarding-resume-banner")?.classList.toggle("hidden", !resumed);
    renderOnboardingStep();
    openModal("onboarding-modal", trigger);
  }

  function renderOnboardingStep() {
    const body = $("#onboarding-step-body");
    const err = $("#onboarding-error");
    const pb = $("#onboarding-pb-fill");
    const count = $("#onboarding-step-count");
    const backBtn = $("#onboarding-back");
    const skipBtn = $("#onboarding-skip");
    const nextBtn = $("#onboarding-next");
    if (!body) return;
    if (err) err.textContent = "";
    if (pb) pb.style.width = Math.round((onboardStep / 6) * 100) + "%";
    if (count) count.textContent = onboardStep + "/6";
    if (backBtn) backBtn.disabled = onboardStep <= 1;
    if (skipBtn) skipBtn.classList.toggle("hidden", onboardStep === 1 || onboardStep === 6);
    if (nextBtn) nextBtn.textContent = onboardStep === 1 ? "Get started →" : onboardStep === 6 ? "Save and start learning →" : "Continue →";

    if (onboardStep === 1) {
      body.innerHTML = `
        <div class="onboarding-welcome">
          <span class="chip t">Private · Stored on this device</span>
          <h2 id="onboarding-title">Speak with confidence, one practice at a time.</h2>
          <p>English, interviews, and project communication in a calm space where mistakes are welcome.</p>
          <p class="onboarding-note">Prepped does not store raw voice recordings.</p>
        </div>`;
    } else if (onboardStep === 2) {
      const opts = [
        ["english_fluency", "English fluency", "Speak more naturally"],
        ["placement_interviews", "Job interviews", "HR and technical rounds"],
        ["professional_communication", "Professional communication", "Emails, meetings, workplace"],
        ["project_communication", "Project explanations", "College and portfolio talks"],
      ];
      body.innerHTML = `
        <h2 id="onboarding-title">What do you want to improve?</h2>
        <p class="section-help">Choose all that apply. You can change this later in Profile.</p>
        <div class="opt-stack">${opts.map(([val, title, desc]) => {
          const on = onboardData.goals.includes(val);
          return `<button type="button" class="opt ${on ? "on" : ""}" data-goal="${val}" aria-pressed="${on}"><span class="bx ${on ? "on" : ""}" aria-hidden="true">${on ? "✓" : ""}</span><span><strong>${title}</strong><small>${desc}</small></span></button>`;
        }).join("")}</div>`;
      for (const btn of body.querySelectorAll("[data-goal]")) {
        btn.addEventListener("click", () => {
          const v = btn.dataset.goal;
          if (onboardData.goals.includes(v)) onboardData.goals = onboardData.goals.filter((g) => g !== v);
          else onboardData.goals.push(v);
          saveOnboardDraft();
          renderOnboardingStep();
        });
      }
    } else if (onboardStep === 3) {
      const levels = [
        ["beginner", "Just starting", "Short sentences feel hard"],
        ["developing", "Comfortable", "I can talk, but pause often"],
        ["confident", "Confident", "I want polish and precision"],
      ];
      body.innerHTML = `
        <h2 id="onboarding-title">Where are you starting?</h2>
        <p class="section-help">No wrong answer. You can change this any time.</p>
        <div class="opt-stack">${levels.map(([val, title, desc]) => {
          const on = onboardData.confidence === val;
          return `<button type="button" class="opt ${on ? "on" : ""}" data-level="${val}" aria-pressed="${on}"><span class="bx rd ${on ? "on" : ""}" aria-hidden="true"></span><span><strong>${title}</strong><small>${desc}</small></span></button>`;
        }).join("")}</div>`;
      for (const btn of body.querySelectorAll("[data-level]")) {
        btn.addEventListener("click", () => {
          onboardData.confidence = btn.dataset.level;
          saveOnboardDraft();
          renderOnboardingStep();
        });
      }
    } else if (onboardStep === 4) {
      body.innerHTML = `
        <h2 id="onboarding-title">How much time each day?</h2>
        <p class="section-help">Small and steady works best. Used as a personal target only.</p>
        <div class="time-choice-row">${[5, 10, 20].map((m) => `<button type="button" class="button ${onboardData.dailyMinutes === m ? "button-primary" : "button-secondary"}" data-mins="${m}">${m} min</button>`).join("")}</div>`;
      for (const btn of body.querySelectorAll("[data-mins]")) {
        btn.addEventListener("click", () => {
          onboardData.dailyMinutes = Number(btn.dataset.mins);
          saveOnboardDraft();
          renderOnboardingStep();
        });
      }
    } else if (onboardStep === 5) {
      const ans = onboardData.quickAnswer;
      body.innerHTML = `
        <span class="chip t">Quick warm-up</span>
        <h2 id="onboarding-title">Choose the clearer sentence.</h2>
        <div class="opt-stack">
          <button type="button" class="opt ${ans === "a" ? "on" : ""}" data-q="a"><span class="bx rd ${ans === "a" ? "on" : ""}"></span><span><strong>“I am having 2 years of experience.”</strong></span></button>
          <button type="button" class="opt ${ans === "b" ? "on" : ""}" data-q="b"><span class="bx rd ${ans === "b" ? "on" : ""}"></span><span><strong>“I have two years of experience.”</strong></span></button>
        </div>
        ${ans === "b" ? '<div class="al al-success"><div><strong>Correct.</strong> Use “have” for experience, not “am having”.</div></div>' : ""}
        ${ans === "a" ? '<div class="al al-attention"><div><strong>Try the other phrasing.</strong> In standard workplace English, use “I have…” rather than “I am having…” for experience.</div></div>' : ""}`;
      for (const btn of body.querySelectorAll("[data-q]")) {
        btn.addEventListener("click", () => {
          onboardData.quickAnswer = btn.dataset.q;
          saveOnboardDraft();
          renderOnboardingStep();
        });
      }
    } else {
      body.innerHTML = `
        <div class="onboarding-ready">
          <span class="chip g">Your path is ready</span>
          <h2 id="onboarding-title">Ready to begin</h2>
          <p class="section-help">Your primary focus and confidence level will be saved to your local profile. Progress is never deleted when you change goals.</p>
          <div class="opt"><span><strong>1. Explore your recommended lessons</strong><small>Short, step-by-step practice in Learn</small></span></div>
          <div class="opt"><span><strong>2. Try a calm voice or text rehearsal</strong><small>Project Practice or Career Studios</small></span></div>
        </div>`;
    }
  }

  $("#onboarding-back")?.addEventListener("click", () => {
    if (onboardStep > 1) {
      onboardStep -= 1;
      saveOnboardDraft();
      renderOnboardingStep();
    }
  });
  $("#onboarding-skip")?.addEventListener("click", () => {
    if (onboardStep < 6) {
      onboardStep += 1;
      saveOnboardDraft();
      renderOnboardingStep();
    }
  });
  $("#onboarding-next")?.addEventListener("click", async () => {
    if (onboardStep === 2 && onboardData.goals.length === 0) {
      const err = $("#onboarding-error");
      if (err) err.textContent = "Choose at least one goal to continue, or skip this step.";
      return;
    }
    if (onboardStep < 6) {
      onboardStep += 1;
      saveOnboardDraft();
      renderOnboardingStep();
      return;
    }
    // Step 6: persist primary_goal & confidence_level via existing /api/profile contract
    try {
      const primaryGoal = onboardData.goals[0] || "placement_interviews";
      const areaMap = {
        english_fluency: "speaking_fluency",
        placement_interviews: "hr_interviews",
        professional_communication: "professional_communication",
        project_communication: "project_explanation",
      };
      const improvementAreas = onboardData.goals.map((g) => areaMap[g]).filter(Boolean);
      const res = await fetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_goal: primaryGoal,
          confidence_level: onboardData.confidence,
          improvement_areas: improvementAreas,
        }),
      });
      if (!res.ok) throw new Error("Could not save profile settings.");
      try { localStorage.removeItem(ONBOARD_KEY); } catch {}
      closeModal("onboarding-modal");
      showToast("Profile updated on this device.");
      $("#dashboard-refresh")?.click();
    } catch (error) {
      const err = $("#onboarding-error");
      if (err) err.textContent = error.message || "Could not save profile.";
    }
  });
})();
