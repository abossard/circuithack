from __future__ import annotations

from pathlib import Path

import pytest

from circuithack.rompatch import IpsPatchError, apply_ips_patch, apply_ips_patch_file


def _u24(value: int) -> bytes:
    return value.to_bytes(3, "big")


def _record(offset: int, payload: bytes) -> bytes:
    return _u24(offset) + len(payload).to_bytes(2, "big") + payload


def _rle_record(offset: int, run_length: int, run_value: int) -> bytes:
    return _u24(offset) + b"\x00\x00" + run_length.to_bytes(2, "big") + bytes((run_value,))


def test_apply_ips_patch_with_data_record() -> None:
    patch = b"PATCH" + _record(1, b"xy") + b"EOF"
    out, stats = apply_ips_patch(b"ABCDE", patch)
    assert out == b"AxyDE"
    assert stats.records == 1
    assert stats.rle_records == 0


def test_apply_ips_patch_with_rle_and_extension() -> None:
    patch = b"PATCH" + _rle_record(5, 3, ord("Z")) + b"EOF"
    out, stats = apply_ips_patch(b"abc", patch)
    assert out == b"abc\x00\x00ZZZ"
    assert stats.records == 1
    assert stats.rle_records == 1


def test_apply_ips_patch_honors_optional_final_size() -> None:
    patch = b"PATCH" + b"EOF" + (4).to_bytes(3, "big")
    out, stats = apply_ips_patch(b"0123456789", patch)
    assert out == b"0123"
    assert stats.final_size == 4


def test_apply_ips_patch_rejects_invalid_header() -> None:
    with pytest.raises(IpsPatchError):
        apply_ips_patch(b"abc", b"BAD!\x00")


def test_apply_ips_patch_file_respects_overwrite(tmp_path: Path) -> None:
    rom_path = tmp_path / "game.gb"
    patch_path = tmp_path / "hack.ips"
    out_path = tmp_path / "game_hacked.gb"

    rom_path.write_bytes(b"hello")
    patch_path.write_bytes(b"PATCH" + _record(0, b"H") + b"EOF")

    result = apply_ips_patch_file(rom_path, patch_path, out_path)
    assert result["ok"] is True
    assert out_path.read_bytes() == b"Hello"

    with pytest.raises(FileExistsError):
        apply_ips_patch_file(rom_path, patch_path, out_path, overwrite=False)
