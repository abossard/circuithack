# Pure MicroPython Games: Easy Codee Port Candidates

Updated: 2026-02-14

Goal of this list: only include projects that are Python-first and do **not** require a custom C game engine.

Codee target assumptions: ESP32-S3, 128x128 display, 4 buttons, buzzer.

## Selection rules used
- Repo contains runnable `.py` game/app code (not only docs/assets).
- No `USER_C_MODULES` or engine-C build requirement in project itself.
- Uses common MicroPython/CircuitPython APIs (`machine`, `framebuf`, `ssd1306`, etc.).
- Portability judged mainly on input mapping + display adapter effort.

## Best easy ports (pure Python)

| Project | Why it is easy to port to Codee | Codee effort | Screenshot |
|---|---|---|---|
| [joos-too/Microsnake](https://github.com/joos-too/Microsnake) | ESP32 + MicroPython snake with 4 directional buttons and optional buzzer; straightforward control remap. | Low | ![Microsnake](assets/pure-micropython-game-screenshots/microsnake.png) |
| [snacsnoc/ESP-arcade-playground](https://github.com/snacsnoc/ESP-arcade-playground) | Multi-game framework (dodge/collect/zombie) already uses 4-button navigation and pure `.py` modules. | Low | _(no screenshot in repo)_ |
| [dagabi/esp32-game](https://github.com/dagabi/esp32-game) | Simple MicroPython clicker game loop with button + buzzer + OLED. Good first adapter test. | Low | ![ClickFrenzy](assets/pure-micropython-game-screenshots/clickfrenzy.jpeg) |
| [itay-mal/single_button_game](https://github.com/itay-mal/single_button_game) | Explicit `micropython_files/` implementation; useful one-button timing mechanics for Codee mini-games. | Low | ![Single Button](assets/pure-micropython-game-screenshots/single-button-1.jpg) |
| [gliber/esp32_catch_the_stars](https://github.com/gliber/esp32_catch_the_stars) | ESP32 + MicroPython + buzzer architecture; gameplay logic is portable even though original input is one-button. | Low/Medium | ![gameESP SPI board](assets/pure-micropython-game-screenshots/gameesp-spi.jpg) |
| [cheungbx/gameESP-micropython](https://github.com/cheungbx/gameESP-micropython) | Many pure-Python sample games (`breakout.py`, `invader.py`, `pong.py`, `snake.py`, `tetris.py`) plus reusable game helper module. | Medium | ![gameESP SPI](assets/pure-micropython-game-screenshots/gameesp-spi.jpg) |
| [cheungbx/ESP8266-micropython-Snake-Game](https://github.com/cheungbx/ESP8266-micropython-Snake-Game) | Focused snake codebase with direct GPIO/button handling; easy game-logic transplant. | Low | ![gameESP I2C](assets/pure-micropython-game-screenshots/gameesp-i2c.jpg) |
| [jefflau1/micropython-esp32-ssd1306-conway-s-game-of-life](https://github.com/jefflau1/micropython-esp32-ssd1306-conway-s-game-of-life) | Very small pure MicroPython simulation game; ideal for display/timing adapter validation. | Low | _(no screenshot in repo)_ |
| [olance/usimon](https://github.com/olance/usimon) | Pure MicroPython Simon implementation using buttons/LED logic and async flow; good for reaction/timing game ports. | Low | _(no screenshot in repo)_ |
| [mcauser/MicroPython-ESP8266-Nokia-5110-Conways-Game-of-Life](https://github.com/mcauser/MicroPython-ESP8266-Nokia-5110-Conways-Game-of-Life) | Classic pure MicroPython Game-of-Life with simple framebuffer model; display backend is replaceable. | Low | ![Nokia GoL](assets/pure-micropython-game-screenshots/nokia-gol-life.jpg) |
| [beastbroak30/pingpong-pico-micropython](https://github.com/beastbroak30/pingpong-pico-micropython) | Pure Python game on ST7735-based setup; close to Codee-style control/display adaptation flow. | Medium | ![Tetris console photo](assets/pure-micropython-game-screenshots/tetris-console-preview.jpg) |

## Important exclusions (why)
- [TinyCircuits/TinyCircuits-Tiny-Game-Engine](https://github.com/TinyCircuits/TinyCircuits-Tiny-Game-Engine): requires C user modules and platform-specific C drivers (not “easy pure Python”).
- [WoXy-Sensei/tetris-game-console](https://github.com/WoXy-Sensei/tetris-game-console): Python-based but built for CircuitPython APIs (`displayio`, `adafruit_*`), not vanilla MicroPython.

## Freshness and licensing snapshot

| Repo | Last push (UTC) | SPDX |
|---|---|---|
| joos-too/Microsnake | 2024-06-25T19:26:04Z | NOASSERTION |
| snacsnoc/ESP-arcade-playground | 2024-11-07T09:31:00Z | GPL-3.0 |
| dagabi/esp32-game | 2024-03-20T09:57:17Z | NOASSERTION |
| gliber/esp32_catch_the_stars | 2024-04-08T15:03:58Z | MIT |
| cheungbx/gameESP-micropython | 2021-07-20T09:17:34Z | NOASSERTION |
| cheungbx/ESP8266-micropython-Snake-Game | 2019-09-28T10:01:45Z | NOASSERTION |
| jefflau1/micropython-esp32-ssd1306-conway-s-game-of-life | 2020-12-18T07:56:50Z | NOASSERTION |
| olance/usimon | 2021-01-10T15:59:46Z | NOASSERTION |
| mcauser/MicroPython-ESP8266-Nokia-5110-Conways-Game-of-Life | 2018-08-07T16:07:50Z | MIT |
| itay-mal/single_button_game | 2024-03-06T23:48:12Z | NOASSERTION |
| beastbroak30/pingpong-pico-micropython | 2024-04-23T12:52:01Z | CC0-1.0 |

## Notes for Codee porting
- Almost all easy candidates here are monochrome SSD1306-era projects. Keep gameplay logic intact and swap rendering to your `ports/codee/codee_display.py` adapter.
- Most will map cleanly to Codee A/B/C/D via `ports/codee/codee_input.py` with minimal gameplay edits.
- For repos marked `NOASSERTION`, verify license per game/repo before redistribution.
