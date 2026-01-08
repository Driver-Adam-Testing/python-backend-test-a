"""Root conftest for all content_services tests.

Adds src directory to Python path so that imports work correctly.
"""
import sys
from pathlib import Path

# Add src directory to Python path for imports
_src_path = Path(__file__).resolve().parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

