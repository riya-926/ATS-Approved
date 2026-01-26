# Testing Guide - How to Test the Rewrite System

## Quick Test Options

### Option 1: Test with Python Script (Recommended)

**Requirements:**
- A resume DOCX file
- A job description text file
- Python environment with dependencies installed

**Steps:**

1. **Prepare your files:**
   - Place your resume as `resume.docx` (or any name)
   - Create a job description text file (e.g., `jd.txt`)

2. **Run the test script:**
   ```bash
   python scripts/test_rewrite.py resume.docx jd.txt
   ```

3. **What it does:**
   - Parses your resume
   - Extracts JD signals
   - Maps evidence
   - Generates rewrite suggestions
   - Shows bullet point analysis
   - Shows length analysis
   - Saves results to `rewrite_suggestions.json`

**Example:**
```bash
cd c:\Users\riyas\IdeaProjects\ATS-Approved
python scripts/test_rewrite.py my_resume.docx job_description.txt
```

---

### Option 2: Test via API (Full Integration Test)

**Requirements:**
- API server running
- HTTP client (curl, Postman, or Python requests)

**Steps:**

1. **Start the API server:**
   ```bash
   cd c:\Users\riyas\IdeaProjects\ATS-Approved
   uvicorn app.main:app --reload
   ```

2. **Test the complete flow:**

   **Step 1: Parse Resume**
   ```bash
   curl -X POST "http://localhost:8000/parse/docx" \
     -F "file=@resume.docx"
   ```
   Save the response as `resume_data.json`

   **Step 2: Extract JD Signals**
   ```bash
   curl -X POST "http://localhost:8000/jd/extract" \
     -H "Content-Type: application/json" \
     -d '{"text": "Your job description text here..."}'
   ```
   Save the response as `jd_signals.json`

   **Step 3: Map Evidence**
   ```bash
   curl -X POST "http://localhost:8000/evidence/map" \
     -H "Content-Type: application/json" \
     -d @evidence_request.json
   ```
   Where `evidence_request.json` contains:
   ```json
   {
     "jd_signals": {...},
     "resume_json": {...}
   }
   ```
   Save the response as `evidence_map.json`

   **Step 4: Generate Rewrite Suggestions**
   ```bash
   curl -X POST "http://localhost:8000/rewrite/suggest" \
     -H "Content-Type: application/json" \
     -d @rewrite_request.json
   ```
   Where `rewrite_request.json` contains:
   ```json
   {
     "jd_signals": {...},
     "evidence_map": {...},
     "resume_json": {...},
     "max_suggestions": 10
   }
   ```

---

### Option 3: Quick Feature Test (No Files Needed)

Test just the new analysis features:

```bash
python scripts/test_new_features.py
```

This tests:
- Bullet point consistency analysis
- Length estimation
- Import validation

---

## Python API Test Script

Create a simple test script:

```python
# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Parse resume
print("Step 1: Parsing resume...")
with open("resume.docx", "rb") as f:
    response = requests.post(f"{BASE_URL}/parse/docx", files={"file": f})
resume_data = response.json()
print(f"✅ Parsed {len(resume_data['content_units'])} content units")

# Step 2: Extract JD signals
print("\nStep 2: Extracting JD signals...")
with open("jd.txt", "r", encoding="utf-8") as f:
    jd_text = f.read()
response = requests.post(f"{BASE_URL}/jd/extract", json={"text": jd_text})
jd_signals = response.json()
print(f"✅ Extracted {len(jd_signals['hard_skills'])} skills")

# Step 3: Map evidence
print("\nStep 3: Mapping evidence...")
response = requests.post(
    f"{BASE_URL}/evidence/map",
    json={"jd_signals": jd_signals, "resume_json": resume_data}
)
evidence_map = response.json()
print(f"✅ Coverage: {evidence_map['coverage_score']:.2%}")

# Step 4: Generate rewrite suggestions
print("\nStep 4: Generating rewrite suggestions...")
response = requests.post(
    f"{BASE_URL}/rewrite/suggest",
    json={
        "jd_signals": jd_signals,
        "evidence_map": evidence_map,
        "resume_json": resume_data,
        "max_suggestions": 10
    }
)
suggestions = response.json()
print(f"✅ Generated {suggestions['total_suggestions']} suggestions")

# Display results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

for i, suggestion in enumerate(suggestions['suggestions'], 1):
    print(f"\n--- Suggestion {i} ---")
    print(f"Original: {suggestion['original_text']}")
    print(f"Suggested: {suggestion['suggested_text']}")
    print(f"Confidence: {suggestion['confidence']:.2%}")

# Show metadata
if 'bullet_analysis' in suggestions['metadata']:
    print(f"\n📊 Bullet Analysis:")
    print(f"   Target: {suggestions['metadata']['bullet_analysis']['target_bullets']} bullets")
    
if 'length_analysis' in suggestions['metadata']:
    print(f"\n📄 Length Analysis:")
    print(f"   Pages: {suggestions['metadata']['length_analysis']['estimated_pages']:.2f}")
    print(f"   Needs compression: {suggestions['metadata']['length_analysis']['needs_compression']}")
```

Run it:
```bash
python test_api.py
```

---

## What to Check

### ✅ Bullet Point Consistency
- Check if all experience/project sections have the same number of bullets
- Look for metadata: `bullet_analysis.target_bullets`
- Verify suggestions maintain consistency

### ✅ 1-Page Limit
- Check estimated pages in metadata: `length_analysis.estimated_pages`
- If > 1.0, verify suggestions compress content
- Check `needs_compression` flag

### ✅ ATS Optimization
- Suggestions should use standard terminology
- No fluff words
- Tense consistency maintained
- Meaning preserved

### ✅ Quality Checks
- No hallucinations (no new skills/metrics)
- Meaning preserved
- JD alignment improved
- Confidence scores reasonable

---

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"
- Create a `.env` file in project root
- Add: `ANTHROPIC_API_KEY=your_key_here`

### Error: "Module not found"
- Install dependencies: `pip install -r requirements.txt`

### Error: "File not found"
- Check file paths are correct
- Use absolute paths if needed

### API not responding
- Make sure server is running: `uvicorn app.main:app --reload`
- Check port 8000 is available

---

## Expected Output

When testing, you should see:

```
================================================================================
Testing Rewrite Suggestions
================================================================================

[1/4] Parsing resume...
✅ Parsed 25 content units

[2/4] Extracting JD signals...
✅ Extracted 12 skills, 8 responsibilities

[3/4] Mapping evidence...
✅ Found 10 skill matches
   Coverage score: 0.75

[4/4] Generating rewrite suggestions...
✅ Generated 8 suggestions

================================================================================
REWRITE SUGGESTIONS
================================================================================

--- Suggestion 1 ---
Content Unit ID: exp_bullet_1
Confidence: 0.85

Original:
  Worked on developing APIs

Suggested:
  Developed REST APIs using Python and FastAPI

Reasoning:
  Improved ATS keyword alignment and removed fluff words...

📊 Bullet Point Analysis:
   Target bullets per section: 3
   Is consistent: False

📄 Resume Length Analysis:
   Estimated pages: 1.2
   Needs compression: Yes
```

---

## Quick Start (Fastest Way)

1. **Have a resume.docx and jd.txt ready**

2. **Run:**
   ```bash
   python scripts/test_rewrite.py resume.docx jd.txt
   ```

3. **Check the output file:**
   - `rewrite_suggestions.json` - Full results

That's it! 🎉
