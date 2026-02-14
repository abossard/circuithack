from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .util import run_cmd


@dataclass(frozen=True)
class GameSource:
    id: str
    repo: str
    description: str


DEFAULT_GAME_SOURCES: tuple[GameSource, ...] = (
    GameSource(
        id="thumby-color-games",
        repo="TinyCircuits/TinyCircuits-Thumby-Color-Games",
        description="Color MicroPython game collection for handheld devices.",
    ),
    GameSource(
        id="thumby-games",
        repo="TinyCircuits/TinyCircuits-Thumby-Games",
        description="Large MicroPython game corpus (mostly monochrome).",
    ),
    GameSource(
        id="tiny-game-engine",
        repo="TinyCircuits/TinyCircuits-Tiny-Game-Engine",
        description="Reusable TinyCircuits MicroPython game engine.",
    ),
    GameSource(
        id="gameesp-micropython",
        repo="cheungbx/gameESP-micropython",
        description="ESP32/ESP8266 MicroPython game modules and examples.",
    ),
    GameSource(
        id="odroid-go-micropython-games",
        repo="cheungbx/Odroid-Go-Micropython-games",
        description="ESP32 color TFT game examples.",
    ),
    GameSource(
        id="esp-arcade-playground",
        repo="snacsnoc/ESP-arcade-playground",
        description="Multi-game MicroPython framework for ESP32/ESP8266.",
    ),
    GameSource(
        id="thumby-silicon8",
        repo="Timendus/thumby-silicon8",
        description="MicroPython CHIP-8 interpreter for Thumby.",
    ),
    GameSource(
        id="thumby-virtual-pet",
        repo="SarahBass/Thumby-Virtual-Pet",
        description="MicroPython virtual pet prototype.",
    ),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _to_repo_url(repo: str) -> str:
    if repo.startswith(("https://", "http://", "ssh://", "git@")):
        return repo
    if repo.startswith(("/", "./", "../")):
        return repo
    return f"https://github.com/{repo}.git"


def _git(cmd: list[str], cwd: str | Path | None = None, timeout: int = 300) -> str:
    res = run_cmd(cmd if cwd is None else ["git", "-C", str(cwd), *cmd[1:]], timeout=timeout)
    if not res.ok:
        message = [
            f"Command failed ({res.returncode}): {' '.join(cmd)}",
            f"stdout: {res.stdout.strip()}",
            f"stderr: {res.stderr.strip()}",
        ]
        raise RuntimeError("\n".join(message))
    return res.stdout.strip()


def _git_run(cwd: str | Path, args: list[str], timeout: int = 300) -> str:
    return _git(["git", *args], cwd=cwd, timeout=timeout)


def _repo_default_branch(repo_url: str) -> str:
    out = _git(["git", "ls-remote", "--symref", repo_url, "HEAD"], timeout=120)
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("ref:") and line.endswith("HEAD"):
            # Example: ref: refs/heads/main HEAD
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "HEAD":
                ref = parts[0].replace("ref:", "", 1).strip()
                prefix = "refs/heads/"
                if ref.startswith(prefix):
                    return ref[len(prefix) :]
    return "main"


def _normalize_url(url: str) -> str:
    if url.startswith(("http://", "https://", "ssh://", "git@")):
        return url.rstrip("/")
    return str(Path(url).expanduser().resolve())


def _assert_origin_matches(repo_dir: Path, expected_repo_url: str) -> None:
    existing = _git_run(repo_dir, ["remote", "get-url", "origin"]).strip()
    if _normalize_url(existing) != _normalize_url(expected_repo_url):
        raise RuntimeError(
            f"Existing repo remote mismatch for {repo_dir}: origin={existing} expected={expected_repo_url}"
        )


def _clone_or_update_repo(repo_url: str, dest_dir: Path, branch: str) -> dict:
    if not dest_dir.exists():
        parent = dest_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        _git(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(dest_dir)], timeout=600)
    else:
        if not (dest_dir / ".git").exists():
            raise RuntimeError(f"Destination exists but is not a git repo: {dest_dir}")
        _assert_origin_matches(dest_dir, repo_url)
        _git_run(dest_dir, ["fetch", "--prune", "origin"], timeout=600)

        checkout = run_cmd(["git", "-C", str(dest_dir), "checkout", branch], timeout=120)
        if not checkout.ok:
            _git_run(dest_dir, ["checkout", "-B", branch, f"origin/{branch}"], timeout=120)

        _git_run(dest_dir, ["merge", "--ff-only", f"origin/{branch}"], timeout=300)

    commit = _git_run(dest_dir, ["rev-parse", "HEAD"]).strip()
    commit_short = _git_run(dest_dir, ["rev-parse", "--short", "HEAD"]).strip()
    commit_time = _git_run(dest_dir, ["show", "-s", "--format=%cI", "HEAD"]).strip()

    return {
        "branch": branch,
        "commit": commit,
        "commit_short": commit_short,
        "commit_time": commit_time,
    }


def _select_sources(
    sources: Iterable[GameSource],
    selected: Iterable[str] | None,
) -> list[GameSource]:
    src_list = list(sources)
    if not selected:
        return src_list

    selected_set = {x.strip() for x in selected if x.strip()}
    out: list[GameSource] = []
    for source in src_list:
        if source.id in selected_set or source.repo in selected_set:
            out.append(source)

    if not out:
        raise ValueError(
            "No matching sources. Pass source ids/repo names from DEFAULT_GAME_SOURCES."
        )
    return out


def sync_game_sources(
    dest_root: str | Path = "third_party_games",
    manifest_path: str | Path | None = None,
    selected_sources: Iterable[str] | None = None,
    sources: Iterable[GameSource] = DEFAULT_GAME_SOURCES,
) -> dict:
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    if manifest_path is None:
        manifest_path = dest_root / "sources.lock.json"
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    chosen = _select_sources(sources, selected_sources)

    synced: list[dict] = []
    for source in chosen:
        repo_url = _to_repo_url(source.repo)
        branch = _repo_default_branch(repo_url)
        local_dir = dest_root / source.id
        git_meta = _clone_or_update_repo(repo_url, local_dir, branch)

        synced.append(
            {
                "id": source.id,
                "repo": source.repo,
                "repo_url": repo_url,
                "description": source.description,
                "local_path": str(local_dir),
                "branch": git_meta["branch"],
                "commit": git_meta["commit"],
                "commit_short": git_meta["commit_short"],
                "commit_time": git_meta["commit_time"],
                "synced_at": _now_iso(),
            }
        )

    manifest = {
        "generated_at": _now_iso(),
        "dest_root": str(dest_root),
        "sources": synced,
        "count": len(synced),
    }

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "manifest_path": str(manifest_path),
        "dest_root": str(dest_root),
        "count": len(synced),
        "sources": synced,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sync_game_sources",
        description="Clone/update selected upstream MicroPython game sources and write a lock manifest.",
    )
    parser.add_argument("--dest-root", default="third_party_games")
    parser.add_argument("--manifest-path")
    parser.add_argument(
        "--source",
        action="append",
        help="Source id or owner/repo (repeatable). If omitted, sync all defaults.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = sync_game_sources(
        dest_root=args.dest_root,
        manifest_path=args.manifest_path,
        selected_sources=args.source,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
