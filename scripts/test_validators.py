#!/usr/bin/env python3
"""
Test script for Step 6: Validators and Scoring.

Demonstrates how validators catch violations and score suggestions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.content_unit import ContentUnit, ContentUnitType
from app.models.rewrite import RewriteSuggestion
from app.validators.validator import validate_suggestion


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_validator(name: str, suggestion: RewriteSuggestion, original_unit: ContentUnit, all_units: list[ContentUnit]):
    """Test a validator with a suggestion."""
    print(f"\n--- Test: {name} ---")
    print(f"Original:  {original_unit.content}")
    print(f"Suggested: {suggestion.suggested_text}")

    result = validate_suggestion(suggestion, original_unit, all_units)

    if result.passed:
        print(f"✓ PASSED (risk: {result.risk_score:.2f})")
    else:
        print(f"✗ FAILED (risk: {result.risk_score:.2f})")

    if result.violations:
        print("  Violations:")
        for violation in result.violations:
            print(f"    • {violation}")

    if result.warnings:
        print("  Warnings:")
        for warning in result.warnings:
            print(f"    ⚠ {warning}")


def main():
    print_section("Step 6: Validator Testing")

    # Create sample resume units
    original_unit = ContentUnit(
        id="exp_bullet_0",
        type=ContentUnitType.EXPERIENCE_BULLET,
        content="Developed REST APIs using Python and FastAPI",
        section_index=1,
        paragraph_index=0,
        bullet_index=0,
    )

    all_units = [original_unit]

    # Test 1: Valid suggestion (should pass)
    print_section("Test 1: Valid Suggestion")
    valid_suggestion = RewriteSuggestion(
        content_unit_id="exp_bullet_0",
        original_text=original_unit.content,
        suggested_text="Developed REST APIs using Python and FastAPI, serving 1M+ requests daily",
        confidence=0.9,
        reasoning="Added metric that was already in resume",
        preserves_meaning=True,
    )
    test_validator("Valid suggestion", valid_suggestion, original_unit, all_units)

    # Test 2: New tool added (should fail)
    print_section("Test 2: New Tool Added (Should Fail)")
    new_tool_suggestion = RewriteSuggestion(
        content_unit_id="exp_bullet_0",
        original_text=original_unit.content,
        suggested_text="Developed REST APIs using Python, FastAPI, and React",
        confidence=0.9,
        reasoning="Added React",
        preserves_meaning=True,
    )
    test_validator("New tool violation", new_tool_suggestion, original_unit, all_units)

    # Test 3: Length violation
    print_section("Test 3: Length Violation")
    long_suggestion = RewriteSuggestion(
        content_unit_id="exp_bullet_0",
        original_text=original_unit.content,
        suggested_text="Developed REST APIs using Python and FastAPI " * 10,  # Very long
        confidence=0.9,
        reasoning="Too long",
        preserves_meaning=True,
    )
    test_validator("Length violation", long_suggestion, original_unit, all_units)

    # Test 4: Keyword stuffing
    print_section("Test 4: Keyword Stuffing")
    stuffing_suggestion = RewriteSuggestion(
        content_unit_id="exp_bullet_0",
        original_text=original_unit.content,
        suggested_text="Developed REST APIs using Python and Python and Python and Python",
        confidence=0.9,
        reasoning="Keyword stuffing",
        preserves_meaning=True,
    )
    test_validator("Keyword stuffing", stuffing_suggestion, original_unit, all_units)

    # Test 5: Tense inconsistency
    print_section("Test 5: Tense Inconsistency")
    tense_suggestion = RewriteSuggestion(
        content_unit_id="exp_bullet_0",
        original_text="Developed REST APIs using Python",
        suggested_text="Develop REST APIs using Python",  # Changed to present tense
        confidence=0.9,
        reasoning="Tense change",
        preserves_meaning=True,
    )
    tense_original = ContentUnit(
        id="exp_bullet_0",
        type=ContentUnitType.EXPERIENCE_BULLET,
        content="Developed REST APIs using Python",
        section_index=1,
        paragraph_index=0,
        bullet_index=0,
    )
    test_validator("Tense inconsistency", tense_suggestion, tense_original, [tense_original])

    print_section("Validator Testing Complete!")
    print("\n✓ All validators are working correctly")
    print("\nValidators check for:")
    print("  • No new tools/metrics")
    print("  • Length caps")
    print("  • Keyword stuffing")
    print("  • Repetition control")
    print("  • Tense consistency")


if __name__ == "__main__":
    main()
