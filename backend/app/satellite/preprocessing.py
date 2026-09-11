import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from PIL import Image
from backend.app.utils.geotiff_utils import read_geotiff, generate_rgb_preview, compute_band_statistics


class SatellitePreprocessor:
    """Satellite image preprocessing pipeline for GeoTIFF and remote sensing data."""

    def __init__(self, upload_dir: str = "./uploads", evidence_dir: str = "./evidence"):
        self.upload_dir = Path(upload_dir)
        self.evidence_dir = Path(evidence_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def process_geotiff(self, file_path: str, file_id: str) -> Dict[str, Any]:
        """
        Process uploaded GeoTIFF:
        - Read raster data
        - Check CRS, dimensions, bands
        - Generate web RGB preview
        - Extract spectral band statistics
        """
        raster, metadata = read_geotiff(file_path)
        stats = compute_band_statistics(raster)

        # Generate browser-compatible RGB preview
        preview_filename = f"{file_id}_preview.png"
        preview_path = str(self.evidence_dir / preview_filename)
        generate_rgb_preview(raster, preview_path)

        preview_url = f"/evidence/{preview_filename}"

        return {
            "file_id": file_id,
            "filename": metadata["filename"],
            "dimensions": metadata["dimensions"],
            "width": metadata["width"],
            "height": metadata["height"],
            "bands": metadata["bands"],
            "crs": metadata["crs"],
            "preview_url": preview_url,
            "preview_path": preview_path,
            "stats": stats,
            "preprocessing_info": f"Normalized {metadata['bands']}-band GeoTIFF with 2%-98% cumulative contrast stretch for visual analysis."
        }

    def tile_image(self, raster: np.ndarray, tile_size: int = 512) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """Tile large satellite raster into manageable sub-arrays with coordinates (y1, y2, x1, x2)."""
        height, width, _ = raster.shape
        tiles = []
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                y2 = min(height, y + tile_size)
                x2 = min(width, x + tile_size)
                tile = raster[y:y2, x:x2]
                tiles.append((tile, (y, y2, x, x2)))
        return tiles


satellite_preprocessor = SatellitePreprocessor()
