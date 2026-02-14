# Codee Port Wokwi Project

This is a self-contained Wokwi project for the Codee game port suite:
- Codee Launcher
- 2048
- TinyCity
- Chess

It runs the same port modules from `ports/codee/` via a vendored `codee/` snapshot in this folder.

## Controls
- Menu: `A/B` select, `C` or `D` start
- In game: hold `A+C+D` to return to menu

Wokwi keyboard mapping:
- `A` key -> button `A`
- `S` key -> button `B`
- `D` key -> button `C`
- `F` key -> button `D`

## Run in Wokwi Web
1. Open [Wokwi simulator](https://wokwi.com)
2. Create a new **MicroPython ESP32** project
3. Replace project files with this folder contents
4. Start simulation and open serial monitor

## Run with CLI
```bash
uv run circuithack-wokwi lint ports/codee/wokwi
```

## Refresh vendored modules after port changes
```bash
cp ../__init__.py ../codee_audio.py ../codee_display.py ../codee_input.py ../codee_save.py ../game_2048.py ../game_tinycity.py ../game_chess.py ../game_launcher.py codee/
```
