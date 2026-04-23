"""Repository root resolution for scripts under apps/ or scripts/."""
from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    """Return the project root (directory containing pyproject.toml)."""
    here = (start or Path(__file__).resolve()).parent
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").is_file():
            return p
    raise RuntimeError("pyproject.toml not found when resolving repo root")
