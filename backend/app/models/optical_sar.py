import os
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image

from backend.app.utils.geotiff_utils import read_geotiff, generate_rgb_preview
from backend.app.utils.confidence import calculate_image_analysis_confidence


class OpticalSARModel:
    """Multimodal Optical and Synthetic Aperture Radar (SAR) fusion analysis engine."""

    def __init__(self, evidence_dir: str = "./evidence"):
        self.name = "RS-Optical-SAR-Fusion-Baseline"
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self, image_paths: List[str], query: str = "") -> Dict[str, Any]:
        start_time = time.time()

        if not image_paths:
            raise ValueError("Optical-SAR analysis requires at least one satellite image.")

        # If 2 images are provided, assume img1 is optical and img2 is SAR (or detect by band count)
        if len(image_paths) >= 2:
            opt_raster, opt_meta = read_geotiff(image_paths[0])
            sar_raster, sar_meta = read_geotiff(image_paths[1])

            # Swap if img1 is 1-band and img2 is 3-band
            if opt_raster.shape[2] == 1 and sar_raster.shape[2] >= 3:
                opt_raster, sar_raster = sar_raster, opt_raster
                opt_meta, sar_meta = sar_meta, opt_meta
                opt_path, sar_path = image_paths[1], image_paths[0]
            else:
                opt_path, sar_path = image_paths[0], image_paths[1]
        else:
            # Single image analyzed for radar/multispectral characteristics
            opt_raster, opt_meta = read_geotiff(image_paths[0])
            sar_raster, sar_meta = opt_raster, opt_meta
            opt_path, sar_path = image_paths[0], image_paths[0]

        # Optical normalization
        opt_h, opt_w, opt_b = opt_raster.shape
        if opt_b >= 3:
            opt_rgb = opt_raster[:, :, :3].astype(np.float32)
        else:
            opt_gray = opt_raster[:, :, 0].astype(np.float32)
            opt_rgb = np.stack([opt_gray, opt_gray, opt_gray], axis=-1)

        opt_norm = np.zeros_like(opt_rgb)
        for c in range(3):
            ch = opt_rgb[:, :, c]
            p2, p98 = np.percentile(ch, 2), np.percentile(ch, 98)
            opt_norm[:, :, c] = np.clip((ch - p2) / (max(1e-5, p98 - p2)), 0.0, 1.0)

        # SAR processing: microwave radar data reflects physical surface roughness & dielectric permittivity
        sar_data = sar_raster[:, :, 0].astype(np.float32)
        # Apply log transform / decibel scaling for radar amplitude: 10 * log10(DN^2 + 1e-6)
        sar_db = 10.0 * np.log10(np.square(sar_data) + 1.0)
        sar_p5, sar_p95 = np.percentile(sar_db, 5), np.percentile(sar_db, 95)
        sar_norm = np.clip((sar_db - sar_p5) / (max(1e-5, sar_p95 - sar_p5)), 0.0, 1.0)

        # Radar backscatter statistics
        mean_backscatter = round(float(np.mean(sar_db)), 2)
        radar_roughness = round(float(np.std(sar_norm)), 3)

        # Smooth surfaces (calm water) have specular reflection pointing away -> very low SAR return (< 0.15)
        specular_water_mask = sar_norm < 0.18
        specular_water_pct = round(float(np.sum(specular_water_mask) / sar_norm.size * 100), 1)

        # Built structures / hard angles produce double-bounce corner reflection -> very bright SAR return (> 0.80)
        double_bounce_mask = sar_norm > 0.80
        double_bounce_pct = round(float(np.sum(double_bounce_mask) / sar_norm.size * 100), 1)

        # Volume scattering (vegetation canopy) produces moderate backscatter with high texture
        volume_scatter_pct = round(max(0.0, 100.0 - (specular_water_pct + double_bounce_pct)), 1)

        # Create fusion visualization: Side-by-side comparison of Optical RGB and SAR Microwave Intensity
        h_vis = min(opt_h, 512)
        w_vis = min(opt_w, 512)

        opt_pil = Image.fromarray((opt_norm * 255).astype(np.uint8)).resize((w_vis, h_vis), Image.Resampling.BILINEAR)
        # False-color SAR map (Yellow/Orange for double bounce, Dark blue for specular absorption)
        sar_cmap = np.zeros((sar_norm.shape[0], sar_norm.shape[1], 3), dtype=np.uint8)
        sar_cmap[:, :, 0] = (sar_norm * 255).astype(np.uint8)
        sar_cmap[:, :, 1] = (np.power(sar_norm, 1.5) * 200).astype(np.uint8)
        sar_cmap[:, :, 2] = ((1.0 - sar_norm) * 80).astype(np.uint8)
        sar_pil = Image.fromarray(sar_cmap).resize((w_vis, h_vis), Image.Resampling.BILINEAR)

        # Stitch side-by-side
        fusion_img = Image.new("RGB", (w_vis * 2 + 20, h_vis), (15, 23, 42))
        fusion_img.paste(opt_pil, (0, 0))
        fusion_img.paste(sar_pil, (w_vis + 20, 0))

        fusion_filename = f"fusion_{Path(opt_path).stem}_{Path(sar_path).stem}.png"
        fusion_path = str(self.evidence_dir / fusion_filename)
        fusion_img.save(fusion_path, "PNG")

        opt_preview = f"{Path(opt_path).stem}_preview.png"
        sar_preview = f"{Path(sar_path).stem}_preview.png"
        generate_rgb_preview(opt_raster, str(self.evidence_dir / opt_preview))
        generate_rgb_preview(sar_raster, str(self.evidence_dir / sar_preview))

        summary = (
            f"This analysis compares a standard optical satellite photo with a radar (SAR) satellite capture. "
            f"Combining both gives a much clearer understanding of land features, moisture, and man-made structures."
        )

        key_findings = [
            f"Buildings & Hard Surfaces: Reflect radar strongly and appear very bright in the radar view (covers about {double_bounce_pct}% of the scene).",
            f"Water & Flat Surfaces: Absorb or deflect radar waves and appear dark (covers about {specular_water_pct}% of the area).",
            f"Trees & Forest Foliage: Scatter the radar signals in all directions with medium texture (covers about {volume_scatter_pct}%).",
            "Cloud Penetration: Radar passes right through clouds and haze, capturing the ground even in poor weather."
        ]

        explanation = (
            "What this means: Standard satellite cameras take photos using sunlight, but can be blocked by weather and clouds. "
            "Radar satellites send down radio waves that pierce through clouds to measure surface texture, moisture, and buildings. "
            "In the side-by-side comparison below, you can see how optical colors compare directly with radar reflections."
        )

        confidence = calculate_image_analysis_confidence(
            sar_raster,
            target_coverage_fraction=(double_bounce_pct + specular_water_pct) / 100.0,
            contrast_metric=radar_roughness * 2.0
        )

        processing_time = round(time.time() - start_time, 2)

        return {
            "model_name": self.name,
            "mean_backscatter_db": mean_backscatter,
            "answer": {
                "summary": summary,
                "key_findings": key_findings,
                "explanation": explanation
            },
            "evidence": {
                "original_image": f"/evidence/{opt_preview}",
                "overlay_image": f"/evidence/{sar_preview}",
                "difference_image": f"/evidence/{fusion_filename}"
            },
            "technical_details": {
                "dimensions": f"{opt_w} x {opt_h}",
                "bands": opt_b + sar_raster.shape[2],
                "crs": opt_meta["crs"],
                "processing_time_sec": processing_time,
                "preprocessing_info": f"Log-decibel calibrated SAR amplitude combined with 2%-98% contrast stretched optical reflectance."
            },
            "confidence": confidence
        }


optical_sar_model = OpticalSARModel()
