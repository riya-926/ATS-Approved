"""
API endpoints for evidence mapping between JD signals and resume content.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.evidence.mapper import map_evidence
from app.models.content_unit import ParsedResume
from app.models.jd_signals import JobDescriptionSignals

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceMappingRequest(BaseModel):
    """Request model for evidence mapping."""

    jd_signals: dict = Field(..., description="Job description signals (from Step 3)")
    resume_json: dict = Field(..., description="Parsed resume content (from Step 1)")


@router.post("/map")
async def map_evidence_endpoint(request: EvidenceMappingRequest):
    """
    Map JD signals to resume content to find evidence.

    This endpoint prevents hallucinations by only suggesting rewrites
    based on existing evidence in the resume.

    Args:
        request: Contains jd_signals and resume_json

    Returns:
        EvidenceMap with skill_matches, responsibility_matches,
        keyword_matches, unsupported_requirements, and coverage_score
    """
    try:
        # Parse JD signals from dict
        jd_signals = JobDescriptionSignals(**request.jd_signals)

        # Parse resume from dict
        resume = ParsedResume(**request.resume_json)

        # Map evidence
        evidence_map = map_evidence(jd_signals, resume)

        # Return formatted response
        return {
            "skill_matches": [
                {
                    "jd_skill": match.jd_skill,
                    "resume_bullets": match.resume_bullets,
                    "confidence": match.confidence,
                    "match_details": [m.model_dump() for m in match.match_details],
                }
                for match in evidence_map.skill_matches
            ],
            "responsibility_matches": [
                {
                    "jd_responsibility": match.jd_responsibility,
                    "resume_bullets": match.resume_bullets,
                    "confidence": match.confidence,
                    "match_details": [m.model_dump() for m in match.match_details],
                }
                for match in evidence_map.responsibility_matches
            ],
            "keyword_matches": [
                {
                    "jd_keyword": match.jd_keyword,
                    "resume_units": match.resume_units,
                    "confidence": match.confidence,
                    "match_details": [m.model_dump() for m in match.match_details],
                }
                for match in evidence_map.keyword_matches
            ],
            "unsupported_requirements": [
                {
                    "type": req.type,
                    "name": req.name,
                    "jd_item_data": req.jd_item_data,
                    "reason": req.reason,
                }
                for req in evidence_map.unsupported_requirements
            ],
            "coverage_score": evidence_map.coverage_score,
            "metadata": evidence_map.metadata,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error mapping evidence: {str(e)}")
