from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

IPS_MAGIC = b"PATCH"
IPS_EOF = b"EOF"


class IpsPatchError(ValueError):
    pass


@dataclass(frozen=True)
class IpsPatchStats:
    records: int
    rle_records: int
    final_size: int


def apply_ips_patch(rom_data: bytes, patch_data: bytes) -> tuple[bytes, IpsPatchStats]:
    if not patch_data.startswith(IPS_MAGIC):
        raise IpsPatchError("Invalid IPS patch: missing PATCH header")

    pos = len(IPS_MAGIC)
    out = bytearray(rom_data)
    records = 0
    rle_records = 0

    while True:
        if pos + 3 > len(patch_data):
            raise IpsPatchError("Invalid IPS patch: unexpected end before EOF marker")

        offset_bytes = patch_data[pos : pos + 3]
        pos += 3

        if offset_bytes == IPS_EOF:
            break

        offset = int.from_bytes(offset_bytes, "big")

        if pos + 2 > len(patch_data):
            raise IpsPatchError("Invalid IPS patch: missing record size")

        size = int.from_bytes(patch_data[pos : pos + 2], "big")
        pos += 2

        if size == 0:
            if pos + 3 > len(patch_data):
                raise IpsPatchError("Invalid IPS patch: truncated RLE record")
            run_length = int.from_bytes(patch_data[pos : pos + 2], "big")
            run_value = patch_data[pos + 2]
            pos += 3
            payload = bytes((run_value,)) * run_length
            rle_records += 1
        else:
            if pos + size > len(patch_data):
                raise IpsPatchError("Invalid IPS patch: truncated data record")
            payload = patch_data[pos : pos + size]
            pos += size

        end = offset + len(payload)
        if end > len(out):
            out.extend(b"\x00" * (end - len(out)))
        out[offset:end] = payload
        records += 1

    remaining = len(patch_data) - pos
    # Some IPS patches include an optional 3-byte final size after EOF.
    if remaining == 3:
        final_size = int.from_bytes(patch_data[pos : pos + 3], "big")
        if final_size < len(out):
            del out[final_size:]
        elif final_size > len(out):
            out.extend(b"\x00" * (final_size - len(out)))
    elif remaining != 0:
        raise IpsPatchError("Invalid IPS patch: unexpected trailing bytes")

    return bytes(out), IpsPatchStats(records=records, rle_records=rle_records, final_size=len(out))


def apply_ips_patch_file(
    rom_path: str | Path,
    patch_path: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
) -> dict:
    rom_path = Path(rom_path)
    patch_path = Path(patch_path)
    output_path = Path(output_path)

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}")

    patched_data, stats = apply_ips_patch(rom_path.read_bytes(), patch_path.read_bytes())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(patched_data)

    return {
        "ok": True,
        "rom_path": str(rom_path),
        "patch_path": str(patch_path),
        "output_path": str(output_path),
        "records": stats.records,
        "rle_records": stats.rle_records,
        "final_size": stats.final_size,
    }
