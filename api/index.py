import sys
from pathlib import Path


project_dir = Path(__file__).resolve().parents[1] / "preorder_app"
sys.path.insert(0, str(project_dir))

from wsgi import app


__all__ = ["app"]