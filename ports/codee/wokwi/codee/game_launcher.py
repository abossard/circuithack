from __future__ import annotations

import random
import time

from .codee_audio import CodeeAudio
from .codee_display import BLACK, WHITE, CodeeDisplay, rgb565
from .codee_input import BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, CodeeInput
from .codee_save import CodeeSave
from .game_2048 import Game2048App
from .game_chess import ChessApp
from .game_tinycity import TinyCityApp


class LauncherEntry:
    def __init__(self, game_id: str, title: str) -> None:
        self.game_id = game_id
        self.title = title


class LauncherMenuModel:
    """Pure menu state for the Codee launcher."""

    def __init__(self, entries: list[LauncherEntry]) -> None:
        if not entries:
            raise ValueError("Launcher requires at least one entry")
        self.entries = entries
        self.selected_index = 0

    @property
    def selected(self) -> LauncherEntry:
        return self.entries[self.selected_index]

    def move(self, step: int) -> None:
        self.selected_index = (self.selected_index + step) % len(self.entries)

    def to_dict(self) -> dict:
        return {"selected_index": self.selected_index}

    def from_dict(self, state: dict) -> None:
        idx = int(state.get("selected_index", 0))
        self.selected_index = idx % len(self.entries)


class CodeeLauncherApp:
    """Launcher shell that hosts multiple Codee game apps."""

    def __init__(
        self,
        display: CodeeDisplay,
        input_state: CodeeInput,
        audio: CodeeAudio,
        save: CodeeSave | None = None,
        seed: int | None = None,
    ) -> None:
        self.display = display
        self.input = input_state
        self.audio = audio

        self.menu_save = save if save is not None else CodeeSave("save/launcher.json")
        self._save_dir = self.menu_save.path.parent

        self._rng = random.Random(seed)
        self.menu = LauncherMenuModel(
            [
                LauncherEntry("2048", "2048"),
                LauncherEntry("tinycity", "TinyCity"),
                LauncherEntry("chess", "Chess"),
            ]
        )

        state = self.menu_save.load(default={})
        if state:
            self.menu.from_dict(state)

        self._active_game: Game2048App | TinyCityApp | ChessApp | None = None
        self._active_game_id = ""
        self._ingame_exit_frames = 0

    def _persist_menu(self) -> None:
        self.menu_save.save(self.menu.to_dict())

    def _new_game_save(self, game_id: str) -> CodeeSave:
        return CodeeSave(str(self._save_dir / f"{game_id}.json"))

    def _next_seed(self) -> int:
        return self._rng.randint(0, 2**31 - 1)

    def _start_selected_game(self) -> None:
        game_id = self.menu.selected.game_id
        self._active_game_id = game_id
        self._ingame_exit_frames = 0

        if game_id == "2048":
            self._active_game = Game2048App(
                display=self.display,
                input_state=self.input,
                audio=self.audio,
                save=self._new_game_save(game_id),
            )
        elif game_id == "tinycity":
            self._active_game = TinyCityApp(
                display=self.display,
                input_state=self.input,
                audio=self.audio,
                save=self._new_game_save(game_id),
                seed=self._next_seed(),
            )
        else:
            self._active_game = ChessApp(
                display=self.display,
                input_state=self.input,
                audio=self.audio,
                save=self._new_game_save(game_id),
                seed=self._next_seed(),
            )

        self.audio.tone(1040, 30)

    def _return_to_menu(self) -> None:
        self._active_game = None
        self._active_game_id = ""
        self._ingame_exit_frames = 0
        self.audio.tone(540, 30)

    def _ingame_exit_combo_active(self) -> bool:
        return (
            self.input.pressed(BUTTON_A)
            and self.input.pressed(BUTTON_C)
            and self.input.pressed(BUTTON_D)
        )

    def _update_ingame_exit(self) -> bool:
        if not self._ingame_exit_combo_active():
            self._ingame_exit_frames = 0
            return False

        self._ingame_exit_frames += 1
        return self._ingame_exit_frames >= 8

    def _step_menu(self) -> None:
        self.input.update()

        if (
            self.input.just_pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_D)
        ):
            self.menu.move(-1)
            self.audio.move_sound()
            self._persist_menu()
        elif (
            self.input.just_pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_D)
        ):
            self.menu.move(1)
            self.audio.move_sound()
            self._persist_menu()

        if (
            self.input.just_pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_D)
        ) or (
            self.input.just_pressed(BUTTON_D)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_C)
        ):
            self._start_selected_game()
            return

        self.render_menu()

    def _step_active_game(self) -> None:
        if self._active_game is None:
            return

        self._active_game.step()

        child_exit = bool(getattr(self._active_game, "wants_exit", False))
        if child_exit or self._update_ingame_exit():
            self._return_to_menu()
            self.render_menu()

    def step(self) -> None:
        if self._active_game is None:
            self._step_menu()
            return
        self._step_active_game()

    def render_menu(self) -> None:
        bg = rgb565(12, 17, 28)
        panel = rgb565(22, 37, 54)
        selected_bg = rgb565(236, 196, 63)

        self.display.clear(bg)
        self.display.center_text("Codee Launcher", 4, WHITE)

        self.display.fill_rect(8, 18, self.display.width - 16, 72, panel)

        for idx, entry in enumerate(self.menu.entries):
            y = 24 + idx * 20
            selected = idx == self.menu.selected_index
            if selected:
                self.display.fill_rect(12, y - 2, self.display.width - 24, 16, selected_bg)
            color = BLACK if selected else WHITE
            label = f"{idx + 1}. {entry.title}"
            self.display.text(label, 16, y, color)

        self.display.text("A/B select", 8, 98, WHITE)
        self.display.text("C or D start", 8, 108, WHITE)
        self.display.text("ACD hold: back", 8, 118, WHITE)

        self.display.present()



def run_loop(app: CodeeLauncherApp, tick_ms: int = 50) -> None:
    while True:
        app.step()
        time.sleep(tick_ms / 1000)
