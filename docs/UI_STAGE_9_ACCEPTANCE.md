# UI Stage 9 — Final UI Acceptance & Release Integration

## Purpose
Stage 9 is the final integration gate for UI redesign Stages 1–8. It verifies that learner-facing workspaces operate as one coherent local application and connects UI acceptance evidence to the source-checkout release gate. This is integration and acceptance—not a new feature phase or visual redesign.

## Scope and boundaries
- Integrate Home, Learn, Practice, Career, Progress, and History through shared navigation.
- Preserve profile, lesson, project-session, Career, Memory, Progress, History, and backup/restore behavior.
- Confirm current-page semantics, destination focus, visible focus, and reduced-motion handling.
- Exercise all primary workspaces at desktop, tablet, and narrow mobile widths.
- Connect UI evidence to Phase L release review and the documented local verification command.
- Keep FastAPI + SQLite + HTML/CSS/JavaScript and the local-first, zero-required-cost boundary.

No new API, schema/migration, curriculum, provider, dependency, paid service, account system, deployment target, or learner-data collection is introduced.

## Implementation and automated coverage
- tests/test_ui_stage9.py checks the six primary workspace links, named destinations, and release-document/workflow integration.
- test_stage9_release_smoke_all_workspaces_at_supported_widths in tests/test_browser_acceptance.py traverses all six workspaces at 1280, 768, and 390 CSS pixels, checks active-page and focus behavior, reduced-motion mode, horizontal overflow, and uncaught browser exceptions.
- Existing Stage 5–8 regressions and learner-flow browser tests remain part of the full suite.
- CI runs pytest/browser tests on pushes to feature/** and pull requests to main or feature/learner-profile; see .github/workflows/tests.yml.

Run on the target laptop after pulling:

    cd ~/Prepped-repo
    git pull --ff-only origin feature/learner-profile
    source .venv/bin/activate
    bash scripts/prepped.sh verify

Record the exact commit and complete output. Local or CI success verifies only that commit and does not replace manual acceptance.

## Final manual UI acceptance — required on target laptop
Use a disposable test database for destructive journeys. Never use the only learner database for restore/delete testing.

### Shared shell and accessibility
- [ ] Keyboard-only: skip link, all six destinations, visible focus, focus reaches selected workspace, hidden views are not tabbable.
- [ ] Screen reader: navigation label/current-page announcement, headings, form labels, errors, and live statuses are understandable; no false expanded/collapsed semantics.
- [ ] Reduced motion: navigation does not force smooth scrolling.
- [ ] Zoom at 200% and 400%; no clipped controls or lost functionality.
- [ ] Desktop, tablet, and narrow mobile; no horizontal overflow; touch targets and labels remain usable.
- [ ] Browser console has no uncaught JavaScript errors through the navigation pass.

### Integrated learner journeys and data preservation
- [ ] Profile: create, edit, cancel, save, reload; profile changes do not alter practice history.
- [ ] Learn: open recommended lesson, complete exercise, resume/review; activity is accurately represented without proficiency claims.
- [ ] Practice: start, answer, skip, complete, retry, review, delete disposable session; text fallback works.
- [ ] Career: start studio, answer, review coaching, retry/resume, delete disposable session.
- [ ] Memory: save learner-selected item, review it, verify History reflects it.
- [ ] Progress: inspect activity/goals/plans/recommendations; test backup export and full replacement restore on disposable data; verify readiness and integrity.
- [ ] History: search/filter, open destinations, verify deletion refreshes timeline without orphaned records.
- [ ] Voice, if local tools are installed: permission, record/stop, editable transcript, playback/stop, cancellation on navigation, and text fallback. Record unavailable tools honestly; mocked CI is not real voice acceptance.
- [ ] Confirm raw audio is not persisted and learner data, backups, models, keys, or private transcripts are not added to Git.

## Release integration gate
Stage 9 engineering is accepted only when:
- [ ] Exact-commit CI is green.
- [ ] Target-laptop scripts/prepped.sh verify is green.
- [ ] Manual UI checks are completed or each unavailable item is explicitly deferred with reason and owner.
- [ ] Phase I voice and Phase J content/accessibility gates are resolved or explicitly deferred in release review.
- [ ] Phase L fresh-install, update/uninstall, backup recovery, restore-interruption, and operational observations are completed or explicitly deferred.
- [ ] Project licence decision is recorded before redistribution or release tag/archive.
- [ ] No public/LAN deployment, production readiness, security certification, or learner-study result is implied.

## Acceptance record
| Evidence | Result |
|---|---|
| Branch / commit SHA | |
| Date and target device/browser | |
| Local full verification | |
| Exact-commit CI run | |
| Shared shell / keyboard / screen reader | |
| Zoom / responsive / reduced motion | |
| Integrated learner journeys | |
| Voice provider and result (or unavailable) | |
| Data preservation / backup recovery | |
| Deferred blockers, reason, owner | |
| Release decision / licence | |

Status rule: implementation and automated coverage may be committed while target-device acceptance remains pending. Do not mark the final UI/release gate complete until evidence is recorded. No release is created by this stage alone.
