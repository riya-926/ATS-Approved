"""Content unit models for structured resume data."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ContentUnitType(str, Enum):
    """Types of content units that can be edited."""

    SUMMARY = "summary"
    EXPERIENCE_BULLET = "experience_bullet"
    SKILLS_LINE = "skills_line"
    EDUCATION_DESCRIPTION = "education_description"
    PROJECT_DESCRIPTION = "project_description"


class ContentUnit(BaseModel):
    """
    A single editable content unit with a stable ID.

    This represents a piece of text that can be edited while preserving
    the document structure.
    """

    id: str = Field(..., description="Stable identifier for this content unit")
    type: ContentUnitType = Field(..., description="Type of content unit")
    content: str = Field(..., description="Current text content")
    section_index: Optional[int] = Field(None, description="Section index (for ordering)")
    paragraph_index: Optional[int] = Field(None, description="Paragraph index within section")
    bullet_index: Optional[int] = Field(None, description="Bullet index (if applicable)")

    class Config:
        use_enum_values = True


class ParsedResume(BaseModel):
    """Structured representation of a parsed resume."""

    content_units: list[ContentUnit] = Field(..., description="All editable content units")
    metadata: dict = Field(default_factory=dict, description="Document metadata")

