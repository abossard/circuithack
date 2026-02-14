from __future__ import annotations

import shutil
from pathlib import Path

from .util import CommandResult, run_cmd


def mpremote_executable() -> list[str]:
    if shutil.which("mpremote"):
        return ["mpremote"]
    return ["python3", "-m", "mpremote"]


def run_script(port: str, script_path: str | Path) -> CommandResult:
    script_path = str(Path(script_path))
    cmd = [*mpremote_executable(), "connect", port, "run", script_path]
    return run_cmd(cmd, timeout=300)


def copy_file(port: str, local_path: str | Path, remote_path: str) -> CommandResult:
    local_path = str(Path(local_path))
    cmd = [*mpremote_executable(), "connect", port, "cp", local_path, f":{remote_path}"]
    return run_cmd(cmd, timeout=300)

