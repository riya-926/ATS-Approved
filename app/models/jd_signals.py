"""Data models for job description signals."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SkillCategory(str, Enum):
    """Categories of technical skills."""

    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    TOOL = "tool"
    PLATFORM = "platform"
    LIBRARY = "library"
    PROTOCOL = "protocol"
    METHODOLOGY = "methodology"
    CERTIFICATION = "certification"


class ResponsibilityType(str, Enum):
    """Types of responsibilities extracted from JD."""

    DEVELOPMENT = "development"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DEVOPS = "devops"
    COLLABORATION = "collaboration"
    LEADERSHIP = "leadership"
    DESIGN = "design"
    ANALYSIS = "analysis"
    MANAGEMENT = "management"


class HardSkill(BaseModel):
    """A hard skill extracted from the job description."""

    name: str = Field(..., description="Normalized skill name (e.g., 'Python', 'SQL', 'AWS')")
    category: SkillCategory = Field(..., description="Category of the skill")
    variations: list[str] = Field(
        default_factory=list, description="Variations found in the JD (e.g., 'Structured Query Language' for 'SQL')"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score for this extraction (0.0-1.0)"
    )
    mentions: int = Field(default=1, description="Number of times this skill is mentioned")


class Responsibility(BaseModel):
    """A responsibility extracted from the job description."""

    verb: str = Field(..., description="Action verb (e.g., 'develop', 'design', 'implement')")
    object: str = Field(..., description="What is being acted upon (e.g., 'REST APIs', 'microservices')")
    full_text: str = Field(..., description="Full responsibility phrase as it appeared")
    type: ResponsibilityType = Field(..., description="Category of responsibility")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")


class SeniorityCue(BaseModel):
    """Seniority level indicators from the job description."""

    level: str = Field(..., description="Detected level (e.g., 'junior', 'mid', 'senior', 'lead', 'principal')")
    years_experience: Optional[int] = Field(None, description="Required years of experience if mentioned")
    indicators: list[str] = Field(
        default_factory=list, description="Text phrases that indicated this seniority (e.g., '5+ years', 'Senior Engineer')"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")


class JDKeyword(BaseModel):
    """A keyword or phrase extracted from the job description."""

    keyword: str = Field(..., description="The keyword or phrase")
    category: str = Field(..., description="Category (e.g., 'industry_term', 'technology', 'methodology')")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0.0-1.0)")
    mentions: int = Field(default=1, description="Number of mentions")


class JobDescriptionSignals(BaseModel):
    """Structured signals extracted from a job description."""

    hard_skills: list[HardSkill] = Field(default_factory=list, description="Hard skills extracted")
    responsibilities: list[Responsibility] = Field(default_factory=list, description="Responsibilities extracted")
    keywords: list[JDKeyword] = Field(default_factory=list, description="Important keywords/phrases")
    seniority_cues: list[SeniorityCue] = Field(default_factory=list, description="Seniority level indicators")
    raw_text: str = Field(..., description="Original job description text")
    metadata: dict = Field(default_factory=dict, description="Additional metadata about extraction")

