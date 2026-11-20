# Prepped Content Review Log

**Content versions:** curriculum 1.2.0; Career Studios 1.3.0  
**Review date:** 2026-11-20  
**Review type:** AI-assisted editorial audit; qualified human sign-off is still required.

## Review method

The audit checked unique IDs, track/unit/lesson references, prerequisite cycles, lesson outcomes, completion conditions, worked examples, exercise prompts, objective answer keys and explanations, open-response self-review guidance, audio transcripts, Career Studio question mappings, and source references.

This is not a claim of independent teacher, language-specialist, or CS-expert review. A qualified human reviewer must record their name/role, date, exact content version, changes, and unresolved disagreements before release-candidate content is called fully reviewed.

## Curriculum inventory

| Area | Count | Review note |
|---|---:|---|
| Skills | 14 | Active skills must be covered by a lesson or mapped Career Studio |
| Tracks | 4 | Explicit outcomes and studio links are recorded |
| Units | 9 | Existing unit outcomes and lesson membership retained |
| Lessons | 14 | Completion conditions and review metadata added |
| Exercises | 49 | Seven supported types; open responses remain self-review |
| Listening exercises | 5 | Each retains audio text and transcript |
| Pronunciation exercises | 2 | Each retains a transcript and non-scoring self-review guidance |

## Lesson-by-lesson review

| Lesson | Main outcome focus | Source register | Review disposition |
|---|---|---|---|
| sentence-building | Complete and focused sentences | Authored examples; no external factual claim | AI-assisted editorial review; human language review pending |
| sentence-shaping | Add useful detail without changing facts | Authored examples | AI-assisted editorial review; human language review pending |
| grammar-in-context | Tense, articles, prepositions in context | British Council present/past simple, questions, articles, and adjective-preposition references | AI-assisted source check; human language review pending |
| question-formation | Present/past question forms and clarification | British Council grammar, articles, and adjective-preposition references | AI-assisted source check; human language review pending |
| vocabulary-in-context | Precise words in a study/project context | Authored examples | AI-assisted editorial review; human language review pending |
| phrases-for-study | Collocations and phrasal verbs | Cambridge Dictionary carry out / look into | AI-assisted source check; human language review pending |
| listening-for-details | Distinguish completed, current, and planned actions | Authored audio/text pair | AI-assisted editorial review; learner comprehension not validated |
| listening-conversations | Identify request, response, and next action | Authored audio/text pairs | AI-assisted editorial review; learner comprehension not validated |
| speaking-structured | Context, action, detail, and retelling | Authored prompts | AI-assisted editorial review; human language review pending |
| speaking-opinions | Compare, support, and acknowledge alternatives | Authored prompts | AI-assisted editorial review; human language review pending |
| pronunciation-self-review | Private listen/repeat and self-review | Authored model phrases | AI-assisted editorial review; no pronunciation scoring |
| structured-project-summary | Problem, approach, intended user | Authored example | AI-assisted editorial review; human communication review pending |
| specific-explanations | Specific claims, evidence, limitations | Authored examples | AI-assisted editorial review; human communication review pending |
| baseline-check | Low-stakes starting snapshot | Authored prompts | AI-assisted editorial review; not a level test |

## Career Studio mapping and sources

| Studio | Skills mapped | Source register | Review disposition |
|---|---|---|---|
| Project Explanation | Project summary, clarity, project explanation, interview readiness | None required for authored prompts | AI-assisted editorial review; human communication review pending |
| HR & Behavioural | Behavioural interviews, professional communication, confidence | None required for authored prompts | AI-assisted editorial review; human communication review pending |
| Technical Fundamentals | Technical interviews, clarity | OpenDSA lists; MDN HTTP status; PostgreSQL indexes; OSTEP | AI-assisted source check; human CS review pending |

## Source register

### Curriculum
- British Council LearnEnglish — [Present simple](https://learnenglish.britishcouncil.org/free-resources/grammar/english-grammar-reference/present-simple), [Past simple](https://learnenglish.britishcouncil.org/free-resources/grammar/english-grammar-reference/past-simple), [Questions and negatives](https://learnenglish.britishcouncil.org/free-resources/grammar/english-grammar-reference/questions-negatives), [Articles](https://learnenglish.britishcouncil.org/free-resources/grammar/a1-a2-grammar/articles-a-an-the), and [Adjectives and prepositions](https://learnenglish.britishcouncil.org/free-resources/grammar/a1-a2/adjectives-prepositions).
- Cambridge Dictionary — [carry out](https://dictionary.cambridge.org/dictionary/english/carry-out) and [look into](https://dictionary.cambridge.org/dictionary/english/look-into).

### Technical interview studio
- Virginia Tech OpenDSA — [Lists and linked lists](https://opendsa.cs.vt.edu/ODSA/StandaloneModules/20231208145515/html/ListIntro.html).
- MDN Web Docs — [HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).
- PostgreSQL Global Development Group — [Indexes](https://www.postgresql.org/docs/current/indexes.html).
- Remzi H. and Andrea C. Arpaci-Dusseau — [Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/).

## Outstanding human review

- [ ] English grammar and usage review.
- [ ] Vocabulary and collocation review.
- [ ] CS fundamentals review (data structures, HTTP, indexes, processes/threads).
- [ ] Interview/behavioural prompt review for clarity, fairness, and cultural breadth.
- [ ] Accessibility review with keyboard and assistive technology.


## Exercise-level review metadata (curriculum 1.2.0)

A follow-up engineering pass added metadata to all 49 exercises:
- A specific learner-facing outcome derived from the task being practised.
- A 1–2 minute effort estimate, included within the parent lesson's total estimate.
- Explicit inherited skill_ids and source_ids, so an exercise cannot silently drift away from the lesson's declared learning context or source register.

The curriculum loader now rejects missing outcomes, invalid effort values, exercise effort totals that exceed the lesson estimate, and mismatched inherited skill/source references. Regression tests cover these conditions. This is structural/editorial quality control, not evidence that the estimates match actual learner time or that the outcomes have been validated with learners. Those require human review and usability evidence.
