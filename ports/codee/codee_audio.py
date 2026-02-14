from __future__ import annotations

import time
from typing import Callable


class CodeeAudio:
    """Simple tone wrapper with optional effect helpers."""

    def __init__(self, tone_callback: Callable[[int, int], None] | None = None) -> None:
        self._tone_callback = tone_callback

    def tone(self, frequency_hz: int, duration_ms: int = 80) -> None:
        if self._tone_callback:
            self._tone_callback(int(frequency_hz), int(duration_ms))
            return
        time.sleep(duration_ms / 1000)

    def move_sound(self) -> None:
        self.tone(880, 35)

    def merge_sound(self) -> None:
        self.tone(1200, 25)
        self.tone(1500, 25)

    def game_over_sound(self) -> None:
        self.tone(440, 80)
        self.tone(330, 100)
        self.tone(220, 120)
