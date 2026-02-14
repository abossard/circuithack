import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ports.codee import (
    BUTTON_A,
    BUTTON_B,
    BUTTON_C,
    BUTTON_D,
    CodeeAudio,
    CodeeDisplay,
    CodeeInput,
    CodeeLauncherApp,
    CodeeSave,
    MemoryDisplayBackend,
)


def test_launcher_menu_navigation_and_start_game(tmp_path: Path) -> None:
    backend = MemoryDisplayBackend(128, 128)
    display = CodeeDisplay(backend)

    masks = [BUTTON_B, 0, BUTTON_C, 0]

    def poll() -> int:
        return masks.pop(0) if masks else 0

    app = CodeeLauncherApp(
        display=display,
        input_state=CodeeInput(poll),
        audio=CodeeAudio(),
        save=CodeeSave(str(tmp_path / "launcher.json")),
        seed=99,
    )

    app.step()
    assert app.menu.selected.game_id == "tinycity"

    app.step()
    app.step()
    assert app._active_game_id == "tinycity"


def test_launcher_ingame_exit_combo_returns_to_menu(tmp_path: Path) -> None:
    backend = MemoryDisplayBackend(128, 128)
    display = CodeeDisplay(backend)

    masks = [BUTTON_C, 0] + [BUTTON_A | BUTTON_C | BUTTON_D] * 8

    def poll() -> int:
        return masks.pop(0) if masks else 0

    app = CodeeLauncherApp(
        display=display,
        input_state=CodeeInput(poll),
        audio=CodeeAudio(),
        save=CodeeSave(str(tmp_path / "launcher.json")),
        seed=99,
    )

    app.step()
    app.step()
    assert app._active_game_id == "2048"

    for _ in range(8):
        app.step()

    assert app._active_game is None
    assert app._active_game_id == ""
