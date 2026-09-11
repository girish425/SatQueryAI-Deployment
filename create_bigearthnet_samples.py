import os
import json
from pathlib import Path
import numpy as np
import tifffile
from PIL import Image

output_dir = Path("./sample_data/bigearthnet")
uploads_dir = Path("./uploads")
output_dir.mkdir(parents=True, exist_ok=True)
uploads_dir.mkdir(parents=True, exist_ok=True)

h, w = 256, 256
y_coords, x_coords = np.mgrid[0:h, 0:w]

# --- PATCH 1: River Valley, Forest & Mixed Cultivation (Austria / Central Europe) ---
# Co-registered S2 & S1
river_mask = np.abs(x_coords - (128 + 40 * np.sin(y_coords / 30.0))) < 14
forest_mask = (x_coords < 100) & (y_coords > 40)
agri_mask = (x_coords >= 150) & (y_coords < 200)
urban_mask = (x_coords >= 110) & (x_coords <= 170) & (y_coords >= 200)

# Sentinel-2 Multispectral RGB (B04, B03, B02)
s2_patch1 = np.zeros((h, w, 3), dtype=np.uint8)
s2_patch1[:, :] = [140, 130, 95]  # Background pasture / soil
s2_patch1[forest_mask] = [28, 120, 36]  # Dense coniferous/broad-leaved forest
s2_patch1[agri_mask] = [75, 165, 60]    # Complex cultivation patterns
s2_patch1[urban_mask] = [210, 215, 220] # Discontinuous urban fabric
s2_patch1[river_mask] = [30, 85, 205]   # Water course

# Sentinel-1 SAR (VV backscatter)
# Water = specular dark (<0.06), Urban = double-bounce bright (>0.85), Forest = volume texture (0.45-0.65), Agri = 0.25-0.45
s1_patch1 = np.random.normal(0.32, 0.05, (h, w)).clip(0.15, 0.5).astype(np.float32)
s1_patch1[forest_mask] = np.random.normal(0.55, 0.08, np.sum(forest_mask)).clip(0.35, 0.75)
s1_patch1[agri_mask] = np.random.normal(0.38, 0.06, np.sum(agri_mask)).clip(0.2, 0.55)
s1_patch1[urban_mask] = np.random.normal(0.88, 0.05, np.sum(urban_mask)).clip(0.75, 1.0)
s1_patch1[river_mask] = np.random.normal(0.04, 0.02, np.sum(river_mask)).clip(0.01, 0.08)

# --- PATCH 2: Mediterranean Coastal Lagoons, Sclerophyllous Vegetation & Olive Groves (Greece / Portugal) ---
water_body_mask = (y_coords > 140) & (x_coords > 80)
sclero_mask = (y_coords <= 140) & (x_coords <= 160)
olive_mask = (y_coords <= 140) & (x_coords > 160)

s2_patch2 = np.zeros((h, w, 3), dtype=np.uint8)
s2_patch2[:, :] = [165, 145, 110]
s2_patch2[sclero_mask] = [50, 105, 45]   # Sclerophyllous scrub
s2_patch2[olive_mask] = [115, 155, 70]   # Permanent crops / olive groves
s2_patch2[water_body_mask] = [20, 60, 180] # Coastal lagoon / water body

s1_patch2 = np.random.normal(0.30, 0.05, (h, w)).clip(0.12, 0.45).astype(np.float32)
s1_patch2[sclero_mask] = np.random.normal(0.48, 0.07, np.sum(sclero_mask)).clip(0.3, 0.7)
s1_patch2[olive_mask] = np.random.normal(0.42, 0.06, np.sum(olive_mask)).clip(0.25, 0.6)
s1_patch2[water_body_mask] = np.random.normal(0.03, 0.015, np.sum(water_body_mask)).clip(0.01, 0.07)

# --- PATCH 3: Industrial Port & Continuous Urban Fabric (Hamburg / Rotterdam / North Sea) ---
harbor_water = (x_coords < 120) & (y_coords > 60)
industrial_units = (x_coords >= 120) & (x_coords <= 220) & (y_coords >= 40) & (y_coords <= 180)
urban_fabric = (y_coords > 180) | ((x_coords > 220) & (y_coords <= 180))

s2_patch3 = np.zeros((h, w, 3), dtype=np.uint8)
s2_patch3[:, :] = [130, 130, 130]
s2_patch3[harbor_water] = [25, 75, 160]
s2_patch3[industrial_units] = [230, 230, 235]  # High albedo industrial metal roofs
s2_patch3[urban_fabric] = [190, 160, 150]      # Reddish tile / urban fabric

s1_patch3 = np.random.normal(0.35, 0.05, (h, w)).clip(0.2, 0.5).astype(np.float32)
s1_patch3[harbor_water] = np.random.normal(0.05, 0.02, np.sum(harbor_water)).clip(0.01, 0.09)
s1_patch3[industrial_units] = np.random.normal(0.92, 0.04, np.sum(industrial_units)).clip(0.82, 1.0)
s1_patch3[urban_fabric] = np.random.normal(0.78, 0.06, np.sum(urban_fabric)).clip(0.65, 0.95)

# Save GeoTIFFs
files_to_write = [
    ("BigEarthNet_S2_patch_01_austria.tif", s2_patch1, 'rgb'),
    ("BigEarthNet_S1_patch_01_austria.tif", (s1_patch1 * 255).astype(np.uint8), 'minisblack'),
    ("BigEarthNet_S2_patch_02_mediterranean.tif", s2_patch2, 'rgb'),
    ("BigEarthNet_S1_patch_02_mediterranean.tif", (s1_patch2 * 255).astype(np.uint8), 'minisblack'),
    ("BigEarthNet_S2_patch_03_port.tif", s2_patch3, 'rgb'),
    ("BigEarthNet_S1_patch_03_port.tif", (s1_patch3 * 255).astype(np.uint8), 'minisblack'),
]

import shutil
for fname, arr, photometric in files_to_write:
    p = output_dir / fname
    if photometric == 'rgb':
        tifffile.imwrite(str(p), arr, photometric='rgb', metadata={'axes': 'YXS', 'source': 'BigEarthNet.txt Sentinel-2'})
    else:
        tifffile.imwrite(str(p), arr, metadata={'axes': 'YX', 'source': 'BigEarthNet.txt Sentinel-1 SAR'})
    shutil.copyfile(str(p), str(uploads_dir / fname))

print("Created BigEarthNet co-registered Sentinel-1 & Sentinel-2 GeoTIFF patches successfully.")
