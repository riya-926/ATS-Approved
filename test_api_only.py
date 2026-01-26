"""
API-Only Test Script - Tests the complete system through API endpoints only.
This ensures the API is working correctly without using hardcoded function calls.
"""
import json
import sys
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

def check_server_running():
    """Check if the API server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

def test_complete_flow(resume_path, jd_path):
    """Test the complete flow through API endpoints only."""
    
    print("=" * 80)
    print("API-Only Test - Complete System Flow")
    print("=" * 80)
    print()
    
    # Check server
    print("[0/5] Checking API server...")
    if not check_server_running():
        print("❌ API server is not running!")
        print("\nPlease start the server first:")
        print("  uvicorn app.main:app --reload")
        sys.exit(1)
    print("✅ API server is running")
    print()
    
    # Step 1: Parse Resume
    print("[1/5] Parsing resume via API...")
    try:
        with open(resume_path, "rb") as f:
            files = {"file": (Path(resume_path).name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            response = requests.post(f"{BASE_URL}/parse/docx", files=files, timeout=30)
            response.raise_for_status()
            resume_data = response.json()
        print(f"✅ Parsed {len(resume_data.get('content_units', []))} content units")
    except Exception as e:
        print(f"❌ Error parsing resume: {e}")
        sys.exit(1)
    print()
    
    # Step 2: Extract JD Signals
    print("[2/5] Extracting JD signals via API...")
    try:
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
        response = requests.post(
            f"{BASE_URL}/jd/extract",
            json={"text": jd_text},
            timeout=30
        )
        response.raise_for_status()
        jd_signals = response.json()
        skills_count = len(jd_signals.get('hard_skills', []))
        resp_count = len(jd_signals.get('responsibilities', []))
        print(f"✅ Extracted {skills_count} skills, {resp_count} responsibilities")
    except Exception as e:
        print(f"❌ Error extracting JD signals: {e}")
        sys.exit(1)
    print()
    
    # Step 3: Map Evidence
    print("[3/5] Mapping evidence via API...")
    try:
        response = requests.post(
            f"{BASE_URL}/evidence/map",
            json={
                "jd_signals": jd_signals,
                "resume_json": resume_data
            },
            timeout=30
        )
        response.raise_for_status()
        evidence_map = response.json()
        skill_matches = len(evidence_map.get('skill_matches', []))
        coverage = evidence_map.get('coverage_score', 0)
        print(f"✅ Found {skill_matches} skill matches")
        print(f"   Coverage score: {coverage:.2%}")
    except Exception as e:
        print(f"❌ Error mapping evidence: {e}")
        sys.exit(1)
    print()
    
    # Step 4: Generate Rewrite Suggestions
    print("[4/5] Generating rewrite suggestions via API...")
    try:
        response = requests.post(
            f"{BASE_URL}/rewrite/suggest",
            json={
                "jd_signals": jd_signals,
                "evidence_map": evidence_map,
                "resume_json": resume_data,
                "max_suggestions": 10
            },
            timeout=120  # Longer timeout for AI generation
        )
        response.raise_for_status()
        suggestions = response.json()
        total_suggestions = suggestions.get('total_suggestions', 0)
        print(f"✅ Generated {total_suggestions} suggestions")
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)
    print()
    
    # Step 5: Display Results
    print("[5/5] Displaying results...")
    print()
    print("=" * 80)
    print("REWRITE SUGGESTIONS")
    print("=" * 80)
    
    for i, suggestion in enumerate(suggestions.get('suggestions', []), 1):
        print(f"\n--- Suggestion {i} ---")
        print(f"Content Unit ID: {suggestion.get('content_unit_id', 'N/A')}")
        print(f"Confidence: {suggestion.get('confidence', 0):.2%}")
        print(f"\nOriginal:")
        print(f"  {suggestion.get('original_text', 'N/A')}")
        print(f"\nSuggested:")
        print(f"  {suggestion.get('suggested_text', 'N/A')}")
        print(f"\nReasoning:")
        print(f"  {suggestion.get('reasoning', 'N/A')}")
        jd_align = suggestion.get('jd_alignment', {})
        if jd_align:
            print(f"\nJD Alignment:")
            if jd_align.get('skills_addressed'):
                print(f"  Skills: {jd_align['skills_addressed']}")
            if jd_align.get('responsibilities_addressed'):
                print(f"  Responsibilities: {jd_align['responsibilities_addressed']}")
    
    # Display metadata
    print("\n" + "=" * 80)
    print("METADATA ANALYSIS")
    print("=" * 80)
    
    metadata = suggestions.get('metadata', {})
    
    # Bullet point analysis
    if 'bullet_analysis' in metadata:
        bullet_info = metadata['bullet_analysis']
        print(f"\n📊 Bullet Point Analysis:")
        print(f"   Target bullets per section: {bullet_info.get('target_bullets', 'N/A')}")
        print(f"   Is consistent: {bullet_info.get('is_consistent', 'N/A')}")
        if bullet_info.get('experience_bullet_counts'):
            print(f"   Experience sections: {bullet_info['experience_bullet_counts']}")
        if bullet_info.get('project_bullet_counts'):
            print(f"   Project sections: {bullet_info['project_bullet_counts']}")
    
    # Length analysis
    if 'length_analysis' in metadata:
        length_info = metadata['length_analysis']
        print(f"\n📄 Resume Length Analysis:")
        print(f"   Estimated pages: {length_info.get('estimated_pages', 0):.2f}")
        print(f"   Total words: {length_info.get('total_words', 0)}")
        print(f"   Total characters: {length_info.get('total_chars', 0)}")
        needs_compression = length_info.get('needs_compression', False)
        print(f"   Needs compression: {'Yes' if needs_compression else 'No'}")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   Total suggestions: {suggestions.get('total_suggestions', 0)}")
    print(f"   Coverage improvement: {suggestions.get('coverage_improvement', 0):.2%}")
    
    # Save results
    output_file = "api_test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(suggestions, f, indent=2, default=str)
    print(f"\n✅ Results saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ API TEST COMPLETE - All endpoints working correctly!")
    print("=" * 80)
    
    return suggestions

if __name__ == "__main__":
    # Create test files if they don't exist
    resume_path = "test_resume.docx"
    jd_path = "test_jd.txt"
    
    if not Path(resume_path).exists():
        print("Creating test resume...")
        try:
            from scripts.create_test_resume import create_test_resume
            create_test_resume()
        except ImportError as e:
            print(f"❌ Error: {e}")
            print("\nPlease install dependencies first:")
            print("  pip install python-docx")
            print("\nOr use your own resume.docx file by modifying the script.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error creating test resume: {e}")
            print("\nYou can use your own resume.docx file instead.")
            print("Just rename it to 'test_resume.docx' or modify this script.")
            sys.exit(1)
    
    if not Path(jd_path).exists():
        print(f"❌ Job description file not found: {jd_path}")
        print("\nPlease create test_jd.txt or modify the script to use your own JD file.")
        sys.exit(1)
    
    # Run the test
    print("\n" + "=" * 80)
    print("Starting API-Only Test")
    print("=" * 80)
    print("\nMake sure the API server is running:")
    print("  uvicorn app.main:app --reload")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(0)
    
    test_complete_flow(resume_path, jd_path)
