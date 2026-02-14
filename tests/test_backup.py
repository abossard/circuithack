from pathlib import Path

from circuithack.backup import parse_partition_table, select_state_partitions


def _entry(label: str, ptype: int, subtype: int, offset: int, size: int, flags: int = 0) -> bytes:
    import struct

    label_raw = label.encode("ascii")[:15] + b"\x00"
    label_raw = label_raw.ljust(16, b"\x00")
    return struct.pack("<HBBII16sI", 0x50AA, ptype, subtype, offset, size, label_raw, flags)


def test_parse_partition_table_reads_labels(tmp_path: Path) -> None:
    blob = b"".join(
        [
            _entry("nvs", 0x01, 0x02, 0x11000, 0x6000),
            _entry("factory", 0x00, 0x00, 0x20000, 0xFA000),
            _entry("storage", 0x01, 0x82, 0x11A000, 0x2E6000),
            b"\xff" * 32,
        ]
    )
    p = tmp_path / "partitions.bin"
    p.write_bytes(blob)
    parts = parse_partition_table(p)
    labels = [x.label for x in parts]
    assert labels == ["nvs", "factory", "storage"]
    assert parts[0].offset == 0x11000
    assert parts[2].size == 0x2E6000


def test_select_state_partitions_filters_expected_labels(tmp_path: Path) -> None:
    blob = b"".join(
        [
            _entry("otadata", 0x01, 0x00, 0xE000, 0x2000),
            _entry("nvs", 0x01, 0x02, 0x11000, 0x6000),
            _entry("factory", 0x00, 0x00, 0x20000, 0xFA000),
            _entry("storage", 0x01, 0x82, 0x11A000, 0x2E6000),
        ]
    )
    p = tmp_path / "partitions.bin"
    p.write_bytes(blob)
    parts = parse_partition_table(p)
    state_parts = select_state_partitions(parts)
    assert [x.label for x in state_parts] == ["nvs", "factory", "storage"]
