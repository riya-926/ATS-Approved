# ATS-Approved

Production-grade web application that optimizes resumes for Applicant Tracking Systems (ATS) while preserving the user's original resume structure and layout.

## Overview

This product performs targeted, evidence-based text edits (bullets, summaries, skills wording) so the resume:
- Parses correctly in ATS systems
- Aligns more closely with a given job description
- Remains truthful and user-controlled

**Key constraint**: The AI never changes layout (columns, tables, fonts, spacing, section order, headings). It only edits specific text fields.

## Project Status

### ✅ Step 1: Core Round-Trip Validation (COMPLETE)

The first step validates the core constraint: **editing content without changing layout**.

**What's implemented:**
- DOCX parser that extracts content units with stable IDs
- DOCX patcher that applies edits back preserving structure
- Test endpoints and scripts to validate the round-trip

**Structure:**
```
app/
  ├── main.py              # FastAPI application
  ├── models/              # Data models (ContentUnit, ParsedResume)
  ├── docx/                # DOCX parsing and patching modules
  │   ├── parser.py        # Parse DOCX → structured JSON with IDs
  │   └── patcher.py       # Apply edits back → DOCX (structure preserved)
  └── api/                 # API endpoints
      ├── parse.py         # Parse endpoint
      └── test_roundtrip.py # Round-trip test endpoint
scripts/
  └── test_roundtrip.py    # Standalone test script
```

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Running the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Parse DOCX
```bash
POST /parse/docx
Content-Type: multipart/form-data
Body: file (resume.docx)
```

Returns structured JSON with content units and stable IDs.

#### Test Round-Trip
```bash
POST /test/roundtrip
Content-Type: multipart/form-data
Body: file (resume.docx)
```

Parses the DOCX, edits the first content unit (appends " [TESTED]"), patches it back, and returns the patched DOCX file.

### Testing with Script

You can also test the round-trip using the standalone script:

```bash
python scripts/test_roundtrip.py path/to/your/resume.docx
```

This will:
1. Parse the DOCX
2. Edit the first content unit
3. Apply the edit back to the DOCX
4. Save the patched version
5. Print comparison instructions

**Example:**
```bash
python scripts/test_roundtrip.py test_files/sample_resume.docx
```

## Testing the Round-Trip

After running the test, compare the original and patched DOCX files. Verify that:

1. ✅ **Only the text content changed** (first content unit has " [TESTED]" appended)
2. ✅ **Layout is preserved** (columns, tables, spacing unchanged)
3. ✅ **Styles are preserved** (fonts, formatting, indentation unchanged)
4. ✅ **Structure is unchanged** (sections, headings in same order)

If all checks pass, the core constraint is validated! ✅

## Next Steps

Once the round-trip is validated, we can proceed with:
1. Enhanced parsing (more sections, better heuristics)
2. Job description signal extraction
3. Evidence mapping
4. AI-powered rewrite suggestions
5. Validators and risk scoring
6. Review UI
7. DOCX → PDF export

## Architecture

**Current (MVP)**: Modular monolith
- FastAPI backend
- Python worker (same process for now)
- Can split services later

**Planned**: 3-service architecture
- Frontend: Next.js
- API: FastAPI (orchestration, persistence, auth)
- Worker: Python (DOCX parsing, JD analysis, rewriting, validators, DOCX patching, PDF export)

## Constraints (Non-Negotiable)

1. **Input**: DOCX only (v1)
2. **Output**: DOCX (editable) + PDF (ATS-safe, selectable text)
3. **Layout is frozen**: Never change columns, tables, fonts, spacing, section order, headings
4. **No hallucinations**: Never add tools, skills, or metrics not already present
5. **Targeted edits only**: Only edit specific text fields (bullets, summary, skills)

## License

[Your License Here]
