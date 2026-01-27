"""Data models for rewrite suggestions."""
from pydantic import BaseModel, Field


class RewriteSuggestion(BaseModel):
    """A suggestion to rewrite a resume content unit."""

    content_unit_id: str = Field(..., description="ID of the content unit to rewrite")
    original_text: str = Field(..., description="Original text from the resume")
    suggested_text: str = Field(..., description="AI-generated improved version")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this suggestion (0.0-1.0)")
    reasoning: str = Field(..., description="Explanation of why this change improves the resume")
    jd_alignment: dict = Field(
        default_factory=dict,
        description="Which JD requirements this rewrite addresses (skills, responsibilities, keywords)",
    )
    risk_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Risk score (0.0=low risk, 1.0=high risk)"
    )
    preserves_meaning: bool = Field(
        default=True, description="Whether the rewrite preserves the original meaning"
    )


class RewriteSuggestions(BaseModel):
    """Collection of rewrite suggestions for a resume."""

    suggestions: list[RewriteSuggestion] = Field(
        default_factory=list, description="All rewrite suggestions"
    )
    total_suggestions: int = Field(..., description="Total number of suggestions")
    coverage_improvement: float = Field(
        ..., ge=0.0, le=1.0, description="Expected improvement in JD coverage (0.0-1.0)"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
