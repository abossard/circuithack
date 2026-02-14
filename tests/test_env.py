import os
from pathlib import Path

from circuithack.env import auto_load_env, find_env_file, parse_env_text


def test_parse_env_text_ignores_comments_and_strips_quotes() -> None:
    parsed = parse_env_text(
        """
        # comment
        WOKWI_CLI_TOKEN="abc123"
        PLAIN=value
        EMPTY=
        INVALID_LINE
        """
    )
    assert parsed["WOKWI_CLI_TOKEN"] == "abc123"
    assert parsed["PLAIN"] == "value"
    assert parsed["EMPTY"] == ""
    assert "INVALID_LINE" not in parsed


def test_auto_load_env_finds_parent_env_without_overriding(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "repo"
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    (root / ".env").write_text("WOKWI_CLI_TOKEN=test-token\n", encoding="utf-8")

    monkeypatch.setenv("WOKWI_CLI_TOKEN", "existing")
    loaded = auto_load_env(start=nested)

    assert loaded == {}
    assert os.environ["WOKWI_CLI_TOKEN"] == "existing"


def test_find_env_file_returns_none_when_missing(tmp_path: Path) -> None:
    start = tmp_path / "x" / "y"
    start.mkdir(parents=True)
    assert find_env_file(start=start) is None
