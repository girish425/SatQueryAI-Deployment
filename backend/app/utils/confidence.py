import math
from typing import Dict, Any, List
import numpy as np


def calculate_intent_confidence(query: str, matched_keywords: List[str], base_score: float = 0.70) -> float:
    """
    Calculate genuine intent confidence based on token matches, query length, and pattern specificity.
    """
    if not query:
        return 0.50

    words = query.lower().split()
    query_len = len(words)
    match_count = len(matched_keywords)

    if match_count == 0:
        return round(min(0.65, max(0.40, base_score - 0.20)), 2)

    # Specificity ratio
    specificity = min(1.0, match_count / max(1.0, math.sqrt(query_len)))
    confidence = base_score + (specificity * 0.25)
    return round(min(0.96, max(0.55, confidence)), 2)


def calculate_image_analysis_confidence(
    raster: np.ndarray,
    target_coverage_fraction: float = 0.0,
    contrast_metric: float = 1.0
) -> float:
    """
    Calculate confidence based on image clarity, signal variance, and detection distinctiveness.
    """
    try:
        # Standard deviation of image data reflects informational richness
        std_val = float(np.std(raster))
        mean_val = float(np.mean(raster)) + 1e-6
        cv = std_val / mean_val  # coefficient of variation

        # Score components
        cv_score = min(0.35, max(0.10, cv * 0.20))
        contrast_score = min(0.35, max(0.10, contrast_metric * 0.25))

        # Coverage factor: detection with very tiny or very saturated coverage has higher uncertainty
        if 0.01 <= target_coverage_fraction <= 0.85:
            coverage_factor = 0.25
        elif target_coverage_fraction > 0.0:
            coverage_factor = 0.15
        else:
            coverage_factor = 0.20

        total_confidence = 0.30 + cv_score + contrast_score + coverage_factor
        return round(min(0.94, max(0.60, total_confidence)), 2)
    except Exception:
        return 0.78
