import random
import time
from machine import Pin, PWM, SPI

# Codee 2.0 pin map (Revision2) from Codee-Firmware main/src/Util/Pins.cpp.
PIN = {
    "BTN_A": 8,
    "BTN_B": 9,
    "BTN_C": 17,
    "BTN_D": 16,
    "BUZZ": 7,
    "TFT_SCK": 2,
    "TFT_MOSI": 3,
    "TFT_DC": 4,
    "TFT_CS": 6,
    "TFT_MISO": 1,
}

buttons = {
    "A": Pin(PIN["BTN_A"], Pin.IN, Pin.PULL_UP),
    "B": Pin(PIN["BTN_B"], Pin.IN, Pin.PULL_UP),
    "C": Pin(PIN["BTN_C"], Pin.IN, Pin.PULL_UP),
    "D": Pin(PIN["BTN_D"], Pin.IN, Pin.PULL_UP),
}

buzzer = PWM(Pin(PIN["BUZZ"]))
buzzer.duty(0)


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ILI9341:
    def __init__(self, spi, dc, cs, width=240, height=320):
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.width = width
        self.height = height
        self.cs(1)
        self.dc(1)
        self._init()

    def _write_cmd(self, cmd):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def _write_data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def _init(self):
        self._write_cmd(0x01)  # SWRESET
        time.sleep_ms(150)
        self._write_cmd(0x11)  # SLPOUT
        time.sleep_ms(120)
        self._write_cmd(0x3A)  # COLMOD
        self._write_data(b"\x55")  # 16-bit
        self._write_cmd(0x36)  # MADCTL
        self._write_data(b"\x48")
        self._write_cmd(0x29)  # DISPON
        time.sleep_ms(20)

    def _set_window(self, x0, y0, x1, y1):
        self._write_cmd(0x2A)
        self._write_data(bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._write_cmd(0x2B)
        self._write_data(bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._write_cmd(0x2C)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def fill_rect(self, x, y, w, h, color):
        x1 = min(self.width - 1, x + w - 1)
        y1 = min(self.height - 1, y + h - 1)
        if x1 < x or y1 < y:
            return
        self._set_window(x, y, x1, y1)
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        pixels = (x1 - x + 1) * (y1 - y + 1)
        chunk = bytes([hi, lo]) * 256
        self.dc(1)
        self.cs(0)
        while pixels >= 256:
            self.spi.write(chunk)
            pixels -= 256
        if pixels:
            self.spi.write(bytes([hi, lo]) * pixels)
        self.cs(1)


display = None
try:
    spi = SPI(
        1,
        baudrate=20_000_000,  # safer across sims
        polarity=0,
        phase=0,
        sck=Pin(PIN["TFT_SCK"]),
        mosi=Pin(PIN["TFT_MOSI"]),
        miso=Pin(PIN["TFT_MISO"]),
    )
    display = ILI9341(
        spi,
        dc=Pin(PIN["TFT_DC"], Pin.OUT),
        cs=Pin(PIN["TFT_CS"], Pin.OUT),
    )
    print("Display init OK", display.width, display.height)
    display.fill(0)
except Exception as exc:
    print("Display init failed:", exc)
    display = None


def tone(freq_hz, duration_ms, duty=256):
    buzzer.freq(freq_hz)
    buzzer.duty(duty)
    time.sleep_ms(duration_ms)
    buzzer.duty(0)


def is_pressed(name):
    return buttons[name].value() == 0


def wait_release(name):
    while is_pressed(name):
        time.sleep_ms(10)


def wait_any(timeout_ms):
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        for name in ("A", "B", "C", "D"):
            if is_pressed(name):
                wait_release(name)
                return name
        time.sleep_ms(8)
    return None


def status(msg):
    print(msg)


def show_color(color):
    if display:
        display.fill(color)


def blink(color, times=2, delay_ms=120):
    if not display:
        return
    for _ in range(times):
        display.fill(color)
        time.sleep_ms(delay_ms)
        display.fill(0)
        time.sleep_ms(delay_ms)


status("=== Codee Wokwi Recreation ===")
status("Buttons: A/S/D/F keys (A/B/C/D)")
status("Press A to start each round.")
print("heartbeat: game booted")

TARGET_COLORS = {
    "A": rgb565(255, 64, 64),
    "B": rgb565(64, 255, 128),
    "C": rgb565(64, 128, 255),
    "D": rgb565(255, 220, 64),
}
blink(rgb565(32, 32, 32), times=1, delay_ms=80)

score = 0
round_no = 0

while True:
    status("\nPress A to start")
    pulse_on = False
    last_anim = time.ticks_ms()
    anim_count = 0
    while not is_pressed("A"):
        now = time.ticks_ms()
        if time.ticks_diff(now, last_anim) > 250:
            last_anim = now
            pulse_on = not pulse_on
            anim_count += 1
            color = random.randrange(0x10000)
            show_color(color)
            if display:
                display.fill_rect(10, 10, 40, 40, rgb565(255, 255, 255) if pulse_on else 0)
                display.fill_rect(60, 10, 40, 40, color)
            print("heartbeat tick", anim_count)
        time.sleep_ms(10)
    wait_release("A")

    round_no += 1
    timeout_ms = max(900, 2800 - round_no * 100)
    target = random.choice(("A", "B", "C", "D"))

    tone(1047, 50)
    show_color(TARGET_COLORS[target])
    blink(TARGET_COLORS[target], times=1, delay_ms=60)
    status("Round {} | target={} | timeout={}ms".format(round_no, target, timeout_ms))

    choice = wait_any(timeout_ms)
    if choice is None:
        tone(220, 200)
        blink(rgb565(255, 128, 0), times=2, delay_ms=80)
        status("Timeout")
        continue

    if choice == target:
        score += 1
        tone(880, 80)
        tone(1320, 80)
        blink(rgb565(0, 255, 0), times=2, delay_ms=80)
        status("Correct | score={}".format(score))
    else:
        tone(220, 250)
        blink(rgb565(255, 0, 0), times=2, delay_ms=80)
        status("Wrong ({}) | score={}".format(choice, score))
