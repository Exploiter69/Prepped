# UI Stage 8 — Whole-app consistency & accessibility

## Implementation scope

Completed on `feature/learner-profile`:

- Added a keyboard-visible skip link to the main content landmark.
- Every primary workspace can receive programmatic focus when navigation changes; the focused destination is announced by its existing accessible section label.
- Primary navigation now has one synchronized active/current-page state for Home, Learn, Practice, Career, Progress, and History. Navigation buttons no longer expose disclosure-only `aria-expanded` semantics.
- Added missing navigation control relationships and consistent minimum touch/focus targets for common controls.
- Workspace changes respect the reduced-motion preference instead of always requesting smooth scrolling.
- Existing responsive navigation, visible focus indicators, and reduced-motion CSS remain intact.

No API, database/schema, curriculum, provider, dependency, learner-data, or route changes. Existing practice, learning, Career, Memory, Progress, History, voice, and backup/restore behavior is preserved.

## Automated checks

- Static regression checks: `tests/test_ui_stage8.py`.
- Browser acceptance: `test_stage8_skip_link_and_primary_navigation_are_accessible` in `tests/test_browser_acceptance.py`.
- Run `bash scripts/prepped.sh verify`; run the optional Chromium browser tests using the repository's documented browser-test setup.

Record the exact test count and CI result for the tested commit. A commit alone is not a verification result.

## Target-device acceptance — pending

- [ ] Keyboard-only: Tab to Skip to main content, activate it, and confirm focus reaches the main landmark.
- [ ] Keyboard-only: visit Home, Learn, Practice, Career, Progress, and History; confirm the visible destination and focused heading/landmark match.
- [ ] Screen reader: verify the active navigation item is announced as the current page, with no false expanded/collapsed state.
- [ ] Check navigation at desktop, tablet, and narrow mobile widths; verify no horizontal overflow and all six labels remain understandable.
- [ ] Check browser zoom at 200% and 400%, visible focus, form labels/errors/status announcements, and touch targets.
- [ ] Enable reduced motion in the operating system/browser; verify navigation does not force smooth scrolling and existing animations are reduced.
- [ ] Run representative journeys across Learning, project practice, Career, Memory, Progress, History, and backup/restore; confirm no behavior or learner data changed.
- [ ] Check browser console for errors during navigation and confirm hidden workspaces are not keyboard reachable.

Stage 8 implementation and automated coverage may be complete while this manual acceptance record remains open. Do not claim screen-reader or target-device acceptance without actually performing it.
