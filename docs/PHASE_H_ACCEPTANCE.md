# Phase H — Adaptive Learning Intelligence

**Status:** Phase H implementation and automated CI are green on commit ba5d4091c3679afe6b261852ca87f2940ba40877. Target-laptop and learner validation are deliberately deferred.  
**Architecture:** Existing FastAPI + SQLite + plain HTML/CSS/JavaScript modular monolith. No required external service or AI API.  
**Database:** Additive schema version 4. Existing version 3 backups remain restorable.

## Delivered scope

### H1 — Evidence-backed learner skill profile

- Skill records are derived from the existing versioned curriculum's active skill IDs. The HR/behavioural and technical IDs are also surfaced only as clearly labelled practice-evidence views for their already implemented Career studios while their curriculum lessons remain planned; no missing lesson curriculum is implied. There is no duplicated persistent learner-skill table.
- Lesson attempts, authored closed-exercise outcomes, open self-review responses, project-practice activity, Career studio activity, and explicitly learner-approved lesson-, project-practice-, and Career-session-linked memory reviews are represented as distinct evidence types.
- Closed-exercise correctness is included only for authored choice, vocabulary, listening, and ordering exercises where the existing lesson engine already has an answer key.
- Reflection, short response, pronunciation self-review, project practice, Career sessions, and Career heuristic feedback are never treated as objectively graded performance.
- Evidence shows source type/ID, activity title, timestamp, freshness, count/coverage, and explicit limitations. Evidence lists are bounded to recent source records.
- Conservative states are descriptive (Not enough evidence, Practice recorded, Revisit suggested, Mixed exercise evidence, Repeated correct responses observed, or One closed-exercise response observed). None is a proficiency or mastery label.
- Freshness is shown as recent (0–14 days), ageing (15–45 days), stale (46+ days), or unknown. Evidence coverage is shown as none, limited, some, or broader; it is not a percentage score.

### H2 — Deterministic adaptive learning engine

- Recommendations use recent repeated review-needed closed-exercise responses, declared curriculum prerequisites, the learner's saved profile route, due memory items, and active learner-owned goals.
- Every recommendation includes a reason and source. Recommendations can be dismissed and restored using the existing local preference table.
- Learners can override a recommendation by selecting any authored lesson, interview studio, or project-practice activity for their plan.
- Profile-based routing remains the fallback when there is little or no evidence.
- The current curriculum does not declare difficulty metadata. Therefore Phase H adapts ordering and selection only; it does not invent questions or silently change exercise difficulty.

### H3 — Daily and weekly learning plan

- Daily plans combine up to two due memory reviews, a suitable lesson, and optional Career/project practice where the learner's profile/goals and time budget support it.
- Weekly generation creates seven dated daily plans, avoids repeating lesson and revision targets within the generated week, and places optional interview/project practice on separate days.
- Learners choose a 5–180 minute daily budget, regenerate pending suggestions, add activities, reorder items, and skip/restore items.
- Plan completion is derived from a saved linked memory review, completed lesson, completed Career session, or completed project-practice session after that plan item was created. It is not a self-awarded completion or skill rating.
- Existing completed/skipped items are preserved on regeneration. New items respect the day's time budget.

### H4 — Evidence-based analytics and history

- Skill cards show source-linked recent evidence and distinguish practice activity, closed-exercise outcomes, open self-review, and linked learner-rated revision.
- The dashboard shows 30-day saved activity, due revision, learner-rated Again/Hard/Good/Easy revision counts, repeated review-needed exercises, evidence freshness, and active-goal-aware next steps.
- The interface explicitly states that the data is not a composite ability score, certified proficiency, confidence measure, learning-gain claim, or placement prediction.

## API and persistence

- GET /api/intelligence/catalog
- GET /api/intelligence/overview
- GET /api/intelligence/plan?plan_date=YYYY-MM-DD
- POST /api/intelligence/plan/generate
- GET /api/intelligence/plan/week?week_start=YYYY-MM-DD
- POST /api/intelligence/plan/week/generate
- POST /api/intelligence/plan/items
- PATCH /api/intelligence/plan/items/{item_id}
- POST /api/intelligence/recommendations/dismiss
- POST /api/intelligence/recommendations/restore

The two additive tables are adaptive_plans and adaptive_plan_items. Skill evidence is computed from existing source tables; no duplicate skill state needs synchronization. SQLite schema version is now 4.

Backup export includes both new tables. Restore accepts version 4 backups and migrates version 3 backups by initialising the new tables empty, preserving all older learner data. Restore still validates in a temporary database before replacing current data.

## Automated regression coverage added

- Empty/sparse evidence remains explicitly insufficient.
- Closed exercise outcomes and open self-review remain separate.
- Repeated review-needed responses suggest a linked lesson.
- Conflicting correct/review-needed responses remain mixed, not collapsed into a score.
- Stale evidence is visibly stale.
- Declared prerequisites and saved profile goals shape recommendations.
- Lesson-, project-practice-, and Career-linked memory reviews appear as revision activity, not mastery evidence.
- Daily plan completion requires the linked saved activity.
- Due memory review appears in the plan and completes only after an actual review.
- Weekly generation creates seven days without duplicate lesson assignments.
- Learner add/skip/reorder and time-budget constraints are covered, including regeneration after a completed activity with a smaller time budget.
- Active goals influence next steps and plans.
- Adaptive dismiss/restore is covered.
- Backup round-trip includes plans; version 3 backup restore compatibility is covered.
- Browser acceptance covers evidence rendering and daily/weekly plan generation.
- Static unsafe-HTML-sink checks and JavaScript syntax CI now include static/intelligence.js.

## Remaining gates

- [x] Final GitHub Actions run passes: [run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261) — 134 passed, 2 optional espeak-ng skips, 1 Starlette deprecation warning. Python compilation, seven JS syntax checks, dependency consistency, pip-audit, API tests, and Chromium browser acceptance passed.
- [x] Recording lifecycle hardening (Phase G.1) passes its deferred-permission browser regressions in the same green CI run.
- [ ] Manual Omarchy acceptance: progress evidence, recommendation dismissal/restore, daily and weekly plan generation, add/skip/reorder/regenerate, plan completion from saved activity, and backup/restore with plans.
- [ ] Manual accessibility and responsive review across Progress/Adaptive Learning.
- [ ] Learner wording and usefulness review; no pilot results or learning outcomes are claimed.

## Known limitations

- This is deterministic local adaptation, not an AI tutor or a validated adaptive-learning model.
- No difficulty adjustment is performed because the authored curriculum currently has no difficulty metadata.
- Objective outcomes exist only for the authored closed exercises; open answers and Career feedback are not graded.
- A skill can have no evidence even when the learner practises outside the tracked app. Sparse data remains insufficient.
- Evidence counts can be linked to more than one curriculum skill when a lesson declares multiple skills; they are source-linked references, not unique learner-performance totals.
- Plans are local and user-triggered. There are no notifications, background jobs, or automatic daily scheduling.
- Existing application limitations remain: single-user loopback only, no authentication/multi-user isolation, unencrypted backups, and no public deployment support.

Do not mark Phase H fully accepted until the automated gates and later manual acceptance are recorded separately.


**Final automated evidence:** [GitHub Actions run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261), commit ba5d4091c3679afe6b261852ca87f2940ba40877. The two skips are optional espeak-ng tests because espeak-ng is not installed on the hosted runner. The single pytest warning is Starlette's httpx-backed TestClient deprecation. Manual device and learner acceptance remain unchecked by design.
