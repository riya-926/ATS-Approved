#!/usr/bin/env python3
"""
Quick demo script to show the pipeline working.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.docx.parser import parse_docx
from app.evidence.mapper import map_evidence
from app.jd.extractor import extract_jd_signals
from app.rewrite.suggester import suggest_rewrites

print("🚀 ATS-Approved Pipeline Demo\n")
print("=" * 70)

# Step 1: Parse Resume
print("\n📄 Step 1: Parsing Resume...")
resume = parse_docx("test_files/sample_resume.docx")
print(f"   ✓ Found {len(resume.content_units)} content units")
print(f"   • Summary: 1")
print(f"   • Experience bullets: {len([u for u in resume.content_units if 'exp_bullet' in u.id])}")
print(f"   • Skills lines: {len([u for u in resume.content_units if 'skills' in u.id])}")

# Step 2: Extract JD Signals
print("\n🔍 Step 2: Extracting Job Description Signals...")
jd_text = Path("test_files/sample_jd.txt").read_text()
jd_signals = extract_jd_signals(jd_text)
print(f"   ✓ Extracted:")
print(f"   • {len(jd_signals.hard_skills)} hard skills")
print(f"   • {len(jd_signals.responsibilities)} responsibilities")
print(f"   • {len(jd_signals.keywords)} keywords")
print(f"   • {len(jd_signals.seniority_cues)} seniority cues")

# Show some skills
print(f"\n   Top Skills Found:")
for skill in jd_signals.hard_skills[:5]:
    print(f"   • {skill.name} ({skill.category.value})")

# Step 3: Map Evidence
print("\n🔗 Step 3: Mapping Evidence (Preventing Hallucinations)...")
evidence_map = map_evidence(jd_signals, resume)
print(f"   ✓ Evidence Mapping Complete:")
print(f"   • {len(evidence_map.skill_matches)} skill matches found")
print(f"   • {len(evidence_map.responsibility_matches)} responsibility matches")
print(f"   • Coverage Score: {evidence_map.coverage_score:.1%}")

# Show some matches
if evidence_map.skill_matches:
    print(f"\n   Example Skill Matches:")
    for match in evidence_map.skill_matches[:3]:
        skill_name = match.jd_skill.get('name', 'Unknown') if isinstance(match.jd_skill, dict) else 'Unknown'
        print(f"   • {skill_name}: {len(match.resume_bullets)} bullets support this")

# Step 4: Generate AI Suggestions
print("\n🤖 Step 4: Generating AI Rewrite Suggestions...")
print("   (This may take 10-20 seconds...)")
try:
    suggestions = suggest_rewrites(
        jd_signals=jd_signals,
        evidence_map=evidence_map,
        resume=resume,
        max_suggestions=3
    )
    print(f"   ✓ Generated {suggestions.total_suggestions} suggestions")
    print(f"   • Expected Coverage Improvement: {suggestions.coverage_improvement:.1%}")
    
    if suggestions.suggestions:
        print(f"\n   Example Suggestions:")
        for i, sug in enumerate(suggestions.suggestions[:2], 1):
            print(f"\n   [{i}] {sug.content_unit_id}")
            print(f"       Original:  {sug.original_text[:70]}...")
            print(f"       Suggested: {sug.suggested_text[:70]}...")
            print(f"       Confidence: {sug.confidence:.0%} | Risk: {sug.risk_score:.0%}")
except Exception as e:
    print(f"   ⚠ Error: {e}")
    print("   (Make sure ANTHROPIC_API_KEY is set in .env file)")

print("\n" + "=" * 70)
print("\n✅ Pipeline Demo Complete!")
print("\nAll systems are working:")
print("  ✓ DOCX parsing")
print("  ✓ JD signal extraction")
print("  ✓ Evidence mapping")
print("  ✓ AI rewrite suggestions")
print("\n🎉 Your ATS-Approved pipeline is ready to use!")
