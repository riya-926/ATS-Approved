"""
API endpoints for job description signal extraction.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.jd.extractor import extract_jd_signals

router = APIRouter(prefix="/jd", tags=["job-description"])


class JDTextRequest(BaseModel):
    """Request model for JD text extraction."""

    text: str = Field(..., description="Job description text", min_length=1)


@router.post("/extract")
async def extract_jd_signals_endpoint(request: JDTextRequest):
    """
    Extract structured signals from a job description.

    Returns hard skills, responsibilities, keywords, and seniority cues
    as structured JSON.
    """
    try:
        signals = extract_jd_signals(request.text)

        return {
            "hard_skills": [skill.model_dump() for skill in signals.hard_skills],
            "responsibilities": [resp.model_dump() for resp in signals.responsibilities],
            "keywords": [kw.model_dump() for kw in signals.keywords],
            "seniority_cues": [cue.model_dump() for cue in signals.seniority_cues],
            "metadata": signals.metadata,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting signals: {str(e)}")

