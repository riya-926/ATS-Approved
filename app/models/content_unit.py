"""Content unit models for structured resume data"""
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


class DisplayItem(BaseModel):
    """Non-editable display item for full document layout."""

    kind: str = Field(..., description="display | editable")
    content: Optional[str] = Field(None, description="Text content for display items")
    display_type: Optional[str] = Field(None, description="name | contact | section_header | job_title | company_dates | education_degree | education_school")
    unit_id: Optional[str] = Field(None, description="Content unit ID for editable items")


class ParsedResume(BaseModel):
    """Structured representation of a parsed resume."""

    content_units: list[ContentUnit] = Field(..., description="All editable content units")
    display_order: list[dict] = Field(default_factory=list, description="Full document structure in order for display")
    metadata: dict = Field(default_factory=dict, description="Document metadata")

