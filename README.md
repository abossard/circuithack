# CircuitHack: CircuitMess Codee 2.0 Tooling

This repo now contains a local Python MCP server and CLI focused on Codee 2.0 first.

## What it does (Codee 2.0)
- Detects USB serial devices and likely Codee candidates on macOS/Linux.
- Downloads official stock firmware from `CircuitMess/Codee-Firmware` releases.
- Switches device into ESP32-S3 programmer mode (`esptool` reset handshake).
- Restores stock firmware (`write_flash 0x0`).
- Installs MicroPython from:
  - a provided `.bin`, or
  - CircuitMess MicroPython source (`CM_Codee`) build + flash.
- Runs MicroPython scripts on device via `mpremote`.

## Install
```bash
uv sync --dev
```

## CLI examples
```bash
uv run circuithack-cli scan
uv run circuithack-cli download-stock --out-dir downloads/codee
uv run circuithack-cli enter-programmer --port /dev/cu.usbmodemXXXX
uv run circuithack-cli restore-stock --port /dev/cu.usbmodemXXXX
uv run circuithack-cli install-mpy-bin --port /dev/cu.usbmodemXXXX --bin-path firmware.bin
uv run circuithack-cli install-mpy-source --port /dev/cu.usbmodemXXXX --repo-dir third_party/circuitmess-micropython --board CM_Codee
uv run circuithack-cli run-script --port /dev/cu.usbmodemXXXX --script-path examples/hello.py
uv run circuithack-cli backup-state --port /dev/cu.usbmodemXXXX --out-dir backups
uv run circuithack-cli backup-full --port /dev/cu.usbmodemXXXX --out-dir backups --flash-size 0x400000
uv run circuithack-cli restore-full-backup --port /dev/cu.usbmodemXXXX --backup-path backups/codee-fullflash-YYYYmmdd-HHMMSS.bin
uv run circuithack-cli flash-firmware --port /dev/cu.usbmodemXXXX --source official
uv run circuithack-cli flash-firmware --port /dev/cu.usbmodemXXXX --source local-build --build-dir third_party/Codee-Firmware/build
uv run circuithack-cli decode-nvs --nvs-path backups/codee-nvs-YYYYmmdd-HHMMSS.bin
uv run circuithack-cli sync-games --dest-root third_party_games
uv run python scripts/sync_game_sources.py --dest-root third_party_games --source thumby-color-games
uv run circuithack-cli sync-gamewatch-source --repo-dir third_party/M5Tab5-Game-and-Watch
uv run circuithack-cli download-gamewatch-assets --out-dir downloads/gamewatch --rom-base-url https://example.com/roms --artwork-base-url https://example.com/artworks --rom-extension .gw.gz --artwork-extension .jpg.gz
uv run circuithack-cli codee-gamewatch-plan
uv run circuithack-wokwi lint wokwi/codee-sim
```

## Wokwi token
If you place `WOKWI_CLI_TOKEN=...` in a repo-local `.env`, Python entrypoints auto-load it:
- `circuithack-cli`
- `circuithack-mcp`
- `circuithack-wokwi`

## MCP server
Run local MCP server:
```bash
uv run circuithack-mcp
```

Available MCP tools:
- `scan_codee`
- `download_codee_stock_firmware`
- `enter_codee_programmer_mode`
- `restore_codee_stock_firmware`
- `install_codee_micropython_binary`
- `build_and_install_codee_micropython`
- `run_codee_script`
- `backup_codee_state`
- `backup_codee_full_flash`
- `restore_codee_full_flash_backup`
- `flash_codee_firmware`
- `decode_codee_nvs_backup`
- `sync_codee_game_sources`
- `sync_codee_gamewatch_source`
- `download_codee_gamewatch_assets`
- `codee_gamewatch_adaptation_plan`

## Codee port kit
- `ports/codee/` contains a MicroPython adapter layer:
  - `codee_display.py`
  - `codee_input.py`
  - `codee_audio.py`
  - `codee_save.py`
- Included games: `ports/codee/game_2048.py`, `ports/codee/game_tinycity.py`, `ports/codee/game_chess.py`
- Multi-game launcher: `ports/codee/game_launcher.py`
- Integration notes: `ports/codee/README.md`

## Upstream game source sync
- `sync-games` clones/updates curated upstream repositories into `third_party_games/`.
- It writes commit-locked metadata in `third_party_games/sources.lock.json`.
- You can pass repeated `--source` values (source id or `owner/repo`) to sync only a subset.

## SpaceTrader Palm asset conversion
- Convert Palm `.rsrc` graphics to Bit-compatible RGB565 `.raw` files:
```bash
uv run python scripts/spacetrader_preview.py \
  --source-dir /Users/abossard/Downloads/SpaceTraderSource/Rsc \
  --header /Users/abossard/Downloads/SpaceTraderSource/Rsc/MerchantGraphics.h \
  --out-dir downloads/SpaceTraderSource/converted_bit_assets \
  --bit-spiffs-dir third_party/Bit-Firmware/spiffs_image/Games/SpaceTrader
```
- Output includes:
  - extracted PNG previews,
  - RGB565 `.raw` assets,
  - `assets_manifest.json` with width/height/size and source variant,
  - optional sync into Bit-Firmware SPIFFS game folder.

## Game & Watch (M5Tab5) integration for Codee
- `sync-gamewatch-source` clones/updates `tobozo/M5Tab5-Game-and-Watch`.
- `download-gamewatch-assets` downloads:
  - firmware `.bin` from `--firmware-url` or release assets, and
  - ROMs from explicit `--rom-url` entries, or from `--rom-base-url` + `--rom-id`.
  - artworks from explicit `--artwork-url` entries, or from `--artwork-base-url` + `--rom-id`.
- `codee-gamewatch-plan` prints a Codee adaptation checklist.
- Default behavior prepares a LittleFS-root bundle in `downloads/gamewatch/littlefs`.
- LittleFS bundling auto-unpacks `.gw.gz` -> `.gw` and `.jpg.gz` -> `.jpg` for on-device compatibility.
- Upstream currently publishes no GitHub release assets, so in practice you usually pass explicit URLs.
- No-SD setup: use LittleFS only, and ensure each ROM has matching artwork (`gnw_xxx.gw(.gz)` + `gnw_xxx.jpg(.gz)`).
- The upstream project does not include redistributable ROM files/artworks; use your own legally obtained sources.

### Codee C++ standalone port (no SD, no touch, no USB HID, no RTC RAM)
- Added in `third_party/Codee-Firmware/main/src/GameWatchPort/`.
- Uses Codee `Display`, `Input`, `SPIFFS`, and `ChirpSystem`.
- Forces a Codee-friendly model:
  - ROM discovery from `/spiffs` root (`gnw_*.gw`)
  - 4-button mapping (`A/B/C/D`) with combo actions
  - no SD card picker, no touch gestures, no USB keyboard/gamepad path
- Build switch: set `CODEE_GAMEWATCH_STANDALONE=1` when configuring `Codee-Firmware`.
  - Example: `idf.py -D CODEE_GAMEWATCH_STANDALONE=1 build`
- If you only want ROMs (no artwork dependency), use:
  - `uv run circuithack-cli download-gamewatch-assets ... --allow-missing-artworks`

## Reliable Mac connection checklist (Codee)
- Use a known USB data cable (not charge-only).
- Connect directly to Mac (avoid hubs during flashing).
- If port does not appear, force bootloader:
  1. Hold `BOOT`.
  2. Tap `RESET`.
  3. Release `BOOT` after ~1 second.
- Re-run `circuithack-cli scan`.
- If still missing, unplug/replug and try a different cable/USB port.

## Notes
- CircuitMess MicroPython fork includes `CM_Codee` and `CM_Bit` ESP32-S3 boards.
- Building MicroPython from source requires a working ESP-IDF environment.
