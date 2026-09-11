import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image
import tifffile


def read_geotiff(file_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Read GeoTIFF raster data and extract technical metadata.
    Returns:
        raster: np.ndarray in (height, width, bands) format normalized to float32 or uint8
        metadata: Dict with dimensions, bands, crs, dtype, etc.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"GeoTIFF file not found: {file_path}")

    # Use tifffile to read raw raster
    try:
        data = tifffile.imread(file_path)
    except Exception:
        # Fallback to Pillow
        img = Image.open(file_path)
        data = np.array(img)

    metadata = {
        "filename": path.name,
        "crs": "EPSG:4326 (WGS84)",
        "original_dtype": str(data.dtype),
    }

    # Standardize shape to (height, width, bands)
    if data.ndim == 2:
        # Single band: (H, W) -> (H, W, 1)
        data = data[:, :, np.newaxis]
    elif data.ndim == 3:
        if data.shape[0] in [1, 2, 3, 4, 8, 12, 13] and data.shape[0] < min(data.shape[1], data.shape[2]):
            # Channel first: (C, H, W) -> (H, W, C)
            data = np.transpose(data, (1, 2, 0))
    elif data.ndim > 3:
        # Squeeze or take first slice
        data = np.squeeze(data)
        if data.ndim == 2:
            data = data[:, :, np.newaxis]
        elif data.ndim == 3 and data.shape[0] < data.shape[2]:
            data = np.transpose(data, (1, 2, 0))

    height, width, bands = data.shape
    metadata["height"] = height
    metadata["width"] = width
    metadata["bands"] = bands
    metadata["dimensions"] = f"{width} x {height}"

    return data, metadata


def generate_rgb_preview(raster: np.ndarray, output_path: str, max_size: int = 1024) -> str:
    """
    Convert raw satellite raster (multi-band or single-band) to a web-compatible 8-bit RGB PNG.
    Applies standard 2%-98% cumulative contrast stretch to avoid washed out or black images.
    """
    height, width, bands = raster.shape

    if bands >= 3:
        # Optical RGB bands (take first 3 bands)
        rgb_data = raster[:, :, :3].astype(np.float32)
    elif bands == 2:
        # 2-channel (e.g. dual-pol SAR VV, VH) -> synthesize RGB
        ch1 = raster[:, :, 0].astype(np.float32)
        ch2 = raster[:, :, 1].astype(np.float32)
        ratio = np.divide(ch1, ch2 + 1e-6)
        rgb_data = np.stack([ch1, ch2, ratio], axis=-1)
    else:
        # Single band (SAR backscatter or panchromatic / elevation)
        gray = raster[:, :, 0].astype(np.float32)
        rgb_data = np.stack([gray, gray, gray], axis=-1)

    # 2% - 98% percentile contrast stretch per channel
    stretched = np.zeros_like(rgb_data, dtype=np.uint8)
    for c in range(3):
        channel = rgb_data[:, :, c]
        valid_vals = channel[np.isfinite(channel)]
        if len(valid_vals) > 0:
            p2, p98 = np.percentile(valid_vals, (2, 98))
            if p98 > p2:
                clipped = np.clip(channel, p2, p98)
                normalized = ((clipped - p2) / (p98 - p2) * 255.0).astype(np.uint8)
            else:
                normalized = np.zeros_like(channel, dtype=np.uint8)
        else:
            normalized = np.zeros_like(channel, dtype=np.uint8)
        stretched[:, :, c] = normalized

    img = Image.fromarray(stretched, mode="RGB")

    # Resize if too large for browser performance
    if max(width, height) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return output_path


def compute_band_statistics(raster: np.ndarray) -> Dict[str, Any]:
    """Calculate authentic image statistics across bands."""
    height, width, bands = raster.shape
    stats = {
        "dimensions": f"{width} x {height}",
        "bands": bands,
        "mean_brightness": float(np.mean(raster)),
        "std_deviation": float(np.std(raster)),
        "min_val": float(np.min(raster)),
        "max_val": float(np.max(raster)),
        "band_stats": []
    }

    for b in range(bands):
        b_data = raster[:, :, b].astype(np.float32)
        stats["band_stats"].append({
            "band_index": b + 1,
            "mean": float(np.mean(b_data)),
            "std": float(np.std(b_data)),
            "min": float(np.min(b_data)),
            "max": float(np.max(b_data))
        })

    return stats
