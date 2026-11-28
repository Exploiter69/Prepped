"""Deterministic, evidence-based speaking and transcript analytics (Pack A).

All metrics are derived strictly from the learner's submitted transcript and,
when recorded via voice, measured client-side capture timing. Nothing here
estimates CEFR levels, pronunciation accuracy, or placement probability.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

FILLER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("um", re.compile(r"\bum+\b", re.I)),
    ("uh", re.compile(r"\buh+\b", re.I)),
    ("er", re.compile(r"\berm?\b", re.I)),
    ("ah", re.compile(r"\bah+\b", re.I)),
    ("you know", re.compile(r"\byou\s+know\b", re.I)),
    ("i mean", re.compile(r"\bi\s+mean\b", re.I)),
    ("basically", re.compile(r"\bbasically\b", re.I)),
    ("actually", re.compile(r"\bactually\b", re.I)),
    ("literally", re.compile(r"\bliterally\b", re.I)),
    ("kind of", re.compile(r"\bkind\s+of\b", re.I)),
    ("sort of", re.compile(r"\bsort\s+of\b", re.I)),
    ("like", re.compile(r"(?:,\s*|\b(?:is|was|are|were|it|just|so|and|but)\s+)\blike\b", re.I)),
)

GRAMMAR_HEURISTICS: tuple[tuple[str, re.Pattern[str], str, str, str], ...] = (
    (
        "progressive_have",
        re.compile(r"\b(?:i\s+am|i'm|we\s+are|he\s+is|she\s+is)\s+having\b", re.I),
        "Used continuous form 'having' for possession or experience.",
        "In standard interview English, 'have' is normally used for skills, projects, or years of experience.",
        "Try replacing 'I am having...' with 'I have...'.",
    ),
    (
        "myself_intro",
        re.compile(r"\b[Mm]yself\s+[A-Z][a-z]+\b"),
        "Introduced yourself with 'Myself [Name]'.",
        "In formal interviews, 'Myself' is reflexive rather than a subject pronoun.",
        "Open directly with 'I am [Name]' or 'My name is [Name]'.",
    ),
    (
        "redundant_phrase",
        re.compile(r"\b(revert\s+back|return\s+back|repeat\s+again|more\s+better|discuss\s+about|cope\s+up\s+with)\b", re.I),
        "Contains a common redundant phrasing.",
        "Trimming repeated words makes technical and workplace explanations sound crisper.",
        "Use the shorter form (for example, 'discuss', 'better', 'repeat', or 'cope with').",
    ),
    (
        "did_past_tense",
        re.compile(r"\b(?:did|didn't|did\s+not)\s+(went|built|made|wrote|tested|created|implemented|used|had|did)\b", re.I),
        "Paired 'did/didn't' with a past-tense verb.",
        "After 'did' or 'didn't', English uses the base verb (e.g., 'didn't build', not 'didn't built').",
        "Check the verb right after 'did' or 'didn't' and switch it to its base form.",
    ),
    (
        "passive_team_only",
        re.compile(r"\bwe\s+(?:did|made|built|worked\s+on)\b", re.I),
        "Described the work using 'we' without separating your own role.",
        "Interviewers listen for what you personally owned versus what the broader team did.",
        "Follow 'we' with one specific 'I...' sentence naming the part you built or tested.",
    ),
)

RELEVANT_VOCABULARY: tuple[str, ...] = (
    "architecture", "trade-off", "tradeoff", "constraint", "latency", "throughput",
    "validation", "migration", "endpoint", "automated", "integration", "regression",
    "scalability", "reliability", "bottleneck", "benchmark", "prototype", "modular",
    "responsible", "collaborated", "coordinated", "measured", "verified", "diagnosed",
    "prioritised", "prioritized", "refactored", "optimised", "optimized", "implemented",
)

STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "have", "were", "been", "they",
    "them", "their", "there", "about", "which", "when", "what", "where", "will",
    "would", "could", "should", "into", "then", "than", "also", "very", "just",
    "more", "some", "only", "your", "ours", "ourselves", "myself", "because",
    "project", "system", "work", "used", "using", "make", "made",
}


def _word_tokens(text: str) -> list[re.Match[str]]:
    return list(re.finditer(r"\b[A-Za-z][A-Za-z'-]*\b", text))


def _count_syllables(word: str) -> int:
    cleaned = re.sub(r"[^a-z]", "", word.lower())
    if not cleaned or len(cleaned) <= 3:
        return 1
    cleaned = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", cleaned)
    cleaned = re.sub(r"^y", "", cleaned)
    groups = re.findall(r"[aeiouy]{1,2}", cleaned)
    return max(1, len(groups))


def _sentences_with_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for match in re.finditer(r"[^.!?]+[.!?]?", text):
        raw = match.group(0)
        stripped = raw.strip()
        if not stripped:
            continue
        lead = len(raw) - len(raw.lstrip())
        start = match.start() + lead
        end = start + len(stripped)
        spans.append((start, end, stripped))
    return spans


def _pace_label(wpm: float | None) -> str:
    if wpm is None:
        return "Not measured (typed answer)"
    if wpm < 105:
        return "Unrushed pace"
    if wpm <= 155:
        return "Conversational pace"
    if wpm <= 185:
        return "Brisk pace"
    return "Fast pace — try pausing between points"


def analyze_transcript(
    text: str,
    *,
    duration_seconds: float | None = None,
    pause_count: int | None = None,
    silence_seconds: float | None = None,
) -> dict[str, Any]:
    """Produce honest, evidence-linked speaking and transcript analytics."""
    clean = text or ""
    tokens = _word_tokens(clean)
    word_count = len(tokens)
    sentences = _sentences_with_spans(clean)
    sentence_count = len(sentences)
    avg_words_per_sentence = round(word_count / sentence_count, 1) if sentence_count else 0.0

    lower_words = [m.group(0).lower() for m in tokens]
    unique_word_ratio = round(len(set(lower_words)) / word_count, 2) if word_count else 0.0

    valid_duration = (
        round(float(duration_seconds), 1)
        if duration_seconds is not None and duration_seconds >= 2.0
        else None
    )
    wpm = round((word_count / valid_duration) * 60.0, 1) if (valid_duration and word_count > 0) else None

    readability_band = "Not enough text"
    if word_count >= 12 and sentence_count >= 1:
        total_syllables = sum(_count_syllables(w) for w in lower_words)
        fk_grade = 0.39 * (word_count / sentence_count) + 11.8 * (total_syllables / word_count) - 15.59
        if fk_grade <= 7.5:
            readability_band = "Direct, easy-to-follow phrasing"
        elif fk_grade <= 11.5:
            readability_band = "Clear conversational / workplace phrasing"
        else:
            readability_band = "Dense phrasing — shorter sentences may sound clearer aloud"

    highlights: list[dict[str, Any]] = []
    filler_counts: Counter[str] = Counter()
    for label, pattern in FILLER_PATTERNS:
        for match in pattern.finditer(clean):
            span_text = match.group(0)
            if label == "like":
                sub = re.search(r"\blike\b", span_text, re.I)
                if not sub:
                    continue
                start = match.start() + sub.start()
                end = match.start() + sub.end()
                matched_word = clean[start:end]
            else:
                start, end = match.start(), match.end()
                matched_word = span_text
            filler_counts[label] += 1
            highlights.append({
                "category": "filler",
                "certainty": "confirmed_transcript_evidence",
                "start": start,
                "end": end,
                "text": matched_word,
                "what": f"Filler word detected: '{matched_word}'.",
                "why": "Occasional fillers are natural, but frequent fillers can blur key points during interviews.",
                "practice": "Try replacing filler words with a calm half-second silent pause.",
            })

    repeated_words: Counter[str] = Counter()
    for match in re.finditer(r"\b([A-Za-z]+)\s+\1\b", clean, re.I):
        word = match.group(1).lower()
        repeated_words[word] += 1
        highlights.append({
            "category": "repeated",
            "certainty": "confirmed_transcript_evidence",
            "start": match.start(),
            "end": match.end(),
            "text": match.group(0),
            "what": f"Immediate repetition: '{match.group(0)}'.",
            "why": "Word repetitions often happen while searching for the next thought mid-sentence.",
            "practice": "Slow the opening of your sentence slightly so the next phrase is ready.",
        })

    content_counts = Counter(w for w in lower_words if len(w) >= 4 and w not in STOPWORDS)
    overused_words = {word: count for word, count in content_counts.items() if count >= 4}
    for word, count in overused_words.items():
        seen = 0
        for tok in tokens:
            if tok.group(0).lower() == word:
                seen += 1
                if seen >= 3:
                    highlights.append({
                        "category": "repeated",
                        "certainty": "possible_issue",
                        "start": tok.start(),
                        "end": tok.end(),
                        "text": tok.group(0),
                        "what": f"'{word}' appears {count} times in this answer.",
                        "why": "Varying wording or tightening repeated clauses helps listeners track new points.",
                        "practice": "Check whether any repeated mention can be combined into one sharper sentence.",
                    })

    grammar_notes: list[dict[str, str]] = []
    for rule_id, pattern, what, why, practice in GRAMMAR_HEURISTICS:
        for match in pattern.finditer(clean):
            highlights.append({
                "category": "grammar_hint",
                "certainty": "possible_issue",
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0),
                "what": what,
                "why": why,
                "practice": practice,
            })
            grammar_notes.append({
                "rule_id": rule_id,
                "excerpt": match.group(0),
                "what": what,
                "why": why,
                "practice": practice,
            })

    long_sentences: list[dict[str, Any]] = []
    for start, end, sent in sentences:
        sent_words = len(_word_tokens(sent))
        if sent_words > 35:
            long_sentences.append({
                "word_count": sent_words,
                "excerpt": sent[:160] + ("…" if len(sent) > 160 else ""),
            })
            highlights.append({
                "category": "grammar_hint",
                "certainty": "possible_issue",
                "start": start,
                "end": min(end, start + 140),
                "text": clean[start : min(end, start + 140)],
                "what": f"Long sentence ({sent_words} words) without a full stop.",
                "why": "In spoken interviews, sentences over ~30 words are harder for listeners to follow in one breath.",
                "practice": "Split this thought into two shorter sentences: state the point first, then give the reason or example.",
            })

    vocab_found: list[str] = []
    vocab_seen: set[str] = set()
    for term in RELEVANT_VOCABULARY:
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.I)
        for match in pattern.finditer(clean):
            key = term.lower()
            if key not in vocab_seen:
                vocab_seen.add(key)
                vocab_found.append(match.group(0))
                highlights.append({
                    "category": "vocabulary",
                    "certainty": "confirmed_transcript_evidence",
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "what": f"Specific technical/professional term used: '{match.group(0)}'.",
                    "why": "Concrete terms anchor your explanation in real engineering work.",
                    "practice": "Keep pairing specific terms with one plain-language example or result.",
                })

    highlights.sort(key=lambda h: (h["start"], -(h["end"] - h["start"])))

    pause_analysis: dict[str, Any] = {
        "available": pause_count is not None or silence_seconds is not None,
        "pause_count": int(pause_count) if pause_count is not None else None,
        "silence_seconds": round(float(silence_seconds), 1) if silence_seconds is not None else None,
        "note": (
            f"{int(pause_count)} noticeable pause(s) recorded ({round(float(silence_seconds or 0.0), 1)}s quiet time)."
            if pause_count is not None
            else "Pause timing is measured only during microphone recording."
        ),
    }

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": avg_words_per_sentence,
        "unique_word_ratio": unique_word_ratio,
        "duration_seconds": valid_duration,
        "wpm": wpm,
        "pace_label": _pace_label(wpm),
        "readability_observation": readability_band,
        "pause_analysis": pause_analysis,
        "filler_total": sum(filler_counts.values()),
        "filler_counts": dict(filler_counts),
        "repeated_total": sum(repeated_words.values()) + len(overused_words),
        "repeated_words": dict(repeated_words),
        "overused_words": overused_words,
        "long_sentences": long_sentences,
        "grammar_observations": grammar_notes,
        "relevant_vocabulary": vocab_found,
        "highlights": highlights,
        "certainty_legend": {
            "confirmed_transcript_evidence": "Directly observed in your submitted transcript or measured recording timer.",
            "possible_issue": "Deterministic text pattern worth reviewing yourself; not a validated grammar verdict.",
            "suggestion": "Concrete next practice step you can try on your next attempt.",
        },
    }


def summarize_session_delivery(question_analytics: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate honest session-level speaking analytics across answered questions."""
    total_words = sum(a["word_count"] for a in question_analytics)
    recorded = [a for a in question_analytics if a["duration_seconds"] is not None]
    total_duration = round(sum(a["duration_seconds"] for a in recorded), 1) if recorded else None
    recorded_words = sum(a["word_count"] for a in recorded)
    avg_wpm = (
        round((recorded_words / total_duration) * 60.0, 1)
        if (total_duration and total_duration >= 2.0 and recorded_words > 0)
        else None
    )
    total_fillers = sum(a["filler_total"] for a in question_analytics)
    total_repeated = sum(a["repeated_total"] for a in question_analytics)
    total_long = sum(len(a["long_sentences"]) for a in question_analytics)
    total_grammar_hints = sum(len(a["grammar_observations"]) for a in question_analytics)
    vocab = sorted({v.lower() for a in question_analytics for v in a["relevant_vocabulary"]})
    pauses = [a["pause_analysis"]["pause_count"] for a in question_analytics if a["pause_analysis"]["pause_count"] is not None]
    silences = [a["pause_analysis"]["silence_seconds"] for a in question_analytics if a["pause_analysis"]["silence_seconds"] is not None]

    return {
        "recorded_answer_count": len(recorded),
        "total_duration_seconds": total_duration,
        "average_wpm": avg_wpm,
        "pace_label": _pace_label(avg_wpm),
        "total_words": total_words,
        "total_fillers": total_fillers,
        "total_repeated": total_repeated,
        "long_sentence_count": total_long,
        "grammar_hint_count": total_grammar_hints,
        "relevant_vocabulary": vocab[:20],
        "total_pauses": sum(pauses) if pauses else None,
        "total_silence_seconds": round(sum(silences), 1) if silences else None,
        "audio_retained": False,
        "audio_note": "Raw voice recordings are not stored permanently on disk. Temporary in-memory replay is cleared when you submit or leave.",
    }


def compare_attempts(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Produce an evidence-grounded comparison between two completed attempts."""
    prev_del = previous.get("delivery_summary") or {}
    curr_del = current.get("delivery_summary") or {}

    def _delta(a: float | int | None, b: float | int | None) -> float | int | None:
        if a is None or b is None:
            return None
        diff = b - a
        return round(diff, 1) if isinstance(diff, float) else diff

    prev_rubric = {r["criterion_id"]: r for r in previous.get("rubric_feedback", [])}
    improvements: list[str] = []
    recurring: list[str] = []
    rubric_changes: list[dict[str, Any]] = []

    for curr_r in current.get("rubric_feedback", []):
        old_r = prev_rubric.get(curr_r["criterion_id"])
        old_status = old_r["status"] if old_r else "not_enough_evidence"
        new_status = curr_r["status"]
        rubric_changes.append({
            "criterion_id": curr_r["criterion_id"],
            "label": curr_r["label"],
            "previous_status": old_status,
            "current_status": new_status,
        })
        if old_status != "evidence_found" and new_status == "evidence_found":
            improvements.append(f"{curr_r['label']}: evidence found in attempt {current['attempt_number']}.")
        elif old_status != "evidence_found" and new_status != "evidence_found":
            recurring.append(f"{curr_r['label']}: still worth strengthening.")

    filler_delta = _delta(prev_del.get("total_fillers", 0), curr_del.get("total_fillers", 0))
    if filler_delta is not None and filler_delta < 0:
        improvements.append(f"Detected filler words dropped by {abs(filler_delta)} compared with attempt {previous['attempt_number']}.")
    elif filler_delta is not None and filler_delta > 0:
        recurring.append(f"Detected filler words increased by {filler_delta}; pause briefly between sentences on your next pass.")

    wpm_delta = _delta(prev_del.get("average_wpm"), curr_del.get("average_wpm"))
    duration_delta = _delta(prev_del.get("total_duration_seconds"), curr_del.get("total_duration_seconds"))
    word_delta = _delta(previous.get("total_words", 0), current.get("total_words", 0))

    return {
        "previous_attempt": previous.get("attempt_number"),
        "current_attempt": current.get("attempt_number"),
        "metrics": {
            "previous_words": previous.get("total_words", 0),
            "current_words": current.get("total_words", 0),
            "word_delta": word_delta,
            "previous_duration_seconds": prev_del.get("total_duration_seconds"),
            "current_duration_seconds": curr_del.get("total_duration_seconds"),
            "duration_delta_seconds": duration_delta,
            "previous_wpm": prev_del.get("average_wpm"),
            "current_wpm": curr_del.get("average_wpm"),
            "wpm_delta": wpm_delta,
            "previous_fillers": prev_del.get("total_fillers", 0),
            "current_fillers": curr_del.get("total_fillers", 0),
            "filler_delta": filler_delta,
            "previous_long_sentences": prev_del.get("long_sentence_count", 0),
            "current_long_sentences": curr_del.get("long_sentence_count", 0),
        },
        "rubric_changes": rubric_changes,
        "improvements": improvements,
        "recurring_difficulties": recurring,
        "note": "Comparison reflects observable transcript and timing differences between attempts, not an objective fluency score.",
    }
