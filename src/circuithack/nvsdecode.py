from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import requests


NVS_TOOL_VERSION = "v5.3.1"
NVS_TOOL_FILES = ("nvs_tool.py", "nvs_parser.py", "nvs_check.py", "nvs_logger.py")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_tool_dir() -> Path:
    return _repo_root() / "third_party" / "esp-idf-nvs-tool"


def _tool_url(filename: str) -> str:
    return (
        "https://raw.githubusercontent.com/espressif/esp-idf/"
        f"{NVS_TOOL_VERSION}/components/nvs_flash/nvs_partition_tool/{filename}"
    )


def ensure_nvs_tool(tool_dir: str | Path | None = None) -> Path:
    directory = Path(tool_dir) if tool_dir else _default_tool_dir()
    directory.mkdir(parents=True, exist_ok=True)
    missing = [name for name in NVS_TOOL_FILES if not (directory / name).exists()]
    for name in missing:
        response = requests.get(_tool_url(name), timeout=30)
        response.raise_for_status()
        (directory / name).write_text(response.text)
    return directory / "nvs_tool.py"


def parse_minimal_nvs_output(text: str, namespace: str = "Codee") -> dict[str, bytes]:
    escaped_namespace = re.escape(namespace)
    pattern = re.compile(rf"^\s*{escaped_namespace}:(\w+)\[0\]\s*=\s*(b'.*')\s*$")
    out: dict[str, bytes] = {}
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        out[match.group(1)] = ast.literal_eval(match.group(2))
    return out


def decode_codee_nvs_entries(entries: dict[str, bytes]) -> dict:
    decoded: dict[str, dict] = {}

    settings = entries.get("Settings", b"")
    if len(settings) >= 3:
        decoded["settings"] = {
            "screen_brightness": settings[0],
            "sleep_time_index": settings[1],
            "sound_enabled": bool(settings[2]),
        }

    stats = entries.get("Stats", b"")
    if len(stats) >= 6:
        decoded["stats"] = {
            "happiness": stats[0],
            "oil_level": stats[1],
            "experience": int.from_bytes(stats[2:4], "little"),
            "hours_on_zero_stats": stats[4],
            "hatched": bool(stats[5]),
        }

    stats_time = entries.get("StatsTime", b"")
    if len(stats_time) >= 8:
        decoded["stats_time"] = {
            "unix_seconds": int.from_bytes(stats_time[:8], "little", signed=False),
        }

    return decoded


def decode_codee_nvs_backup(nvs_path: str | Path, tool_dir: str | Path | None = None) -> dict:
    path = Path(nvs_path)
    if not path.exists():
        return {"ok": False, "error": f"NVS backup file not found: {path}"}

    tool_path = ensure_nvs_tool(tool_dir)
    cmd = [
        sys.executable,
        str(tool_path),
        "-d",
        "minimal",
        "-f",
        "text",
        str(path),
    ]
    proc = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "nvs_path": str(path),
            "tool_path": str(tool_path),
            "cmd": cmd,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    entries = parse_minimal_nvs_output(proc.stdout)
    decoded = decode_codee_nvs_entries(entries)
    return {
        "ok": True,
        "nvs_path": str(path),
        "tool_path": str(tool_path),
        "keys": sorted(entries.keys()),
        "entries_raw_hex": {k: v.hex() for k, v in entries.items()},
        "decoded": decoded,
        "cmd": cmd,
        "stdout": proc.stdout,
    }
