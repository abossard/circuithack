from __future__ import annotations

from pathlib import Path

try:
    import ujson as json  # type: ignore[import-not-found]
except ImportError:  # CPython fallback
    import json  # type: ignore[no-redef]


class CodeeSave:
    """Small JSON save helper for MicroPython/CPython."""

    def __init__(self, path: str = "save_2048.json") -> None:
        self.path = Path(path)

    def load(self, default: dict | None = None) -> dict:
        if default is None:
            default = {}
        if not self.path.exists():
            return dict(default)
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return dict(default)

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data), encoding="utf-8")
        tmp_path.replace(self.path)
