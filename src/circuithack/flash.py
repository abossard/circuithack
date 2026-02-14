from __future__ import annotations

import shutil
from pathlib import Path

from .util import CommandResult, run_cmd


def esptool_executable() -> list[str]:
    if shutil.which("esptool"):
        return ["esptool"]
    return ["python3", "-m", "esptool"]


def build_esptool_base(
    port: str,
    baud: int = 460800,
    chip: str = "esp32s3",
    before: str = "default-reset",
    after: str = "hard-reset",
) -> list[str]:
    return [
        *esptool_executable(),
        "--chip",
        chip,
        "--port",
        port,
        "--baud",
        str(baud),
        "--before",
        before,
        "--after",
        after,
    ]


def enter_programmer_mode(port: str, baud: int = 460800) -> CommandResult:
    # chip_id requires successful ROM bootloader handshake.
    cmd = build_esptool_base(
        port=port,
        baud=baud,
        chip="esp32s3",
        before="default-reset",
        after="no-reset",
    ) + ["chip-id"]
    return run_cmd(cmd)


def erase_flash(port: str, baud: int = 460800) -> CommandResult:
    cmd = build_esptool_base(port=port, baud=baud) + ["erase_flash"]
    return run_cmd(cmd, timeout=600)


def write_flash_zero(port: str, firmware_bin: str | Path, baud: int = 460800) -> CommandResult:
    fw = str(Path(firmware_bin))
    cmd = build_esptool_base(port=port, baud=baud) + ["write_flash", "0x0", fw]
    return run_cmd(cmd, timeout=900)


def read_flash(
    port: str,
    offset: int,
    size: int,
    out_path: str | Path,
    baud: int = 921600,
    timeout: int = 1800,
) -> CommandResult:
    path = str(Path(out_path))
    cmd = build_esptool_base(port=port, baud=baud) + [
        "read-flash",
        hex(offset),
        hex(size),
        path,
    ]
    return run_cmd(cmd, timeout=timeout)


def write_flash_at(
    port: str,
    offset: int,
    in_path: str | Path,
    baud: int = 921600,
    timeout: int = 1800,
) -> CommandResult:
    path = str(Path(in_path))
    cmd = build_esptool_base(port=port, baud=baud) + [
        "write-flash",
        hex(offset),
        path,
    ]
    return run_cmd(cmd, timeout=timeout)
