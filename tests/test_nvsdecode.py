from pathlib import Path

from circuithack.nvsdecode import decode_codee_nvs_backup, decode_codee_nvs_entries, parse_minimal_nvs_output


def test_parse_minimal_nvs_output_extracts_entries() -> None:
    text = """
Page no. 0, Status: Active
 Codee:Settings[0] = b'\\x50\\x01\\x01'
 Codee:StatsTime[0] = b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
 Codee:Stats[0] = b'\\x64\\x64\\x92\\x00\\x00\\x01'
"""
    entries = parse_minimal_nvs_output(text)
    assert entries["Settings"] == b"\x50\x01\x01"
    assert entries["Stats"] == b"\x64\x64\x92\x00\x00\x01"
    assert entries["StatsTime"] == b"\x00" * 8


def test_decode_codee_nvs_entries_decodes_known_fields() -> None:
    entries = {
        "Settings": b"\x50\x01\x01",
        "Stats": b"\x64\x64\x92\x00\x00\x01",
        "StatsTime": b"\x00\x00\x00\x00\x00\x00\x00\x00",
    }
    decoded = decode_codee_nvs_entries(entries)
    assert decoded["settings"]["screen_brightness"] == 80
    assert decoded["settings"]["sleep_time_index"] == 1
    assert decoded["settings"]["sound_enabled"] is True
    assert decoded["stats"]["happiness"] == 100
    assert decoded["stats"]["oil_level"] == 100
    assert decoded["stats"]["experience"] == 146
    assert decoded["stats"]["hours_on_zero_stats"] == 0
    assert decoded["stats"]["hatched"] is True
    assert decoded["stats_time"]["unix_seconds"] == 0


def test_decode_codee_nvs_backup_end_to_end(tmp_path: Path) -> None:
    nvs_path = tmp_path / "nvs.bin"
    nvs_path.write_bytes(b"\x00" * 64)

    tool_dir = tmp_path / "tool"
    tool_dir.mkdir(parents=True)
    for name in ("nvs_parser.py", "nvs_check.py", "nvs_logger.py"):
        (tool_dir / name).write_text("")
    (tool_dir / "nvs_tool.py").write_text(
        "print('Page no. 0, Status: Active')\n"
        "print(\" Codee:Settings[0] = b'\\\\x50\\\\x01\\\\x01'\")\n"
        "print(\" Codee:StatsTime[0] = b'\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00\\\\x00'\")\n"
        "print(\" Codee:Stats[0] = b'\\\\x64\\\\x64\\\\x92\\\\x00\\\\x00\\\\x01'\")\n"
    )

    result = decode_codee_nvs_backup(nvs_path=nvs_path, tool_dir=tool_dir)
    assert result["ok"] is True
    assert result["decoded"]["settings"]["screen_brightness"] == 80
    assert result["decoded"]["stats"]["experience"] == 146
