from __future__ import annotations

import subprocess
from pathlib import Path

from circuithack.gamesync import GameSource, sync_game_sources


def _git(args: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout.strip()


def _create_remote_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote-games.git"
    _git(["init", "--bare", "--initial-branch=main", str(remote)])

    seed = tmp_path / "seed"
    _git(["clone", str(remote), str(seed)])
    _git(["config", "user.name", "Test User"], cwd=seed)
    _git(["config", "user.email", "test@example.com"], cwd=seed)

    (seed / "README.md").write_text("v1\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=seed)
    _git(["commit", "-m", "initial"], cwd=seed)
    _git(["push", "origin", "main"], cwd=seed)
    return remote, seed


def test_sync_game_sources_clones_and_writes_manifest(tmp_path: Path) -> None:
    remote, _seed = _create_remote_repo(tmp_path)

    source = GameSource(
        id="local-source",
        repo=str(remote),
        description="local fixture source",
    )

    result = sync_game_sources(
        dest_root=tmp_path / "third_party_games",
        sources=[source],
    )

    assert result["ok"] is True
    assert result["count"] == 1
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.exists()

    synced = result["sources"][0]
    assert synced["id"] == "local-source"
    assert synced["branch"] == "main"
    assert len(synced["commit"]) == 40

    local_clone = Path(synced["local_path"])
    assert (local_clone / "README.md").exists()


def test_sync_game_sources_updates_commit_on_remote_change(tmp_path: Path) -> None:
    remote, seed = _create_remote_repo(tmp_path)

    source = GameSource(
        id="local-source",
        repo=str(remote),
        description="local fixture source",
    )

    first = sync_game_sources(dest_root=tmp_path / "third_party_games", sources=[source])
    first_commit = first["sources"][0]["commit"]

    (seed / "README.md").write_text("v2\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=seed)
    _git(["commit", "-m", "update"], cwd=seed)
    _git(["push", "origin", "main"], cwd=seed)

    second = sync_game_sources(dest_root=tmp_path / "third_party_games", sources=[source])
    second_commit = second["sources"][0]["commit"]

    assert first_commit != second_commit


def test_sync_game_sources_filter_selects_subset(tmp_path: Path) -> None:
    remote, _seed = _create_remote_repo(tmp_path)

    sources = [
        GameSource(id="one", repo=str(remote), description="one"),
        GameSource(id="two", repo=str(remote), description="two"),
    ]

    result = sync_game_sources(
        dest_root=tmp_path / "third_party_games",
        sources=sources,
        selected_sources=["two"],
    )

    assert result["count"] == 1
    assert result["sources"][0]["id"] == "two"
