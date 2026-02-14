from __future__ import annotations

from dataclasses import dataclass, field


WHITE = 0xFFFF
BLACK = 0x0000


def rgb565(r: int, g: int, b: int) -> int:
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


@dataclass
class MemoryDisplayBackend:
    width: int = 128
    height: int = 128
    operations: list[tuple] = field(default_factory=list)

    def fill(self, color: int) -> None:
        self.operations.append(("fill", color))

    def pixel(self, x: int, y: int, color: int) -> None:
        self.operations.append(("pixel", x, y, color))

    def rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        self.operations.append(("rect", x, y, w, h, color))

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        self.operations.append(("fill_rect", x, y, w, h, color))

    def text(self, text: str, x: int, y: int, color: int) -> None:
        self.operations.append(("text", text, x, y, color))

    def show(self) -> None:
        self.operations.append(("show",))


class CodeeDisplay:
    """Display adapter used by Codee MicroPython game ports.

    The backend should expose a minimal API compatible with common MicroPython
    framebuffer/display drivers: `fill`, `pixel`, `rect`, `fill_rect`, `text`, `show`.
    """

    def __init__(self, backend: object, width: int = 128, height: int = 128) -> None:
        self.backend = backend
        self.width = width
        self.height = height

    def clear(self, color: int = BLACK) -> None:
        self.backend.fill(color)

    def pixel(self, x: int, y: int, color: int) -> None:
        self.backend.pixel(x, y, color)

    def rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        self.backend.rect(x, y, w, h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        self.backend.fill_rect(x, y, w, h, color)

    def text(self, text: str, x: int, y: int, color: int = WHITE) -> None:
        self.backend.text(text, x, y, color)

    def center_text(self, text: str, y: int, color: int = WHITE) -> None:
        # MicroPython bitmap fonts are commonly 8px wide.
        x = max(0, (self.width - len(text) * 8) // 2)
        self.text(text, x, y, color)

    def present(self) -> None:
        show = getattr(self.backend, "show", None)
        if callable(show):
            show()
