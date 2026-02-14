from __future__ import annotations

import random
try:
    from typing import Iterable
except ImportError:  # MicroPython fallback
    Iterable = object  # type: ignore[assignment]

from .codee_audio import CodeeAudio
from .codee_display import BLACK, WHITE, CodeeDisplay, rgb565
from .codee_input import BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, CodeeInput
from .codee_save import CodeeSave

FILES = "abcdefgh"
RANKS = "87654321"

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000,
}

KNIGHT_OFFSETS = [
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
]

KING_OFFSETS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]

DIAGONAL_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ORTHO_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def side_of(piece: str) -> str:
    if piece == ".":
        return ""
    return "w" if piece.isupper() else "b"


def opposite(side: str) -> str:
    return "b" if side == "w" else "w"


def coords_to_square(x: int, y: int) -> str:
    return FILES[x] + str(8 - y)


def square_to_coords(square: str) -> tuple[int, int]:
    file_char = square[0].lower()
    rank_char = square[1]
    return FILES.index(file_char), 8 - int(rank_char)


class ChessModel:
    """Pure chess state and rules with a lightweight built-in AI."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self.board: list[list[str]] = []
        self.turn = "w"
        self.game_over = False
        self.result_text = ""
        self.last_move: tuple[int, int, int, int, str] | None = None
        self.reset()

    def reset(self) -> None:
        self.board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        self.turn = "w"
        self.game_over = False
        self.result_text = "White to move"
        self.last_move = None

    def to_dict(self) -> dict:
        return {
            "board": ["".join(row) for row in self.board],
            "turn": self.turn,
            "game_over": self.game_over,
            "result_text": self.result_text,
            "last_move": list(self.last_move) if self.last_move else None,
        }

    def from_dict(self, state: dict) -> None:
        board_rows = state.get("board")
        if isinstance(board_rows, list) and len(board_rows) == 8 and all(isinstance(r, str) and len(r) == 8 for r in board_rows):
            self.board = [list(r) for r in board_rows]
        else:
            self.reset()
            return

        turn = state.get("turn", "w")
        self.turn = "w" if turn != "b" else "b"
        self.game_over = bool(state.get("game_over", False))
        self.result_text = str(state.get("result_text", ""))

        last_move = state.get("last_move")
        if isinstance(last_move, list) and len(last_move) == 5:
            self.last_move = (
                int(last_move[0]),
                int(last_move[1]),
                int(last_move[2]),
                int(last_move[3]),
                str(last_move[4]),
            )
        else:
            self.last_move = None

    def piece_at(self, x: int, y: int, board: list[list[str]] | None = None) -> str:
        src = board if board is not None else self.board
        return src[y][x]

    def _slide_moves(
        self,
        board: list[list[str]],
        x: int,
        y: int,
        side: str,
        directions: Iterable[tuple[int, int]],
    ) -> list[tuple[int, int, int, int, str]]:
        moves: list[tuple[int, int, int, int, str]] = []
        for dx, dy in directions:
            nx = x + dx
            ny = y + dy
            while in_bounds(nx, ny):
                target = board[ny][nx]
                if target == ".":
                    moves.append((x, y, nx, ny, ""))
                else:
                    if side_of(target) != side:
                        moves.append((x, y, nx, ny, ""))
                    break
                nx += dx
                ny += dy
        return moves

    def _pseudo_moves_for_piece(
        self,
        board: list[list[str]],
        x: int,
        y: int,
    ) -> list[tuple[int, int, int, int, str]]:
        piece = board[y][x]
        if piece == ".":
            return []

        side = side_of(piece)
        p = piece.upper()
        moves: list[tuple[int, int, int, int, str]] = []

        if p == "P":
            direction = -1 if side == "w" else 1
            start_row = 6 if side == "w" else 1
            promotion_row = 0 if side == "w" else 7

            ny = y + direction
            if in_bounds(x, ny) and board[ny][x] == ".":
                prom = "Q" if ny == promotion_row else ""
                moves.append((x, y, x, ny, prom))
                if y == start_row:
                    ny2 = y + direction * 2
                    if in_bounds(x, ny2) and board[ny2][x] == ".":
                        moves.append((x, y, x, ny2, ""))

            for dx in (-1, 1):
                nx = x + dx
                ny = y + direction
                if not in_bounds(nx, ny):
                    continue
                target = board[ny][nx]
                if target != "." and side_of(target) != side:
                    prom = "Q" if ny == promotion_row else ""
                    moves.append((x, y, nx, ny, prom))

        elif p == "N":
            for dx, dy in KNIGHT_OFFSETS:
                nx = x + dx
                ny = y + dy
                if not in_bounds(nx, ny):
                    continue
                target = board[ny][nx]
                if target == "." or side_of(target) != side:
                    moves.append((x, y, nx, ny, ""))

        elif p == "B":
            moves.extend(self._slide_moves(board, x, y, side, DIAGONAL_DIRS))

        elif p == "R":
            moves.extend(self._slide_moves(board, x, y, side, ORTHO_DIRS))

        elif p == "Q":
            moves.extend(self._slide_moves(board, x, y, side, DIAGONAL_DIRS + ORTHO_DIRS))

        elif p == "K":
            for dx, dy in KING_OFFSETS:
                nx = x + dx
                ny = y + dy
                if not in_bounds(nx, ny):
                    continue
                target = board[ny][nx]
                if target == "." or side_of(target) != side:
                    moves.append((x, y, nx, ny, ""))

        return moves

    def _copy_board(self, board: list[list[str]]) -> list[list[str]]:
        return [row[:] for row in board]

    def _apply_move(
        self,
        board: list[list[str]],
        move: tuple[int, int, int, int, str],
    ) -> list[list[str]]:
        sx, sy, dx, dy, promotion = move
        next_board = self._copy_board(board)
        piece = next_board[sy][sx]
        next_board[sy][sx] = "."
        if promotion:
            piece = promotion if piece.isupper() else promotion.lower()
        next_board[dy][dx] = piece
        return next_board

    def _king_position(self, board: list[list[str]], side: str) -> tuple[int, int] | None:
        target = "K" if side == "w" else "k"
        for y in range(8):
            for x in range(8):
                if board[y][x] == target:
                    return x, y
        return None

    def _square_attacked(self, board: list[list[str]], x: int, y: int, by_side: str) -> bool:
        pawn_dir = -1 if by_side == "w" else 1
        pawn_piece = "P" if by_side == "w" else "p"
        for dx in (-1, 1):
            px = x + dx
            py = y + pawn_dir
            if in_bounds(px, py) and board[py][px] == pawn_piece:
                return True

        knight_piece = "N" if by_side == "w" else "n"
        for dx, dy in KNIGHT_OFFSETS:
            nx = x + dx
            ny = y + dy
            if in_bounds(nx, ny) and board[ny][nx] == knight_piece:
                return True

        bishop_piece = "B" if by_side == "w" else "b"
        rook_piece = "R" if by_side == "w" else "r"
        queen_piece = "Q" if by_side == "w" else "q"
        king_piece = "K" if by_side == "w" else "k"

        for dx, dy in DIAGONAL_DIRS:
            nx = x + dx
            ny = y + dy
            while in_bounds(nx, ny):
                p = board[ny][nx]
                if p != ".":
                    if p in {bishop_piece, queen_piece}:
                        return True
                    break
                nx += dx
                ny += dy

        for dx, dy in ORTHO_DIRS:
            nx = x + dx
            ny = y + dy
            while in_bounds(nx, ny):
                p = board[ny][nx]
                if p != ".":
                    if p in {rook_piece, queen_piece}:
                        return True
                    break
                nx += dx
                ny += dy

        for dx, dy in KING_OFFSETS:
            nx = x + dx
            ny = y + dy
            if in_bounds(nx, ny) and board[ny][nx] == king_piece:
                return True

        return False

    def _is_in_check(self, board: list[list[str]], side: str) -> bool:
        king = self._king_position(board, side)
        if king is None:
            return True
        return self._square_attacked(board, king[0], king[1], opposite(side))

    def _all_legal_moves(
        self,
        board: list[list[str]],
        side: str,
    ) -> list[tuple[int, int, int, int, str]]:
        legal: list[tuple[int, int, int, int, str]] = []
        for y in range(8):
            for x in range(8):
                piece = board[y][x]
                if piece == "." or side_of(piece) != side:
                    continue
                for move in self._pseudo_moves_for_piece(board, x, y):
                    candidate = self._apply_move(board, move)
                    if not self._is_in_check(candidate, side):
                        legal.append(move)
        return legal

    def legal_moves_for_color(self, side: str) -> list[tuple[int, int, int, int, str]]:
        return self._all_legal_moves(self.board, side)

    def legal_moves_from(self, x: int, y: int) -> list[tuple[int, int, int, int, str]]:
        piece = self.board[y][x]
        if piece == "." or side_of(piece) != self.turn:
            return []
        return [m for m in self._all_legal_moves(self.board, self.turn) if m[0] == x and m[1] == y]

    def _material_score(self, board: list[list[str]]) -> int:
        score = 0
        for row in board:
            for piece in row:
                if piece == ".":
                    continue
                value = PIECE_VALUES[piece.upper()]
                score += value if piece.isupper() else -value
        return score

    def _evaluate(self, board: list[list[str]]) -> int:
        score = self._material_score(board)
        white_mobility = len(self._all_legal_moves(board, "w"))
        black_mobility = len(self._all_legal_moves(board, "b"))
        score += (white_mobility - black_mobility) * 2
        return score

    def _search(
        self,
        board: list[list[str]],
        side: str,
        depth: int,
        alpha: int,
        beta: int,
    ) -> int:
        legal = self._all_legal_moves(board, side)
        if depth == 0 or not legal:
            base = self._evaluate(board)
            if not legal:
                if self._is_in_check(board, side):
                    mate_value = -100000 + (2 - depth)
                    return mate_value
                return 0
            return base if side == "w" else -base

        best = -10**9
        for move in legal:
            child = self._apply_move(board, move)
            score = -self._search(child, opposite(side), depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    def _pick_ai_move(self, depth: int = 2) -> tuple[int, int, int, int, str] | None:
        legal = self._all_legal_moves(self.board, self.turn)
        if not legal:
            return None

        self._rng.shuffle(legal)
        best_score = -10**9
        best_move: tuple[int, int, int, int, str] | None = None

        for move in legal:
            child = self._apply_move(self.board, move)
            score = -self._search(child, opposite(self.turn), depth - 1, -10**9, 10**9)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _update_result_state(self) -> None:
        legal = self._all_legal_moves(self.board, self.turn)
        if legal:
            self.game_over = False
            self.result_text = ("White" if self.turn == "w" else "Black") + " to move"
            return

        self.game_over = True
        if self._is_in_check(self.board, self.turn):
            winner = "Black" if self.turn == "w" else "White"
            self.result_text = f"Checkmate: {winner} wins"
        else:
            self.result_text = "Stalemate"

    def _apply_to_model(self, move: tuple[int, int, int, int, str]) -> None:
        self.board = self._apply_move(self.board, move)
        self.last_move = move
        self.turn = opposite(self.turn)
        self._update_result_state()

    def try_player_move(self, sx: int, sy: int, dx: int, dy: int) -> bool:
        if self.game_over or self.turn != "w":
            return False

        legal = self.legal_moves_from(sx, sy)
        chosen: tuple[int, int, int, int, str] | None = None
        for move in legal:
            if move[2] == dx and move[3] == dy:
                chosen = move
                break
        if chosen is None:
            return False

        self._apply_to_model(chosen)
        return True

    def ai_move(self, depth: int = 2) -> tuple[int, int, int, int, str] | None:
        if self.game_over or self.turn != "b":
            return None

        move = self._pick_ai_move(depth=depth)
        if move is None:
            self._update_result_state()
            return None

        self._apply_to_model(move)
        return move


class ChessApp:
    """Codee UI shell around ChessModel."""

    def __init__(
        self,
        display: CodeeDisplay,
        input_state: CodeeInput,
        audio: CodeeAudio,
        save: CodeeSave,
        seed: int | None = None,
    ) -> None:
        self.display = display
        self.input = input_state
        self.audio = audio
        self.save = save

        self.model = ChessModel(seed=seed)
        self.cursor_x = 4
        self.cursor_y = 6
        self.selected: tuple[int, int] | None = None
        self.wants_exit = False

        self._exit_frames = 0
        self._combo_frames: dict[str, int] = {}
        self._combo_latched: dict[str, bool] = {}

        state = self.save.load(default={})
        if state:
            self.model.from_dict(state)

    def _persist(self) -> None:
        self.save.save(self.model.to_dict())

    def _update_exit_combo(self) -> None:
        active = (
            self.input.pressed(BUTTON_A)
            and self.input.pressed(BUTTON_C)
            and self.input.pressed(BUTTON_D)
        )
        if not active:
            self._exit_frames = 0
            return

        self._exit_frames += 1
        if self._exit_frames >= 8:
            self.wants_exit = True

    def _move_cursor(self, dx: int, dy: int) -> None:
        self.cursor_x = (self.cursor_x + dx) % 8
        self.cursor_y = (self.cursor_y + dy) % 8

    def _combo_ready(self, name: str, active: bool, threshold: int) -> bool:
        if not active:
            self._combo_frames[name] = 0
            self._combo_latched[name] = False
            return False

        self._combo_frames[name] = self._combo_frames.get(name, 0) + 1
        if self._combo_frames[name] < threshold:
            return False

        if self._combo_latched.get(name, False):
            return False

        self._combo_latched[name] = True
        return True

    def _handle_select_or_move(self) -> None:
        if self.model.turn != "w" or self.model.game_over:
            return

        piece = self.model.piece_at(self.cursor_x, self.cursor_y)
        if self.selected is None:
            if piece != "." and piece.isupper():
                self.selected = (self.cursor_x, self.cursor_y)
                self.audio.move_sound()
            return

        sx, sy = self.selected
        if sx == self.cursor_x and sy == self.cursor_y:
            self.selected = None
            return

        moved = self.model.try_player_move(sx, sy, self.cursor_x, self.cursor_y)
        if not moved:
            self.audio.tone(260, 45)
            return

        self.selected = None
        self._persist()
        self.audio.merge_sound()

        ai_move = self.model.ai_move(depth=2)
        if ai_move is not None:
            self.audio.tone(700, 40)
            self._persist()

    def step(self) -> None:
        self.input.update()
        self._update_exit_combo()
        if self.wants_exit:
            return

        if (
            self.input.just_pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_D)
        ):
            self._move_cursor(-1, 0)
        elif (
            self.input.just_pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_D)
        ):
            self._move_cursor(1, 0)
        elif (
            self.input.just_pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_D)
        ):
            self._move_cursor(0, -1)
        elif (
            self.input.just_pressed(BUTTON_D)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_C)
        ):
            self._move_cursor(0, 1)

        if self._combo_ready(
            "select_or_move",
            self.input.pressed(BUTTON_A) and self.input.pressed(BUTTON_B),
            threshold=3,
        ):
            self._handle_select_or_move()

        if self._combo_ready(
            "cancel_select",
            self.input.pressed(BUTTON_C) and self.input.pressed(BUTTON_D),
            threshold=3,
        ) and self.selected is not None:
            self.selected = None

        self.render()

    def render(self) -> None:
        bg = rgb565(20, 23, 31)
        light = rgb565(223, 216, 199)
        dark = rgb565(97, 123, 82)
        sel = rgb565(75, 152, 214)
        cursor = rgb565(236, 207, 64)

        self.display.clear(bg)
        self.display.text("Chess", 2, 2, WHITE)

        turn_text = "White" if self.model.turn == "w" else "Black"
        self.display.text(turn_text, 64, 2, WHITE)

        board_x = 8
        board_y = 12
        cell = 14

        for y in range(8):
            for x in range(8):
                base = light if (x + y) % 2 == 0 else dark
                x0 = board_x + x * cell
                y0 = board_y + y * cell
                self.display.fill_rect(x0, y0, cell, cell, base)

                if self.selected == (x, y):
                    self.display.rect(x0 + 1, y0 + 1, cell - 2, cell - 2, sel)

                piece = self.model.piece_at(x, y)
                if piece != ".":
                    glyph = piece.upper()
                    fg = BLACK if piece.isupper() else WHITE
                    self.display.text(glyph, x0 + 3, y0 + 3, fg)

        cx = board_x + self.cursor_x * cell
        cy = board_y + self.cursor_y * cell
        self.display.rect(cx, cy, cell, cell, cursor)

        help_line = "AB select CD cancel"
        self.display.text(help_line[:20], 2, 116, WHITE)

        status = self.model.result_text
        self.display.text(status[:20], 2, 124, WHITE)

        if self.model.game_over:
            self.display.fill_rect(10, 52, 108, 20, rgb565(170, 60, 60))
            self.display.center_text("GAME OVER", 58, WHITE)

        self.display.present()
