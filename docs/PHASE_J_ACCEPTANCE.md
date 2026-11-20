# Phase J — Curriculum Quality, Content Expansion & Learning Validation

**Status:** Initial implementation slice added; automated content validation and full regression suite must pass on the resulting commit. Human subject-matter review, accessibility review, and learner validation remain open.
**Cost and architecture:** No new runtime dependency, paid service, database, migration, or frontend framework. Content remains versioned local JSON.

## Initial audit

The branch baseline contained 14 skills, 4 tracks, 9 units, 14 lessons, and 49 exercises across seven exercise types. All listening and pronunciation exercises had transcript alternatives. Four interview-related skills had no linked lesson; those skills are now explicitly delivered through the existing Project Explanation, HR/Behavioural, and Technical Fundamentals studios rather than duplicating the same prompts as new lessons.

The existing validator already checked IDs, prerequisite cycles, exercise types, option references, and audio text alternatives. It did not require a source register, content-review disclosure, explicit lesson completion conditions, studio-to-skill mappings, or cross-file coverage.

## Implemented in this slice

- Curriculum schema advances to 1.2.0; Career Studio content advances to 1.3.0. Existing saved lesson/session snapshots remain self-contained and readable.
- Curriculum and Career Studio source registers record publisher, stable URL, check date, and what each source supports.
- Lessons declare source references, an explicit completion condition, and an AI-assisted editorial review record.
- Tracks declare observable learning outcomes and the Career Studios that support them.
- Interview skills previously marked planned are marked active only because their existing studios now declare matching outcomes and mappings.
- Every Career Studio and question declares learning outcomes and skill mappings; technical interview prompts link to OpenDSA, MDN, PostgreSQL, and OSTEP references.
- A cross-file linter checks active-skill coverage, exact skill-to-studio mappings, track-to-studio mappings, source references, and curriculum/studio metadata.
- The linter runs during app startup, in GitHub Actions, and through `python -m prepped.content_lint`.
- Objective exercise keys require explanations. Open responses remain private self-review and are not automatically graded.

## Content review record and limitations

This is an AI-assisted editorial review of wording, scaffolding, outcome alignment, source mapping, answer-key consistency, and text alternatives. It is not qualified teacher, language-specialist, or computer-science expert sign-off. Human review is still required before calling the curriculum release-ready. Source links support selected factual claims; they do not certify every example or prove the teaching sequence is effective.

## Accessibility and inclusion review

- Listening and pronunciation activities must retain a complete transcript/text alternative.
- Speaking practice can be completed by typing; recording is optional.
- Prompts use study, project, teamwork, and early-career contexts without requiring disclosure of personal, financial, institutional, or confidential information.
- The product must not grade accent, infer confidence/personality, or require audio participation.
- Existing keyboard, screen-reader smoke, contrast, and 375 px responsive checks remain in the regression suite. A human assistive-technology review is still pending.

## Learner validation

No learner study has been run and no learning gain is claimed. The protocol in [PHASE_J_LEARNER_STUDY_PROTOCOL.md](PHASE_J_LEARNER_STUDY_PROTOCOL.md) is ready for an optional, consent-based usability study. If participants are unavailable, report that plainly; do not fabricate results or block engineering on a pilot.

## Acceptance checklist

- [ ] `python -m prepped.content_lint` passes on the exact commit.
- [ ] Full pytest, Python compilation, JavaScript syntax checks, and GitHub Actions pass on the exact commit.
- [x] All 49 exercises declare a task-specific outcome, bounded effort estimate, and inherited lesson skill/source context; loader validation and regression tests enforce completeness and lesson effort budgets. Exact-commit CI remains required before this automated gate is accepted. Human confirmation that estimates and outcomes are instructionally appropriate remains pending.
- [ ] Human language/grammar review records reviewer, date, version, corrections, and unresolved disagreements.
- [ ] Human CS review records reviewer, date, version, corrections, and unresolved disagreements.
- [ ] Keyboard, screen-reader, contrast, zoom, captions/transcripts, and responsive review is recorded.
- [ ] Core English lesson, listening lesson, speaking lesson, project communication, HR/behavioural, and technical studio journeys are manually exercised.
- [ ] Optional usability protocol is either run and honestly reported or marked not run with the reason. No raw voice is collected by default.
- [ ] Current state and both roadmaps accurately distinguish implemented, automated-tested, human-reviewed, and learner-validated work.

**Exit rule:** do not mark Phase J complete until all release-candidate content has valid source references where factual claims require them, explicit outcomes and completion conditions, reviewed deterministic keys, accessible alternatives, human review records, passing automated/browser checks, and an honest learner-validation record.