from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
from pathlib import Path
import shutil
from typing import Iterable
from urllib.parse import urlparse

import requests

from .util import run_cmd


GAMEWATCH_UPSTREAM_REPO = "tobozo/M5Tab5-Game-and-Watch"
GAMEWATCH_UPSTREAM_URL = f"https://github.com/{GAMEWATCH_UPSTREAM_REPO}.git"
GAMEWATCH_RELEASES_API = f"https://api.github.com/repos/{GAMEWATCH_UPSTREAM_REPO}/releases"

DEFAULT_GAMEWATCH_ROM_IDS: tuple[str, ...] = (
    "gnw_ball",
    "gnw_bfight",
    "gnw_chef",
    "gnw_climber",
    "gnw_dkjr",
    "gnw_dkjrp",
    "gnw_fire",
    "gnw_fireatk",
    "gnw_fires",
    "gnw_flagman",
    "gnw_helmet",
    "gnw_judge",
    "gnw_lion",
    "gnw_manhole",
    "gnw_manholeg",
    "gnw_mariocm",
    "gnw_mariocmt",
    "gnw_mariotj",
    "gnw_mbaway",
    "gnw_mmouse",
    "gnw_mmousep",
    "gnw_octopus",
    "gnw_pchute",
    "gnw_popeye",
    "gnw_popeyep",
    "gnw_smb",
    "gnw_snoopyp",
    "gnw_stennis",
    "gnw_tbridge",
    "gnw_tfish",
    "gnw_vermin",
)


@dataclass(frozen=True)
class GameWatchReleaseAsset:
    tag_name: str
    published_at: str
    name: str
    browser_download_url: str
    kind: str  # firmware|rom|artwork

    def to_dict(self) -> dict:
        return {
            "tag_name": self.tag_name,
            "published_at": self.published_at,
            "name": self.name,
            "browser_download_url": self.browser_download_url,
            "kind": self.kind,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _asset_kind(name: str) -> str | None:
    n = name.lower()
    if n.endswith(".bin"):
        return "firmware"
    if n.endswith(".jpg") or n.endswith(".jpeg") or n.endswith(".png"):
        return "artwork"
    if n.endswith(".jpg.gz") or n.endswith(".jpeg.gz") or n.endswith(".png.gz"):
        return "artwork"
    if n.endswith(".jpg.zip") or n.endswith(".jpeg.zip") or n.endswith(".png.zip"):
        return "artwork"
    if n.endswith(".gw") or n.endswith(".gw.gz") or n.endswith(".gw.zip"):
        return "rom"
    if n.endswith(".zip") and ("rom" in n or "gw" in n):
        return "rom"
    return None


def extract_gamewatch_release_assets(releases: list[dict]) -> list[GameWatchReleaseAsset]:
    assets: list[GameWatchReleaseAsset] = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        tag_name = release.get("tag_name", "")
        published_at = release.get("published_at", "")
        for item in release.get("assets", []):
            name = item.get("name", "")
            kind = _asset_kind(name)
            if kind is None:
                continue
            assets.append(
                GameWatchReleaseAsset(
                    tag_name=tag_name,
                    published_at=published_at,
                    name=name,
                    browser_download_url=item.get("browser_download_url", ""),
                    kind=kind,
                )
            )
    return assets


def fetch_gamewatch_releases(api_url: str = GAMEWATCH_RELEASES_API) -> list[dict]:
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        return payload
    return []


def list_gamewatch_release_assets() -> list[GameWatchReleaseAsset]:
    return extract_gamewatch_release_assets(fetch_gamewatch_releases())


def choose_latest_gamewatch_firmware_asset(
    assets: Iterable[GameWatchReleaseAsset],
) -> GameWatchReleaseAsset | None:
    for asset in assets:
        if asset.kind == "firmware":
            return asset
    return None


def _dedupe_non_empty(values: Iterable[str] | None) -> list[str]:
    if values is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = value.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def select_gamewatch_rom_ids(rom_ids: Iterable[str] | None) -> list[str]:
    selected = _dedupe_non_empty(rom_ids)
    if not selected:
        return list(DEFAULT_GAMEWATCH_ROM_IDS)

    allowed = set(DEFAULT_GAMEWATCH_ROM_IDS)
    normalized: list[str] = []
    invalid: list[str] = []
    for rom_id in selected:
        candidate = rom_id if rom_id.startswith("gnw_") else f"gnw_{rom_id}"
        if candidate not in allowed:
            invalid.append(rom_id)
            continue
        normalized.append(candidate)

    if invalid:
        raise ValueError(f"Unsupported ROM ids: {', '.join(invalid)}")
    return normalized


def build_gamewatch_rom_urls(
    base_url: str,
    rom_ids: Iterable[str] = DEFAULT_GAMEWATCH_ROM_IDS,
    rom_extension: str = ".gw.gz",
) -> list[str]:
    ids = select_gamewatch_rom_ids(rom_ids)
    if not ids:
        return []
    ext = rom_extension.strip() or ".gw.gz"
    if not ext.startswith("."):
        ext = f".{ext}"
    root = base_url.rstrip("/")
    return [f"{root}/{rom_id}{ext}" for rom_id in ids]


def build_gamewatch_artwork_urls(
    base_url: str,
    rom_ids: Iterable[str] = DEFAULT_GAMEWATCH_ROM_IDS,
    artwork_extension: str = ".jpg.gz",
) -> list[str]:
    ids = select_gamewatch_rom_ids(rom_ids)
    if not ids:
        return []
    ext = artwork_extension.strip() or ".jpg.gz"
    if not ext.startswith("."):
        ext = f".{ext}"
    root = base_url.rstrip("/")
    return [f"{root}/{rom_id}{ext}" for rom_id in ids]


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if name:
        return name
    raise ValueError(f"Could not derive filename from URL: {url}")


def _download_url(url: str, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _filename_from_url(url)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with out_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    file.write(chunk)
    return out_path


def _run_checked(cmd: list[str], timeout: int = 300) -> str:
    result = run_cmd(cmd, timeout=timeout)
    if not result.ok:
        raise RuntimeError(
            "\n".join(
                [
                    f"Command failed ({result.returncode}): {' '.join(cmd)}",
                    f"stdout: {result.stdout.strip()}",
                    f"stderr: {result.stderr.strip()}",
                ]
            )
        )
    return result.stdout.strip()


def sync_gamewatch_source(
    repo_dir: str | Path = "third_party/M5Tab5-Game-and-Watch",
    repo_url: str = GAMEWATCH_UPSTREAM_URL,
) -> dict:
    repo_dir = Path(repo_dir)
    if not repo_dir.exists():
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        _run_checked(["git", "clone", "--depth", "1", repo_url, str(repo_dir)], timeout=600)
        sync_mode = "clone"
    else:
        if not (repo_dir / ".git").exists():
            raise RuntimeError(f"Destination exists but is not a git repository: {repo_dir}")
        _run_checked(["git", "-C", str(repo_dir), "pull", "--ff-only"], timeout=600)
        sync_mode = "pull"

    commit = _run_checked(["git", "-C", str(repo_dir), "rev-parse", "HEAD"], timeout=30)
    commit_short = _run_checked(["git", "-C", str(repo_dir), "rev-parse", "--short", "HEAD"], timeout=30)
    branch = _run_checked(["git", "-C", str(repo_dir), "rev-parse", "--abbrev-ref", "HEAD"], timeout=30)
    commit_time = _run_checked(["git", "-C", str(repo_dir), "show", "-s", "--format=%cI", "HEAD"], timeout=30)
    return {
        "repo_url": repo_url,
        "repo_dir": str(repo_dir),
        "sync_mode": sync_mode,
        "branch": branch,
        "commit": commit,
        "commit_short": commit_short,
        "commit_time": commit_time,
        "synced_at": _now_iso(),
    }


def _strip_known_suffix(name: str, suffixes: tuple[str, ...]) -> str:
    lowered = name.lower()
    for suffix in suffixes:
        if lowered.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _rom_id_from_filename(filename: str) -> str:
    return _strip_known_suffix(filename, (".gw.gz", ".gw.zip", ".gw"))


def _artwork_id_from_filename(filename: str) -> str:
    return _strip_known_suffix(
        filename,
        (".jpg.gz", ".jpeg.gz", ".png.gz", ".jpg.zip", ".jpeg.zip", ".png.zip", ".jpg", ".jpeg", ".png"),
    )


def _validate_littlefs_name(filename: str) -> None:
    # Upstream warns about short LittleFS paths. Keep root-level names compact.
    if len(f"/{filename}") > 31:
        raise RuntimeError(f"LittleFS path too long for upstream loader: /{filename}")


def _littlefs_output_name(path: Path) -> str:
    name = path.name
    lower = name.lower()
    if lower.endswith(".gw.gz"):
        return name[: -len(".gw.gz")] + ".gw"
    if lower.endswith(".jpg.gz"):
        return name[: -len(".jpg.gz")] + ".jpg"
    if lower.endswith(".jpeg.gz"):
        return name[: -len(".jpeg.gz")] + ".jpeg"
    if lower.endswith(".png.gz"):
        return name[: -len(".png.gz")] + ".png"
    return name


def _copy_or_unpack_for_littlefs(src: Path, dst: Path) -> None:
    if src.name != dst.name and src.name.lower().endswith(".gz"):
        with gzip.open(src, "rb") as compressed, dst.open("wb") as unpacked:
            shutil.copyfileobj(compressed, unpacked)
        return
    shutil.copy2(src, dst)


def prepare_gamewatch_littlefs_bundle(
    rom_paths: Iterable[str],
    artwork_paths: Iterable[str],
    bundle_dir: str | Path,
    require_artworks: bool = True,
    littlefs_max_bytes: int | None = None,
) -> dict:
    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    rom_files = [Path(path) for path in rom_paths]
    artwork_files = [Path(path) for path in artwork_paths]

    for path in rom_files + artwork_files:
        if not path.exists():
            raise RuntimeError(f"Downloaded asset is missing on disk: {path}")

    artwork_by_id = {_artwork_id_from_filename(path.name): path for path in artwork_files}
    missing_artworks: list[str] = []
    for rom in rom_files:
        rom_id = _rom_id_from_filename(rom.name)
        if rom_id not in artwork_by_id:
            missing_artworks.append(rom_id)

    if require_artworks and missing_artworks:
        missing = ", ".join(missing_artworks)
        raise RuntimeError(
            f"Missing artworks for ROM ids: {missing}. "
            "The emulator expects matching artwork files in LittleFS root."
        )

    copied_files: list[str] = []
    total_bytes = 0
    seen_targets: set[str] = set()
    for path in [*rom_files, *artwork_files]:
        target_name = _littlefs_output_name(path)
        if target_name in seen_targets:
            raise RuntimeError(f"Duplicate LittleFS target filename after normalization: {target_name}")
        seen_targets.add(target_name)
        _validate_littlefs_name(target_name)
        destination = bundle_dir / target_name
        _copy_or_unpack_for_littlefs(path, destination)
        copied_files.append(str(destination))
        total_bytes += destination.stat().st_size

    if littlefs_max_bytes is not None and total_bytes > littlefs_max_bytes:
        raise RuntimeError(
            f"LittleFS bundle exceeds limit: {total_bytes} > {littlefs_max_bytes} bytes. "
            "Select fewer ROMs or higher compression."
        )

    return {
        "bundle_dir": str(bundle_dir),
        "file_count": len(copied_files),
        "total_bytes": total_bytes,
        "max_bytes": littlefs_max_bytes,
        "missing_artworks": missing_artworks,
        "files": copied_files,
    }


def download_gamewatch_assets(
    out_dir: str | Path = "downloads/gamewatch",
    repo_dir: str | Path = "third_party/M5Tab5-Game-and-Watch",
    firmware_url: str | None = None,
    rom_urls: Iterable[str] | None = None,
    rom_base_url: str | None = None,
    rom_ids: Iterable[str] | None = None,
    rom_extension: str = ".gw.gz",
    artwork_urls: Iterable[str] | None = None,
    artwork_base_url: str | None = None,
    artwork_extension: str = ".jpg.gz",
    require_artworks: bool = True,
    prepare_littlefs_bundle: bool = True,
    littlefs_bundle_dir: str | None = None,
    littlefs_max_bytes: int | None = None,
    sync_source: bool = True,
    include_release_assets: bool = True,
) -> dict:
    source_info = sync_gamewatch_source(repo_dir=repo_dir) if sync_source else None

    release_assets: list[GameWatchReleaseAsset] = []
    release_error: str | None = None

    fw_url = (firmware_url or "").strip()
    resolved_rom_urls = _dedupe_non_empty(rom_urls)
    resolved_artwork_urls = _dedupe_non_empty(artwork_urls)
    selected_ids = select_gamewatch_rom_ids(rom_ids)
    if not resolved_rom_urls and rom_base_url:
        resolved_rom_urls = build_gamewatch_rom_urls(
            base_url=rom_base_url,
            rom_ids=selected_ids,
            rom_extension=rom_extension,
        )
    if not resolved_artwork_urls and artwork_base_url:
        resolved_artwork_urls = build_gamewatch_artwork_urls(
            base_url=artwork_base_url,
            rom_ids=selected_ids,
            artwork_extension=artwork_extension,
        )

    needs_release_assets = include_release_assets and (
        not fw_url or not resolved_rom_urls or (require_artworks and not resolved_artwork_urls)
    )
    if needs_release_assets:
        try:
            release_assets = list_gamewatch_release_assets()
        except requests.RequestException as exc:
            release_error = str(exc)

    if not fw_url and release_assets:
        firmware_asset = choose_latest_gamewatch_firmware_asset(release_assets)
        fw_url = firmware_asset.browser_download_url if firmware_asset else ""

    if not resolved_rom_urls and release_assets:
        resolved_rom_urls = [x.browser_download_url for x in release_assets if x.kind == "rom"]
    if not resolved_artwork_urls and release_assets:
        resolved_artwork_urls = [x.browser_download_url for x in release_assets if x.kind == "artwork"]

    out_dir = Path(out_dir)
    firmware_path: str | None = None
    rom_paths: list[str] = []
    artwork_paths: list[str] = []
    warnings: list[str] = []

    if fw_url:
        firmware_path = str(_download_url(fw_url, out_dir / "firmware"))
    else:
        warnings.append(
            "No firmware .bin URL available from releases. Provide firmware_url explicitly or build from source."
        )

    for url in resolved_rom_urls:
        rom_paths.append(str(_download_url(url, out_dir / "roms")))
    for url in resolved_artwork_urls:
        artwork_paths.append(str(_download_url(url, out_dir / "artworks")))

    if not resolved_rom_urls:
        warnings.append(
            "No ROM URLs resolved. Provide rom_urls or rom_base_url + rom_ids. Upstream repo does not ship ROMs."
        )
    if require_artworks and not resolved_artwork_urls:
        warnings.append(
            "No artwork URLs resolved. Provide artwork_urls or artwork_base_url + rom_ids."
        )
    if release_error:
        warnings.append(f"Release asset lookup failed: {release_error}")

    littlefs_bundle: dict | None = None
    if prepare_littlefs_bundle:
        bundle_target = littlefs_bundle_dir or str(out_dir / "littlefs")
        littlefs_bundle = prepare_gamewatch_littlefs_bundle(
            rom_paths=rom_paths,
            artwork_paths=artwork_paths,
            bundle_dir=bundle_target,
            require_artworks=require_artworks,
            littlefs_max_bytes=littlefs_max_bytes,
        )

    return {
        "ok": True,
        "out_dir": str(out_dir),
        "source": source_info,
        "release_asset_count": len(release_assets),
        "release_assets": [x.to_dict() for x in release_assets],
        "firmware": {
            "resolved_url": fw_url or None,
            "download_path": firmware_path,
        },
        "roms": {
            "resolved_url_count": len(resolved_rom_urls),
            "download_count": len(rom_paths),
            "download_paths": rom_paths,
        },
        "artworks": {
            "resolved_url_count": len(resolved_artwork_urls),
            "download_count": len(artwork_paths),
            "download_paths": artwork_paths,
        },
        "storage_mode": "littlefs_no_sd",
        "littlefs_bundle": littlefs_bundle,
        "warnings": warnings,
    }


def codee_gamewatch_adaptation_report() -> dict:
    return {
        "upstream_target": {
            "board": "M5Stack Tab5 (ESP32-P4)",
            "display": "1280x720 landscape touchscreen",
            "input": ["touch", "USB keyboard/gamepad"],
            "storage": ["SD_MMC", "LittleFS"],
            "special_features": ["IMU auto-rotation", "RTC-backed persistence"],
        },
        "codee_target": {
            "board": "Codee 2.0 (ESP32-S3)",
            "display": "small non-touch panel (project uses 128x128 adapters)",
            "input": ["4 hardware buttons"],
            "storage": ["LittleFS/SPIFFS"],
            "audio": "simple buzzer/tone output",
        },
        "required_porting_changes": [
            "Replace Tab5-only framework calls (M5Unified/M5GFX touch, IMU, USB host, RTC RAM).",
            "Implement a Codee display backend with fixed orientation and lower resolution scaling.",
            "Map Game&Watch actions to 4 physical buttons with mode-switch gesture for GameA/GameB/Time/ACL.",
            "Keep ROM/artwork loading in LittleFS root paths only; disable SD-dependent code paths.",
            "Replace Tab5 volume/brightness overlays with lightweight Codee UI and persistence in filesystem.",
            "Tune memory policy: preload fewer ROMs at once, stream assets on demand for ESP32-S3 limits.",
        ],
        "no_sd_requirements": [
            "Use LittleFS only (`gwFS = &LittleFS` path); remove SD picker UI.",
            "Bundle matching `gnw_*.gw(.gz)` and `gnw_*.jpg(.gz)` files in LittleFS root.",
            "Validate asset bundle size against your Codee storage partition before flashing data.",
        ],
        "build_strategy": [
            "Start from LCD-Game-Emulator core and keep board glue in one Codee adapter module.",
            "Compile for Arduino ESP32-S3 target used by Codee firmware toolchain.",
            "Use compressed '.gw.gz' ROM assets and reduced JPEG artwork to control load time and RAM usage.",
        ],
        "rom_note": (
            "M5Tab5-Game-and-Watch does not include redistributable ROMs. "
            "Use your own legally obtained MAME sources and optionally LCD-Game-Shrinker output."
        ),
    }
