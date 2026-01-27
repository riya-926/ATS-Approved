"""
Test script for rewrite suggestions.

This script tests the rewrite suggestion functionality with sample data.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.docx.parser import parse_docx
from app.evidence.mapper import map_evidence
from app.jd.extractor import extract_jd_signals
from app.rewrite.suggester import suggest_rewrites


def main():
    """Test rewrite suggestions with a resume and job description."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_rewrite.py <resume.docx> <job_description.txt>")
        print("\nExample:")
        print("  python scripts/test_rewrite.py test_files/resume.docx test_files/jd.txt")
        sys.exit(1)

    resume_path = sys.argv[1]
    jd_path = sys.argv[2]

    print("=" * 80)
    print("Testing Rewrite Suggestions")
    print("=" * 80)

    # Step 1: Parse resume
    print("\n[1/4] Parsing resume...")
    try:
        resume = parse_docx(resume_path)
        print(f"✅ Parsed {len(resume.content_units)} content units")
    except Exception as e:
        print(f"❌ Error parsing resume: {e}")
        sys.exit(1)

    # Step 2: Extract JD signals
    print("\n[2/4] Extracting JD signals...")
    try:
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
        jd_signals = extract_jd_signals(jd_text)
        print(f"✅ Extracted {len(jd_signals.hard_skills)} skills, {len(jd_signals.responsibilities)} responsibilities")
    except Exception as e:
        print(f"❌ Error extracting JD signals: {e}")
        sys.exit(1)

    # Step 3: Map evidence
    print("\n[3/4] Mapping evidence...")
    try:
        evidence_map = map_evidence(jd_signals, resume)
        print(f"✅ Found {len(evidence_map.skill_matches)} skill matches")
        print(f"   Coverage score: {evidence_map.coverage_score:.2%}")
    except Exception as e:
        print(f"❌ Error mapping evidence: {e}")
        sys.exit(1)

    # Step 4: Generate rewrite suggestions
    print("\n[4/4] Generating rewrite suggestions...")
    try:
        suggestions = suggest_rewrites(jd_signals, evidence_map, resume, max_suggestions=5)
        print(f"✅ Generated {suggestions.total_suggestions} suggestions")
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")
        print("\n⚠️  Make sure you have:")
        print("   1. Created a .env file in the project root")
        print("   2. Added your ANTHROPIC_API_KEY to the .env file")
        print("   3. Installed dependencies: pip install -r requirements.txt")
        sys.exit(1)

    # Display results
    print("\n" + "=" * 80)
    print("REWRITE SUGGESTIONS")
    print("=" * 80)

    for i, suggestion in enumerate(suggestions.suggestions, 1):
        print(f"\n--- Suggestion {i} ---")
        print(f"Content Unit ID: {suggestion.content_unit_id}")
        print(f"Confidence: {suggestion.confidence:.2%}")
        print(f"\nOriginal:")
        print(f"  {suggestion.original_text}")
        print(f"\nSuggested:")
        print(f"  {suggestion.suggested_text}")
        print(f"\nReasoning:")
        print(f"  {suggestion.reasoning}")
        print(f"\nJD Alignment:")
        print(f"  Skills: {suggestion.jd_alignment.get('skills_addressed', [])}")
        print(f"  Responsibilities: {suggestion.jd_alignment.get('responsibilities_addressed', [])}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total suggestions: {suggestions.total_suggestions}")
    print(f"Coverage improvement: {suggestions.coverage_improvement:.2%}")
    
    # Display bullet point analysis
    if "bullet_analysis" in suggestions.metadata:
        bullet_info = suggestions.metadata["bullet_analysis"]
        print(f"\n📊 Bullet Point Analysis:")
        print(f"   Target bullets per section: {bullet_info.get('target_bullets', 'N/A')}")
        print(f"   Is consistent: {bullet_info.get('is_consistent', 'N/A')}")
        if bullet_info.get('experience_bullet_counts'):
            print(f"   Experience sections: {bullet_info['experience_bullet_counts']}")
        if bullet_info.get('project_bullet_counts'):
            print(f"   Project sections: {bullet_info['project_bullet_counts']}")
    
    # Display length analysis
    if "length_analysis" in suggestions.metadata:
        length_info = suggestions.metadata["length_analysis"]
        print(f"\n📄 Resume Length Analysis:")
        print(f"   Estimated pages: {length_info.get('estimated_pages', 0):.2f}")
        print(f"   Total words: {length_info.get('total_words', 0)}")
        print(f"   Total characters: {length_info.get('total_chars', 0)}")
        print(f"   Needs compression: {'Yes' if length_info.get('needs_compression', False) else 'No'}")
    
    print(f"\nMetadata: {json.dumps(suggestions.metadata, indent=2, default=str)}")

    # Save to JSON file
    output_file = "rewrite_suggestions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "suggestions": [s.model_dump() for s in suggestions.suggestions],
                "total_suggestions": suggestions.total_suggestions,
                "coverage_improvement": suggestions.coverage_improvement,
                "metadata": suggestions.metadata,
            },
            f,
            indent=2,
        )
    print(f"\n✅ Suggestions saved to: {output_file}")


if __name__ == "__main__":
    main()
