from __future__ import annotations

import glob
from pathlib import Path

from .flash import write_flash_zero
from .util import CommandResult, run_cmd


CM_MICROPYTHON_REPO = "https://github.com/CircuitMess/micropython.git"


def clone_or_update_micropython(repo_dir: str | Path) -> CommandResult:
    repo_dir = Path(repo_dir)
    if (repo_dir / ".git").exists():
        return run_cmd(["git", "-C", str(repo_dir), "pull", "--ff-only"], timeout=300)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    return run_cmd(
        ["git", "clone", "--depth", "1", CM_MICROPYTHON_REPO, str(repo_dir)],
        timeout=600,
    )


def build_micropython_board(repo_dir: str | Path, board: str = "CM_Codee") -> CommandResult:
    repo_dir = Path(repo_dir)
    ports_esp32 = repo_dir / "ports" / "esp32"
    # Requires ESP-IDF configured in shell env.
    cmd = ["make", "-C", str(ports_esp32), f"BOARD={board}"]
    return run_cmd(cmd, timeout=3600)


def find_built_firmware(repo_dir: str | Path, board: str) -> Path | None:
    repo_dir = Path(repo_dir)
    candidates = glob.glob(str(repo_dir / "ports" / "esp32" / f"build-{board}" / "firmware.bin"))
    if not candidates:
        candidates = glob.glob(str(repo_dir / "ports" / "esp32" / "build*" / "firmware.bin"))
    return Path(candidates[0]) if candidates else None


def build_and_flash_micropython(
    port: str,
    repo_dir: str | Path,
    board: str = "CM_Codee",
    baud: int = 460800,
) -> dict:
    res_clone = clone_or_update_micropython(repo_dir)
    if not res_clone.ok:
        return {
            "ok": False,
            "stage": "clone_or_update",
            "stdout": res_clone.stdout,
            "stderr": res_clone.stderr,
        }

    res_build = build_micropython_board(repo_dir=repo_dir, board=board)
    if not res_build.ok:
        return {
            "ok": False,
            "stage": "build",
            "stdout": res_build.stdout,
            "stderr": res_build.stderr,
            "hint": "ESP-IDF environment is likely not configured in this shell.",
        }

    fw = find_built_firmware(repo_dir=repo_dir, board=board)
    if fw is None:
        return {
            "ok": False,
            "stage": "locate_firmware",
            "stdout": "",
            "stderr": f"Could not find built firmware for board {board}",
        }

    res_flash = write_flash_zero(port=port, firmware_bin=fw, baud=baud)
    return {
        "ok": res_flash.ok,
        "stage": "flash",
        "firmware_path": str(fw),
        "stdout": res_flash.stdout,
        "stderr": res_flash.stderr,
    }

