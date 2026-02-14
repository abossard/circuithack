from __future__ import annotations

import random
import time

from .codee_audio import CodeeAudio
from .codee_display import BLACK, WHITE, CodeeDisplay, rgb565
from .codee_input import BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, CodeeInput
from .codee_save import CodeeSave


class Game2048Model:
    def __init__(self, size: int = 4, seed: int | None = None) -> None:
        self.size = size
        self.score = 0
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        self.game_over = False
        self._rng = random.Random(seed)

    def reset(self) -> None:
        self.score = 0
        self.game_over = False
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self._spawn_tile()
        self._spawn_tile()

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "score": self.score,
            "board": self.board,
            "game_over": self.game_over,
        }

    def from_dict(self, state: dict) -> None:
        if not state:
            self.reset()
            return
        self.size = int(state.get("size", self.size))
        self.score = int(state.get("score", 0))
        board = state.get("board")
        if isinstance(board, list) and len(board) == self.size:
            self.board = [list(row)[: self.size] for row in board]
        else:
            self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.game_over = bool(state.get("game_over", False))

    def _empty_cells(self) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] == 0:
                    out.append((x, y))
        return out

    def _spawn_tile(self) -> bool:
        empties = self._empty_cells()
        if not empties:
            return False
        x, y = self._rng.choice(empties)
        self.board[y][x] = 4 if self._rng.random() < 0.1 else 2
        return True

    @staticmethod
    def _collapse_line(line: list[int]) -> tuple[list[int], int]:
        compact = [value for value in line if value != 0]
        merged: list[int] = []
        score_add = 0
        i = 0
        while i < len(compact):
            cur = compact[i]
            if i + 1 < len(compact) and compact[i + 1] == cur:
                cur *= 2
                score_add += cur
                i += 1
            merged.append(cur)
            i += 1
        merged.extend([0] * (len(line) - len(merged)))
        return merged, score_add

    def _can_move(self) -> bool:
        if self._empty_cells():
            return True
        for y in range(self.size):
            for x in range(self.size):
                v = self.board[y][x]
                if x + 1 < self.size and self.board[y][x + 1] == v:
                    return True
                if y + 1 < self.size and self.board[y + 1][x] == v:
                    return True
        return False

    def move(self, direction: str) -> tuple[bool, int]:
        if self.game_over:
            return False, 0

        if direction not in {"left", "right", "up", "down"}:
            raise ValueError(f"Unsupported direction: {direction}")

        before = [row[:] for row in self.board]
        total_score_add = 0

        if direction in {"left", "right"}:
            for y in range(self.size):
                line = self.board[y][:]
                if direction == "right":
                    line.reverse()
                collapsed, score_add = self._collapse_line(line)
                if direction == "right":
                    collapsed.reverse()
                self.board[y] = collapsed
                total_score_add += score_add
        else:
            for x in range(self.size):
                line = [self.board[y][x] for y in range(self.size)]
                if direction == "down":
                    line.reverse()
                collapsed, score_add = self._collapse_line(line)
                if direction == "down":
                    collapsed.reverse()
                for y in range(self.size):
                    self.board[y][x] = collapsed[y]
                total_score_add += score_add

        changed = self.board != before
        if changed:
            self.score += total_score_add
            self._spawn_tile()
            self.game_over = not self._can_move()
        else:
            self.game_over = not self._can_move()
        return changed, total_score_add


class Game2048App:
    def __init__(
        self,
        display: CodeeDisplay,
        input_state: CodeeInput,
        audio: CodeeAudio,
        save: CodeeSave,
    ) -> None:
        self.display = display
        self.input = input_state
        self.audio = audio
        self.save = save

        self.model = Game2048Model()
        self._load_or_reset()

    def _load_or_reset(self) -> None:
        state = self.save.load(default={})
        if not state:
            self.model.reset()
            return
        self.model.from_dict(state)
        if not self.model._can_move() and not self.model._empty_cells():
            self.model.game_over = True

    def _persist(self) -> None:
        self.save.save(self.model.to_dict())

    def step(self) -> bool:
        self.input.update()

        direction = None
        if self.input.just_pressed(BUTTON_A):
            direction = "left"
        elif self.input.just_pressed(BUTTON_B):
            direction = "right"
        elif self.input.just_pressed(BUTTON_C):
            direction = "up"
        elif self.input.just_pressed(BUTTON_D):
            direction = "down"

        moved = False
        if direction is not None:
            moved, merged_score = self.model.move(direction)
            if moved:
                self.audio.move_sound()
                if merged_score > 0:
                    self.audio.merge_sound()
                self._persist()
            if self.model.game_over:
                self.audio.game_over_sound()

        self.render()
        return moved

    def render(self) -> None:
        bg = rgb565(22, 24, 34)
        grid_bg = rgb565(37, 40, 54)
        cell_empty = rgb565(63, 68, 90)

        self.display.clear(bg)
        self.display.text(f"2048  SCORE:{self.model.score}", 2, 2, WHITE)

        board_x = 6
        board_y = 18
        cell_size = 28
        pad = 2

        self.display.fill_rect(board_x, board_y, 116, 116, grid_bg)
        for y in range(self.model.size):
            for x in range(self.model.size):
                value = self.model.board[y][x]
                x0 = board_x + x * (cell_size + pad)
                y0 = board_y + y * (cell_size + pad)
                color = self._tile_color(value) if value else cell_empty
                self.display.fill_rect(x0, y0, cell_size, cell_size, color)
                if value:
                    text = str(value)
                    tx = x0 + max(2, (cell_size - len(text) * 8) // 2)
                    ty = y0 + (cell_size - 8) // 2
                    self.display.text(text, tx, ty, BLACK)

        if self.model.game_over:
            self.display.fill_rect(10, 52, 108, 24, rgb565(180, 65, 65))
            self.display.center_text("GAME OVER", 60, WHITE)

        self.display.present()

    @staticmethod
    def _tile_color(value: int) -> int:
        palette = {
            2: rgb565(238, 228, 218),
            4: rgb565(237, 224, 200),
            8: rgb565(242, 177, 121),
            16: rgb565(245, 149, 99),
            32: rgb565(246, 124, 95),
            64: rgb565(246, 94, 59),
            128: rgb565(237, 207, 114),
            256: rgb565(237, 204, 97),
            512: rgb565(237, 200, 80),
            1024: rgb565(237, 197, 63),
            2048: rgb565(237, 194, 46),
        }
        return palette.get(value, rgb565(60, 58, 50))


def run_loop(app: Game2048App, tick_ms: int = 50) -> None:
    while True:
        app.step()
        time.sleep(tick_ms / 1000)
