"""
Quick test script - tests the full pipeline with minimal setup.

This script will:
1. Create a sample resume content (if no resume.docx provided)
2. Create a sample job description (if no JD provided)
3. Run the full pipeline: Parse → Extract → Map → Rewrite
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.evidence.mapper import map_evidence
from app.jd.extractor import extract_jd_signals
from app.models.content_unit import ContentUnit, ContentUnitType, ParsedResume
from app.rewrite.suggester import suggest_rewrites


def create_sample_resume() -> ParsedResume:
    """Create a sample resume for testing."""
    content_units = [
        ContentUnit(
            id="summary_1",
            type=ContentUnitType.SUMMARY,
            content="Experienced software engineer with 5 years of experience in Python and web development.",
        ),
        ContentUnit(
            id="exp_bullet_1",
            type=ContentUnitType.EXPERIENCE_BULLET,
            content="Developed REST APIs using Python and Flask framework",
        ),
        ContentUnit(
            id="exp_bullet_2",
            type=ContentUnitType.EXPERIENCE_BULLET,
            content="Deployed applications to AWS cloud infrastructure",
        ),
        ContentUnit(
            id="exp_bullet_3",
            type=ContentUnitType.EXPERIENCE_BULLET,
            content="Worked with SQL databases and wrote complex queries",
        ),
        ContentUnit(
            id="skills_1",
            type=ContentUnitType.SKILLS_LINE,
            content="Python, Flask, AWS, SQL, Git, Docker",
        ),
    ]
    return ParsedResume(content_units=content_units, metadata={"source": "sample"})


def create_sample_jd() -> str:
    """Create a sample job description for testing."""
    return """
Senior Software Engineer - Backend Development

We are looking for an experienced backend engineer to join our team.

Requirements:
- Strong experience with Python programming language
- Experience developing REST APIs and microservices
- Proficiency with cloud platforms (AWS preferred)
- Database experience with SQL and PostgreSQL
- Experience with containerization (Docker, Kubernetes)
- Version control with Git
- CI/CD pipeline experience

Responsibilities:
- Design and develop scalable REST APIs
- Build and maintain microservices architecture
- Deploy and manage applications on AWS
- Write efficient database queries and optimize performance
- Collaborate with cross-functional teams
- Implement CI/CD pipelines for automated deployments

Nice to have:
- Experience with FastAPI framework
- Knowledge of serverless architectures
- Monitoring and logging tools experience
"""


def main():
    """Run quick test with sample data."""
    print("=" * 80)
    print("QUICK TEST - Full Pipeline")
    print("=" * 80)

    # Check if API key is set
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\nERROR: API key not set!")
        print("\nPlease:")
        print("1. Open the .env file in the project root")
        print("2. Replace 'your_api_key_here' with your actual Anthropic API key")
        print("3. The key should start with 'sk-ant-api03-'")
        sys.exit(1)

    print(f"\nAPI Key found: {api_key[:20]}...")

    # Step 1: Create sample resume
    print("\n[1/4] Creating sample resume...")
    resume = create_sample_resume()
    print(f"Created resume with {len(resume.content_units)} content units")
    for unit in resume.content_units:
        print(f"   - {unit.id}: {unit.content[:60]}...")

    # Step 2: Create sample JD
    print("\n[2/4] Creating sample job description...")
    jd_text = create_sample_jd()
    print(f"Created JD ({len(jd_text)} characters)")

    # Step 3: Extract JD signals
    print("\n[3/4] Extracting JD signals...")
    try:
        jd_signals = extract_jd_signals(jd_text)
        print(f"Extracted:")
        print(f"   - {len(jd_signals.hard_skills)} skills: {[s.name for s in jd_signals.hard_skills[:5]]}")
        print(f"   - {len(jd_signals.responsibilities)} responsibilities")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 4: Map evidence
    print("\n[4/4] Mapping evidence...")
    try:
        evidence_map = map_evidence(jd_signals, resume)
        print(f"Evidence mapped:")
        print(f"   - {len(evidence_map.skill_matches)} skill matches")
        print(f"   - {len(evidence_map.responsibility_matches)} responsibility matches")
        print(f"   - Coverage: {evidence_map.coverage_score:.2%}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 5: Generate rewrite suggestions
    print("\n[5/5] Generating rewrite suggestions with Claude...")
    print("   (This may take 10-30 seconds)")
    try:
        suggestions = suggest_rewrites(jd_signals, evidence_map, resume, max_suggestions=3)
        print(f"\nGenerated {suggestions.total_suggestions} suggestions!")
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")
        print("\nThis might be due to:")
        print("  - Invalid API key")
        print("  - No API credits")
        print("  - Network issues")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Display results
    print("\n" + "=" * 80)
    print("REWRITE SUGGESTIONS")
    print("=" * 80)

    for i, suggestion in enumerate(suggestions.suggestions, 1):
        print(f"\n--- Suggestion {i} ({suggestion.content_unit_id}) ---")
        print(f"Confidence: {suggestion.confidence:.2%}")
        print(f"\nOriginal:")
        print(f"  {suggestion.original_text}")
        print(f"\nSuggested:")
        print(f"  {suggestion.suggested_text}")
        print(f"\nReasoning:")
        print(f"  {suggestion.reasoning}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  - Content units processed: {len(resume.content_units)}")
    print(f"  - JD skills extracted: {len(jd_signals.hard_skills)}")
    print(f"  - Evidence matches: {len(evidence_map.skill_matches) + len(evidence_map.responsibility_matches)}")
    print(f"  - Rewrite suggestions: {suggestions.total_suggestions}")
    print(f"  - Coverage improvement: {suggestions.coverage_improvement:.2%}")


if __name__ == "__main__":
    main()
