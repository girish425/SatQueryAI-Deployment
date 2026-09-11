import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.utils.file_validator import validate_file
from backend.app.satellite.preprocessing import satellite_preprocessor

router = APIRouter(tags=["upload"])
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload/")
async def upload_geotiff(file: UploadFile = File(...)):
    """
    Upload and validate a satellite GeoTIFF (.tif / .tiff) image.
    Generates browser preview and extracts technical spatial metadata.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".tif", ".tiff"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .tif or .tiff satellite image."
        )

    file_id = f"sat_{uuid.uuid4().hex[:10]}"
    safe_filename = f"{file_id}_{file.filename}"
    saved_path = UPLOAD_DIR / safe_filename

    # Save to disk
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validate file integrity
    is_valid, message, metadata = validate_file(str(saved_path))
    if not is_valid:
        if saved_path.exists():
            os.remove(saved_path)
        raise HTTPException(status_code=400, detail=message)

    # Preprocess GeoTIFF: extract bands, CRS, dimensions and render contrast-stretched RGB preview
    try:
        proc_result = satellite_preprocessor.process_geotiff(str(saved_path), file_id)
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "saved_filename": safe_filename,
            "file_path": str(saved_path),
            "preview_url": proc_result["preview_url"],
            "dimensions": proc_result["dimensions"],
            "bands": proc_result["bands"],
            "crs": proc_result["crs"],
            "message": "Satellite GeoTIFF uploaded and preprocessed successfully."
        }
    except Exception as e:
        if saved_path.exists():
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Failed to preprocess satellite raster: {str(e)}")
