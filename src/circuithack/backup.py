from __future__ import annotations

import struct
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .flash import read_flash, write_flash_at

PARTITION_TABLE_OFFSET = 0x10000
PARTITION_TABLE_SIZE = 0x1000
STATE_PARTITION_LABELS = frozenset({"nvs", "storage", "factory"})


@dataclass
class PartitionEntry:
    label: str
    type: int
    subtype: int
    offset: int
    size: int
    flags: int

    def to_dict(self) -> dict:
        d = asdict(self)
        d["offset_hex"] = hex(self.offset)
        d["size_hex"] = hex(self.size)
        return d


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def parse_partition_table(part_bin_path: str | Path) -> list[PartitionEntry]:
    data = Path(part_bin_path).read_bytes()
    out: list[PartitionEntry] = []
    for i in range(0, len(data), 32):
        entry = data[i : i + 32]
        if len(entry) < 32:
            break
        if entry == b"\xFF" * 32:
            continue
        magic, ptype, subtype, offset, size, label_raw, flags = struct.unpack("<HBBII16sI", entry)
        if magic != 0x50AA:
            continue
        label = label_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        out.append(
            PartitionEntry(
                label=label,
                type=ptype,
                subtype=subtype,
                offset=offset,
                size=size,
                flags=flags,
            )
        )
    return out


def select_state_partitions(entries: list[PartitionEntry]) -> list[PartitionEntry]:
    return [entry for entry in entries if entry.label in STATE_PARTITION_LABELS]


def _read_partition_table_snapshot(
    port: str,
    out_dir: str | Path,
    baud: int,
    offset: int,
    size: int,
) -> tuple[dict, list[PartitionEntry]]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"codee-partitions-{_ts()}.bin"
    res = read_flash(port=port, offset=offset, size=size, out_path=out_path, baud=baud, timeout=300)
    if not res.ok:
        return (
            {
                "ok": False,
                "stage": "read_partition_table",
                "path": str(out_path),
                "stdout": res.stdout,
                "stderr": res.stderr,
            },
            [],
        )
    entries = parse_partition_table(out_path)
    return (
        {
            "ok": True,
            "path": str(out_path),
            "entries": [entry.to_dict() for entry in entries],
            "stdout": res.stdout,
            "stderr": res.stderr,
        },
        entries,
    )


def _backup_single_partition(
    port: str,
    out_dir: str | Path,
    baud: int,
    partition: PartitionEntry,
) -> dict:
    out_path = Path(out_dir) / f"codee-{partition.label}-{_ts()}.bin"
    res = read_flash(
        port=port,
        offset=partition.offset,
        size=partition.size,
        out_path=out_path,
        baud=baud,
        timeout=1800,
    )
    return {
        "label": partition.label,
        "offset": partition.offset,
        "offset_hex": hex(partition.offset),
        "size": partition.size,
        "size_hex": hex(partition.size),
        "path": str(out_path),
        "ok": res.ok,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


def backup_partition_table(
    port: str,
    out_dir: str | Path,
    baud: int = 921600,
    offset: int = PARTITION_TABLE_OFFSET,
    size: int = PARTITION_TABLE_SIZE,
) -> dict:
    info, _ = _read_partition_table_snapshot(
        port=port,
        out_dir=out_dir,
        baud=baud,
        offset=offset,
        size=size,
    )
    return info


def backup_full_flash(
    port: str,
    out_dir: str | Path,
    flash_size: int = 0x400000,
    baud: int = 921600,
) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"codee-fullflash-{_ts()}.bin"
    res = read_flash(port=port, offset=0, size=flash_size, out_path=out_path, baud=baud, timeout=3600)
    return {
        "ok": res.ok,
        "path": str(out_path),
        "flash_size": flash_size,
        "flash_size_hex": hex(flash_size),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


def backup_state_partitions(
    port: str,
    out_dir: str | Path,
    baud: int = 921600,
) -> dict:
    part_info, entries = _read_partition_table_snapshot(
        port=port,
        out_dir=out_dir,
        baud=baud,
        offset=PARTITION_TABLE_OFFSET,
        size=PARTITION_TABLE_SIZE,
    )
    if not part_info.get("ok"):
        return part_info

    wanted = select_state_partitions(entries)
    backups: list[dict] = []

    for p in wanted:
        backup = _backup_single_partition(port=port, out_dir=out_dir, baud=baud, partition=p)
        backups.append(backup)
        if not backup["ok"]:
            return {
                "ok": False,
                "stage": f"backup_{p.label}",
                "partition_table": part_info,
                "backups": backups,
            }

    return {
        "ok": True,
        "partition_table": part_info,
        "backups": backups,
    }


def restore_full_flash_backup(
    port: str,
    backup_path: str | Path,
    baud: int = 921600,
) -> dict:
    path = Path(backup_path)
    if not path.exists():
        return {"ok": False, "error": f"Backup file not found: {path}"}
    res = write_flash_at(port=port, offset=0, in_path=path, baud=baud, timeout=3600)
    return {
        "ok": res.ok,
        "backup_path": str(path),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }
