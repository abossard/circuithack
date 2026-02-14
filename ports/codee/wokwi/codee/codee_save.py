from __future__ import annotations

import os

try:
    from pathlib import Path
except ImportError:  # MicroPython fallback
    Path = None  # type: ignore[assignment]

try:
    import ujson as json  # type: ignore[import-not-found]
except ImportError:  # CPython fallback
    import json  # type: ignore[no-redef]


class CodeeSave:
    """Small JSON save helper for MicroPython/CPython."""

    def __init__(self, path: str = "save_2048.json") -> None:
        self.path = Path(path) if Path is not None else path

    def load(self, default: dict | None = None) -> dict:
        if default is None:
            default = {}
        try:
            if Path is not None:
                if not self.path.exists():
                    return dict(default)
                return json.loads(self.path.read_text(encoding="utf-8"))

            with open(self.path, "r") as handle:
                return json.loads(handle.read())
        except Exception:
            return dict(default)

    def save(self, data: dict) -> None:
        if Path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp_path.write_text(json.dumps(data), encoding="utf-8")
            tmp_path.replace(self.path)
            return

        target = self.path
        parent = ""
        if "/" in target:
            parent = target.rsplit("/", 1)[0]
        if parent:
            try:
                os.makedirs(parent)
            except OSError:
                pass
        tmp_path = target + ".tmp"
        with open(tmp_path, "w") as handle:
            handle.write(json.dumps(data))
        try:
            os.rename(tmp_path, target)
        except OSError:
            try:
                os.remove(target)
            except OSError:
                pass
            os.rename(tmp_path, target)
