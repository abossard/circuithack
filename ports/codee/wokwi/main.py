from __future__ import annotations

import time
from machine import Pin, PWM

from codee import (
    BUTTON_A,
    BUTTON_B,
    BUTTON_C,
    BUTTON_D,
    CodeeAudio,
    CodeeDisplay,
    CodeeInput,
    CodeeLauncherApp,
    CodeeSave,
)

# Codee 2.0 pin map (Revision2) from Codee-Firmware main/src/Util/Pins.cpp.
PIN = {
    "BTN_A": 8,
    "BTN_B": 9,
    "BTN_C": 17,
    "BTN_D": 16,
    "BUZZ": 7,
}

buttons = {
    "A": Pin(PIN["BTN_A"], Pin.IN, Pin.PULL_UP),
    "B": Pin(PIN["BTN_B"], Pin.IN, Pin.PULL_UP),
    "C": Pin(PIN["BTN_C"], Pin.IN, Pin.PULL_UP),
    "D": Pin(PIN["BTN_D"], Pin.IN, Pin.PULL_UP),
}

buzzer = PWM(Pin(PIN["BUZZ"]))
buzzer.duty(0)


class ConsoleDisplayBackend:
    """Low-cost Wokwi backend: keeps game rendering API but outputs text to serial."""

    def __init__(self) -> None:
        self._text_ops = []
        self._last_print = time.ticks_ms()

    def fill(self, _color: int) -> None:
        self._text_ops = []

    def pixel(self, _x: int, _y: int, _color: int) -> None:
        return

    def rect(self, _x: int, _y: int, _w: int, _h: int, _color: int) -> None:
        return

    def fill_rect(self, _x: int, _y: int, _w: int, _h: int, _color: int) -> None:
        return

    def text(self, text: str, x: int, y: int, _color: int) -> None:
        self._text_ops.append((y, x, text))

    def show(self) -> None:
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_print) < 180:
            return
        self._last_print = now

        if not self._text_ops:
            return

        rows = sorted(self._text_ops, key=lambda item: (item[0], item[1]))
        preview = []
        for _y, _x, text in rows[:8]:
            preview.append(text)
        print(" | ".join(preview))



def tone(freq_hz: int, duration_ms: int) -> None:
    buzzer.freq(int(freq_hz))
    buzzer.duty(256)
    time.sleep_ms(int(duration_ms))
    buzzer.duty(0)



def button_mask() -> int:
    mask = 0
    if buttons["A"].value() == 0:
        mask |= BUTTON_A
    if buttons["B"].value() == 0:
        mask |= BUTTON_B
    if buttons["C"].value() == 0:
        mask |= BUTTON_C
    if buttons["D"].value() == 0:
        mask |= BUTTON_D
    return mask


backend = ConsoleDisplayBackend()
display = CodeeDisplay(backend, width=128, height=128)
inputs = CodeeInput(button_mask)
audio = CodeeAudio(tone)
save = CodeeSave("save/launcher.json")

app = CodeeLauncherApp(display=display, input_state=inputs, audio=audio, save=save)

print("=== Codee Port Wokwi Launcher ===")
print("Keys: A/S/D/F = buttons A/B/C/D")
print("Menu: A/B select, C or D start")
print("In game: hold A+C+D to return to menu")

while True:
    app.step()
    time.sleep_ms(50)
