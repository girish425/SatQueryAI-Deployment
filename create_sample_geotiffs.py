import os
from pathlib import Path
import numpy as np
import tifffile
from PIL import Image

sample_dir = Path("./sample_data")
uploads_dir = Path("./uploads")
sample_dir.mkdir(parents=True, exist_ok=True)
uploads_dir.mkdir(parents=True, exist_ok=True)

h, w = 512, 512
y_coords, x_coords = np.mgrid[0:h, 0:w]

# 1. Optical Scene: Hyderabad Landscape
# Features:
# - River winding from top-center (x ~ 300, y ~ 0) to bottom-right (x ~ 450, y ~ 512)
river_center = 300 + 150 * (y_coords / h) + 30 * np.sin(y_coords / 40.0)
river_mask = np.abs(x_coords - river_center) < 22

# - Agricultural zone in western half (x < 240)
agri_mask = (x_coords < 240) & (y_coords > 80) & (y_coords < 440)

# - Built-up urban sector in center-left (x: 120-220, y: 160-260)
urban_mask = (x_coords >= 120) & (x_coords <= 220) & (y_coords >= 160) & (y_coords <= 260)

# Bands: 0=Red, 1=Green, 2=Blue (uint8 or uint16)
optical = np.zeros((h, w, 3), dtype=np.uint8)
# Base terrain (warm soil)
optical[:, :, 0] = 160 + (np.random.normal(0, 10, (h, w))).clip(-20, 20).astype(np.uint8)
optical[:, :, 1] = 140 + (np.random.normal(0, 10, (h, w))).clip(-20, 20).astype(np.uint8)
optical[:, :, 2] = 110 + (np.random.normal(0, 10, (h, w))).clip(-20, 20).astype(np.uint8)

# Paint agriculture: high green
optical[agri_mask, 0] = 45
optical[agri_mask, 1] = 175
optical[agri_mask, 2] = 50

# Paint built-up: high brightness neutral albedo
optical[urban_mask, 0] = 220
optical[urban_mask, 1] = 225
optical[urban_mask, 2] = 230

# Paint river: high blue, low red
optical[river_mask, 0] = 25
optical[river_mask, 1] = 85
optical[river_mask, 2] = 210

opt_path = sample_dir / "sample_optical_hyderabad.tif"
tifffile.imwrite(
    str(opt_path),
    optical,
    photometric='rgb',
    metadata={'axes': 'YXS', 'description': 'Sentinel-2 MSI Surface Reflectance Hyderabad'}
)

# 2. SAR Microwave Radar: Hyderabad
# 1-band float32 / uint16
# River = specular absorption (very dark, ~0.05)
# Urban = double-bounce corner reflection (very bright, ~0.95)
# Agriculture/Trees = volume scatter (~0.45)
# Soil = surface scatter (~0.25)
sar = np.random.normal(0.25, 0.05, (h, w)).clip(0.1, 0.4).astype(np.float32)
sar[agri_mask] = np.random.normal(0.48, 0.08, np.sum(agri_mask)).clip(0.3, 0.7)
sar[urban_mask] = np.random.normal(0.88, 0.06, np.sum(urban_mask)).clip(0.75, 1.0)
sar[river_mask] = np.random.normal(0.04, 0.02, np.sum(river_mask)).clip(0.01, 0.08)

sar_path = sample_dir / "sample_sar_hyderabad.tif"
tifffile.imwrite(
    str(sar_path),
    (sar * 255).astype(np.uint8),
    metadata={'axes': 'YX', 'description': 'Sentinel-1 C-SAR IW GRD Hyderabad'}
)

# 3. Bi-temporal Pair for Change Detection:
# T1 (Pre-development)
t1 = optical.copy()
# T2 (Post-development: New development built in northeast quadrant x: 380-480, y: 40-140)
t2 = optical.copy()
new_dev_mask = (x_coords >= 360) & (x_coords <= 480) & (y_coords >= 40) & (y_coords <= 160)
t2[new_dev_mask, 0] = 235
t2[new_dev_mask, 1] = 235
t2[new_dev_mask, 2] = 240

# Also some vegetation loss in agri belt (harvested / dry)
harvest_mask = (x_coords >= 50) & (x_coords <= 150) & (y_coords >= 280) & (y_coords <= 380)
t2[harvest_mask, 0] = 180
t2[harvest_mask, 1] = 145
t2[harvest_mask, 2] = 95

t1_path = sample_dir / "sample_change_t1.tif"
t2_path = sample_dir / "sample_change_t2.tif"
tifffile.imwrite(str(t1_path), t1, photometric='rgb')
tifffile.imwrite(str(t2_path), t2, photometric='rgb')

# Copy to uploads so they can be immediately queried
import shutil
for p in [opt_path, sar_path, t1_path, t2_path]:
    shutil.copyfile(str(p), str(uploads_dir / p.name))

print("Created sample remote sensing GeoTIFF datasets successfully.")
