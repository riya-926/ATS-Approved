"""
API endpoint for applying user decisions and generating final DOCX.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.docx.patcher import patch_docx
from app.models.content_unit import ContentUnit, ParsedResume

router = APIRouter(prefix="/rewrite", tags=["rewrite"])


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
        for decision in request.decisions:
            unit_id = decision.get("content_unit_id")
            status = decision.get("status", "pending")

            if unit_id not in unit_map:
                continue

            original_unit = unit_map[unit_id]

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

        # Find original file (for now, use a placeholder - in production, store original path)
        # This is a simplified version - in production, you'd store the original file path
        upload_dir = Path("test_files")
        original_path = upload_dir / request.original_filename

        if not original_path.exists():
            # Try to find any DOCX file as fallback
            docx_files = list(upload_dir.glob("*.docx"))
            if docx_files:
                original_path = docx_files[0]
            else:
                raise HTTPException(status_code=404, detail="Original resume file not found")

        # Generate output path
        output_path = upload_dir / f"tailored_{request.original_filename}"

        # Apply patches
        success = patch_docx(original_path, output_path, updated_units, resume)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply edits")

        # Return the patched file
        return FileResponse(
            path=output_path,
            filename=f"tailored_{request.original_filename}",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying edits: {str(e)}")
