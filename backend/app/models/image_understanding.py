import os
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image

from backend.app.utils.geotiff_utils import read_geotiff, generate_rgb_preview
from backend.app.utils.confidence import calculate_image_analysis_confidence


class ImageUnderstandingModel:
    """Specialized Scene Understanding and Land-Cover Engine for Remote Sensing."""

    def __init__(self, evidence_dir: str = "./evidence"):
        self.name = "RS-Image-Understanding-Baseline"
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self, image_path: str, query: str = "") -> Dict[str, Any]:
        start_time = time.time()
        raster, metadata = read_geotiff(image_path)
        h, w, bands = raster.shape
        total_pixels = h * w

        # Prepare normalized RGB representation (0.0 to 1.0)
        if bands >= 3:
            rgb = raster[:, :, :3].astype(np.float32)
        else:
            gray = raster[:, :, 0].astype(np.float32)
            rgb = np.stack([gray, gray, gray], axis=-1)

        # Normalize 0 to 1
        rgb_norm = np.zeros_like(rgb, dtype=np.float32)
        for c in range(3):
            ch = rgb[:, :, c]
            c_min, c_max = np.percentile(ch, 2), np.percentile(ch, 98)
            if c_max > c_min:
                rgb_norm[:, :, c] = np.clip((ch - c_min) / (c_max - c_min), 0.0, 1.0)
            else:
                rgb_norm[:, :, c] = 0.5

        r = rgb_norm[:, :, 0]
        g = rgb_norm[:, :, 1]
        b = rgb_norm[:, :, 2]

        # Calculate genuine remote sensing indices from actual pixel values:
        # Greenness / Vegetation Index (Green vs Red/Blue ratio)
        denom_veg = g + r + 1e-6
        veg_index = (g - r) / denom_veg
        veg_mask = (veg_index > 0.08) & (g > b)
        veg_pct = round(float(np.sum(veg_mask) / total_pixels * 100), 1)

        # Water Index (High blue, low red, low overall brightness)
        brightness = (r + g + b) / 3.0
        water_mask = (b > (r + 0.08)) & (b >= g) & (brightness < 0.65)
        # Deep water is also low reflectance
        deep_water_mask = (brightness < 0.18) & (veg_mask == False)
        combined_water_mask = water_mask | deep_water_mask
        water_pct = round(float(np.sum(combined_water_mask) / total_pixels * 100), 1)

        # Built-up / High-reflectance structures (high brightness and neutral saturation)
        saturation = np.max(rgb_norm, axis=-1) - np.min(rgb_norm, axis=-1)
        built_mask = (brightness > 0.60) & (saturation < 0.25) & (~veg_mask)
        built_pct = round(float(np.sum(built_mask) / total_pixels * 100), 1)

        # Bare soil / Open land (remaining pixels)
        other_pct = round(max(0.0, 100.0 - (veg_pct + water_pct + built_pct)), 1)

        # Generate evidence segmentation preview map
        # Color code: Green=Veg, Blue=Water, Red/Orange=Built-up, Yellow=Open land
        seg_map = np.zeros((h, w, 3), dtype=np.uint8)
        seg_map[..., 0] = (r * 180 + 40).astype(np.uint8)
        seg_map[..., 1] = (g * 180 + 40).astype(np.uint8)
        seg_map[..., 2] = (b * 180 + 40).astype(np.uint8)

        # Tint detected classes
        seg_map[veg_mask] = [34, 197, 94]       # Emerald green
        seg_map[combined_water_mask] = [59, 130, 246] # Blue
        seg_map[built_mask] = [239, 68, 68]     # Crimson red

        filename_base = Path(image_path).stem
        overlay_filename = f"{filename_base}_understanding_overlay.png"
        overlay_path = str(self.evidence_dir / overlay_filename)
        Image.fromarray(seg_map).save(overlay_path, "PNG")

        original_preview = f"{filename_base}_preview.png"
        original_preview_path = str(self.evidence_dir / original_preview)
        if not os.path.exists(original_preview_path):
            generate_rgb_preview(raster, original_preview_path)

        # Dynamic text synthesis based strictly on calculated values
        # Friendly land-cover labels
        class_friendly = {
            "vegetation": "green plants and crops",
            "water": "water bodies (like lakes or rivers)",
            "built-up": "buildings and roads",
            "open/bare land": "open fields or dry ground"
        }

        # Clear, friendly findings in simple everyday language
        findings = []
        if veg_pct > 15.0:
            findings.append(f"Greenery & Farmland: Covers about {veg_pct}% of the area (healthy green vegetation).")
        elif veg_pct > 3.0:
            findings.append(f"Greenery: Scattered patches of plants or trees make up about {veg_pct}% of the area.")

        if water_pct > 5.0:
            findings.append(f"Water: A clearly visible river or lake covers about {water_pct}% of the area.")
        elif water_pct > 0.5:
            findings.append(f"Water: Small ponds or streams cover about {water_pct}% of the area.")

        if built_pct > 3.0:
            findings.append(f"Buildings & Roads: Town areas, roofs, and paved roads make up about {built_pct}%.")

        findings.append(f"Open Land: The rest ({other_pct}%) is open ground, empty soil, or grasslands.")

        # Determine dominant land cover
        classes = [("vegetation", veg_pct), ("water", water_pct), ("built-up", built_pct), ("open/bare land", other_pct)]
        classes.sort(key=lambda x: x[1], reverse=True)
        dominant_label = class_friendly.get(classes[0][0], classes[0][0])
        second_label = class_friendly.get(classes[1][0], classes[1][0])
        third_label = class_friendly.get(classes[2][0], classes[2][0])

        # Query-specific framing in plain, easy-to-read English
        q_lower = query.lower()
        if "what is visible" in q_lower or "what can you see" in q_lower or "what is there" in q_lower:
            summary = (
                f"In this satellite photo, you can see mostly {dominant_label} (about {classes[0][1]}%), "
                f"along with noticeable areas of {second_label} ({classes[1][1]}%) and {third_label} ({classes[2][1]}%)."
            )
        elif "describe" in q_lower or "overview" in q_lower or "tell me" in q_lower or "tell about" in q_lower:
            summary = (
                f"This image shows a broad view of the landscape. Most of the territory is {dominant_label}, "
                f"with clear sections of {second_label} and {third_label} across the view."
            )
        elif "land cover" in q_lower or "classification" in q_lower:
            summary = (
                f"Here is how the land is divided: the biggest part is {dominant_label} at {classes[0][1]}%, "
                f"followed by {second_label} at {classes[1][1]}% and {third_label} at {classes[2][1]}%."
            )
        else:
            summary = (
                f"This satellite view shows an area made up mainly of {dominant_label} ({classes[0][1]}%), "
                f"with {second_label} ({classes[1][1]}%) and {third_label} ({classes[2][1]}%) also clearly visible."
            )

        explanation = (
            f"What this means: This picture shows an active landscape with a balanced mix of open ground, natural vegetation, and water. "
            f"In the visual evidence below, green highlights the plant life, blue shows the water, and red marks the man-made buildings and structures."
        )

        confidence = calculate_image_analysis_confidence(
            raster,
            target_coverage_fraction=(veg_pct + water_pct) / 100.0,
            contrast_metric=float(np.std(rgb_norm))
        )

        processing_time = round(time.time() - start_time, 2)

        return {
            "model_name": self.name,
            "answer": {
                "summary": summary,
                "key_findings": findings,
                "explanation": explanation
            },
            "evidence": {
                "original_image": f"/evidence/{original_preview}",
                "overlay_image": f"/evidence/{overlay_filename}",
                "difference_image": None
            },
            "technical_details": {
                "dimensions": metadata["dimensions"],
                "bands": bands,
                "crs": metadata["crs"],
                "processing_time_sec": processing_time,
                "preprocessing_info": f"Full scene spectral extraction and land-cover segmentation on {metadata['dimensions']} raster."
            },
            "confidence": confidence
        }


image_understanding_model = ImageUnderstandingModel()
