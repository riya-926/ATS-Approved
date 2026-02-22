"""
API endpoints for rewrite suggestions.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.content_unit import ParsedResume
from app.models.evidence import EvidenceMap
from app.models.jd_signals import JobDescriptionSignals
from app.rewrite.suggester import (
    _analyze_bullet_point_consistency,
    _estimate_resume_length,
    suggest_rewrite_for_unit,
    suggest_rewrites,
)

router = APIRouter(prefix="/rewrite", tags=["rewrite"])


class RewriteRequest(BaseModel):
    """Request model for rewrite suggestions."""

    jd_signals: dict = Field(..., description="Job description signals (from /jd/extract)")
    evidence_map: dict = Field(..., description="Evidence mapping (from /evidence/map)")
    resume_json: dict = Field(..., description="Parsed resume content (from /parse/docx)")
    max_suggestions: int = Field(default=10, ge=1, le=50, description="Maximum number of suggestions to generate")


@router.post("/suggest")
async def suggest_rewrites_endpoint(request: RewriteRequest):
    """
    Generate AI-powered rewrite suggestions for resume content.

    This endpoint:
    - Analyzes resume content against job description requirements
    - Generates improved versions that align with JD while preserving meaning
    - Ensures ATS optimization (80%+ score target)
    - Maintains tense consistency and removes fluff words
    - Only suggests meaningful, impactful changes

    Args:
        request: Contains jd_signals, evidence_map, resume_json, and max_suggestions

    Returns:
        RewriteSuggestions with all generated suggestions, including:
        - Original and suggested text for each content unit
        - Confidence scores and reasoning
        - JD alignment information
        - Coverage improvement metrics
    """
    try:
        # Parse JD signals from dict
        jd_signals = JobDescriptionSignals(**request.jd_signals)

        # Parse evidence map from dict
        evidence_map = EvidenceMap(**request.evidence_map)

        # Parse resume from dict
        resume = ParsedResume(**request.resume_json)

        # Generate rewrite suggestions
        rewrite_suggestions = suggest_rewrites(
            jd_signals=jd_signals,
            evidence_map=evidence_map,
            resume=resume,
            max_suggestions=request.max_suggestions,
        )

        # Return formatted response
        return {
            "suggestions": [
                {
                    "content_unit_id": suggestion.content_unit_id,
                    "original_text": suggestion.original_text,
                    "suggested_text": suggestion.suggested_text,
                    "confidence": suggestion.confidence,
                    "reasoning": suggestion.reasoning,
                    "jd_alignment": suggestion.jd_alignment,
                    "preserves_meaning": suggestion.preserves_meaning,
                    "risk_score": suggestion.risk_score,
                }
                for suggestion in rewrite_suggestions.suggestions
            ],
            "total_suggestions": rewrite_suggestions.total_suggestions,
            "coverage_improvement": rewrite_suggestions.coverage_improvement,
            "metadata": rewrite_suggestions.metadata,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating rewrite suggestions: {str(e)}")


class SuggestOneRequest(BaseModel):
    """Request model for regenerating a single suggestion."""

    content_unit_id: str = Field(..., description="ID of the content unit to regenerate")
    jd_signals: dict = Field(..., description="Job description signals")
    evidence_map: dict = Field(..., description="Evidence mapping")
    resume_json: dict = Field(..., description="Parsed resume content")


@router.post("/suggest-one")
async def suggest_one_endpoint(request: SuggestOneRequest):
    """
    Regenerate AI suggestion for a single content unit (redo button).
    """
    try:
        jd_signals = JobDescriptionSignals(**request.jd_signals)
        evidence_map = EvidenceMap(**request.evidence_map)
        resume = ParsedResume(**request.resume_json)

        unit = next((u for u in resume.content_units if u.id == request.content_unit_id), None)
        if not unit:
            raise HTTPException(status_code=404, detail=f"Content unit {request.content_unit_id} not found")

        bullet_analysis = _analyze_bullet_point_consistency(resume)
        length_analysis = _estimate_resume_length(resume)

        suggestion = suggest_rewrite_for_unit(
            unit, jd_signals, evidence_map, resume.content_units, bullet_analysis, length_analysis
        )

        if not suggestion:
            raise HTTPException(status_code=500, detail="Failed to generate suggestion")

        return {
            "content_unit_id": suggestion.content_unit_id,
            "original_text": suggestion.original_text,
            "suggested_text": suggestion.suggested_text,
            "confidence": suggestion.confidence,
            "reasoning": suggestion.reasoning,
            "jd_alignment": suggestion.jd_alignment,
            "preserves_meaning": suggestion.preserves_meaning,
            "risk_score": suggestion.risk_score,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating suggestion: {str(e)}")
