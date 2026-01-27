"""
Rule-based validators for rewrite suggestions.

These validators enforce constraints to prevent hallucinations and ensure
quality. They run after AI generation to catch violations deterministically.
"""
import re
from collections import Counter
from typing import Optional

from app.models.content_unit import ContentUnit, ParsedResume
from app.models.rewrite import RewriteSuggestion


class ValidatorResult:
    """Result of validating a rewrite suggestion."""

    def __init__(
        self,
        passed: bool,
        risk_score: float,
        violations: list[str],
        warnings: list[str],
    ):
        self.passed = passed
        self.risk_score = risk_score  # 0.0 (low risk) to 1.0 (high risk)
        self.violations = violations  # Critical issues that should block the suggestion
        self.warnings = warnings  # Non-critical issues that should be flagged

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"ValidatorResult({status}, risk={self.risk_score:.2f}, violations={len(self.violations)}, warnings={len(self.warnings)})"


def validate_suggestion(
    suggestion: RewriteSuggestion,
    original_unit: ContentUnit,
    all_resume_units: list[ContentUnit],
    jd_signals: Optional[dict] = None,
) -> ValidatorResult:
    """
    Run all validators on a rewrite suggestion.

    Args:
        suggestion: The rewrite suggestion to validate
        original_unit: The original content unit
        all_resume_units: All content units in the resume (for context)
        jd_signals: Optional JD signals for keyword checking

    Returns:
        ValidatorResult with pass/fail status, risk score, violations, and warnings
    """
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    # Run all validators
    result_no_new_tools = _validate_no_new_tools_metrics(suggestion, original_unit, all_resume_units)
    result_length = _validate_length(suggestion, original_unit)
    result_keyword_stuffing = _validate_keyword_stuffing(suggestion, original_unit, jd_signals)
    result_repetition = _validate_repetition(suggestion, all_resume_units)
    result_tense = _validate_tense_consistency(suggestion, original_unit)

    # Collect violations and warnings
    for result in [result_no_new_tools, result_length, result_keyword_stuffing, result_repetition, result_tense]:
        violations.extend(result.violations)
        warnings.extend(result.warnings)
        risk_score = max(risk_score, result.risk_score)

    # Determine if passed (no critical violations)
    passed = len(violations) == 0

    return ValidatorResult(
        passed=passed,
        risk_score=risk_score,
        violations=violations,
        warnings=warnings,
    )


def _validate_no_new_tools_metrics(
    suggestion: RewriteSuggestion, original_unit: ContentUnit, all_resume_units: list[ContentUnit]
) -> ValidatorResult:
    """
    Validate that no new tools, technologies, or metrics were added.

    This prevents hallucinations by ensuring only existing content is referenced.
    """
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    original_text = original_unit.content.lower()
    suggested_text = suggestion.suggested_text.lower()

    # Extract all skills/tools from the entire resume
    all_resume_text = " ".join([unit.content.lower() for unit in all_resume_units])

    # Common tech/tool patterns (can be expanded)
    tech_patterns = [
        r"\b(python|java|javascript|typescript|go|rust|ruby|php|swift|kotlin|c\+\+|c#|scala|r|matlab)\b",
        r"\b(react|angular|vue|django|flask|fastapi|express|spring|rails|laravel|asp\.net|next\.js)\b",
        r"\b(postgresql|mysql|mongodb|redis|cassandra|elasticsearch|dynamodb|oracle|sql server)\b",
        r"\b(aws|azure|gcp|docker|kubernetes|jenkins|git|github|gitlab|terraform|ansible)\b",
        r"\b(rest|graphql|api|microservices|ci/cd|devops|agile|scrum)\b",
    ]

    # Extract tools/tech from suggested text
    suggested_tools = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, suggested_text, re.IGNORECASE)
        suggested_tools.update([m.lower() if isinstance(m, str) else m for m in matches])

    # Extract tools/tech from original text
    original_tools = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        original_tools.update([m.lower() if isinstance(m, str) else m for m in matches])

    # Extract tools/tech from entire resume
    resume_tools = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, all_resume_text, re.IGNORECASE)
        resume_tools.update([m.lower() if isinstance(m, str) else m for m in matches])

    # Check for new tools not in original or resume
    new_tools = suggested_tools - original_tools - resume_tools

    if new_tools:
        violations.append(f"Added new tools/technologies not in resume: {', '.join(new_tools)}")
        risk_score = max(risk_score, 1.0)  # Critical violation

    # Check for metrics/numbers (percentages, counts, etc.)
    metric_pattern = r"\b(\d+%|\d+\+|\d+k|\d+M|\d+\.\d+%|\$\d+[KM]?)\b"
    original_metrics = set(re.findall(metric_pattern, original_text))
    suggested_metrics = set(re.findall(metric_pattern, suggested_text))

    new_metrics = suggested_metrics - original_metrics
    if new_metrics:
        violations.append(f"Added new metrics/numbers not in original: {', '.join(new_metrics)}")
        risk_score = max(risk_score, 1.0)  # Critical violation

    return ValidatorResult(passed=len(violations) == 0, risk_score=risk_score, violations=violations, warnings=warnings)


def _validate_length(suggestion: RewriteSuggestion, original_unit: ContentUnit) -> ValidatorResult:
    """
    Validate that the suggestion doesn't exceed length caps.

    Bullet points should be concise for ATS parsing.
    """
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    original_length = len(original_unit.content)
    suggested_length = len(suggestion.suggested_text)

    # Length caps based on content type
    max_lengths = {
        "experience_bullet": 200,  # ~30 words
        "summary": 500,  # ~75 words
        "skills_line": 300,  # ~45 words
        "project_description": 200,
        "education_description": 150,
    }

    max_length = max_lengths.get(original_unit.type, 200)

    if suggested_length > max_length:
        violations.append(
            f"Exceeds length cap ({suggested_length} chars > {max_length} chars for {original_unit.type})"
        )
        risk_score = max(risk_score, 0.8)

    # Warning if significantly longer than original
    if suggested_length > original_length * 1.3:
        warnings.append(f"Significantly longer than original ({suggested_length} vs {original_length} chars)")
        risk_score = max(risk_score, 0.3)

    return ValidatorResult(passed=len(violations) == 0, risk_score=risk_score, violations=violations, warnings=warnings)


def _validate_keyword_stuffing(
    suggestion: RewriteSuggestion, original_unit: ContentUnit, jd_signals: Optional[dict] = None
) -> ValidatorResult:
    """
    Detect keyword stuffing (unnatural repetition of keywords).
    """
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    suggested_text = suggestion.suggested_text.lower()

    # Extract JD keywords if available
    jd_keywords = []
    if jd_signals and "hard_skills" in jd_signals:
        jd_keywords = [skill.get("name", "").lower() for skill in jd_signals["hard_skills"]]

    # Count word frequency
    words = re.findall(r"\b\w+\b", suggested_text)
    word_counts = Counter(words)

    # Check for excessive repetition of any word (more than 3 times in a short text)
    for word, count in word_counts.items():
        if len(word) > 3 and count > 3:  # Ignore short words like "the", "and"
            if word in jd_keywords:
                violations.append(f"Keyword stuffing detected: '{word}' appears {count} times")
                risk_score = max(risk_score, 0.9)
            else:
                warnings.append(f"Repeated word: '{word}' appears {count} times")
                risk_score = max(risk_score, 0.4)

    # Check for unnatural JD keyword density
    if jd_keywords:
        jd_keyword_count = sum(word_counts.get(kw, 0) for kw in jd_keywords)
        total_words = len(words)
        if total_words > 0:
            keyword_density = jd_keyword_count / total_words
            if keyword_density > 0.3:  # More than 30% JD keywords
                warnings.append(f"High JD keyword density: {keyword_density:.1%} (may appear unnatural)")
                risk_score = max(risk_score, 0.5)

    return ValidatorResult(passed=len(violations) == 0, risk_score=risk_score, violations=violations, warnings=warnings)


def _validate_repetition(suggestion: RewriteSuggestion, all_resume_units: list[ContentUnit]) -> ValidatorResult:
    """
    Check for verb repetition across the resume.

    Using the same verb too often reduces impact.
    """
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    # Common action verbs
    action_verbs = [
        "develop",
        "design",
        "implement",
        "build",
        "create",
        "maintain",
        "optimize",
        "improve",
        "manage",
        "lead",
        "deliver",
        "achieve",
        "increase",
        "reduce",
        "deploy",
        "configure",
        "automate",
        "analyze",
        "collaborate",
    ]

    suggested_text = suggestion.suggested_text.lower()
    suggested_verbs = [verb for verb in action_verbs if verb in suggested_text]

    # Count verb usage across all resume units
    all_text = " ".join([unit.content.lower() for unit in all_resume_units])
    verb_counts = Counter([verb for verb in action_verbs if verb in all_text])

    # Check if suggested verb is overused
    for verb in suggested_verbs:
        count = verb_counts.get(verb, 0)
        if count >= 5:  # Verb used 5+ times across resume
            warnings.append(f"Verb '{verb}' is overused ({count} times across resume)")
            risk_score = max(risk_score, 0.4)

    return ValidatorResult(passed=len(violations) == 0, risk_score=risk_score, violations=violations, warnings=warnings)


def _validate_tense_consistency(suggestion: RewriteSuggestion, original_unit: ContentUnit) -> ValidatorResult:
    """
    Validate that verb tense is consistent with original.
    """
    violations: list[str] = []
    warnings: list[str] = []
    risk_score = 0.0

    original_text = original_unit.content.lower()
    suggested_text = suggestion.suggested_text.lower()

    # Past tense indicators
    past_tense_words = [
        "developed",
        "designed",
        "implemented",
        "created",
        "built",
        "managed",
        "led",
        "improved",
        "optimized",
        "delivered",
        "achieved",
        "increased",
        "reduced",
        "maintained",
        "deployed",
        "configured",
        "automated",
        "analyzed",
        "collaborated",
    ]

    # Present tense indicators
    present_tense_words = [
        "develop",
        "design",
        "implement",
        "create",
        "build",
        "manage",
        "lead",
        "improve",
        "optimize",
        "deliver",
        "achieve",
        "increase",
        "reduce",
        "maintain",
        "deploy",
        "configure",
        "automate",
        "analyze",
        "collaborate",
    ]

    # Determine original tense
    original_has_past = any(word in original_text for word in past_tense_words)
    original_has_present = any(word in original_text for word in present_tense_words)

    # Determine suggested tense
    suggested_has_past = any(word in suggested_text for word in past_tense_words)
    suggested_has_present = any(word in suggested_text for word in present_tense_words)

    # Check for tense inconsistency
    if original_has_past and suggested_has_present and not suggested_has_past:
        violations.append("Tense inconsistency: Original uses past tense, suggestion uses present tense")
        risk_score = max(risk_score, 0.9)

    if original_has_present and suggested_has_past and not suggested_has_present:
        violations.append("Tense inconsistency: Original uses present tense, suggestion uses past tense")
        risk_score = max(risk_score, 0.9)

    return ValidatorResult(passed=len(violations) == 0, risk_score=risk_score, violations=violations, warnings=warnings)
