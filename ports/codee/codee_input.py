from __future__ import annotations

from typing import Callable


BUTTON_A = 1 << 0
BUTTON_B = 1 << 1
BUTTON_C = 1 << 2
BUTTON_D = 1 << 3


class CodeeInput:
    """Button-state helper.

    `poll_mask` should return a bitmask using BUTTON_A/B/C/D flags.
    """

    def __init__(self, poll_mask: Callable[[], int]) -> None:
        self._poll_mask = poll_mask
        self._current = 0
        self._previous = 0

    def update(self) -> int:
        self._previous = self._current
        self._current = int(self._poll_mask()) & (BUTTON_A | BUTTON_B | BUTTON_C | BUTTON_D)
        return self._current

    def pressed(self, button: int) -> bool:
        return bool(self._current & button)

    def just_pressed(self, button: int) -> bool:
        return bool((self._current & button) and not (self._previous & button))

    def just_released(self, button: int) -> bool:
        return bool((self._previous & button) and not (self._current & button))


def mask_from_bools(a: bool, b: bool, c: bool, d: bool) -> int:
    return (
        (BUTTON_A if a else 0)
        | (BUTTON_B if b else 0)
        | (BUTTON_C if c else 0)
        | (BUTTON_D if d else 0)
    )
