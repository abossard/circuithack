from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backup import backup_full_flash, backup_state_partitions, restore_full_flash_backup
from .codee import FIRMWARE_SOURCES, decode_codee_savegame, flash_codee_firmware
from .device import detect_codee_candidates, list_serial_devices, resolve_codee_port
from .env import auto_load_env
from .firmware import download_asset, latest_stock_asset
from .flash import enter_programmer_mode, write_flash_zero
from .gamewatch import (
    codee_gamewatch_adaptation_report,
    download_gamewatch_assets,
    sync_gamewatch_source,
)
from .gamesync import sync_game_sources
from .micropython import build_and_flash_micropython
from .rompatch import apply_ips_patch_file
from .runner import run_script


def _print(obj: dict) -> None:
    print(json.dumps(obj, indent=2))


def cmd_scan(_: argparse.Namespace) -> None:
    _print(
        {
            "devices": [x.to_dict() for x in list_serial_devices(only_likely_usb=True)],
            "codee_candidates": [x.to_dict() for x in detect_codee_candidates()],
        }
    )


def cmd_download(args: argparse.Namespace) -> None:
    asset = latest_stock_asset("codee")
    path = download_asset(asset, args.out_dir)
    _print({"asset": asset.to_dict(), "download_path": str(path)})


def cmd_programmer(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    res = enter_programmer_mode(port=port, baud=args.baud)
    _print({"ok": res.ok, "port": port, "stdout": res.stdout, "stderr": res.stderr})


def cmd_restore(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    firmware_path = args.firmware_path
    if not firmware_path:
        asset = latest_stock_asset("codee")
        firmware_path = str(download_asset(asset, "downloads/codee"))
    res = write_flash_zero(port=port, firmware_bin=firmware_path, baud=args.baud)
    _print(
        {
            "ok": res.ok,
            "port": port,
            "firmware_path": firmware_path,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    )


def cmd_install_binary(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    res = write_flash_zero(port=port, firmware_bin=args.bin_path, baud=args.baud)
    _print(
        {
            "ok": res.ok,
            "port": port,
            "firmware_path": args.bin_path,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    )


def cmd_install_source(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    result = build_and_flash_micropython(
        port=port,
        repo_dir=args.repo_dir,
        board=args.board,
        baud=args.baud,
    )
    _print(result)


def cmd_run(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    res = run_script(port=port, script_path=args.script_path)
    _print({"ok": res.ok, "port": port, "stdout": res.stdout, "stderr": res.stderr})


def cmd_backup_full(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    _print(
        backup_full_flash(
            port=port,
            out_dir=args.out_dir,
            flash_size=args.flash_size,
            baud=args.baud,
        )
    )


def cmd_backup_state(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    _print(
        backup_state_partitions(
            port=port,
            out_dir=args.out_dir,
            baud=args.baud,
        )
    )


def cmd_restore_full_backup(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    _print(
        restore_full_flash_backup(
            port=port,
            backup_path=args.backup_path,
            baud=args.baud,
        )
    )


def cmd_flash_firmware(args: argparse.Namespace) -> None:
    port = resolve_codee_port(args.port)
    _print(
        flash_codee_firmware(
            port=port,
            source=args.source,
            firmware_path=args.firmware_path,
            official_out_dir=args.official_out_dir,
            build_dir=args.build_dir,
            baud=args.baud,
        )
    )


def cmd_decode_nvs(args: argparse.Namespace) -> None:
    _print(
        decode_codee_savegame(
            nvs_path=args.nvs_path,
            tool_dir=args.tool_dir,
        )
    )


def cmd_sync_games(args: argparse.Namespace) -> None:
    _print(
        sync_game_sources(
            dest_root=args.dest_root,
            manifest_path=args.manifest_path,
            selected_sources=args.source,
        )
    )


def cmd_sync_gamewatch_source(args: argparse.Namespace) -> None:
    _print(
        sync_gamewatch_source(
            repo_dir=args.repo_dir,
        )
    )


def cmd_download_gamewatch(args: argparse.Namespace) -> None:
    _print(
        download_gamewatch_assets(
            out_dir=args.out_dir,
            repo_dir=args.repo_dir,
            firmware_url=args.firmware_url,
            rom_urls=args.rom_url,
            rom_base_url=args.rom_base_url,
            rom_ids=args.rom_id,
            rom_extension=args.rom_extension,
            artwork_urls=args.artwork_url,
            artwork_base_url=args.artwork_base_url,
            artwork_extension=args.artwork_extension,
            require_artworks=not args.allow_missing_artworks,
            prepare_littlefs_bundle=not args.skip_littlefs_bundle,
            littlefs_bundle_dir=args.littlefs_bundle_dir,
            littlefs_max_bytes=args.littlefs_max_bytes,
            sync_source=not args.skip_source_sync,
            include_release_assets=not args.skip_release_assets,
        )
    )


def cmd_codee_gamewatch_plan(_: argparse.Namespace) -> None:
    _print(codee_gamewatch_adaptation_report())


def cmd_apply_ips(args: argparse.Namespace) -> None:
    if args.in_place and args.out_path:
        raise ValueError("Use either --in-place or --out-path, not both")
    if args.in_place and not args.force:
        raise ValueError("--in-place requires --force")

    rom_path = Path(args.rom_path)
    if args.in_place:
        output_path = rom_path
    elif args.out_path:
        output_path = Path(args.out_path)
    else:
        output_path = rom_path.with_name(f"{rom_path.stem}.patched{rom_path.suffix}")

    _print(
        apply_ips_patch_file(
            rom_path=rom_path,
            patch_path=args.patch_path,
            output_path=output_path,
            overwrite=args.force,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="circuithack-cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="Scan serial ports and detect Codee candidates.")
    s.set_defaults(func=cmd_scan)

    s = sub.add_parser("download-stock", help="Download latest official Codee stock firmware.")
    s.add_argument("--out-dir", default="downloads/codee")
    s.set_defaults(func=cmd_download)

    s = sub.add_parser("enter-programmer", help="Reset into ESP32S3 bootloader/programmer mode.")
    s.add_argument("--port")
    s.add_argument("--baud", type=int, default=460800)
    s.set_defaults(func=cmd_programmer)

    s = sub.add_parser("restore-stock", help="Flash stock Codee firmware at 0x0.")
    s.add_argument("--port")
    s.add_argument("--firmware-path")
    s.add_argument("--baud", type=int, default=460800)
    s.set_defaults(func=cmd_restore)

    s = sub.add_parser("install-mpy-bin", help="Flash a MicroPython .bin at 0x0.")
    s.add_argument("--port")
    s.add_argument("--bin-path", required=True)
    s.add_argument("--baud", type=int, default=460800)
    s.set_defaults(func=cmd_install_binary)

    s = sub.add_parser("install-mpy-source", help="Build CM_Codee MicroPython from CircuitMess fork and flash.")
    s.add_argument("--port")
    s.add_argument("--repo-dir", default="third_party/circuitmess-micropython")
    s.add_argument("--board", default="CM_Codee")
    s.add_argument("--baud", type=int, default=460800)
    s.set_defaults(func=cmd_install_source)

    s = sub.add_parser("run-script", help="Run a local Python script on device using mpremote.")
    s.add_argument("--port")
    s.add_argument("--script-path", required=True)
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("backup-full", help="Backup full flash (includes firmware and all partitions).")
    s.add_argument("--port")
    s.add_argument("--out-dir", default="backups")
    s.add_argument("--flash-size", type=lambda x: int(x, 0), default=0x400000)
    s.add_argument("--baud", type=int, default=921600)
    s.set_defaults(func=cmd_backup_full)

    s = sub.add_parser("backup-state", help="Backup nvs + storage + factory using live partition table.")
    s.add_argument("--port")
    s.add_argument("--out-dir", default="backups")
    s.add_argument("--baud", type=int, default=921600)
    s.set_defaults(func=cmd_backup_state)

    s = sub.add_parser("restore-full-backup", help="Restore a full-flash backup at offset 0x0.")
    s.add_argument("--port")
    s.add_argument("--backup-path", required=True)
    s.add_argument("--baud", type=int, default=921600)
    s.set_defaults(func=cmd_restore_full_backup)

    s = sub.add_parser(
        "flash-firmware",
        help="Flash Codee firmware from official release, local build, or explicit path.",
    )
    s.add_argument("--port")
    s.add_argument("--source", choices=FIRMWARE_SOURCES, default="official")
    s.add_argument("--firmware-path")
    s.add_argument("--official-out-dir", default="downloads/codee-official")
    s.add_argument("--build-dir", default="third_party/Codee-Firmware/build")
    s.add_argument("--baud", type=int, default=460800)
    s.set_defaults(func=cmd_flash_firmware)

    s = sub.add_parser(
        "decode-nvs",
        help="Decode Codee save-state fields from an NVS backup binary.",
    )
    s.add_argument("--nvs-path", required=True)
    s.add_argument("--tool-dir")
    s.set_defaults(func=cmd_decode_nvs)

    s = sub.add_parser(
        "sync-games",
        help="Clone/update upstream MicroPython game repos into third_party_games and write lock manifest.",
    )
    s.add_argument("--dest-root", default="third_party_games")
    s.add_argument("--manifest-path")
    s.add_argument(
        "--source",
        action="append",
        help="Source id or owner/repo. Repeat to sync only selected sources.",
    )
    s.set_defaults(func=cmd_sync_games)

    s = sub.add_parser(
        "sync-gamewatch-source",
        help="Clone/update tobozo/M5Tab5-Game-and-Watch source in local third_party.",
    )
    s.add_argument("--repo-dir", default="third_party/M5Tab5-Game-and-Watch")
    s.set_defaults(func=cmd_sync_gamewatch_source)

    s = sub.add_parser(
        "download-gamewatch-assets",
        help="Download Game&Watch firmware/ROM assets for Codee adaptation.",
    )
    s.add_argument("--out-dir", default="downloads/gamewatch")
    s.add_argument("--repo-dir", default="third_party/M5Tab5-Game-and-Watch")
    s.add_argument("--firmware-url")
    s.add_argument(
        "--rom-url",
        action="append",
        help="Explicit ROM URL. Repeat for multiple files.",
    )
    s.add_argument(
        "--rom-base-url",
        help="Base URL used to build ROM URLs as <base>/<rom-id><rom-extension>.",
    )
    s.add_argument(
        "--rom-id",
        action="append",
        help="ROM id (e.g. gnw_pchute). Used with --rom-base-url; defaults to full set.",
    )
    s.add_argument("--rom-extension", default=".gw.gz")
    s.add_argument(
        "--artwork-url",
        action="append",
        help="Explicit artwork URL. Repeat for multiple files.",
    )
    s.add_argument(
        "--artwork-base-url",
        help="Base URL used to build artwork URLs as <base>/<rom-id><artwork-extension>.",
    )
    s.add_argument("--artwork-extension", default=".jpg.gz")
    s.add_argument(
        "--allow-missing-artworks",
        action="store_true",
        help="Allow ROM-only download. Disabled by default because emulator expects matching artworks.",
    )
    s.add_argument(
        "--skip-littlefs-bundle",
        action="store_true",
        help="Skip LittleFS root bundle creation.",
    )
    s.add_argument(
        "--littlefs-bundle-dir",
        help="Output directory for LittleFS-ready root files (defaults to <out-dir>/littlefs).",
    )
    s.add_argument(
        "--littlefs-max-bytes",
        type=int,
        help="Optional max allowed total bytes for LittleFS bundle.",
    )
    s.add_argument("--skip-source-sync", action="store_true")
    s.add_argument("--skip-release-assets", action="store_true")
    s.set_defaults(func=cmd_download_gamewatch)

    s = sub.add_parser(
        "codee-gamewatch-plan",
        help="Show adaptation checklist from M5Tab5 Game&Watch to Codee.",
    )
    s.set_defaults(func=cmd_codee_gamewatch_plan)

    s = sub.add_parser("apply-ips", help="Apply an IPS patch to a ROM file.")
    s.add_argument("--rom-path", required=True, help="Input ROM path.")
    s.add_argument("--patch-path", required=True, help="IPS patch path.")
    s.add_argument("--out-path", help="Output ROM path (default: <rom>.patched<suffix>).")
    s.add_argument("--in-place", action="store_true", help="Write output over the input ROM.")
    s.add_argument("--force", action="store_true", help="Overwrite existing output path.")
    s.set_defaults(func=cmd_apply_ips)

    return p


def main() -> None:
    auto_load_env()
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        _print({"ok": False, "error": str(exc), "command": args.cmd})
        raise SystemExit(1)


if __name__ == "__main__":
    main()
