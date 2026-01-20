"""Data models for evidence mapping between JD signals and resume content."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MatchType(str, Enum):
    """Types of evidence matches."""

    SKILL = "skill"
    RESPONSIBILITY = "responsibility"
    KEYWORD = "keyword"


class EvidenceMatch(BaseModel):
    """A single match between a JD signal and a resume content unit."""

    jd_item_id: str = Field(..., description="Identifier for the JD signal (e.g., 'skill_python_1')")
    resume_unit_id: str = Field(..., description="Identifier for the resume content unit that supports this match")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this match (0.0-1.0)")
    match_type: MatchType = Field(..., description="Type of match (skill, responsibility, keyword)")
    match_reason: str = Field(..., description="Explanation of why this match was made")
    jd_item_data: dict = Field(..., description="The JD signal data that was matched")
    resume_unit_content: str = Field(..., description="The resume content that supports this match")

    class Config:
        use_enum_values = True


class SkillMatch(BaseModel):
    """A match between a JD hard skill and resume content."""

    jd_skill: dict = Field(..., description="The JD hard skill that was matched")
    resume_bullets: list[dict] = Field(
        default_factory=list, description="Resume content units that support this skill"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence for this skill match")
    match_details: list[EvidenceMatch] = Field(
        default_factory=list, description="Individual evidence matches for this skill"
    )


class ResponsibilityMatch(BaseModel):
    """A match between a JD responsibility and resume content."""

    jd_responsibility: dict = Field(..., description="The JD responsibility that was matched")
    resume_bullets: list[dict] = Field(
        default_factory=list, description="Resume content units that support this responsibility"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence for this responsibility match")
    match_details: list[EvidenceMatch] = Field(
        default_factory=list, description="Individual evidence matches for this responsibility"
    )


class KeywordMatch(BaseModel):
    """A match between a JD keyword and resume content."""

    jd_keyword: dict = Field(..., description="The JD keyword that was matched")
    resume_units: list[dict] = Field(
        default_factory=list, description="Resume content units that contain this keyword"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence for this keyword match")
    match_details: list[EvidenceMatch] = Field(
        default_factory=list, description="Individual evidence matches for this keyword"
    )


class UnsupportedRequirement(BaseModel):
    """A JD requirement that has no evidence in the resume."""

    type: str = Field(..., description="Type of requirement (skill, responsibility, keyword)")
    name: str = Field(..., description="Name or description of the requirement")
    jd_item_data: dict = Field(..., description="The JD signal data")
    reason: str = Field(..., description="Why no evidence was found")


class EvidenceMap(BaseModel):
    """Complete evidence mapping between JD signals and resume content."""

    skill_matches: list[SkillMatch] = Field(
        default_factory=list, description="Matches between JD skills and resume content"
    )
    responsibility_matches: list[ResponsibilityMatch] = Field(
        default_factory=list, description="Matches between JD responsibilities and resume content"
    )
    keyword_matches: list[KeywordMatch] = Field(
        default_factory=list, description="Matches between JD keywords and resume content"
    )
    unsupported_requirements: list[UnsupportedRequirement] = Field(
        default_factory=list, description="JD requirements with no evidence in resume"
    )
    coverage_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall coverage score (0.0-1.0) indicating how much of JD is supported"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata about the mapping")
