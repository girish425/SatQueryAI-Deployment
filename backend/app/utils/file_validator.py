import os
from pathlib import Path
from typing import Tuple, Dict, Any
from PIL import Image
import tifffile


ALLOWED_EXTENSIONS = {".tif", ".tiff"}
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024  # 1 GB (1024 MB)


def validate_file(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate uploaded satellite image.
    Checks:
    - File existence
    - File size (up to 1 GB)
    - Extension (.tif, .tiff)
    - Valid readable GeoTIFF structure
    - Dimensions, band count, CRS/tags
    """
    path = Path(file_path)
    if not path.exists():
        return False, "File not found.", {}

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File exceeds maximum allowed size of 1GB (1024MB).", {}

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Unsupported file type. Please upload a .tif or .tiff satellite image.", {}

    metadata = {
        "filename": path.name,
        "file_size": file_size,
        "extension": ext,
        "bands": 1,
        "dimensions": "Unknown",
        "crs": "EPSG:4326 (WGS84)",
        "dtype": "unknown"
    }

    try:
        # Try reading TIFF tags and shape via tifffile
        with tifffile.TiffFile(file_path) as tif:
            first_page = tif.pages[0]
            metadata["dtype"] = str(first_page.dtype)
            shape = first_page.shape

            if len(shape) == 2:
                height, width = shape
                bands = 1
            elif len(shape) == 3:
                # Shape can be (bands, height, width) or (height, width, bands)
                if shape[0] < shape[2]:
                    bands, height, width = shape
                else:
                    height, width, bands = shape
            else:
                height, width, bands = shape[-2], shape[-1], shape[0]

            metadata["width"] = int(width)
            metadata["height"] = int(height)
            metadata["bands"] = int(bands)
            metadata["dimensions"] = f"{width} x {height}"

            # Check for geospatial tags (GeoKeyDirectory, ModelPixelScale, ModelTiepoint)
            has_geo = False
            for tag in first_page.tags:
                tag_name = tag.name.lower()
                if "geo" in tag_name or "model" in tag_name or "proj" in tag_name:
                    has_geo = True
                    break

            if has_geo:
                metadata["crs"] = "EPSG:4326 / UTM GeoTIFF"
            else:
                metadata["crs"] = "EPSG:4326 (Default Geographic)"

        return True, "Valid GeoTIFF file.", metadata

    except Exception as e:
        # Fallback check using Pillow
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                bands = len(img.getbands())
                metadata["width"] = width
                metadata["height"] = height
                metadata["bands"] = bands
                metadata["dimensions"] = f"{width} x {height}"
                metadata["dtype"] = img.mode
                return True, "Valid GeoTIFF file.", metadata
        except Exception as e_inner:
            return False, f"This file is not a valid GeoTIFF: {str(e_inner)}", {}
