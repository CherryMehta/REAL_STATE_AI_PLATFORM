from __future__ import annotations

from pathlib import Path

# Keep the current backend layout importable as the "app" package.
# This lets uvicorn app.main:app resolve app.api, app.core, etc.
_backend_root = Path(__file__).resolve().parent.parent
__path__.append(str(_backend_root))
