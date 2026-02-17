from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .backup import backup_full_flash, backup_state_partitions, restore_full_flash_backup
from .codee import (
    FIRMWARE_SOURCES,
    decode_codee_savegame,
    flash_codee_firmware as flash_codee_firmware_flow,
)
from .env import auto_load_env
from .device import (
    detect_codee_candidates,
    list_serial_devices,
    macos_usb_summary,
    resolve_codee_port,
    serial_node_snapshot,
)
from .firmware import download_asset, latest_stock_asset
from .flash import enter_programmer_mode, write_flash_zero
from .gamewatch import (
    codee_gamewatch_adaptation_report,
    download_gamewatch_assets as download_gamewatch_assets_flow,
    sync_gamewatch_source,
)
from .gamesync import sync_game_sources
from .micropython import build_and_flash_micropython
from .runner import run_script, run_script_paste_mode
from .util import format_cmd

mcp = FastMCP("circuithack-codee")


@mcp.tool()
def scan_codee() -> dict:
    """List USB serial devices and highlight likely Codee candidates (macOS/Linux)."""
    devices = [x.to_dict() for x in list_serial_devices(only_likely_usb=True)]
    candidates = [x.to_dict() for x in detect_codee_candidates()]
    return {
        "devices": devices,
        "codee_candidates": candidates,
        "serial_nodes": serial_node_snapshot(),
        "macos_usb_summary": macos_usb_summary(),
    }


@mcp.tool(description="Download the latest stock Codee firmware asset")
def download_codee_stock_firmware(out_dir: str = "downloads/codee") -> dict:
    """Download the latest stock Codee firmware release asset (returns path + metadata)."""
    asset = latest_stock_asset("codee")
    path = download_asset(asset, out_dir)
    return {
        "asset": asset.to_dict(),
        "download_path": str(path),
    }


@mcp.tool(description="Enter ESP32-S3 programmer/bootloader mode")
def enter_codee_programmer_mode(port: str | None = None, baud: int = 460800) -> dict:
    """Toggle ESP32-S3 into programmer/bootloader mode using esptool handshakes."""
    resolved = resolve_codee_port(port)
    res = enter_programmer_mode(resolved, baud=baud)
    return {
        "ok": res.ok,
        "port": resolved,
        "cmd": format_cmd(res.cmd),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@mcp.tool(description="Flash official stock Codee firmware")
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


@mcp.tool(description="Flash a provided MicroPython .bin to Codee")
def install_codee_micropython_binary(
    port: str | None = None,
    micropython_bin_path: str = "",
    baud: int = 460800,
) -> dict:
    """Flash a provided MicroPython .bin onto Codee (write_flash @0x0)."""
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


@mcp.tool(description="Build CircuitMess MicroPython (CM_Codee) and flash")
def build_and_install_codee_micropython(
    port: str | None = None,
    repo_dir: str = "third_party/circuitmess-micropython",
    board: str = "CM_Codee",
    baud: int = 460800,
) -> dict:
    """Build CircuitMess MicroPython (board=CM_Codee) and flash it."""
    resolved = resolve_codee_port(port)
    return build_and_flash_micropython(
        port=resolved,
        repo_dir=repo_dir,
        board=board,
        baud=baud,
    )


@mcp.tool(description="Run a local MicroPython script on a real Codee via mpremote")
def run_codee_script(port: str | None = None, script_path: str = "") -> dict:
    """Run a local MicroPython script on Codee via mpremote (raw REPL)."""
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


@mcp.tool(description="Run a MicroPython script on Wokwi via RFC2217 paste-mode")
def run_wokwi_script(
    script_path: str,
    port: str = "rfc2217://localhost:4000",
) -> dict:
    """Run a MicroPython script on the Wokwi sim using paste-mode over RFC2217."""
    if not script_path:
        raise ValueError("script_path is required")
    res = run_script_paste_mode(port=port, script_path=script_path)
    return {
        "ok": res.ok,
        "port": port,
        "script_path": script_path,
        "cmd": format_cmd(res.cmd),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


@mcp.tool(description="Dump full Codee flash to file (esptool)")
def backup_codee_full_flash(
    port: str | None = None,
    out_dir: str = "backups",
    flash_size: int = 0x400000,
    baud: int = 921600,
) -> dict:
    """Dump full flash to file using esptool (default 4MB)."""
    resolved = resolve_codee_port(port)
    return backup_full_flash(
        port=resolved,
        out_dir=out_dir,
        flash_size=flash_size,
        baud=baud,
    )


@mcp.tool(description="Backup Codee state partitions (SPIFFS/NVS)")
def backup_codee_state(
    port: str | None = None,
    out_dir: str = "backups",
    baud: int = 921600,
) -> dict:
    """Backup state partitions (SPIFFS/NVS) to files."""
    resolved = resolve_codee_port(port)
    return backup_state_partitions(
        port=resolved,
        out_dir=out_dir,
        baud=baud,
    )


@mcp.tool(description="Restore a previously captured full flash backup")
def restore_codee_full_flash_backup(
    backup_path: str,
    port: str | None = None,
    baud: int = 921600,
) -> dict:
    """Restore a previously captured full flash backup image."""
    resolved = resolve_codee_port(port)
    return restore_full_flash_backup(
        port=resolved,
        backup_path=backup_path,
        baud=baud,
    )


@mcp.tool(description="Flash Codee firmware from official or local build")
def flash_codee_firmware(
    port: str | None = None,
    source: str = "official",
    firmware_path: str | None = None,
    official_out_dir: str = "downloads/codee-official",
    build_dir: str = "third_party/Codee-Firmware/build",
    baud: int = 460800,
) -> dict:
    """Flash Codee firmware from official release or local build directory."""
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


@mcp.tool(description="Decode a Codee NVS backup/savegame")
def decode_codee_nvs_backup(
    nvs_path: str,
    tool_dir: str | None = None,
) -> dict:
    """Decode an NVS backup (savegame) into human-readable fields."""
    return decode_codee_savegame(
        nvs_path=nvs_path,
        tool_dir=tool_dir,
    )


@mcp.tool(description="Sync curated game sources into third_party_games")
def sync_codee_game_sources(
    dest_root: str = "third_party_games",
    manifest_path: str | None = None,
    source: list[str] | None = None,
) -> dict:
    """Sync curated game sources into third_party_games (writes sources.lock.json)."""
    return sync_game_sources(
        dest_root=dest_root,
        manifest_path=manifest_path,
        selected_sources=source,
    )


@mcp.tool(description="Clone/update tobozo/M5Tab5-Game-and-Watch source repo")
def sync_codee_gamewatch_source(
    repo_dir: str = "third_party/M5Tab5-Game-and-Watch",
) -> dict:
    """Clone or fast-forward update the upstream M5Tab5 Game&Watch project."""
    return sync_gamewatch_source(repo_dir=repo_dir)


@mcp.tool(description="Download Game&Watch firmware and ROM assets for Codee adaptation")
def download_codee_gamewatch_assets(
    out_dir: str = "downloads/gamewatch",
    repo_dir: str = "third_party/M5Tab5-Game-and-Watch",
    firmware_url: str | None = None,
    rom_url: list[str] | None = None,
    rom_base_url: str | None = None,
    rom_id: list[str] | None = None,
    rom_extension: str = ".gw.gz",
    artwork_url: list[str] | None = None,
    artwork_base_url: str | None = None,
    artwork_extension: str = ".jpg.gz",
    require_artworks: bool = True,
    prepare_littlefs_bundle: bool = True,
    littlefs_bundle_dir: str | None = None,
    littlefs_max_bytes: int | None = None,
    sync_source: bool = True,
    include_release_assets: bool = True,
) -> dict:
    """
    Download firmware/ROM artifacts:
    - explicit URLs (firmware_url/rom_url), or
    - derived ROM URLs from rom_base_url + rom_id, or
    - fallback to any matching GitHub release assets.
    """
    return download_gamewatch_assets_flow(
        out_dir=out_dir,
        repo_dir=repo_dir,
        firmware_url=firmware_url,
        rom_urls=rom_url,
        rom_base_url=rom_base_url,
        rom_ids=rom_id,
        rom_extension=rom_extension,
        artwork_urls=artwork_url,
        artwork_base_url=artwork_base_url,
        artwork_extension=artwork_extension,
        require_artworks=require_artworks,
        prepare_littlefs_bundle=prepare_littlefs_bundle,
        littlefs_bundle_dir=littlefs_bundle_dir,
        littlefs_max_bytes=littlefs_max_bytes,
        sync_source=sync_source,
        include_release_assets=include_release_assets,
    )


@mcp.tool(description="Show a practical adaptation checklist from M5Tab5 Game&Watch to Codee")
def codee_gamewatch_adaptation_plan() -> dict:
    """Return an architecture/configuration checklist to adapt the emulator for Codee."""
    return codee_gamewatch_adaptation_report()


def main() -> None:
    auto_load_env()
    mcp.run()


if __name__ == "__main__":
    main()
