"""
Test endpoint to validate the DOCX parse → edit → patch round-trip.

This endpoint allows testing the core constraint: editing content without
changing document structure.
"""
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.docx.parser import parse_docx
from app.docx.patcher import patch_docx
from app.models.content_unit import ContentUnit

router = APIRouter(prefix="/test", tags=["test"])


@router.post("/roundtrip")
async def test_roundtrip(file: UploadFile = File(...)):
    """
    Test the round-trip: parse DOCX → edit one unit → patch back → verify.

    This validates that we can edit content units without changing layout.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="File must be a .docx file")

    # Save uploaded file temporarily
    upload_dir = Path("test_files")
    upload_dir.mkdir(exist_ok=True)

    original_path = upload_dir / f"original_{file.filename}"
    output_path = upload_dir / f"patched_{file.filename}"

    try:
        # Save uploaded file
        with open(original_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Step 1: Parse DOCX
        parsed = parse_docx(original_path)

        if not parsed.content_units:
            raise HTTPException(
                status_code=400, detail="No content units found. Ensure the resume has Experience/Skills/Summary sections."
            )

        # Step 2: Edit one content unit (for testing)
        # Modify the first content unit by appending " [TESTED]"
        updated_units = []
        first_unit = parsed.content_units[0]
        updated_unit = ContentUnit(
            id=first_unit.id,
            type=first_unit.type,
            content=first_unit.content + " [TESTED]",
            section_index=first_unit.section_index,
            paragraph_index=first_unit.paragraph_index,
            bullet_index=first_unit.bullet_index,
        )
        updated_units.append(updated_unit)

        # Keep all other units unchanged
        for unit in parsed.content_units[1:]:
            updated_units.append(unit)

        # Step 3: Apply edit back to DOCX
        success = patch_docx(original_path, output_path, updated_units, parsed)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to patch document")

        # Return the patched file
        return FileResponse(
            path=output_path,
            filename=f"patched_{file.filename}",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up original file (keep output for download)
        if original_path.exists():
            original_path.unlink()

