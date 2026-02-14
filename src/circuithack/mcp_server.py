from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .backup import backup_full_flash, backup_state_partitions, restore_full_flash_backup
from .codee import (
    FIRMWARE_SOURCES,
    decode_codee_savegame,
    flash_codee_firmware as flash_codee_firmware_flow,
)
from .device import (
    detect_codee_candidates,
    list_serial_devices,
    macos_usb_summary,
    resolve_codee_port,
    serial_node_snapshot,
)
from .firmware import download_asset, latest_stock_asset
from .flash import enter_programmer_mode, write_flash_zero
from .gamesync import sync_game_sources
from .micropython import build_and_flash_micropython
from .runner import run_script
from .util import format_cmd

mcp = FastMCP("circuithack-codee")


@mcp.tool()
def scan_codee() -> dict:
    devices = [x.to_dict() for x in list_serial_devices(only_likely_usb=True)]
    candidates = [x.to_dict() for x in detect_codee_candidates()]
    return {
        "devices": devices,
        "codee_candidates": candidates,
        "serial_nodes": serial_node_snapshot(),
        "macos_usb_summary": macos_usb_summary(),
    }


@mcp.tool()
def download_codee_stock_firmware(out_dir: str = "downloads/codee") -> dict:
    asset = latest_stock_asset("codee")
    path = download_asset(asset, out_dir)
    return {
        "asset": asset.to_dict(),
        "download_path": str(path),
    }


@mcp.tool()
def enter_codee_programmer_mode(port: str | None = None, baud: int = 460800) -> dict:
    resolved = resolve_codee_port(port)
    res = enter_programmer_mode(resolved, baud=baud)
    return {
        "ok": res.ok,
        "port": resolved,
        "cmd": format_cmd(res.cmd),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@mcp.tool()
def restore_codee_stock_firmware(
    port: str | None = None,
    firmware_path: str | None = None,
    baud: int = 460800,
) -> dict:
    resolved = resolve_codee_port(port)
    if firmware_path:
        fw = Path(firmware_path)
    else:
        asset = latest_stock_asset("codee")
        fw = download_asset(asset, "downloads/codee")
    res = write_flash_zero(port=resolved, firmware_bin=fw, baud=baud)
    return {
        "ok": res.ok,
        "port": resolved,
        "firmware_path": str(fw),
        "cmd": format_cmd(res.cmd),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@mcp.tool()
def install_codee_micropython_binary(
    port: str | None = None,
    micropython_bin_path: str = "",
    baud: int = 460800,
) -> dict:
    if not micropython_bin_path:
        raise ValueError("micropython_bin_path is required")
    resolved = resolve_codee_port(port)
    res = write_flash_zero(port=resolved, firmware_bin=micropython_bin_path, baud=baud)
    return {
        "ok": res.ok,
        "port": resolved,
        "firmware_path": micropython_bin_path,
        "cmd": format_cmd(res.cmd),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@mcp.tool()
def build_and_install_codee_micropython(
    port: str | None = None,
    repo_dir: str = "third_party/circuitmess-micropython",
    board: str = "CM_Codee",
    baud: int = 460800,
) -> dict:
    resolved = resolve_codee_port(port)
    return build_and_flash_micropython(
        port=resolved,
        repo_dir=repo_dir,
        board=board,
        baud=baud,
    )


@mcp.tool()
def run_codee_script(port: str | None = None, script_path: str = "") -> dict:
    if not script_path:
        raise ValueError("script_path is required")
    resolved = resolve_codee_port(port)
    res = run_script(port=resolved, script_path=script_path)
    return {
        "ok": res.ok,
        "port": resolved,
        "script_path": script_path,
        "cmd": format_cmd(res.cmd),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@mcp.tool()
def backup_codee_full_flash(
    port: str | None = None,
    out_dir: str = "backups",
    flash_size: int = 0x400000,
    baud: int = 921600,
) -> dict:
    resolved = resolve_codee_port(port)
    return backup_full_flash(
        port=resolved,
        out_dir=out_dir,
        flash_size=flash_size,
        baud=baud,
    )


@mcp.tool()
def backup_codee_state(
    port: str | None = None,
    out_dir: str = "backups",
    baud: int = 921600,
) -> dict:
    resolved = resolve_codee_port(port)
    return backup_state_partitions(
        port=resolved,
        out_dir=out_dir,
        baud=baud,
    )


@mcp.tool()
def restore_codee_full_flash_backup(
    backup_path: str,
    port: str | None = None,
    baud: int = 921600,
) -> dict:
    resolved = resolve_codee_port(port)
    return restore_full_flash_backup(
        port=resolved,
        backup_path=backup_path,
        baud=baud,
    )


@mcp.tool()
def flash_codee_firmware(
    port: str | None = None,
    source: str = "official",
    firmware_path: str | None = None,
    official_out_dir: str = "downloads/codee-official",
    build_dir: str = "third_party/Codee-Firmware/build",
    baud: int = 460800,
) -> dict:
    if source not in FIRMWARE_SOURCES:
        raise ValueError(f"Invalid source '{source}', expected one of {FIRMWARE_SOURCES}")
    resolved = resolve_codee_port(port)
    return flash_codee_firmware_flow(
        port=resolved,
        source=source,
        firmware_path=firmware_path,
        official_out_dir=official_out_dir,
        build_dir=build_dir,
        baud=baud,
    )


@mcp.tool()
def decode_codee_nvs_backup(
    nvs_path: str,
    tool_dir: str | None = None,
) -> dict:
    return decode_codee_savegame(
        nvs_path=nvs_path,
        tool_dir=tool_dir,
    )


@mcp.tool()
def sync_codee_game_sources(
    dest_root: str = "third_party_games",
    manifest_path: str | None = None,
    source: list[str] | None = None,
) -> dict:
    return sync_game_sources(
        dest_root=dest_root,
        manifest_path=manifest_path,
        selected_sources=source,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
