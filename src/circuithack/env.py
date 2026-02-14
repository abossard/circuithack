from __future__ import annotations

import os
from pathlib import Path


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_text(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        pairs[key] = _strip_quotes(value.strip())
    return pairs


def load_env_file(path: str | Path, override: bool = False) -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}
    parsed = parse_env_text(env_path.read_text(encoding="utf-8"))
    loaded: dict[str, str] = {}
    for key, value in parsed.items():
        if override or key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded


def find_env_file(start: str | Path | None = None, filename: str = ".env") -> Path | None:
    start_path = Path.cwd() if start is None else Path(start).resolve()
    for base in [start_path, *start_path.parents]:
        candidate = base / filename
        if candidate.exists():
            return candidate
    return None


def auto_load_env(start: str | Path | None = None, filename: str = ".env") -> dict[str, str]:
    env_file = find_env_file(start=start, filename=filename)
    if env_file is None:
        return {}
    return load_env_file(env_file, override=False)
