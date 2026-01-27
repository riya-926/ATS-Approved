#!/usr/bin/env python3
"""
Full pipeline test script.

Tests the complete flow:
1. Parse DOCX resume
2. Extract JD signals
3. Map evidence
4. Generate rewrite suggestions
5. Apply edits back to DOCX

Usage:
    python scripts/test_full_pipeline.py <resume.docx> <job_description.txt>
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.docx.parser import parse_docx
from app.docx.patcher import patch_docx
from app.evidence.mapper import map_evidence
from app.jd.extractor import extract_jd_signals
from app.rewrite.suggester import suggest_rewrites


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_full_pipeline.py <resume.docx> <job_description.txt>")
        print("\nExample:")
        print("  python scripts/test_full_pipeline.py test_files/resume.docx test_files/sample_jd.txt")
        sys.exit(1)

    resume_path = Path(sys.argv[1])
    jd_path = Path(sys.argv[2])

    if not resume_path.exists():
        print(f"Error: Resume file not found: {resume_path}")
        sys.exit(1)

    if not jd_path.exists():
        print(f"Error: Job description file not found: {jd_path}")
        sys.exit(1)

    print_section("ATS-Approved Full Pipeline Test")
    print(f"\nResume: {resume_path}")
    print(f"Job Description: {jd_path}")

    # Step 1: Parse DOCX Resume
    print_section("Step 1: Parse DOCX Resume")
    try:
        parsed_resume = parse_docx(resume_path)
        print(f"✓ Parsed {len(parsed_resume.content_units)} content units")
        print(f"  Metadata: {parsed_resume.metadata}")

        if not parsed_resume.content_units:
            print("  ⚠ Warning: No content units found!")
            print("  Ensure the resume has Experience/Skills/Summary sections.")
            sys.exit(1)

        print(f"\n  Content Units Preview:")
        for i, unit in enumerate(parsed_resume.content_units[:5]):
            print(f"    {i+1}. [{unit.id}] {unit.type}: {unit.content[:60]}...")
        if len(parsed_resume.content_units) > 5:
            print(f"    ... and {len(parsed_resume.content_units) - 5} more")

    except Exception as e:
        print(f"✗ Error parsing resume: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 2: Extract JD Signals
    print_section("Step 2: Extract JD Signals")
    try:
        jd_text = jd_path.read_text()
        jd_signals = extract_jd_signals(jd_text)

        print(f"✓ Extracted signals from JD ({len(jd_text)} chars)")
        print(f"\n  Hard Skills: {len(jd_signals.hard_skills)}")
        for skill in jd_signals.hard_skills[:5]:
            print(f"    • {skill.name} ({skill.category.value})")
        if len(jd_signals.hard_skills) > 5:
            print(f"    ... and {len(jd_signals.hard_skills) - 5} more")

        print(f"\n  Responsibilities: {len(jd_signals.responsibilities)}")
        for resp in jd_signals.responsibilities[:3]:
            print(f"    • {resp.verb.upper()} {resp.object[:50]}...")
        if len(jd_signals.responsibilities) > 3:
            print(f"    ... and {len(jd_signals.responsibilities) - 3} more")

        print(f"\n  Keywords: {len(jd_signals.keywords)}")
        print(f"  Seniority Cues: {len(jd_signals.seniority_cues)}")

    except Exception as e:
        print(f"✗ Error extracting JD signals: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 3: Map Evidence
    print_section("Step 3: Map Evidence (Prevent Hallucinations)")
    try:
        evidence_map = map_evidence(jd_signals, parsed_resume)

        print(f"✓ Evidence mapping complete")
        print(f"\n  Skill Matches: {len(evidence_map.skill_matches)}")
        for match in evidence_map.skill_matches[:3]:
            print(f"    • {match.jd_skill.get('name', 'Unknown')}: {len(match.resume_bullets)} bullets matched")
        if len(evidence_map.skill_matches) > 3:
            print(f"    ... and {len(evidence_map.skill_matches) - 3} more")

        print(f"\n  Responsibility Matches: {len(evidence_map.responsibility_matches)}")
        for match in evidence_map.responsibility_matches[:3]:
            print(f"    • {match.jd_responsibility.get('verb', 'Unknown')}: {len(match.resume_bullets)} bullets matched")
        if len(evidence_map.responsibility_matches) > 3:
            print(f"    ... and {len(evidence_map.responsibility_matches) - 3} more")

        print(f"\n  Keyword Matches: {len(evidence_map.keyword_matches)}")
        print(f"  Unsupported Requirements: {len(evidence_map.unsupported_requirements)}")
        print(f"\n  Coverage Score: {evidence_map.coverage_score:.2%}")

        if evidence_map.unsupported_requirements:
            print(f"\n  ⚠ Unsupported Requirements (no evidence in resume):")
            for req in evidence_map.unsupported_requirements[:5]:
                print(f"    • {req.name} ({req.type})")

    except Exception as e:
        print(f"✗ Error mapping evidence: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 4: Generate Rewrite Suggestions
    print_section("Step 4: Generate Rewrite Suggestions (AI-Powered)")
    try:
        print("  Generating suggestions (this may take a moment)...")
        rewrite_suggestions = suggest_rewrites(
            jd_signals=jd_signals,
            evidence_map=evidence_map,
            resume=parsed_resume,
            max_suggestions=5,  # Limit for testing
        )

        print(f"✓ Generated {rewrite_suggestions.total_suggestions} suggestions")
        print(f"  Coverage Improvement: {rewrite_suggestions.coverage_improvement:.2%}")

        print(f"\n  Suggestions Preview:")
        for i, suggestion in enumerate(rewrite_suggestions.suggestions[:3], 1):
            print(f"\n    [{i}] {suggestion.content_unit_id}")
            print(f"        Original:  {suggestion.original_text[:70]}...")
            print(f"        Suggested: {suggestion.suggested_text[:70]}...")
            print(f"        Confidence: {suggestion.confidence:.2f}")
            print(f"        Risk Score: {suggestion.risk_score:.2f}")
            print(f"        Reasoning: {suggestion.reasoning[:80]}...")

        if len(rewrite_suggestions.suggestions) > 3:
            print(f"\n    ... and {len(rewrite_suggestions.suggestions) - 3} more suggestions")

    except ValueError as e:
        if "ANTHROPIC_API_KEY" in str(e):
            print(f"\n✗ Error: {e}")
            print("\n  Please set up your Anthropic API key:")
            print("  1. Create a .env file in the project root")
            print("  2. Add: ANTHROPIC_API_KEY=your-key-here")
            print("  3. See SETUP_API_KEY.md for detailed instructions")
            sys.exit(1)
        else:
            print(f"✗ Error generating suggestions: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error generating suggestions: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Step 5: Apply Edits Back to DOCX (Optional - only if suggestions exist)
    if rewrite_suggestions.suggestions:
        print_section("Step 5: Apply Edits Back to DOCX")
        try:
            # Create updated content units from suggestions
            updated_units = []
            suggestion_map = {s.content_unit_id: s for s in rewrite_suggestions.suggestions}

            for unit in parsed_resume.content_units:
                if unit.id in suggestion_map:
                    # Use suggested text
                    updated_unit = unit.model_copy()
                    updated_unit.content = suggestion_map[unit.id].suggested_text
                    updated_units.append(updated_unit)
                else:
                    # Keep original
                    updated_units.append(unit)

            # Apply patches
            output_path = resume_path.parent / f"{resume_path.stem}_tailored.docx"
            success = patch_docx(resume_path, output_path, updated_units, parsed_resume)

            if success:
                print(f"✓ Successfully created tailored resume: {output_path}")
                print(f"\n  Applied {len(suggestion_map)} edits")
                print(f"  Original: {resume_path}")
                print(f"  Tailored: {output_path}")
                print("\n  Compare the files to verify:")
                print("    - Only text content changed")
                print("    - Layout and formatting preserved")
            else:
                print("⚠ Warning: Patch completed but no changes detected")

        except Exception as e:
            print(f"✗ Error applying edits: {e}")
            import traceback

            traceback.print_exc()
            # Don't exit - this is optional

    # Summary
    print_section("Pipeline Test Complete!")
    print("\n✓ All steps completed successfully")
    print("\nSummary:")
    print(f"  • Parsed {len(parsed_resume.content_units)} resume content units")
    print(f"  • Extracted {len(jd_signals.hard_skills)} skills, {len(jd_signals.responsibilities)} responsibilities")
    print(f"  • Found {len(evidence_map.skill_matches)} skill matches")
    print(f"  • Generated {rewrite_suggestions.total_suggestions} rewrite suggestions")
    print(f"  • Coverage: {evidence_map.coverage_score:.2%} → {evidence_map.coverage_score + rewrite_suggestions.coverage_improvement:.2%}")

    # Save results to JSON (optional)
    if "--save-json" in sys.argv:
        output_json = resume_path.parent / f"{resume_path.stem}_pipeline_results.json"
        results = {
            "resume": {
                "content_units": [u.model_dump() for u in parsed_resume.content_units],
                "metadata": parsed_resume.metadata,
            },
            "jd_signals": jd_signals.model_dump(),
            "evidence_map": {
                "skill_matches": len(evidence_map.skill_matches),
                "responsibility_matches": len(evidence_map.responsibility_matches),
                "keyword_matches": len(evidence_map.keyword_matches),
                "unsupported_requirements": len(evidence_map.unsupported_requirements),
                "coverage_score": evidence_map.coverage_score,
            },
            "suggestions": {
                "total": rewrite_suggestions.total_suggestions,
                "coverage_improvement": rewrite_suggestions.coverage_improvement,
                "suggestions": [s.model_dump() for s in rewrite_suggestions.suggestions],
            },
        }
        with open(output_json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to: {output_json}")


if __name__ == "__main__":
    main()
