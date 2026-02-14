from circuithack.firmware import pick_latest_stock_asset


def test_pick_latest_stock_asset_uses_first_non_prerelease_bin() -> None:
    releases = [
        {
            "tag_name": "v9.9.9-rc1",
            "draft": False,
            "prerelease": True,
            "published_at": "2026-01-01T00:00:00Z",
            "assets": [{"name": "Codee-rc.bin", "browser_download_url": "https://example/rc.bin"}],
        },
        {
            "tag_name": "v2.0.1",
            "draft": False,
            "prerelease": False,
            "published_at": "2025-09-30T10:56:08Z",
            "assets": [{"name": "Codee.bin", "browser_download_url": "https://example/codee.bin"}],
        },
    ]
    asset = pick_latest_stock_asset("codee", releases)
    assert asset.tag_name == "v2.0.1"
    assert asset.name == "Codee.bin"
    assert asset.browser_download_url.endswith("codee.bin")

