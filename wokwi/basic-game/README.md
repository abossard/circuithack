# Wokwi Basic Game (ESP32-S3 + MicroPython)

This is a starter game scaffold for game porting work:
- board: `board-esp32-s3-devkitc-1`
- input: 4 buttons mapped to GPIO 4/5/6/7
- runtime: MicroPython script (`main.py`)

## Run in Wokwi Web
1. Open https://wokwi.com
2. Create a new ESP32 MicroPython project
3. Replace `main.py` and `diagram.json` with files from this folder
4. Start simulation and use keys `A/S/D/F` (or click buttons)

## Run with Wokwi CLI
`wokwi-cli` requires a CI token (`WOKWI_CLI_TOKEN`) for cloud simulations.

```bash
export WOKWI_CLI_TOKEN=...   # from https://wokwi.com/dashboard/ci
/Users/abossard/bin/wokwi-cli lint
/Users/abossard/bin/wokwi-cli . --timeout 60000
```
