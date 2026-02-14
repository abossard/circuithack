from __future__ import annotations

import shutil
import time
from pathlib import Path

import serial

from .util import CommandResult, run_cmd


def mpremote_executable() -> list[str]:
    if shutil.which("mpremote"):
        return ["mpremote"]
    return ["python3", "-m", "mpremote"]


def run_script(port: str, script_path: str | Path) -> CommandResult:
    script_path = str(Path(script_path))
    cmd = [*mpremote_executable(), "connect", port, "run", script_path]
    return run_cmd(cmd, timeout=300)


def run_script_paste_mode(
    port: str,
    script_path: str | Path,
    baud: int = 115200,
    read_timeout: int = 3,
) -> CommandResult:
    script_path = Path(script_path)
    cmd = ["paste", port, str(script_path)]
    payload = script_path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    # Try mpremote fs cp first (works even when raw REPL is blocked)
    try:
        fs_cmd = [*mpremote_executable(), "connect", port, "fs", "cp", str(script_path), ":main.py"]
        res = run_cmd(fs_cmd, timeout=30)
        if res.ok:
            # Soft reset to run :main.py
            run_cmd([*mpremote_executable(), "connect", port, "soft-reset"], timeout=10)
            return CommandResult(cmd=fs_cmd, returncode=0, stdout=res.stdout, stderr=res.stderr)
    except Exception:
        pass  # fall back to paste mode

    # Paste mode fallback
    try:
        ser = serial.serial_for_url(port, baudrate=baud, timeout=1)
        try:
            ser.reset_input_buffer()
            ser.write(b"\x05")  # Ctrl-E paste mode
            for line in payload.split("\n"):
                # trim overly long lines to reduce echo wrapping in REPL
                chunks = [line[i : i + 120] for i in range(0, len(line), 120)] or [""]
                for chunk in chunks:
                    ser.write(chunk.encode("utf-8") + b"\n")
            ser.write(b"\x04")  # Ctrl-D to execute

            start = time.time()
            output = b""
            while time.time() - start < read_timeout:
                chunk = ser.read(400)
                if chunk:
                    output += chunk

            return CommandResult(
                cmd=cmd,
                returncode=0,
                stdout=output.decode("utf-8", errors="replace"),
                stderr="",
            )
        finally:
            ser.close()
    except Exception as exc:  # pragma: no cover - transport errors are environment-specific
        return CommandResult(
            cmd=cmd,
            returncode=1,
            stdout="",
            stderr=str(exc),
        )


def copy_file(port: str, local_path: str | Path, remote_path: str) -> CommandResult:
    local_path = str(Path(local_path))
    cmd = [*mpremote_executable(), "connect", port, "cp", local_path, f":{remote_path}"]
    return run_cmd(cmd, timeout=300)

