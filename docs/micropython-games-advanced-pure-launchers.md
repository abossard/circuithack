# Advanced Pure-MicroPython Games and Launchers for Codee

Updated: 2026-02-14

This list intentionally avoids projects that require a custom C game engine.

## What counts as "pure" here
- Game/runtime logic is written in `.py` files.
- Uses standard MicroPython/CircuitPython-style modules (`machine`, `framebuf`, `ssd1306`, `thumby`, `picographics`, etc.).
- No required `USER_C_MODULES` game-engine build step.

## Advanced games (not toy-level)

| Project | Type | Why it is advanced | Codee port effort | Screenshot |
|---|---|---|---|---|
| [chrisdiana/TinyCity](https://github.com/chrisdiana/TinyCity) | City sim / strategy | SimCity-like simulation with zoning, budget, disasters, milestones, save/load. Repo includes adapter interfaces (`DisplayInterface`, `ButtonInterface`) which helps non-Thumby ports. | Medium | ![TinyCity title](assets/advanced-micropython-game-screenshots/tinycity-title.png) ![TinyCity game](assets/advanced-micropython-game-screenshots/tinycity-game.png) |
| [TinyRogue (inside TinyCircuits-Thumby-Games)](https://github.com/TinyCircuits/TinyCircuits-Thumby-Games/tree/master/TinyRogue) | Roguelike | Single-file but substantial gameplay loop (~900+ lines), procedural/randomized progression. | Medium | ![TinyRogue](assets/advanced-micropython-game-screenshots/tinyrogue.png) |
| [Thelda (inside TinyCircuits-Thumby-Games)](https://github.com/TinyCircuits/TinyCircuits-Thumby-Games/tree/master/Thelda) | Zelda-like action adventure | Multi-module game (player, scenes, enemies, bosses, inventory/hud, save flow). | Medium/High | _(no screenshot asset in repo)_ |
| [Thumgeon (inside TinyCircuits-Thumby-Games)](https://github.com/TinyCircuits/TinyCircuits-Thumby-Games/tree/master/Thumgeon) | Dungeon crawler | Larger RPG-style system in pure Python (~1600+ line main module). | Medium/High | _(no screenshot asset in repo)_ |
| [jacklinquan/micropython-sunfish](https://github.com/jacklinquan/micropython-sunfish) | Chess engine | Pure MicroPython Sunfish chess engine tested on ESP32; good base for your own Codee UI front-end. | Medium | _(text/terminal engine; no gameplay image in repo)_ |
| [niutech/chess-badger2040](https://github.com/niutech/chess-badger2040) | Chess game (UI + engine) | Full chess game front-end around MicroPython Sunfish; stronger end-user reference than engine-only repo. | Medium/High | ![Chess Badger](https://github.com/niutech/chess-badger2040/assets/384997/6ed7ec5c-53f3-4208-a7cb-1f728c058d48) |
| [Timendus/thumby-silicon8](https://github.com/Timendus/thumby-silicon8) | CHIP-8/SCHIP/XO-CHIP interpreter | Gives you a large effective game catalog once ported. Pure Python interpreter architecture. | High | ![Silicon8 menu](assets/advanced-micropython-game-screenshots/silicon8-menu.png) ![Silicon8 pong](assets/advanced-micropython-game-screenshots/silicon8-pong.png) |

## Multi-game launcher options (best for your goal)

| Project | What you get | Why it fits Codee | Port effort | Screenshot |
|---|---|---|---|---|
| [denix372/Pico-Game-Arcade](https://github.com/denix372/Pico-Game-Arcade) | Actual launcher menu + multiple games (2048, Snake, Flappy, Pong, etc.) | Closest direct blueprint to a Codee launcher architecture; dispatches into per-game modules and returns cleanly. | Medium | _(no screenshot in repo)_ |
| [LCDGallery (inside TinyCircuits-Thumby-Games)](https://github.com/TinyCircuits/TinyCircuits-Thumby-Games/tree/master/LCDGallery) | Lightweight launcher with multiple mini-games and score persistence | Good "small but real" launcher pattern (titlescreen + game selection + highscores). | Medium | _(no screenshot asset in repo)_ |
| [snacsnoc/ESP-arcade-playground](https://github.com/snacsnoc/ESP-arcade-playground) | ESP32/ESP8266 game framework + menu + multiple games | Simpler than Pico-Game-Arcade, but already pure ESP MicroPython and menu-driven. | Low/Medium | ![Microsnake hardware style](assets/advanced-micropython-game-screenshots/microsnake.png) |

## Recommended direction for Codee (pragmatic)
1. Start launcher architecture from `Pico-Game-Arcade` menu pattern.
2. Port one advanced game first: `TinyCity` (best strategy/sim candidate with clean interface abstractions).
3. Add chess as second "deep" game using `micropython-sunfish` + your Codee UI wrapper.
4. Add one RPG candidate (`TinyRogue` or `Thelda`) as the stress test for memory/input/rendering.

## Freshness and license snapshot

| Repo | Last push (UTC) | SPDX |
|---|---|---|
| chrisdiana/TinyCity | 2026-01-27T03:30:21Z | GPL-3.0 |
| denix372/Pico-Game-Arcade | 2025-11-14T11:29:16Z | NOASSERTION |
| jacklinquan/micropython-sunfish | 2025-02-19T22:47:03Z | GPL-3.0 |
| niutech/chess-badger2040 | 2023-08-30T14:22:14Z | GPL-3.0 |
| snacsnoc/ESP-arcade-playground | 2024-11-07T09:31:00Z | GPL-3.0 |
| TinyCircuits/TinyCircuits-Thumby-Games | 2026-02-10T16:14:32Z | NOASSERTION |
| Timendus/thumby-silicon8 | 2022-09-09T12:20:55Z | GPL-3.0 |
| olance/usimon | 2021-01-10T15:59:46Z | NOASSERTION |

## Caveats
- `NOASSERTION` repos need manual license verification before redistribution.
- Thumby-targeted projects are still pure Python, but depend on `thumby*` APIs; those calls need mapping to your Codee adapter layer.
- Some advanced projects are memory-sensitive; do incremental ports and profile heap early.
