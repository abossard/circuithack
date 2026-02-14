from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests


DEVICE_REPO = {
    "codee": "CircuitMess/Codee-Firmware",
    "bit": "CircuitMess/Bit-Firmware",
}


@dataclass
class FirmwareAsset:
    device: str
    tag_name: str
    published_at: str
    name: str
    browser_download_url: str

    def to_dict(self) -> dict:
        return {
            "device": self.device,
            "tag_name": self.tag_name,
            "published_at": self.published_at,
            "name": self.name,
            "browser_download_url": self.browser_download_url,
        }


def _releases_url(device: str) -> str:
    repo = DEVICE_REPO[device]
    return f"https://api.github.com/repos/{repo}/releases"


def fetch_releases(device: str) -> list[dict]:
    device = device.lower()
    if device not in DEVICE_REPO:
        raise ValueError(f"Unsupported device '{device}'")
    r = requests.get(_releases_url(device), timeout=30)
    r.raise_for_status()
    return r.json()


def pick_latest_stock_asset(device: str, releases: list[dict]) -> FirmwareAsset:
    for rel in releases:
        if rel.get("draft") or rel.get("prerelease"):
            continue
        assets = rel.get("assets", [])
        for a in assets:
            name = (a.get("name") or "").lower()
            if name.endswith(".bin"):
                return FirmwareAsset(
                    device=device,
                    tag_name=rel.get("tag_name", ""),
                    published_at=rel.get("published_at", ""),
                    name=a.get("name", ""),
                    browser_download_url=a.get("browser_download_url", ""),
                )
    raise RuntimeError(f"No .bin asset found in releases for {device}")


def latest_stock_asset(device: str) -> FirmwareAsset:
    return pick_latest_stock_asset(device, fetch_releases(device))


def download_asset(asset: FirmwareAsset, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / asset.name
    with requests.get(asset.browser_download_url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
    return out_path

