from pathlib import Path

import pytest

from circuithack.codee import (
    FIRMWARE_SOURCE_LOCAL_BUILD,
    FIRMWARE_SOURCE_OFFICIAL,
    FIRMWARE_SOURCE_PATH,
    flash_codee_firmware,
    resolve_codee_firmware_path,
)
from circuithack.firmware import FirmwareAsset
from circuithack.util import CommandResult


def test_resolve_codee_firmware_path_local_build(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)
    codee_bin = build_dir / "Codee.bin"
    codee_bin.write_bytes(b"bin")

    path, source_info = resolve_codee_firmware_path(
        source=FIRMWARE_SOURCE_LOCAL_BUILD,
        build_dir=str(build_dir),
    )
    assert path == codee_bin
    assert source_info["source"] == FIRMWARE_SOURCE_LOCAL_BUILD


def test_resolve_codee_firmware_path_path_source(tmp_path: Path) -> None:
    fw = tmp_path / "firmware.bin"
    fw.write_bytes(b"bin")
    path, source_info = resolve_codee_firmware_path(
        source=FIRMWARE_SOURCE_PATH,
        firmware_path=str(fw),
    )
    assert path == fw
    assert source_info["source"] == FIRMWARE_SOURCE_PATH


def test_resolve_codee_firmware_path_official_download(monkeypatch, tmp_path: Path) -> None:
    out = tmp_path / "downloads"
    expected = out / "Codee.bin"

    monkeypatch.setattr(
        "circuithack.codee.latest_stock_asset",
        lambda _: FirmwareAsset(
            device="codee",
            tag_name="v2.0.1",
            published_at="2025-09-30T10:56:08Z",
            name="Codee.bin",
            browser_download_url="https://example.invalid/Codee.bin",
        ),
    )
    monkeypatch.setattr(
        "circuithack.codee.download_asset",
        lambda *_args, **_kwargs: expected,
    )

    path, source_info = resolve_codee_firmware_path(
        source=FIRMWARE_SOURCE_OFFICIAL,
        official_out_dir=str(out),
    )
    assert path == expected
    assert source_info["source"] == FIRMWARE_SOURCE_OFFICIAL
    assert source_info["asset"]["name"] == "Codee.bin"


def test_flash_codee_firmware_end_to_end_local_build(monkeypatch, tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)
    fw = build_dir / "Codee.bin"
    fw.write_bytes(b"bin")

    captured: dict = {}

    def fake_write_flash_zero(port: str, firmware_bin: str | Path, baud: int = 460800) -> CommandResult:
        captured["port"] = port
        captured["firmware_bin"] = str(firmware_bin)
        captured["baud"] = baud
        return CommandResult(
            cmd=["esptool", "write_flash", "0x0", str(firmware_bin)],
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr("circuithack.codee.write_flash_zero", fake_write_flash_zero)

    result = flash_codee_firmware(
        port="/dev/cu.usbmodem2101",
        source=FIRMWARE_SOURCE_LOCAL_BUILD,
        build_dir=str(build_dir),
        baud=460800,
    )
    assert result["ok"] is True
    assert result["source"] == FIRMWARE_SOURCE_LOCAL_BUILD
    assert result["firmware_path"] == str(fw)
    assert captured["port"] == "/dev/cu.usbmodem2101"
    assert captured["firmware_bin"] == str(fw)
    assert captured["baud"] == 460800


def test_resolve_codee_firmware_path_missing_local_build(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Local build firmware not found"):
        resolve_codee_firmware_path(
            source=FIRMWARE_SOURCE_LOCAL_BUILD,
            build_dir=str(tmp_path / "build"),
        )
