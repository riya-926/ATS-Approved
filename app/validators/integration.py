"""
Integration helpers for using validators with rewrite suggestions.

This module provides helper functions to integrate validators into the
rewrite suggestion pipeline.
"""
from typing import Optional

from app.models.content_unit import ContentUnit, ParsedResume
from app.models.rewrite import RewriteSuggestion
from app.validators.scorer import score_suggestion
from app.validators.validator import validate_suggestion


def validate_and_score_suggestion(
    suggestion: RewriteSuggestion,
    original_unit: ContentUnit,
    resume: ParsedResume,
    jd_signals: Optional[dict] = None,
) -> tuple[float, dict]:
    """
    Validate and score a rewrite suggestion, updating its risk_score.

    This is the main integration point for using validators with rewrite suggestions.

    Args:
        suggestion: The rewrite suggestion to validate
        original_unit: The original content unit
        resume: The parsed resume (for context)
        jd_signals: Optional JD signals dict

    Returns:
        Tuple of (final_score, validation_info)
        final_score: 0.0-1.0 (higher is better)
        validation_info: Dict with validation details
    """
    # Run validators
    validator_result = validate_suggestion(
        suggestion, original_unit, resume.content_units, jd_signals
    )

    # Score the suggestion
    score, _ = score_suggestion(
        suggestion, original_unit, resume.content_units, jd_signals
    )

    # Update suggestion's risk_score
    suggestion.risk_score = validator_result.risk_score

    # Build validation info
    validation_info = {
        "passed": validator_result.passed,
        "risk_score": validator_result.risk_score,
        "final_score": score,
        "violations": validator_result.violations,
        "warnings": validator_result.warnings,
    }

    return score, validation_info


def filter_validated_suggestions(
    suggestions: list[RewriteSuggestion],
    resume: ParsedResume,
    jd_signals: Optional[dict] = None,
    min_score: float = 0.5,
) -> list[tuple[RewriteSuggestion, float, dict]]:
    """
    Filter and score suggestions, returning only those that pass validation.

    Args:
        suggestions: List of rewrite suggestions
        resume: Parsed resume
        jd_signals: Optional JD signals
        min_score: Minimum score threshold (default 0.5)

    Returns:
        List of tuples: (suggestion, score, validation_info)
        Only includes suggestions that pass validation and meet min_score
    """
    validated = []

    # Create mapping of content_unit_id to ContentUnit
    unit_map = {unit.id: unit for unit in resume.content_units}

    for suggestion in suggestions:
        original_unit = unit_map.get(suggestion.content_unit_id)
        if not original_unit:
            continue

        score, validation_info = validate_and_score_suggestion(
            suggestion, original_unit, resume, jd_signals
        )

        # Only include if passes validation and meets minimum score
        if validation_info["passed"] and score >= min_score:
            validated.append((suggestion, score, validation_info))

    # Sort by score (highest first)
    validated.sort(key=lambda x: x[1], reverse=True)

    return validated
