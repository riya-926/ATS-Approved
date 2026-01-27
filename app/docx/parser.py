"""
DOCX parser that extracts content units with stable IDs

This parser extracts editable text content while preserving document structure.
It assigns stable IDs to each content unit for later patching.
"""
from pathlib import Path
from typing import Optional

from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph

from app.models.content_unit import ContentUnit, ContentUnitType, ParsedResume


def parse_docx(file_path: str | Path) -> ParsedResume:
    """
    Parse a DOCX file into structured content units with stable IDs.

    Args:
        file_path: Path to the DOCX file

    Returns:
        ParsedResume with content units and metadata
    """
    doc = Document(file_path)
    content_units: list[ContentUnit] = []

    # Track section indices
    section_idx = 0
    exp_bullet_counter = 0  # Global counter for experience bullets across all experience entries
    skills_idx = 0
    bullet_idx = 0  # Local bullet counter per experience entry

    # Simple heuristics to identify sections (can be improved)
    current_section = None
    para_idx = 0

    for element in doc.element.body:
        if isinstance(element, CT_P):
            # It's a paragraph
            paragraph = Paragraph(element, doc)
            text = paragraph.text.strip()

            if not text:
                continue

            # Detect section headers (check for Heading style OR bold + short text + common headers)
            is_header = (
                len(text) < 80
                and text.upper() in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "SKILLS", "SUMMARY", "EDUCATION"]
                and (
                    paragraph.style.name.startswith("Heading")
                    or any(run.bold for run in paragraph.runs)
                )
            )

            if is_header:
                current_section = text.upper()
                para_idx = 0
                section_idx += 1
                bullet_idx = 0  # Reset bullet counter for new section
                continue

            # Extract content units based on section
            if current_section in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT"]:
                # Check if it's a bullet point (indented or starts with bullet)
                if paragraph.style.name.startswith("List") or text.startswith(("•", "-", "*")):
                    bullet_text = text.lstrip("•-* ").strip()
                    if bullet_text:
                        unit = ContentUnit(
                            id=f"exp_bullet_{exp_bullet_counter}",
                            type=ContentUnitType.EXPERIENCE_BULLET,
                            content=bullet_text,
                            section_index=section_idx,
                            paragraph_index=para_idx,
                            bullet_index=bullet_idx,
                        )
                        content_units.append(unit)
                        bullet_idx += 1
                        exp_bullet_counter += 1
                para_idx += 1

            elif current_section == "SKILLS":
                # Skills are often comma-separated or one per line
                skills_text = text.strip()
                if skills_text:
                    unit = ContentUnit(
                        id=f"skills_line_{skills_idx}",
                        type=ContentUnitType.SKILLS_LINE,
                        content=skills_text,
                        section_index=section_idx,
                        paragraph_index=para_idx,
                    )
                    content_units.append(unit)
                    skills_idx += 1
                para_idx += 1

            elif current_section == "SUMMARY":
                # Summary is typically the first paragraph in summary section
                if para_idx == 0:
                    unit = ContentUnit(
                        id="summary_1",
                        type=ContentUnitType.SUMMARY,
                        content=text,
                        section_index=section_idx,
                        paragraph_index=0,
                    )
                    content_units.append(unit)
                para_idx += 1

        elif isinstance(element, CT_Tbl):
            # It's a table - for now, skip tables (can be extended later)
            pass

    metadata = {
        "paragraph_count": len(doc.paragraphs),
        "sections_found": section_idx,
    }

    return ParsedResume(content_units=content_units, metadata=metadata)

