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

    upload_dir = Path("test_files")
    upload_dir.mkdir(exist_ok=True)

    temp_path = upload_dir / f"temp_{file.filename}"

    try:
        # Save uploaded file temporarily
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Parse the document
        parsed = parse_docx(temp_path)

        # Return structured data
        return {
            "content_units": [unit.model_dump() for unit in parsed.content_units],
            "metadata": parsed.metadata,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()

