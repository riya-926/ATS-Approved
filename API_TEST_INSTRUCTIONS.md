# API-Only Testing Instructions

## Setup

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Create test files**:
   ```bash
   python scripts/create_test_resume.py
   ```
   This creates `test_resume.docx`
   
   The `test_jd.txt` file is already created.

3. **Start the API server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   Keep this running in a separate terminal.

4. **Run the API-only test**:
   ```bash
   python test_api_only.py
   ```

## What This Tests

This test **ONLY uses API endpoints** - no hardcoded function calls. It tests:

1. ✅ `POST /parse/docx` - Parse resume
2. ✅ `POST /jd/extract` - Extract JD signals  
3. ✅ `POST /evidence/map` - Map evidence
4. ✅ `POST /rewrite/suggest` - Generate rewrite suggestions

All through HTTP requests to the API server.

## Expected Output

```
================================================================================
API-Only Test - Complete System Flow
================================================================================

[0/5] Checking API server...
✅ API server is running

[1/5] Parsing resume via API...
✅ Parsed 15 content units

[2/5] Extracting JD signals via API...
✅ Extracted 10 skills, 6 responsibilities

[3/5] Mapping evidence via API...
✅ Found 8 skill matches
   Coverage score: 0.75

[4/5] Generating rewrite suggestions via API...
✅ Generated 8 suggestions

[5/5] Displaying results...

================================================================================
REWRITE SUGGESTIONS
================================================================================
...
```

## Files Created

- `test_resume.docx` - Test resume with 2 jobs (one with 3 bullets, one with 2 bullets)
- `test_jd.txt` - Test job description
- `api_test_results.json` - Full API response saved for review

## Notes

- The test resume has **inconsistent bullet points** (3 and 2) to test consistency feature
- The test resume is designed to be **< 1 page** to test length analysis
- All testing is done **through API endpoints only** - no direct function calls
