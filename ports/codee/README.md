# Codee Port Kit (MicroPython)

This folder contains a hardware-agnostic adapter layer and a first target game (`2048`) for Codee 2.0.

## Files
- `codee_display.py`: display abstraction (`CodeeDisplay`) plus `MemoryDisplayBackend` for simulation/tests.
- `codee_input.py`: button bitmask state machine (`CodeeInput`) with edge detection.
- `codee_audio.py`: tone/effect helper (`CodeeAudio`).
- `codee_save.py`: JSON save/load helper (`CodeeSave`) with atomic writes.
- `game_2048.py`: playable 2048 game model + render loop (`Game2048App`).

## Button mapping in `Game2048App`
- `A` -> left
- `B` -> right
- `C` -> up
- `D` -> down

## Typical integration on Codee
Wire these adapters to your board-specific display/buttons/buzzer implementation.

```python
from ports.codee import (
    BUTTON_A,
    BUTTON_B,
    BUTTON_C,
    BUTTON_D,
    CodeeAudio,
    CodeeDisplay,
    CodeeInput,
    CodeeSave,
    Game2048App,
)

# board_display: object exposing fill/pixel/rect/fill_rect/text/show
# read_buttons_mask: function returning BUTTON_* bitmask
# tone_cb: function(freq_hz, duration_ms)

display = CodeeDisplay(board_display, width=128, height=128)
inputs = CodeeInput(read_buttons_mask)
audio = CodeeAudio(tone_cb)
save = CodeeSave("/save/game_2048.json")

app = Game2048App(display, inputs, audio, save)
while True:
    app.step()
```

## Host-side simulation
For local logic testing without hardware:

```python
from ports.codee import CodeeAudio, CodeeDisplay, CodeeInput, CodeeSave, Game2048App, MemoryDisplayBackend

backend = MemoryDisplayBackend(128, 128)
display = CodeeDisplay(backend)
inputs = CodeeInput(lambda: 0)
audio = CodeeAudio()
save = CodeeSave("/tmp/game_2048.json")
app = Game2048App(display, inputs, audio, save)
app.step()
```
