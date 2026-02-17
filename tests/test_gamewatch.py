from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from circuithack.gamewatch import (
    GameWatchReleaseAsset,
    build_gamewatch_rom_urls,
    choose_latest_gamewatch_firmware_asset,
    download_gamewatch_assets,
    extract_gamewatch_release_assets,
    select_gamewatch_rom_ids,
)


def test_build_gamewatch_rom_urls_normalizes_extension() -> None:
    urls = build_gamewatch_rom_urls(
        base_url="https://example.invalid/roms/",
        rom_ids=["gnw_ball", "gnw_ball", "gnw_fire"],
        rom_extension="gw.gz",
    )
    assert urls == [
        "https://example.invalid/roms/gnw_ball.gw.gz",
        "https://example.invalid/roms/gnw_fire.gw.gz",
    ]


def test_select_gamewatch_rom_ids_normalizes_short_names() -> None:
    assert select_gamewatch_rom_ids(["ball", "gnw_fire"]) == ["gnw_ball", "gnw_fire"]


def test_select_gamewatch_rom_ids_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Unsupported ROM ids"):
        select_gamewatch_rom_ids(["not-a-rom"])


def test_extract_gamewatch_release_assets_filters_kind() -> None:
    releases = [
        {
            "tag_name": "v0.9.0-rc1",
            "draft": False,
            "prerelease": True,
            "published_at": "2026-01-01T00:00:00Z",
            "assets": [
                {"name": "ignored.bin", "browser_download_url": "https://example.invalid/ignored.bin"}
            ],
        },
        {
            "tag_name": "v1.0.0",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-01-10T00:00:00Z",
            "assets": [
                {"name": "GameWatch.bin", "browser_download_url": "https://example.invalid/fw.bin"},
                {
                    "name": "gnw_ball.gw.gz",
                    "browser_download_url": "https://example.invalid/gnw_ball.gw.gz",
                },
                {"name": "notes.txt", "browser_download_url": "https://example.invalid/notes.txt"},
            ],
        },
    ]

    assets = extract_gamewatch_release_assets(releases)
    assert [x.name for x in assets] == ["GameWatch.bin", "gnw_ball.gw.gz"]
    assert [x.kind for x in assets] == ["firmware", "rom"]


def test_choose_latest_gamewatch_firmware_asset() -> None:
    assets = [
        GameWatchReleaseAsset(
            tag_name="v1.0.0",
            published_at="2026-01-10T00:00:00Z",
            name="gnw_ball.gw.gz",
            browser_download_url="https://example.invalid/gnw_ball.gw.gz",
            kind="rom",
        ),
        GameWatchReleaseAsset(
            tag_name="v1.0.0",
            published_at="2026-01-10T00:00:00Z",
            name="GameWatch.bin",
            browser_download_url="https://example.invalid/GameWatch.bin",
            kind="firmware",
        ),
    ]
    picked = choose_latest_gamewatch_firmware_asset(assets)
    assert picked is not None
    assert picked.name == "GameWatch.bin"


def test_download_gamewatch_assets_with_explicit_urls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: list[tuple[str, str]] = []

    def fake_sync_gamewatch_source(*_args, **_kwargs) -> dict:
        return {"repo_dir": "third_party/M5Tab5-Game-and-Watch"}

    def fake_download_url(url: str, out_dir: str | Path) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        captured.append((url, str(out)))
        target = out / Path(url).name
        if str(target).endswith(".gz"):
            with gzip.open(target, "wb") as f:
                f.write(b"asset")
        else:
            target.write_bytes(b"asset")
        return target

    monkeypatch.setattr("circuithack.gamewatch.sync_gamewatch_source", fake_sync_gamewatch_source)
    monkeypatch.setattr("circuithack.gamewatch.list_gamewatch_release_assets", lambda: [])
    monkeypatch.setattr("circuithack.gamewatch._download_url", fake_download_url)

    result = download_gamewatch_assets(
        out_dir=tmp_path,
        firmware_url="https://example.invalid/fw/GameWatch.bin",
        rom_base_url="https://example.invalid/roms",
        artwork_base_url="https://example.invalid/artworks",
        rom_ids=["gnw_ball", "gnw_fire"],
        sync_source=True,
        include_release_assets=False,
    )

    assert result["ok"] is True
    assert result["firmware"]["resolved_url"].endswith("GameWatch.bin")
    assert result["roms"]["download_count"] == 2
    assert result["artworks"]["download_count"] == 2
    assert result["warnings"] == []
    assert result["littlefs_bundle"]["file_count"] == 4
    littlefs_files = {Path(x).name for x in result["littlefs_bundle"]["files"]}
    assert littlefs_files == {"gnw_ball.gw", "gnw_fire.gw", "gnw_ball.jpg", "gnw_fire.jpg"}

    downloaded_urls = [x[0] for x in captured]
    assert "https://example.invalid/fw/GameWatch.bin" in downloaded_urls
    assert "https://example.invalid/roms/gnw_ball.gw.gz" in downloaded_urls
    assert "https://example.invalid/roms/gnw_fire.gw.gz" in downloaded_urls
    assert "https://example.invalid/artworks/gnw_ball.jpg.gz" in downloaded_urls
    assert "https://example.invalid/artworks/gnw_fire.jpg.gz" in downloaded_urls


def test_download_gamewatch_assets_without_sources_or_urls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("circuithack.gamewatch.list_gamewatch_release_assets", lambda: [])
    result = download_gamewatch_assets(
        out_dir=tmp_path,
        sync_source=False,
        include_release_assets=True,
    )
    assert result["ok"] is True
    assert result["firmware"]["download_path"] is None
    assert result["roms"]["download_count"] == 0
    assert result["artworks"]["download_count"] == 0
    assert len(result["warnings"]) == 3


def test_download_gamewatch_assets_errors_when_artworks_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_download_url(url: str, out_dir: str | Path) -> Path:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        target = out / Path(url).name
        if str(target).endswith(".gz"):
            with gzip.open(target, "wb") as f:
                f.write(b"asset")
        else:
            target.write_bytes(b"asset")
        return target

    monkeypatch.setattr("circuithack.gamewatch.sync_gamewatch_source", lambda **_kwargs: {"repo_dir": "x"})
    monkeypatch.setattr("circuithack.gamewatch.list_gamewatch_release_assets", lambda: [])
    monkeypatch.setattr("circuithack.gamewatch._download_url", fake_download_url)

    with pytest.raises(RuntimeError, match="Missing artworks for ROM ids"):
        download_gamewatch_assets(
            out_dir=tmp_path,
            firmware_url="https://example.invalid/fw.bin",
            rom_base_url="https://example.invalid/roms",
            rom_ids=["gnw_ball"],
            include_release_assets=False,
        )
