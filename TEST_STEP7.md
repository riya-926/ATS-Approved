# Testing Step 7: Review UI

## Quick Start Guide

### 1. Start Backend

In one terminal:
```bash
cd /Users/taru/IdeaProjects/ats-approved
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Start Frontend

In another terminal:
```bash
cd /Users/taru/IdeaProjects/ats-approved/frontend
npm run dev
```

You should see:
```
✓ Ready in X seconds
○ Local:        http://localhost:3000
```

### 3. Test the Flow

1. **Open Browser**: Go to `http://localhost:3000`

2. **Upload Resume**:
   - Click "Choose File" and select `test_files/sample_resume.docx`
   - Paste job description from `test_files/sample_jd.txt`
   - Click "Analyze Resume"

3. **Review Page**:
   - You should see suggestions with diff view
   - Test Accept button (should turn green)
   - Test Reject button (should turn red)
   - Test Edit button (should show textarea)
   - Check keyword highlighting (yellow highlights)
   - Check risk warnings (if any)

4. **Download**:
   - Click "Continue to Download"
   - Click "Download Tailored Resume"
   - File should download

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**CORS errors:**
- Make sure backend is running on port 8000
- Check `app/main.py` has CORS middleware configured

### Frontend Issues

**npm install fails:**
```bash
# Clear cache and retry
rm -rf node_modules package-lock.json
npm install
```

**Port 3000 already in use:**
```bash
# Use different port
PORT=3001 npm run dev
```

**API connection errors:**
- Check backend is running: `curl http://localhost:8000/health`
- Check `next.config.js` has correct proxy settings
- Check browser console for errors

### Common Issues

1. **"Failed to load suggestions"**
   - Check backend logs for errors
   - Verify all API endpoints are working
   - Check browser Network tab for failed requests

2. **"Original resume file not found"**
   - Make sure `test_files/sample_resume.docx` exists
   - Or upload a resume through the UI

3. **Diff view not showing**
   - Check browser console for JavaScript errors
   - Verify `diff-match-patch` is installed

## Manual API Testing

Test backend endpoints directly:

```bash
# Health check
curl http://localhost:8000/health

# Parse resume
curl -X POST http://localhost:8000/parse/docx \
  -F "file=@test_files/sample_resume.docx"

# Extract JD signals
curl -X POST http://localhost:8000/jd/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Senior Software Engineer with Python experience..."}'
```

## Expected Behavior

✅ Upload page loads
✅ File upload works
✅ Job description textarea works
✅ Submit button triggers analysis
✅ Review page shows suggestions
✅ Diff view displays correctly
✅ Accept/Reject/Edit buttons work
✅ Keyword highlighting works
✅ Risk warnings display
✅ Download generates file

## Next Steps After Testing

- Fix any bugs found
- Improve error handling
- Add loading states
- Add success/error notifications
- Test with different resumes
