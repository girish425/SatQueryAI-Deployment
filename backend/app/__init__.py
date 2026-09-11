"""SatQuery AI Backend Application Package."""
import sys
from pathlib import Path

# Ensure workspace root and backend directory are always present in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
_workspace_dir = _backend_dir.parent
for _p in [str(_workspace_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

__version__ = "1.0.0"

