from __future__ import annotations

from pathlib import Path

from .firmware import download_asset, latest_stock_asset
from .flash import write_flash_zero
from .nvsdecode import decode_codee_nvs_backup


FIRMWARE_SOURCE_OFFICIAL = "official"
FIRMWARE_SOURCE_LOCAL_BUILD = "local-build"
FIRMWARE_SOURCE_PATH = "path"
FIRMWARE_SOURCES = (
    FIRMWARE_SOURCE_OFFICIAL,
    FIRMWARE_SOURCE_LOCAL_BUILD,
    FIRMWARE_SOURCE_PATH,
)


def resolve_codee_firmware_path(
    source: str,
    firmware_path: str | None = None,
    official_out_dir: str = "downloads/codee-official",
    build_dir: str = "third_party/Codee-Firmware/build",
) -> tuple[Path, dict]:
    if source == FIRMWARE_SOURCE_OFFICIAL:
        asset = latest_stock_asset("codee")
        path = download_asset(asset, official_out_dir)
        return path, {"source": source, "asset": asset.to_dict()}

    if source == FIRMWARE_SOURCE_LOCAL_BUILD:
        path = Path(build_dir) / "Codee.bin"
        if not path.exists():
            raise RuntimeError(
                f"Local build firmware not found: {path}. Build it first in {build_dir}."
            )
        return path, {"source": source, "build_dir": build_dir}

    if source == FIRMWARE_SOURCE_PATH:
        if not firmware_path:
            raise ValueError("firmware_path is required when source='path'")
        path = Path(firmware_path)
        if not path.exists():
            raise RuntimeError(f"Firmware file not found: {path}")
        return path, {"source": source}

    raise ValueError(f"Invalid firmware source '{source}', expected one of {FIRMWARE_SOURCES}")


def flash_codee_firmware(
    port: str,
    source: str = FIRMWARE_SOURCE_OFFICIAL,
    firmware_path: str | None = None,
    official_out_dir: str = "downloads/codee-official",
    build_dir: str = "third_party/Codee-Firmware/build",
    baud: int = 460800,
) -> dict:
    fw_path, source_info = resolve_codee_firmware_path(
        source=source,
        firmware_path=firmware_path,
        official_out_dir=official_out_dir,
        build_dir=build_dir,
    )
    res = write_flash_zero(port=port, firmware_bin=fw_path, baud=baud)
    return {
        "ok": res.ok,
        "port": port,
        "firmware_path": str(fw_path),
        "source": source_info.get("source"),
        "source_info": source_info,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


def decode_codee_savegame(
    nvs_path: str,
    tool_dir: str | None = None,
) -> dict:
    return decode_codee_nvs_backup(nvs_path=nvs_path, tool_dir=tool_dir)
