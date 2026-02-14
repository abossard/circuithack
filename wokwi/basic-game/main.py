import random
import time
from machine import Pin

# Codee-like button mapping on four GPIO pins.
BUTTON_PINS = {
    "A": 4,
    "B": 5,
    "C": 6,
    "D": 7,
}

buttons = {name: Pin(gpio, Pin.IN, Pin.PULL_UP) for name, gpio in BUTTON_PINS.items()}


def pressed(name):
    # Active-low pushbuttons.
    return buttons[name].value() == 0


def wait_release(name):
    while pressed(name):
        time.sleep_ms(10)


def wait_any_press(timeout_ms):
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        for name in ("A", "B", "C", "D"):
            if pressed(name):
                wait_release(name)
                return name
        time.sleep_ms(8)
    return None


print("=== CircuitHack Wokwi Basic Game ===")
print("Press button A to start. Then press the prompted button before timeout.")
print("Controls: A/B/C/D pushbuttons in the diagram.")

score = 0
round_no = 0

while True:
    print("\nPress A to start round", round_no + 1)
    while not pressed("A"):
        time.sleep_ms(10)
    wait_release("A")

    round_no += 1
    target = random.choice(("A", "B", "C", "D"))
    timeout = 3000

    print(f"Round {round_no}: press {target} within {timeout}ms")
    answer = wait_any_press(timeout)

    if answer is None:
        print("Timeout! No button pressed.")
        continue

    if answer == target:
        score += 1
        print(f"Correct! score={score}")
    else:
        print(f"Wrong ({answer}). score={score}")
