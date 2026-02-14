# MicroPython Games to Port to CircuitMess Codee 2.0

Updated: 2026-02-14

## Codee 2.0 target constraints
- MCU: ESP32-S3
- Screen: 128x128 color TFT
- Input: 4 buttons (A/B/C/D)
- Audio: buzzer/speaker (PWM)
- Runtime target: MicroPython on `CM_Codee`

## Best open-source sources to port from

| Repo | What it gives you | Why it fits Codee | Activity signal |
|---|---|---|---|
| https://github.com/TinyCircuits/TinyCircuits-Thumby-Color-Games | Collection of ready-made MicroPython color games | Very close target class (small handheld + buttons + color screen) | pushed 2026-02-09 |
| https://github.com/TinyCircuits/TinyCircuits-Tiny-Game-Engine | Reusable MicroPython game engine + examples | Good foundation for structured game ports and reusable APIs | pushed 2026-02-02 |
| https://github.com/TinyCircuits/TinyCircuits-Thumby-Games | Large MicroPython game corpus (mostly mono) | Fast way to port mechanics, UI loops, and save logic | pushed 2026-02-10 |
| https://github.com/cheungbx/gameESP-micropython | ESP8266/ESP32 MicroPython game module + samples | ESP32-friendly game primitives and examples | pushed 2021-07-20 |
| https://github.com/cheungbx/Odroid-Go-Micropython-games | Color TFT ESP32 MicroPython games | Closer to Codee’s ESP32 + color display stack | pushed 2019-11-16 |
| https://github.com/snacsnoc/ESP-arcade-playground | Lightweight multi-game menu framework | Good starter for a Codee game launcher shell | pushed 2024-11-07 |
| https://github.com/Timendus/thumby-silicon8 | CHIP-8 interpreter in MicroPython | Unlocks many existing ROM-style mini games | pushed 2022-09-09 |
| https://github.com/SarahBass/Thumby-Virtual-Pet | MicroPython virtual pet game | Directly relevant to Codee-style pet gameplay loops | pushed 2022-10-04 |

## High-priority game candidates (fastest wins)

### From TinyCircuits-Thumby-Color-Games
1. `2048` (low porting effort)
2. `4Connect` (low)
3. `Chess` (medium)
4. `ComboPool` (medium)
5. `FroggyRoad` (low/medium)
6. `Monstra` (medium)
7. `PuzzleAttack` (medium)
8. `Solitaire` (medium)
9. `Tetrumb` (low)
10. `ThumbSweeper` (low)
11. `ThumbCommander` (medium)
12. `WallRacerC` (low)

### From TinyCircuits-Thumby-Games
1. `1nvader` (low)
2. `3D_MAZE` (medium)
3. `AlienInvasion` (low)
4. `AstroJumper` (low)
5. `Brickd` (low)
6. `CosmicSurvivor` (medium)
7. `DiscDungeon` (medium)
8. `Flucht` (medium)
9. `GameOfLife` (low)
10. `Journey3Dg` (high)
11. `LCDGallery` (low/medium)
12. `Kombine` (low)

## Recommended port order for Codee
1. `2048`
2. `4Connect`
3. `Tetrumb`
4. `ThumbSweeper`
5. `1nvader`
6. `Brickd`
7. `FroggyRoad`
8. `Flucht`

## Porting notes (Codee-specific)
- Replace source display API with one `codee_display.py` adapter (framebuffer, blit, text, palette).
- Normalize input to Codee’s 4-button map via `codee_input.py`.
- Provide a small audio shim (`tone(freq, ms)`) over Codee buzzer.
- Add a `save.py` wrapper for persistent game state in NVS/files.
- For Thumby mono games, keep gameplay resolution internally and upscale into 128x128.

## License caveat
Many game repos above do not declare SPDX licenses in metadata. Before redistributing a port, verify each game folder/repo license and permissions.

## Sources
- https://github.com/TinyCircuits/TinyCircuits-Thumby-Color-Games
- https://github.com/TinyCircuits/TinyCircuits-Tiny-Game-Engine
- https://github.com/TinyCircuits/TinyCircuits-Thumby-Games
- https://github.com/cheungbx/gameESP-micropython
- https://github.com/cheungbx/Odroid-Go-Micropython-games
- https://github.com/snacsnoc/ESP-arcade-playground
- https://github.com/Timendus/thumby-silicon8
- https://github.com/SarahBass/Thumby-Virtual-Pet
