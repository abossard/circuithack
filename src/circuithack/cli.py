from __future__ import annotations

import argparse
import json

from .backup import backup_full_flash, backup_state_partitions, restore_full_flash_backup
from .codee import FIRMWARE_SOURCES, decode_codee_savegame, flash_codee_firmware
from .device import detect_codee_candidates, list_serial_devices, resolve_codee_port
from .firmware import download_asset, latest_stock_asset
from .flash import enter_programmer_mode, write_flash_zero
from .gamesync import sync_game_sources
from .micropython import build_and_flash_micropython
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

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        _print({"ok": False, "error": str(exc), "command": args.cmd})
        raise SystemExit(1)


if __name__ == "__main__":
    main()
