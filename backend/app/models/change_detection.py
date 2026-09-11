import os
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image

from backend.app.utils.geotiff_utils import read_geotiff, generate_rgb_preview
from backend.app.utils.confidence import calculate_image_analysis_confidence


class ChangeDetectionModel:
    """Bi-temporal change detection engine comparing before-and-after satellite acquisitions."""

    def __init__(self, evidence_dir: str = "./evidence"):
        self.name = "RS-BiTemporal-Change-Baseline"
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self, image_paths: List[str], query: str = "") -> Dict[str, Any]:
        start_time = time.time()

        if len(image_paths) < 2:
            raise ValueError("Change detection requires two images. Please upload a before and after image.")

        # Read both images
        r1, meta1 = read_geotiff(image_paths[0])
        r2, meta2 = read_geotiff(image_paths[1])

        # Align dimensions to match (resize image 2 to image 1 if different)
        h1, w1, b1 = r1.shape
        h2, w2, b2 = r2.shape

        # Normalize both to RGB 0-1
        def to_norm_rgb(r):
            if r.shape[2] >= 3:
                rgb = r[:, :, :3].astype(np.float32)
            else:
                gray = r[:, :, 0].astype(np.float32)
                rgb = np.stack([gray, gray, gray], axis=-1)
            norm = np.zeros_like(rgb, dtype=np.float32)
            for c in range(3):
                ch = rgb[:, :, c]
                p2, p98 = np.percentile(ch, 2), np.percentile(ch, 98)
                if p98 > p2:
                    norm[:, :, c] = np.clip((ch - p2) / (p98 - p2), 0.0, 1.0)
                else:
                    norm[:, :, c] = 0.5
            return norm

        rgb1 = to_norm_rgb(r1)
        rgb2 = to_norm_rgb(r2)

        if (h1, w1) != (h2, w2):
            # Resize img2 to img1 using PIL
            img2_pil = Image.fromarray((rgb2 * 255).astype(np.uint8)).resize((w1, h1), Image.Resampling.BILINEAR)
            rgb2 = np.array(img2_pil).astype(np.float32) / 255.0

        # Compute absolute difference
        abs_diff = np.abs(rgb2 - rgb1)
        mean_diff = np.mean(abs_diff, axis=-1)  # (h1, w1)

        # Dynamic Otsu-like or percentile threshold for change
        diff_threshold = max(0.12, float(np.mean(mean_diff) + 1.2 * np.std(mean_diff)))
        change_mask = mean_diff > diff_threshold

        total_pixels = h1 * w1
        changed_pixels = int(np.sum(change_mask))
        change_pct = round(float(changed_pixels / total_pixels * 100), 2)

        # Directional change: was there vegetation increase/decrease or urban expansion?
        # Greenness channel 1:
        g_diff = rgb2[:, :, 1] - rgb1[:, :, 1]
        veg_gain_mask = change_mask & (g_diff > 0.08)
        veg_loss_mask = change_mask & (g_diff < -0.08)

        # Brightness change:
        br1 = np.mean(rgb1, axis=-1)
        br2 = np.mean(rgb2, axis=-1)
        br_diff = br2 - br1
        dev_gain_mask = change_mask & (br_diff > 0.10) & (~veg_gain_mask)

        veg_gain_pct = round(float(np.sum(veg_gain_mask) / total_pixels * 100), 2)
        veg_loss_pct = round(float(np.sum(veg_loss_mask) / total_pixels * 100), 2)
        dev_gain_pct = round(float(np.sum(dev_gain_mask) / total_pixels * 100), 2)

        # Render Difference Heatmap (Colormap: Blue/Black=no change, Yellow/Red=high change)
        diff_vis = np.zeros((h1, w1, 3), dtype=np.uint8)
        # Background: grayscale of before image
        gray_bg = (np.mean(rgb1, axis=-1) * 120).astype(np.uint8)
        diff_vis[:, :, 0] = gray_bg
        diff_vis[:, :, 1] = gray_bg
        diff_vis[:, :, 2] = gray_bg

        # Highlight changes:
        # Development = Bright Orange/Red [255, 69, 0]
        # Vegetation loss = Magenta [219, 39, 119]
        # Vegetation gain = Vibrant Green [34, 197, 94]
        diff_vis[veg_gain_mask] = [34, 197, 94]
        diff_vis[veg_loss_mask] = [219, 39, 119]
        diff_vis[dev_gain_mask] = [255, 69, 0]
        # Other changes = Yellow
        other_change = change_mask & (~veg_gain_mask) & (~veg_loss_mask) & (~dev_gain_mask)
        diff_vis[other_change] = [234, 179, 8]

        filename_base1 = Path(image_paths[0]).stem
        filename_base2 = Path(image_paths[1]).stem
        diff_filename = f"diff_{filename_base1}_{filename_base2}.png"
        diff_path = str(self.evidence_dir / diff_filename)
        Image.fromarray(diff_vis).save(diff_path, "PNG")

        # Save previews of both
        p1_name = f"{filename_base1}_preview.png"
        p2_name = f"{filename_base2}_preview.png"
        generate_rgb_preview(r1, str(self.evidence_dir / p1_name))
        generate_rgb_preview(r2, str(self.evidence_dir / p2_name))

        summary = f"Comparing the two satellite pictures shows that about {change_pct}% of the land changed between the two dates."

        key_findings = [
            f"Overall Change: About {change_pct}% of the land area looks noticeably different.",
            f"New Construction & Buildings: About {dev_gain_pct}% shows new roofs, concrete, or cleared construction zones (shown in red/orange).",
            f"Plant Growth: About {veg_gain_pct}% shows new green vegetation or crop growth (shown in green).",
            f"Loss of Greenery: About {veg_loss_pct}% shows trees or crops that were removed, dried out, or harvested (shown in pink)."
        ]

        explanation = (
            f"What this means: By comparing the earlier and later pictures, the system spotted where changes took place. "
            f"In the difference picture below: Green shows where plants grew, Pink shows where plants disappeared, "
            f"and Red/Orange shows where new buildings or land clearing occurred."
        )

        confidence = calculate_image_analysis_confidence(
            mean_diff,
            target_coverage_fraction=change_pct / 100.0,
            contrast_metric=float(np.std(mean_diff)) * 2.0
        )

        processing_time = round(time.time() - start_time, 2)

        return {
            "model_name": self.name,
            "change_percentage": change_pct,
            "answer": {
                "summary": summary,
                "key_findings": key_findings,
                "explanation": explanation
            },
            "evidence": {
                "original_image": f"/evidence/{p1_name}",
                "overlay_image": f"/evidence/{p2_name}",
                "difference_image": f"/evidence/{diff_filename}"
            },
            "technical_details": {
                "dimensions": f"{w1} x {h1}",
                "bands": max(b1, b2),
                "crs": meta1["crs"],
                "processing_time_sec": processing_time,
                "preprocessing_info": f"Co-registered two acquisitions to {w1}x{h1}, computed absolute difference and dynamic spectral change mask."
            },
            "confidence": confidence
        }


change_detection_model = ChangeDetectionModel()
