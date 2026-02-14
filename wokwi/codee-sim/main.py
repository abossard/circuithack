import random
import time
from machine import Pin, PWM

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
}

buttons = {
    "A": Pin(PIN["BTN_A"], Pin.IN, Pin.PULL_UP),
    "B": Pin(PIN["BTN_B"], Pin.IN, Pin.PULL_UP),
    "C": Pin(PIN["BTN_C"], Pin.IN, Pin.PULL_UP),
    "D": Pin(PIN["BTN_D"], Pin.IN, Pin.PULL_UP),
}

buzzer = PWM(Pin(PIN["BUZZ"]))
buzzer.duty(0)


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
    # Display is wired in diagram (ILI9341) for future graphics integration.
    # For now, gameplay uses serial output.
    print(msg)


status("=== Codee Wokwi Recreation ===")
status("Buttons: A/S/D/F keys (A/B/C/D)")
status("Press A to start each round.")

score = 0
round_no = 0

while True:
    status("\nPress A to start")
    while not is_pressed("A"):
        time.sleep_ms(10)
    wait_release("A")

    round_no += 1
    timeout_ms = max(900, 2800 - round_no * 100)
    target = random.choice(("A", "B", "C", "D"))

    tone(1047, 50)
    status("Round {} | target={} | timeout={}ms".format(round_no, target, timeout_ms))

    choice = wait_any(timeout_ms)
    if choice is None:
        tone(220, 200)
        status("Timeout")
        continue

    if choice == target:
        score += 1
        tone(880, 80)
        tone(1320, 80)
        status("Correct | score={}".format(score))
    else:
        tone(220, 250)
        status("Wrong ({}) | score={}".format(choice, score))
