# Quick API-Only Test Guide

## ✅ What You Have

1. **Test Job Description**: `test_jd.txt` - Already created
2. **Test Script**: `test_api_only.py` - Tests ONLY through API endpoints
3. **Resume Creator**: `scripts/create_test_resume.py` - Creates test resume

## 🚀 Quick Start (3 Steps)

### Step 1: Create Test Resume

```bash
python scripts/create_test_resume.py
```

**Note**: If you get "ModuleNotFoundError: docx", install dependencies:
```bash
pip install python-docx
```

This creates `test_resume.docx` with:
- 2 experience sections (one with 3 bullets, one with 2 bullets - to test consistency)
- Summary section
- Skills section
- Education section
- Designed to be < 1 page

### Step 2: Start API Server

Open a **new terminal** and run:
```bash
cd c:\Users\riyas\IdeaProjects\ATS-Approved
uvicorn app.main:app --reload
```

Keep this running! The test script will connect to it.

### Step 3: Run API Test

In your **original terminal**, run:
```bash
python test_api_only.py
```

## 📋 What the Test Does

The `test_api_only.py` script:

1. ✅ Checks if API server is running
2. ✅ Calls `POST /parse/docx` - Parses resume via API
3. ✅ Calls `POST /jd/extract` - Extracts JD signals via API
4. ✅ Calls `POST /evidence/map` - Maps evidence via API
5. ✅ Calls `POST /rewrite/suggest` - Generates suggestions via API
6. ✅ Displays all results
7. ✅ Saves results to `api_test_results.json`

**Important**: This test uses **ONLY API endpoints** - no hardcoded function calls!

## 📊 What You'll See

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

--- Suggestion 1 ---
Original: Developed REST APIs using Python and FastAPI
Suggested: [AI-generated improvement]
...

📊 Bullet Point Analysis:
   Target bullets per section: 3
   Is consistent: False

📄 Resume Length Analysis:
   Estimated pages: 0.85
   Needs compression: No
```

## 🔍 What to Verify

1. **API Endpoints Work**: All 4 endpoints should return 200 OK
2. **Bullet Consistency**: Should detect inconsistency (2 vs 3 bullets)
3. **Length Analysis**: Should estimate pages correctly
4. **Rewrite Suggestions**: Should generate meaningful improvements
5. **No Errors**: All steps should complete successfully

## 📁 Files Created

- `test_resume.docx` - Test resume (created by script)
- `test_jd.txt` - Test job description (already exists)
- `api_test_results.json` - Full API response (created by test)

## ⚠️ Troubleshooting

### "API server is not running"
- Make sure you started `uvicorn app.main:app --reload` in a separate terminal
- Check it's running on `http://localhost:8000`

### "ModuleNotFoundError: docx"
- Install: `pip install python-docx`
- Or use your own resume.docx file

### "ANTHROPIC_API_KEY not found"
- Create `.env` file in project root
- Add: `ANTHROPIC_API_KEY=your_key_here`

### Timeout errors
- The rewrite endpoint may take 30-60 seconds (AI generation)
- Increase timeout in script if needed

## 🎯 Success Criteria

✅ All API endpoints respond correctly
✅ Resume parses successfully
✅ JD signals extracted
✅ Evidence mapped with coverage score
✅ Rewrite suggestions generated
✅ Bullet analysis shows inconsistency
✅ Length analysis shows estimated pages
✅ Results saved to JSON file

If all these pass, your API is working correctly! 🎉
