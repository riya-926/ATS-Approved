# Quick Test Guide for Step 7

## Option 1: Use the Start Script (Easiest)

```bash
./scripts/start_test.sh
```

This will:
- Start backend on port 8000
- Start frontend on port 3000
- Show you the URLs

## Option 2: Manual Start

### Terminal 1 - Backend
```bash
cd /Users/taru/IdeaProjects/ats-approved
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend
```bash
cd /Users/taru/IdeaProjects/ats-approved/frontend
npm run dev
```

## Test Steps

1. **Open Browser**: http://localhost:3000

2. **Upload Resume**:
   - Click "Choose File"
   - Select: `test_files/sample_resume.docx`
   - Paste job description from `test_files/sample_jd.txt`
   - Click "Analyze Resume"

3. **Wait for Processing** (may take 10-20 seconds for AI suggestions)

4. **Review Page Should Show**:
   - List of suggestions
   - Diff view (original vs suggested)
   - Accept/Reject/Edit buttons
   - Keyword highlights (yellow)
   - Risk warnings (if any)

5. **Test Actions**:
   - Click "Accept" on one suggestion → Should turn green
   - Click "Reject" on another → Should turn red
   - Click "Edit" → Should show textarea
   - Edit text and save

6. **Download**:
   - Click "Continue to Download"
   - Click "Download Tailored Resume"
   - File should download

## Troubleshooting

**Backend not starting?**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill if needed
kill -9 $(lsof -ti:8000)
```

**Frontend not starting?**
```bash
cd frontend
npm install  # If node_modules missing
npm run dev
```

**API errors?**
- Check backend logs
- Check browser console (F12)
- Verify backend is running: `curl http://localhost:8000/health`

**Missing endpoints?**
- Make sure you're on the right branch
- Check `app/api/` has `evidence.py` and `rewrite.py`

## Expected Results

✅ Upload page loads
✅ File upload works
✅ Analysis completes
✅ Review page shows suggestions
✅ Diff view works
✅ Accept/Reject/Edit work
✅ Download works
