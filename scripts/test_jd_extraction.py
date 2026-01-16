#!/usr/bin/env python3
"""
Standalone script to test JD signal extraction.

Usage:
    python scripts/test_jd_extraction.py <path_to_jd.txt>
    
Or pipe JD text:
    cat job_description.txt | python scripts/test_jd_extraction.py
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.jd.extractor import extract_jd_signals


def main():
    # Read JD text
    if len(sys.argv) > 1:
        # Read from file
        jd_path = Path(sys.argv[1])
        if not jd_path.exists():
            print(f"Error: File not found: {jd_path}")
            sys.exit(1)
        jd_text = jd_path.read_text()
    else:
        # Read from stdin
        jd_text = sys.stdin.read()

    if not jd_text.strip():
        print("Error: No job description text provided")
        sys.exit(1)

    print("=" * 60)
    print("Job Description Signal Extraction")
    print("=" * 60)
    print(f"\nJD Length: {len(jd_text)} characters")
    print(f"JD Preview: {jd_text[:200]}...")
    print("\n" + "-" * 60)

    # Extract signals
    print("\n[1/4] Extracting signals...")
    try:
        signals = extract_jd_signals(jd_text)
    except Exception as e:
        print(f"✗ Error extracting signals: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Display results
    print("\n[2/4] Hard Skills:")
    print("-" * 60)
    if signals.hard_skills:
        for skill in signals.hard_skills:
            print(f"  • {skill.name} ({skill.category.value})")
            if skill.variations:
                print(f"    Variations: {', '.join(skill.variations)}")
            print(f"    Mentions: {skill.mentions}, Confidence: {skill.confidence:.2f}")
    else:
        print("  (none found)")

    print("\n[3/4] Responsibilities:")
    print("-" * 60)
    if signals.responsibilities:
        for resp in signals.responsibilities[:10]:  # Show first 10
            print(f"  • {resp.verb.upper()} {resp.object}")
            print(f"    Type: {resp.type.value}, Confidence: {resp.confidence:.2f}")
        if len(signals.responsibilities) > 10:
            print(f"  ... and {len(signals.responsibilities) - 10} more")
    else:
        print("  (none found)")

    print("\n[4/4] Keywords & Seniority:")
    print("-" * 60)
    if signals.keywords:
        print("  Keywords:")
        for kw in signals.keywords[:10]:
            print(f"    • {kw.keyword} (importance: {kw.importance:.2f}, mentions: {kw.mentions})")

    if signals.seniority_cues:
        print("\n  Seniority Cues:")
        for cue in signals.seniority_cues:
            print(f"    • Level: {cue.level}")
            if cue.years_experience:
                print(f"      Years: {cue.years_experience}+")
            print(f"      Indicators: {', '.join(cue.indicators)}")
            print(f"      Confidence: {cue.confidence:.2f}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Hard Skills: {len(signals.hard_skills)}")
    print(f"  Responsibilities: {len(signals.responsibilities)}")
    print(f"  Keywords: {len(signals.keywords)}")
    print(f"  Seniority Cues: {len(signals.seniority_cues)}")
    print("=" * 60)

    # Optionally output JSON
    if "--json" in sys.argv:
        print("\nJSON Output:")
        print(json.dumps(signals.model_dump(), indent=2))


if __name__ == "__main__":
    main()

