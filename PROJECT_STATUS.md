# ATS-Approved Project Status

## ✅ Completed Steps

### Step 1: Core Round-Trip Validation ✅
**Status:** COMPLETE  
**Location:** `app/docx/parser.py`, `app/docx/patcher.py`

**What it does:**
- Parses DOCX files into structured content units with stable IDs
- Patches edits back to DOCX while preserving layout/structure
- Validates that only text content changes, not formatting

**Pure Python Functions:**
- `parse_docx(file_path) -> ParsedResume`
- `patch_docx(original_path, output_path, content_units, original_parsed) -> bool`

**API Endpoints:**
- `POST /parse/docx` - Parse DOCX to JSON
- `POST /test/roundtrip` - Test round-trip functionality

---

### Step 2: Job Description Signal Extraction ✅
**Status:** COMPLETE  
**Location:** `app/jd/extractor.py`

**What it does:**
- Extracts structured signals from job descriptions:
  - Hard skills (Python, AWS, SQL, etc.)
  - Responsibilities (verb + object patterns)
  - Keywords/phrases
  - Seniority cues

**Pure Python Functions:**
- `extract_jd_signals(jd_text: str) -> JobDescriptionSignals`

**API Endpoints:**
- `POST /jd/extract` - Extract JD signals

---

### Step 3: Evidence Mapping ✅
**Status:** COMPLETE  
**Location:** `app/evidence/mapper.py`

**What it does:**
- Matches JD signals to resume content units
- Finds evidence for each JD requirement in the resume
- Calculates confidence scores and coverage
- Identifies unsupported requirements (prevents hallucinations)

**Pure Python Functions:**
- `map_evidence(jd_signals: JobDescriptionSignals, resume: ParsedResume) -> EvidenceMap`
- `match_skills(jd_skills, resume) -> (skill_matches, unsupported_skills)`
- `match_responsibilities(jd_responsibilities, resume) -> (resp_matches, unsupported_resp)`
- `match_keywords(jd_keywords, resume) -> (keyword_matches, unsupported_keywords)`
- `calculate_confidence_score(...) -> float`

**API Endpoints:**
- `POST /evidence/map` - Map JD signals to resume evidence

---

## 🚧 Next Steps (In Order)

### Step 4: AI-Powered Rewrite Suggestions ⏳
**Status:** NOT STARTED  
**Planned Location:** `app/rewrite/suggester.py`

**What it needs to do:**
- Generate improved versions of resume content units based on:
  - JD signals (what the job wants)
  - Evidence matches (what the resume already has)
  - Original resume content (what to improve)

**Requirements:**
1. **Pure Python Functions First:**
   - `suggest_rewrites(evidence_map: EvidenceMap, jd_signals: JobDescriptionSignals, resume: ParsedResume) -> list[RewriteSuggestion]`
   - `suggest_bullet_improvement(original_bullet: str, jd_responsibility: Responsibility, evidence: EvidenceMatch) -> str`
   - `suggest_skills_wording(original_skills: str, jd_skills: list[HardSkill], matches: list[SkillMatch]) -> str`
   - `suggest_summary_improvement(original_summary: str, jd_signals: JobDescriptionSignals, evidence_map: EvidenceMap) -> str`

2. **Integration with Anthropic API:**
   - Use Claude to generate rewrite suggestions
   - Ensure prompts prevent hallucinations (only use existing evidence)
   - Maintain original meaning and truthfulness

3. **Output Format:**
   ```python
   class RewriteSuggestion(BaseModel):
       content_unit_id: str
       original_text: str
       suggested_text: str
       confidence: float
       reasoning: str
       jd_alignment: dict  # Which JD requirements this addresses
   ```

4. **Testing:**
   - Test with sample resumes and JDs
   - Verify no hallucinations (no new skills/metrics added)
   - Verify improvements align with JD requirements

5. **Then wrap with API:**
   - `POST /rewrite/suggest` - Get rewrite suggestions

---

### Step 5: Validators and Risk Scoring ⏳
**Status:** NOT STARTED  
**Planned Location:** `app/validators/`

**What it needs to do:**
- Validate rewrite suggestions for:
  - Truthfulness (no hallucinations)
  - ATS compatibility
  - Grammar and clarity
  - Risk scoring (how risky is this change?)

**Pure Python Functions:**
- `validate_rewrite(suggestion: RewriteSuggestion, original_resume: ParsedResume) -> ValidationResult`
- `calculate_risk_score(suggestion: RewriteSuggestion) -> float`
- `check_ats_compatibility(text: str) -> bool`

---

### Step 6: Review UI ⏳
**Status:** NOT STARTED  
**Frontend work (Next.js planned)**

---

### Step 7: DOCX → PDF Export ⏳
**Status:** NOT STARTED  
**Planned Location:** `app/docx/exporter.py`

**What it needs to do:**
- Convert patched DOCX to PDF
- Ensure ATS-safe PDF (selectable text, proper encoding)

**Pure Python Functions:**
- `export_to_pdf(docx_path: str, output_path: str) -> bool`

---

## 📋 Current Architecture

```
app/
├── main.py                 # FastAPI app (orchestration)
├── models/                 # Data models
│   ├── content_unit.py    # Resume content structure
│   ├── jd_signals.py      # JD extraction models
│   └── evidence.py        # Evidence mapping models
├── docx/                   # DOCX operations
│   ├── parser.py          # ✅ Parse DOCX → JSON
│   └── patcher.py         # ✅ Apply edits → DOCX
├── jd/                     # Job description processing
│   └── extractor.py       # ✅ Extract JD signals
├── evidence/               # Evidence mapping
│   └── mapper.py          # ✅ Match JD to resume
├── rewrite/                # ⏳ NEXT: Rewrite suggestions
│   └── suggester.py       # TODO: Generate improvements
├── validators/             # ⏳ FUTURE: Validation
└── api/                    # API endpoints
    ├── parse.py           # ✅ Parse endpoint
    ├── jd.py              # ✅ JD extraction endpoint
    ├── evidence.py        # ✅ Evidence mapping endpoint
    └── rewrite.py         # ⏳ TODO: Rewrite endpoint
```

---

## 🎯 Immediate Next Task: Step 4 - Rewrite Suggestions

**Approach:**
1. ✅ Create pure Python functions first (no API)
2. ✅ Test with sample data
3. ✅ Integrate Anthropic API for AI suggestions
4. ✅ Then wrap with API endpoint

**Files to Create:**
- `app/models/rewrite.py` - RewriteSuggestion model
- `app/rewrite/__init__.py`
- `app/rewrite/suggester.py` - Core rewrite logic
- `scripts/test_rewrite.py` - Test script

**Dependencies to Add:**
- `anthropic` - Anthropic SDK for Claude API
