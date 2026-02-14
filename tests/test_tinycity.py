import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ports.codee import (
    BUTTON_A,
    BUTTON_C,
    BUTTON_D,
    CodeeAudio,
    CodeeDisplay,
    CodeeInput,
    CodeeSave,
    MemoryDisplayBackend,
    TinyCityApp,
    TinyCityModel,
)
from ports.codee.game_tinycity import TILE_EMPTY, TOOL_RESIDENTIAL


def test_tinycity_model_build_and_end_year() -> None:
    model = TinyCityModel(width=4, height=4, seed=1)
    model.tiles = [[TILE_EMPTY for _ in range(4)] for _ in range(4)]
    model.zone_level = [[0 for _ in range(4)] for _ in range(4)]
    model.cursor_x = 1
    model.cursor_y = 1
    model.set_tool(TOOL_RESIDENTIAL)

    money_before = model.money
    ok, _ = model.place_current_tool()

    assert ok is True
    assert model.money < money_before
    assert model.tiles[1][1] == TOOL_RESIDENTIAL

    summary = model.end_year()
    assert summary["year"] == 2
    assert summary["population"] >= 6


def test_tinycity_app_exit_combo_sets_wants_exit(tmp_path: Path) -> None:
    backend = MemoryDisplayBackend(128, 128)
    display = CodeeDisplay(backend)

    masks = [BUTTON_A | BUTTON_C | BUTTON_D] * 8

    def poll() -> int:
        return masks.pop(0) if masks else 0

    app = TinyCityApp(
        display=display,
        input_state=CodeeInput(poll),
        audio=CodeeAudio(),
        save=CodeeSave(str(tmp_path / "tinycity.json")),
        seed=3,
    )

    for _ in range(8):
        app.step()

    assert app.wants_exit is True
