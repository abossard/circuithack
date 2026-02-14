import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ports.codee import (
    BUTTON_A,
    CodeeAudio,
    CodeeDisplay,
    CodeeInput,
    CodeeSave,
    Game2048App,
    Game2048Model,
    MemoryDisplayBackend,
)


def test_model_reset_starts_with_two_tiles() -> None:
    model = Game2048Model(seed=7)
    model.reset()
    non_zero = sum(1 for row in model.board for value in row if value != 0)
    assert non_zero == 2


def test_model_move_left_merges_once_per_pair() -> None:
    model = Game2048Model(seed=1)
    model.board = [
        [2, 2, 4, 4],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    model.score = 0
    model.game_over = False
    model._spawn_tile = lambda: True  # type: ignore[method-assign]

    changed, merged_score = model.move("left")

    assert changed is True
    assert merged_score == 12
    assert model.score == 12
    assert model.board[0] == [4, 8, 0, 0]


def test_model_sets_game_over_when_no_moves_available() -> None:
    model = Game2048Model(seed=2)
    model.board = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    model.game_over = False

    changed, _ = model.move("left")

    assert changed is False
    assert model.game_over is True


def test_app_step_moves_and_persists(tmp_path: Path) -> None:
    backend = MemoryDisplayBackend(128, 128)
    display = CodeeDisplay(backend)

    masks = [BUTTON_A, 0]

    def poll() -> int:
        return masks.pop(0) if masks else 0

    inputs = CodeeInput(poll)

    played: list[tuple[int, int]] = []
    audio = CodeeAudio(lambda hz, ms: played.append((hz, ms)))
    save = CodeeSave(str(tmp_path / "game_2048.json"))

    app = Game2048App(display=display, input_state=inputs, audio=audio, save=save)
    app.model.board = [
        [0, 2, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    app.model._spawn_tile = lambda: True  # type: ignore[method-assign]

    moved = app.step()

    assert moved is True
    assert app.model.board[0][0] == 2
    assert save.path.exists()
    assert played
    assert backend.operations[-1] == ("show",)
