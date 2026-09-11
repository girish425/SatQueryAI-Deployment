import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image

from backend.app.utils.geotiff_utils import read_geotiff, generate_rgb_preview
from backend.app.utils.confidence import calculate_image_analysis_confidence


class VQAModel:
    """Remote Sensing Visual Question Answering pipeline with question-aware spectral reasoning."""

    def __init__(self, evidence_dir: str = "./evidence"):
        self.name = "RS-VQA-Spectral-Baseline"
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _extract_target_features(self, query: str) -> Tuple[str, List[str]]:
        """Identify what feature the user is asking about."""
        q = query.lower()
        if any(term in q for term in ["water", "river", "lake", "ocean", "sea", "pond", "reservoir", "stream"]):
            return "water", ["water", "hydrological"]
        elif any(term in q for term in ["crop", "agriculture", "field", "farm", "paddy", "wheat"]):
            return "crops", ["agriculture", "crop fields"]
        elif any(term in q for term in ["vegetation", "forest", "tree", "plant", "greenery"]):
            return "vegetation", ["vegetation", "canopy"]
        elif any(term in q for term in ["building", "structure", "urban", "house", "built-up", "settlement", "city"]):
            return "buildings", ["built-up structures", "urban features"]
        elif any(term in q for term in ["road", "highway", "street", "path", "runway"]):
            return "roads", ["linear infrastructure", "transportation corridors"]
        elif any(term in q for term in ["cloud", "smoke", "haze", "shadow"]):
            return "clouds", ["atmospheric obstruction", "cloud cover"]
        else:
            return "general", ["general terrain"]

    def analyze(self, image_path: str, query: str) -> Dict[str, Any]:
        start_time = time.time()
        raster, metadata = read_geotiff(image_path)
        h, w, bands = raster.shape
        total_pixels = h * w

        # Normalization
        if bands >= 3:
            rgb = raster[:, :, :3].astype(np.float32)
        else:
            gray = raster[:, :, 0].astype(np.float32)
            rgb = np.stack([gray, gray, gray], axis=-1)

        rgb_norm = np.zeros_like(rgb, dtype=np.float32)
        for c in range(3):
            ch = rgb[:, :, c]
            c_min, c_max = np.percentile(ch, 2), np.percentile(ch, 98)
            if c_max > c_min:
                rgb_norm[:, :, c] = np.clip((ch - c_min) / (c_max - c_min), 0.0, 1.0)
            else:
                rgb_norm[:, :, c] = 0.5

        r, g, b = rgb_norm[:, :, 0], rgb_norm[:, :, 1], rgb_norm[:, :, 2]
        brightness = (r + g + b) / 3.0

        target_category, category_labels = self._extract_target_features(query)

        # Calculate feature masks dynamically from real raster pixels
        if target_category == "water":
            # High blue, lower red/green, or very dark body
            mask = ((b > (r + 0.06)) & (b >= g) & (brightness < 0.70)) | ((brightness < 0.15) & (g < 0.25))
            feature_name = "water-like bodies"
        elif target_category in ["crops", "vegetation"]:
            # High green over red & blue
            mask = (g > (r + 0.04)) & (g > b) & (brightness > 0.15)
            feature_name = "agricultural crops and vegetative canopy" if target_category == "crops" else "vegetation"
        elif target_category == "buildings":
            # High brightness with low color saturation (concrete/metal/roofing)
            saturation = np.max(rgb_norm, axis=-1) - np.min(rgb_norm, axis=-1)
            mask = (brightness > 0.58) & (saturation < 0.28) & (g <= (r + 0.08))
            feature_name = "built-up structures and man-made surfaces"
        elif target_category == "roads":
            # Moderate to high brightness linear-like spectral signature
            saturation = np.max(rgb_norm, axis=-1) - np.min(rgb_norm, axis=-1)
            mask = (brightness > 0.45) & (brightness < 0.85) & (saturation < 0.20)
            feature_name = "road network or transport surfaces"
        elif target_category == "clouds":
            # Ultra high brightness across all bands
            mask = (r > 0.85) & (g > 0.85) & (b > 0.85)
            feature_name = "cloud cover or atmospheric reflection"
        else:
            # General presence check
            mask = (brightness > 0.20) & (brightness < 0.90)
            feature_name = "discernible remote sensing features"

        detected_pixels = int(np.sum(mask))
        coverage_pct = round(float(detected_pixels / total_pixels * 100), 2)
        is_present = coverage_pct > 1.5

        # Friendly verbal spatial position
        y_indices, x_indices = np.where(mask)
        spatial_desc = ""
        if is_present and len(y_indices) > 0:
            mean_y = float(np.mean(y_indices)) / h
            mean_x = float(np.mean(x_indices)) / w
            v_pos = "top (north)" if mean_y < 0.35 else ("bottom (south)" if mean_y > 0.65 else "middle")
            h_pos = "left (west)" if mean_x < 0.35 else ("right (east)" if mean_x > 0.65 else "center")
            spatial_desc = f"{v_pos}-{h_pos}"

        # Formulate truthful, question-aware responses in everyday simple English
        filename_base = Path(image_path).stem
        overlay_filename = f"{filename_base}_vqa_overlay.png"
        overlay_path = str(self.evidence_dir / overlay_filename)

        # Highlight detected feature in evidence overlay
        evidence_img = (rgb_norm * 255.0).astype(np.uint8)
        if is_present:
            evidence_img[mask] = [234, 179, 8]  # Amber gold highlight
        Image.fromarray(evidence_img).save(overlay_path, "PNG")

        original_preview = f"{filename_base}_preview.png"
        original_preview_path = str(self.evidence_dir / original_preview)
        if not os.path.exists(original_preview_path):
            generate_rgb_preview(raster, original_preview_path)

        key_findings = []
        if is_present:
            summary = f"Yes, {feature_name} are clearly present in this satellite image."
            key_findings.append(f"Size: Covers about {coverage_pct}% of the total land area.")
            if spatial_desc:
                key_findings.append(f"Location: Most of it is gathered in the {spatial_desc} section.")
            key_findings.append("Visual Map: The detected areas are marked in bright yellow in the evidence image below.")
            explanation = (
                f"What this means: The satellite camera detected distinct color and light patterns that match {target_category}. "
                f"You can see exactly where they are by looking at the yellow areas highlighted in the picture below."
            )
        else:
            summary = f"No clear {target_category} was found in this image."
            key_findings.append(f"Hardly any trace was found (less than {coverage_pct}% of the area).")
            key_findings.append(f"The ground here does not show the typical colors or signs of {target_category}.")
            key_findings.append("Note: If there are very small objects or things hidden under tree shadows, they might not be visible from space.")
            explanation = (
                f"What this means: After scanning every part of this satellite image, the system could not find any recognizable {target_category}. "
                f"If you are expecting to see it here, it might be too small for this satellite camera to resolve."
            )

        confidence = calculate_image_analysis_confidence(
            raster,
            target_coverage_fraction=coverage_pct / 100.0,
            contrast_metric=float(np.std(rgb_norm))
        )

        processing_time = round(time.time() - start_time, 2)

        return {
            "model_name": self.name,
            "target_feature": target_category,
            "answer": {
                "summary": summary,
                "key_findings": key_findings,
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
                "preprocessing_info": f"Normalized {bands}-band raster, evaluated {total_pixels} pixels against {target_category} spectral index."
            },
            "confidence": confidence
        }


vqa_model = VQAModel()
