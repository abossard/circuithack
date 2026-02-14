# Codee Recreation in Wokwi

This sim recreates a **Codee-like ESP32-S3 hardware shell**:
- 4 buttons (A/B/C/D)
- buzzer (PWM)
- SPI color TFT (ILI9341 placeholder display)

It uses Codee **revision2** pin mapping from:
`third_party/Codee-Firmware/main/src/Util/Pins.cpp`

## Pin map used
- Buttons: A=8, B=9, C=17, D=16
- Buzzer: 7
- TFT SPI: SCK=2, MOSI=3, DC=4, CS=6

## Run (Web simulator)
1. Open [Wokwi simulator](https://wokwi.com)
2. Create a new **MicroPython ESP32** project
3. Replace `main.py` and `diagram.json` with files from this folder
4. Start simulation
5. Use keys `A/S/D/F` for buttons A/B/C/D

## Run (CLI via Python entrypoint)
`circuithack-wokwi` auto-loads the nearest `.env` and forwards args to `wokwi-cli`.

```bash
uv run circuithack-wokwi --help
```

Note: Wokwi CLI cloud simulation expects firmware/ELF and token config; web simulation is the easiest path for MicroPython script iteration.
