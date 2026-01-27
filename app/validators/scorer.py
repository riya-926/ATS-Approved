"""
Scoring system for rewrite suggestions.

Scores candidates and selects the best default suggestion based on:
- Validation results
- Confidence scores
- Risk scores
- Coverage improvement potential
"""
from typing import Optional

from app.models.content_unit import ContentUnit
from app.models.rewrite import RewriteSuggestion
from app.validators.validator import ValidatorResult, validate_suggestion


def score_suggestion(
    suggestion: RewriteSuggestion,
    original_unit: ContentUnit,
    all_resume_units: list[ContentUnit],
    jd_signals: Optional[dict] = None,
) -> tuple[float, ValidatorResult]:
    """
    Score a rewrite suggestion.

    Args:
        suggestion: The rewrite suggestion to score
        original_unit: Original content unit
        all_resume_units: All resume content units for context
        jd_signals: Optional JD signals for validation

    Returns:
        Tuple of (final_score, validator_result)
        final_score: 0.0-1.0 (higher is better)
    """
    # Run validators
    validator_result = validate_suggestion(suggestion, original_unit, all_resume_units, jd_signals)

    # Start with base confidence
    score = suggestion.confidence

    # Penalize for violations
    if validator_result.violations:
        score *= 0.1  # Heavy penalty for violations
    else:
        # Reduce score based on risk
        score *= (1.0 - validator_result.risk_score * 0.5)

    # Penalize for warnings (less severe)
    if validator_result.warnings:
        warning_penalty = min(len(validator_result.warnings) * 0.1, 0.3)
        score *= (1.0 - warning_penalty)

    # Bonus for preserving meaning
    if suggestion.preserves_meaning:
        score *= 1.1  # Small bonus
    else:
        score *= 0.7  # Penalty if meaning not preserved

    # Ensure score is in valid range
    score = max(0.0, min(1.0, score))

    return score, validator_result


def select_best_suggestion(
    suggestions: list[RewriteSuggestion],
    original_units: dict[str, ContentUnit],
    all_resume_units: list[ContentUnit],
    jd_signals: Optional[dict] = None,
) -> Optional[RewriteSuggestion]:
    """
    Select the best suggestion from multiple candidates.

    Args:
        suggestions: List of candidate suggestions
        original_units: Dict mapping content_unit_id to original ContentUnit
        all_resume_units: All resume content units
        jd_signals: Optional JD signals

    Returns:
        Best suggestion (highest score, passes validation) or None
    """
    if not suggestions:
        return None

    scored_suggestions = []
    for suggestion in suggestions:
        original_unit = original_units.get(suggestion.content_unit_id)
        if not original_unit:
            continue

        score, validator_result = score_suggestion(
            suggestion, original_unit, all_resume_units, jd_signals
        )

        # Only consider suggestions that pass validation
        if validator_result.passed:
            scored_suggestions.append((score, suggestion, validator_result))

    if not scored_suggestions:
        return None

    # Sort by score (highest first)
    scored_suggestions.sort(key=lambda x: x[0], reverse=True)

    # Return best suggestion
    best_score, best_suggestion, best_validator_result = scored_suggestions[0]

    # Update the suggestion's risk_score with validator result
    best_suggestion.risk_score = best_validator_result.risk_score

    return best_suggestion
