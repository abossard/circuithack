import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ports.codee import (
    BUTTON_A,
    BUTTON_B,
    CodeeAudio,
    CodeeDisplay,
    CodeeInput,
    CodeeSave,
    ChessApp,
    ChessModel,
    MemoryDisplayBackend,
)


def test_chess_model_opening_has_20_legal_white_moves() -> None:
    model = ChessModel(seed=7)
    assert len(model.legal_moves_for_color("w")) == 20


def test_chess_model_player_then_ai_move() -> None:
    model = ChessModel(seed=7)

    moved = model.try_player_move(4, 6, 4, 4)  # e2 -> e4

    assert moved is True
    assert model.turn == "b"

    ai = model.ai_move(depth=1)
    assert ai is not None
    assert model.turn == "w"


def test_chess_app_button_b_moves_cursor_only(tmp_path: Path) -> None:
    backend = MemoryDisplayBackend(128, 128)
    display = CodeeDisplay(backend)

    masks = [BUTTON_B, 0]

    def poll() -> int:
        return masks.pop(0) if masks else 0

    app = ChessApp(
        display=display,
        input_state=CodeeInput(poll),
        audio=CodeeAudio(),
        save=CodeeSave(str(tmp_path / "chess.json")),
        seed=11,
    )

    start_x = app.cursor_x
    app.step()

    assert app.cursor_x == (start_x + 1) % 8
    assert app.selected is None


def test_chess_app_combo_ab_selects_piece(tmp_path: Path) -> None:
    backend = MemoryDisplayBackend(128, 128)
    display = CodeeDisplay(backend)

    masks = [BUTTON_A | BUTTON_B] * 3 + [0]

    def poll() -> int:
        return masks.pop(0) if masks else 0

    app = ChessApp(
        display=display,
        input_state=CodeeInput(poll),
        audio=CodeeAudio(),
        save=CodeeSave(str(tmp_path / "chess.json")),
        seed=11,
    )

    for _ in range(3):
        app.step()

    assert app.selected == (4, 6)
