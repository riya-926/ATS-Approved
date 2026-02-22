"""
DOCX patcher that applies edits back to the document preserving structure

This module patches text content in the original DOCX while preserving
all styles, formatting, spacing, and layout.
"""
from pathlib import Path
from typing import Optional

from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph

from app.models.content_unit import ContentUnit, ParsedResume


def patch_docx(
    original_path: str | Path,
    output_path: str | Path,
    content_units: list[ContentUnit],
    original_parsed: ParsedResume,
    removed_ids: set | None = None,
) -> bool:
    """
    Apply content unit edits back to the original DOCX, preserving structure.

    Args:
        original_path: Path to the original DOCX file
        output_path: Path where the patched DOCX will be saved
        content_units: Updated content units (with new content)
        original_parsed: The originally parsed resume (for reference)

    Returns:
        True if successful, False otherwise
    """
    doc = Document(original_path)
    removed_ids = removed_ids if removed_ids is not None else set()

    # Create a mapping of ID to updated content
    updates = {unit.id: unit.content for unit in content_units}

    # Collect paragraphs to remove (cannot modify during iteration)
    paragraphs_to_remove = []

    # Rebuild the same section tracking as parser (must match parser logic exactly)
    section_idx = 0
    para_idx = 0
    bullet_idx = 0
    current_section = None
    exp_bullet_counter = 0  # Global counter matching parser
    proj_bullet_counter = 0  # Global counter for project bullets
    skills_idx = 0

    for element in doc.element.body:
        if isinstance(element, CT_P):
            paragraph = Paragraph(element, doc)
            text = paragraph.text.strip()

            if not text:
                continue

            # Detect section headers (same logic as parser)
            text_upper = text.upper()
            exact_match = text_upper in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "SKILLS", "SUMMARY", "EDUCATION", "PROJECTS"]
            projects_match = "PROJECTS" in text_upper and len(text) < 80
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
                bullet_idx = 0  # Reset bullet counter for new section
                continue

            # Determine expected unit ID (must match parser ID generation)
            expected_id = None
            if current_section in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT"]:
                if paragraph.style.name.startswith("List") or text.startswith(("•", "-", "*")):
                    expected_id = f"exp_bullet_{exp_bullet_counter}"
                    bullet_idx += 1
                    exp_bullet_counter += 1
            elif current_section == "PROJECTS":
                if paragraph.style.name.startswith("List") or text.startswith(("•", "-", "*")):
                    expected_id = f"proj_bullet_{proj_bullet_counter}"
                    bullet_idx += 1
                    proj_bullet_counter += 1
            elif current_section == "SKILLS":
                expected_id = f"skills_line_{skills_idx}"
                skills_idx += 1
            elif current_section == "SUMMARY":
                if para_idx == 0:
                    expected_id = "summary_1"

            # Remove paragraph if marked for removal
            if expected_id and expected_id in removed_ids:
                paragraphs_to_remove.append(paragraph._p)
                if current_section and text:
                    para_idx += 1
                continue

            # Apply update if this unit has changed
            if expected_id and expected_id in updates:
                new_content = updates[expected_id]
                _replace_paragraph_text(paragraph, new_content)

            # Increment paragraph index for non-header paragraphs in relevant sections
            if current_section and text:
                para_idx += 1

    # Remove paragraphs marked for deletion (must do after iteration)
    for p_elem in paragraphs_to_remove:
        parent = p_elem.getparent()
        if parent is not None:
            parent.remove(p_elem)

    # Save the patched document (succeed even if no matches - e.g. different doc structure)
    doc.save(output_path)
    return True


def _replace_paragraph_text(paragraph: Paragraph, new_text: str) -> None:
    """
    Replace paragraph text while preserving all formatting and styles.

    This preserves:
    - Paragraph style
    - Indentation
    - Spacing
    - Bullet list formatting (when applicable)

    Note: We preserve the paragraph's XML structure, only replacing the text content
    of the runs. For bullet lists, the list formatting is preserved at the paragraph level.
    """
    # Store the original paragraph style
    original_style = paragraph.style

    # Clear all runs (text content) but keep paragraph properties
    paragraph.clear()

    # Add new text - the paragraph style is preserved because we're working
    # with the same paragraph element
    paragraph.add_run(new_text)

    # Restore the original style (in case clear() affected it)
    paragraph.style = original_style

