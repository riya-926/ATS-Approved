# ATS-Approved Frontend

Next.js frontend for the ATS-Approved resume optimizer.

## Features

- **Upload Page**: Upload resume and paste job description
- **Review Page**: Diff-first review with Accept/Reject/Edit functionality
- **Keyword Highlighting**: Highlights inserted keywords from JD
- **Risk Warnings**: Displays validator warnings and risk scores
- **Download Page**: Download tailored resume

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure the FastAPI backend is running on `http://localhost:8000`

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx          # Upload page
│   ├── review/
│   │   └── page.tsx      # Review page with diff view
│   ├── download/
│   │   └── page.tsx      # Download page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── DiffView.tsx      # Diff visualization component
│   └── SuggestionCard.tsx # Individual suggestion card
└── package.json
```

## API Integration

The frontend connects to the FastAPI backend via proxy configured in `next.config.js`:
- `/api/*` routes are proxied to `http://localhost:8000/*`

## Features Implemented

### Step 7: Review UI (Diff-First)

✅ **Diff View**: Side-by-side comparison of original vs suggested text
✅ **Accept/Reject/Edit**: Full control over each suggestion
✅ **Keyword Highlighting**: Visual highlighting of inserted keywords
✅ **Risk Warnings**: Displays validator warnings and risk scores
✅ **Statistics**: Shows total, accepted, rejected, and edited counts

## Next Steps

- Add PDF export functionality
- Add version history
- Add user authentication
- Add save/resume functionality
