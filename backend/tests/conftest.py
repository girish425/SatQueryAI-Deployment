import os
import sys
from pathlib import Path

# Automatically ensure workspace root and backend are in sys.path
workspace_root = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent

for p in [str(workspace_root), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set working directory to workspace root so relative sample_data paths resolve seamlessly
os.chdir(str(workspace_root))
