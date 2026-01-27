#!/usr/bin/env python3
"""
Test pipeline Steps 1-3 (without AI rewrite suggestions).

This tests:
1. Parse DOCX resume
2. Extract JD signals
3. Map evidence

Usage:
    python scripts/test_pipeline_steps_1_3.py <resume.docx> <job_description.txt>
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.docx.parser import parse_docx
from app.evidence.mapper import map_evidence
from app.jd.extractor import extract_jd_signals


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_pipeline_steps_1_3.py <resume.docx> <job_description.txt>")
        sys.exit(1)

    resume_path = Path(sys.argv[1])
    jd_path = Path(sys.argv[2])

    if not resume_path.exists():
        print(f"Error: Resume file not found: {resume_path}")
        sys.exit(1)

    if not jd_path.exists():
        print(f"Error: Job description file not found: {jd_path}")
        sys.exit(1)

    print_section("ATS-Approved Pipeline Test (Steps 1-3)")
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
        for skill in jd_signals.hard_skills[:10]:
            print(f"    • {skill.name} ({skill.category.value}) - {skill.mentions} mentions")
        if len(jd_signals.hard_skills) > 10:
            print(f"    ... and {len(jd_signals.hard_skills) - 10} more")

        print(f"\n  Responsibilities: {len(jd_signals.responsibilities)}")
        for resp in jd_signals.responsibilities[:5]:
            print(f"    • {resp.verb.upper()} {resp.object[:50]}...")
        if len(jd_signals.responsibilities) > 5:
            print(f"    ... and {len(jd_signals.responsibilities) - 5} more")

        print(f"\n  Keywords: {len(jd_signals.keywords)}")
        for kw in jd_signals.keywords[:5]:
            print(f"    • {kw.keyword} (importance: {kw.importance:.2f})")
        
        print(f"\n  Seniority Cues: {len(jd_signals.seniority_cues)}")
        for cue in jd_signals.seniority_cues:
            print(f"    • Level: {cue.level}")
            if cue.years_experience:
                print(f"      Years: {cue.years_experience}+")

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
        for match in evidence_map.skill_matches[:5]:
            skill_name = match.jd_skill.get('name', 'Unknown') if isinstance(match.jd_skill, dict) else 'Unknown'
            print(f"    • {skill_name}: {len(match.resume_bullets)} bullets matched (confidence: {match.confidence:.2f})")
        if len(evidence_map.skill_matches) > 5:
            print(f"    ... and {len(evidence_map.skill_matches) - 5} more")

        print(f"\n  Responsibility Matches: {len(evidence_map.responsibility_matches)}")
        for match in evidence_map.responsibility_matches[:5]:
            verb = match.jd_responsibility.get('verb', 'Unknown') if isinstance(match.jd_responsibility, dict) else 'Unknown'
            print(f"    • {verb}: {len(match.resume_bullets)} bullets matched (confidence: {match.confidence:.2f})")
        if len(evidence_map.responsibility_matches) > 5:
            print(f"    ... and {len(evidence_map.responsibility_matches) - 5} more")

        print(f"\n  Keyword Matches: {len(evidence_map.keyword_matches)}")
        print(f"  Unsupported Requirements: {len(evidence_map.unsupported_requirements)}")
        print(f"\n  📊 Coverage Score: {evidence_map.coverage_score:.2%}")

        if evidence_map.unsupported_requirements:
            print(f"\n  ⚠ Unsupported Requirements (no evidence in resume):")
            for req in evidence_map.unsupported_requirements[:10]:
                print(f"    • {req.name} ({req.type})")

    except Exception as e:
        print(f"✗ Error mapping evidence: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Summary
    print_section("Test Complete!")
    print("\n✓ Steps 1-3 completed successfully")
    print("\nSummary:")
    print(f"  • Parsed {len(parsed_resume.content_units)} resume content units")
    print(f"  • Extracted {len(jd_signals.hard_skills)} skills, {len(jd_signals.responsibilities)} responsibilities")
    print(f"  • Found {len(evidence_map.skill_matches)} skill matches")
    print(f"  • Coverage: {evidence_map.coverage_score:.2%}")
    
    if evidence_map.unsupported_requirements:
        print(f"  • {len(evidence_map.unsupported_requirements)} requirements have no evidence")
        print(f"\n  💡 Tip: To improve coverage, add evidence for unsupported requirements to your resume")

    # Save results
    if "--save-json" in sys.argv:
        output_json = resume_path.parent / f"{resume_path.stem}_steps_1_3_results.json"
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
        }
        with open(output_json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to: {output_json}")


if __name__ == "__main__":
    main()
