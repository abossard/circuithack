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
```

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

## Codee port kit
- `ports/codee/` contains a MicroPython adapter layer:
  - `codee_display.py`
  - `codee_input.py`
  - `codee_audio.py`
  - `codee_save.py`
- First game target included: `ports/codee/game_2048.py`
- Integration notes: `ports/codee/README.md`

## Upstream game source sync
- `sync-games` clones/updates curated upstream repositories into `third_party_games/`.
- It writes commit-locked metadata in `third_party_games/sources.lock.json`.
- You can pass repeated `--source` values (source id or `owner/repo`) to sync only a subset.

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
