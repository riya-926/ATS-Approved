"""
API endpoints for parsing resumes into structured content units
"""
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.docx.parser import parse_docx

router = APIRouter(prefix="/parse", tags=["parse"])


@router.post("/docx")
async def parse_docx_endpoint(file: UploadFile = File(...)):
    """
    Parse a DOCX resume into structured content units with stable IDs.

    Returns the parsed structure as JSON.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="File must be a .docx file")

    # Use project root for test_files (same as apply endpoint)
    upload_dir = Path(__file__).resolve().parent.parent.parent / "test_files"
    upload_dir.mkdir(exist_ok=True)

    # Save uploaded file (kept for apply step)
    saved_path = upload_dir / file.filename

    try:
        content = await file.read()
        with open(saved_path, "wb") as f:
            f.write(content)

        # Parse the document
        parsed = parse_docx(saved_path)

        # Return structured data
        return {
            "content_units": [unit.model_dump() for unit in parsed.content_units],
            "display_order": getattr(parsed, "display_order", []),
            "metadata": parsed.metadata,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")

