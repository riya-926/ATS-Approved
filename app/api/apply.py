"""
API endpoint for applying user decisions and generating final DOCX or PDF.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.docx.patcher import patch_docx
from app.models.content_unit import ContentUnit, ParsedResume

router = APIRouter(prefix="/rewrite", tags=["rewrite"])

# Use project root for test_files (where parse saves uploaded files)
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "test_files"


class ApplyRequest(BaseModel):
    """Request model for applying edits."""

    resume_json: dict = Field(..., description="Parsed resume JSON")
    decisions: list[dict] = Field(..., description="User decisions (accepted/rejected/edited)")
    original_filename: str = Field(..., description="Original resume filename")


@router.post("/apply")
async def apply_edits(request: ApplyRequest):
    """
    Apply user decisions and generate final tailored DOCX.

    Takes user decisions (accept/reject/edit) and applies them to the original DOCX.
    """
    try:
        # Parse resume
        resume = ParsedResume(**request.resume_json)

        # Create mapping of content_unit_id to ContentUnit
        unit_map = {unit.id: unit for unit in resume.content_units}

        # Prepare updated content units based on decisions
        updated_units = []
        removed_ids = set()
        for decision in request.decisions:
            unit_id = decision.get("content_unit_id")
            status = decision.get("status", "pending")

            if unit_id not in unit_map:
                continue

            original_unit = unit_map[unit_id]

            if status == "removed":
                removed_ids.add(unit_id)
                continue

            if status == "accepted":
                # Use edited text if provided, otherwise use suggested text
                final_text = decision.get("final_text", decision.get("suggested_text", original_unit.content))
                updated_unit = ContentUnit(
                    id=original_unit.id,
                    type=original_unit.type,
                    content=final_text,
                    section_index=original_unit.section_index,
                    paragraph_index=original_unit.paragraph_index,
                    bullet_index=original_unit.bullet_index,
                )
                updated_units.append(updated_unit)
            else:
                # Rejected or pending - keep original
                updated_units.append(original_unit)

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        original_path = UPLOAD_DIR / request.original_filename

        if not original_path.exists():
            docx_files = list(UPLOAD_DIR.glob("*.docx"))
            if docx_files:
                original_path = docx_files[0]
            else:
                raise HTTPException(status_code=404, detail="Original resume file not found")

        output_docx = UPLOAD_DIR / f"tailored_{request.original_filename}"
        success = patch_docx(original_path, output_docx, updated_units, resume, removed_ids=removed_ids)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply edits")

        return FileResponse(
            path=output_docx,
            filename=f"tailored_{request.original_filename}",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying edits: {str(e)}")


@router.post("/apply-pdf")
async def apply_edits_pdf(request: ApplyRequest):
    """
    Apply user decisions, generate tailored DOCX, convert to PDF, and return the PDF.
    Requires Microsoft Word (Windows/macOS) or docx2pdf-compatible setup.
    """
    try:
        from docx2pdf import convert as docx2pdf_convert
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires docx2pdf. Install with: pip install docx2pdf. On Windows, Microsoft Word must be installed.",
        )

    # Apply edits and convert to PDF
    try:
        resume = ParsedResume(**request.resume_json)
        unit_map = {unit.id: unit for unit in resume.content_units}
        updated_units = []
        removed_ids = set()
        for decision in request.decisions:
            unit_id = decision.get("content_unit_id")
            status = decision.get("status", "pending")
            if unit_id not in unit_map:
                continue
            original_unit = unit_map[unit_id]
            if status == "removed":
                removed_ids.add(unit_id)
                continue
            if status == "accepted":
                final_text = decision.get("final_text", decision.get("suggested_text", original_unit.content))
                updated_unit = ContentUnit(
                    id=original_unit.id,
                    type=original_unit.type,
                    content=final_text,
                    section_index=original_unit.section_index,
                    paragraph_index=original_unit.paragraph_index,
                    bullet_index=original_unit.bullet_index,
                )
                updated_units.append(updated_unit)
            else:
                updated_units.append(original_unit)

        original_path = UPLOAD_DIR / request.original_filename
        if not original_path.exists():
            docx_files = list(UPLOAD_DIR.glob("*.docx"))
            original_path = docx_files[0] if docx_files else None
        if not original_path or not original_path.exists():
            raise HTTPException(status_code=404, detail="Original resume file not found")

        output_docx = UPLOAD_DIR / f"tailored_{request.original_filename}"
        success = patch_docx(original_path, output_docx, updated_units, resume, removed_ids=removed_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply edits")

        output_pdf = output_docx.with_suffix(".pdf")
        docx2pdf_convert(str(output_docx), str(output_pdf))

        if not output_pdf.exists():
            raise HTTPException(status_code=500, detail="PDF conversion failed")

        return FileResponse(
            path=output_pdf,
            filename=f"tailored_{Path(request.original_filename).stem}.pdf",
            media_type="application/pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting PDF: {str(e)}")
