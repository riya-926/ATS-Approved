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
    display_order: list[dict] = []

    # Track section indices
    section_idx = 0
    exp_bullet_counter = 0  # Global counter for experience bullets across all experience entries
    proj_bullet_counter = 0  # Global counter for project bullets
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
            text_upper = text.upper()
            exact_match = text_upper in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "SKILLS", "SUMMARY", "EDUCATION", "PROJECTS"]
            projects_match = "PROJECTS" in text_upper and len(text) < 80  # e.g. "COMPUTER SCIENCE PROJECTS"
            is_header = (
                len(text) < 80
                and (exact_match or projects_match)
                and (
                    paragraph.style.name.startswith("Heading")
                    or any(run.bold for run in paragraph.runs)
                )
            )

            if is_header:
                current_section = "PROJECTS" if projects_match and not exact_match else text_upper
                para_idx = 0
                section_idx += 1
                bullet_idx = 0
                header_map = {"SUMMARY": "Professional Summary", "EXPERIENCE": "Work Experience",
                              "WORK EXPERIENCE": "Work Experience", "EMPLOYMENT": "Work Experience",
                              "SKILLS": "Skills", "EDUCATION": "Education", "PROJECTS": "Projects"}
                display_order.append({"kind": "display", "content": header_map.get(current_section, text), "display_type": "section_header"})
                continue

            # Before any section (name, contact)
            if current_section is None:
                if not display_order:
                    display_order.append({"kind": "display", "content": text, "display_type": "name"})
                else:
                    display_order.append({"kind": "display", "content": text, "display_type": "contact"})
                continue

            # Extract content units based on section
            if current_section in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT"]:
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
                        display_order.append({"kind": "editable", "unit_id": unit.id})
                        bullet_idx += 1
                        exp_bullet_counter += 1
                else:
                    # Job title or company/dates line (display only)
                    if paragraph.style.name == "Heading 2" or (len(text) < 60 and "|" not in text and "•" not in text):
                        display_order.append({"kind": "display", "content": text, "display_type": "job_title"})
                    else:
                        display_order.append({"kind": "display", "content": text, "display_type": "company_dates"})
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
                    display_order.append({"kind": "editable", "unit_id": unit.id})
                    skills_idx += 1
                para_idx += 1

            elif current_section in ["PROJECTS"]:
                if paragraph.style.name.startswith("List") or text.startswith(("•", "-", "*")):
                    bullet_text = text.lstrip("•-* ").strip()
                    if bullet_text:
                        unit = ContentUnit(
                            id=f"proj_bullet_{proj_bullet_counter}",
                            type=ContentUnitType.PROJECT_DESCRIPTION,
                            content=bullet_text,
                            section_index=section_idx,
                            paragraph_index=para_idx,
                            bullet_index=bullet_idx,
                        )
                        content_units.append(unit)
                        display_order.append({"kind": "editable", "unit_id": unit.id})
                        bullet_idx += 1
                        proj_bullet_counter += 1
                else:
                    display_order.append({"kind": "display", "content": text, "display_type": "project_title"})
                para_idx += 1

            elif current_section == "EDUCATION":
                if paragraph.style.name == "Heading 2":
                    display_order.append({"kind": "display", "content": text, "display_type": "education_degree"})
                else:
                    display_order.append({"kind": "display", "content": text, "display_type": "education_school"})

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
                    display_order.append({"kind": "editable", "unit_id": unit.id})
                para_idx += 1

        elif isinstance(element, CT_Tbl):
            # It's a table - for now, skip tables (can be extended later)
            pass

    metadata = {
        "paragraph_count": len(doc.paragraphs),
        "sections_found": section_idx,
    }

    return ParsedResume(content_units=content_units, display_order=display_order, metadata=metadata)

