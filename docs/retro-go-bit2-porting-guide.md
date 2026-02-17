# retro-go Porting Guide for CircuitMess BIT 2.0

This guide describes the concrete changes required to port `retro-go` to BIT 2.0, based on the current `retro-go` and `Bit-Firmware` trees in this workspace.

## 1) Current Gap Summary

- **PSRAM requirement mismatch**
  - `retro-go` porting prerequisites require PSRAM/SPIRAM (`downloads/retro-go/PORTING.md`).
  - BIT firmware currently has SPIRAM disabled (`third_party/Bit-Firmware/sdkconfig`: `# CONFIG_SPIRAM is not set`, `# CONFIG_ESP32S3_SPIRAM_SUPPORT is not set`).
- **Display mismatch**
  - `retro-go` defaults to ILI9341/ST7789 driver path (`downloads/retro-go/PORTING.md`, `downloads/retro-go/components/retro-go/targets/esp32-s3-devkit/config.h`).
  - BIT firmware uses a 128x128 panel setup (`third_party/Bit-Firmware/main/src/Devices/Display.cpp`).
- **Storage model mismatch**
  - `retro-go` storage roots are under `RG_STORAGE_ROOT` (commonly `/sd`) and rely on SD/FAT or optional flash FAT partition (`downloads/retro-go/components/retro-go/rg_storage.h`, `rg_storage.c`).
  - BIT firmware is SPIFFS-centric (`third_party/Bit-Firmware/main/src/FS/SPIFFS.*`, and SDK SPIFFS config).
- **Input model mismatch**
  - BIT has 7 buttons (Up/Down/Left/Right/A/B/Menu) via GPIO mapping in `third_party/Bit-Firmware/main/src/Pins.hpp` and `Pins.cpp`.
  - retro-go often expects extra keys (`START`, `SELECT`, `OPTION`) depending on app and target config.

## 2) Required Changes in retro-go

## 2.1 Create a BIT target

Add a new target directory:

- `downloads/retro-go/components/retro-go/targets/bit-2-0/config.h`
- `downloads/retro-go/components/retro-go/targets/bit-2-0/env.py`
- `downloads/retro-go/components/retro-go/targets/bit-2-0/sdkconfig`

Use `esp32-s3-devkit` target as starting template.

### config.h must define at least

- `RG_TARGET_NAME`
- storage mode (`RG_STORAGE_*`)
- screen config (`RG_SCREEN_*`)
- button maps (`RG_GAMEPAD_*_MAP`)
- audio backend settings (`RG_AUDIO_*`)

### env.py must define at least

- `IDF_TARGET` for BIT’s chip family
- any board-specific build env needed by `rg_tool.py`

`rg_tool.py` auto-loads target `env.py` and `sdkconfig` defaults.

## 2.2 Register the new target

Update `downloads/retro-go/components/retro-go/config.h` to add:

- `#elif defined(RG_TARGET_BIT_2_0)`
- `#include "targets/bit-2-0/config.h"`

Without this, the build falls back to ODROID-GO defaults.

## 2.3 Memory and sdkconfig alignment

BIT firmware evidence today:

- flash size is 8MB (`CONFIG_ESPTOOLPY_FLASHSIZE="8MB"`)
- SPIRAM disabled (`# CONFIG_SPIRAM is not set`)

For retro-go target sdkconfig:

- enable and validate SPIRAM settings if BIT hardware supports it
- ensure main stack and CPU settings meet retro-go guidance (`PORTING.md`)
- keep FATFS options compatible with long filenames/UTF-8 as recommended by retro-go

If PSRAM is not available in hardware, expect severe scope cuts or a likely non-viable full port.

## 2.4 Build/image and partition sizing

`retro-go` relies on `rg_tool.py` for multi-app builds and image composition (`BUILDING.md`).

Required:

- choose a reduced app list to fit 8MB flash
- tune partition strategy and app placement (see `rg_tool.py` `PROJECT_APPS`, generated partitions flow)
- validate `.img` generation and install path with `rg_tool.py --target bit-2-0 ...`

## 2.5 Display driver integration

Because BIT is 128x128 and existing retro-go default driver path is ILI9341/ST7789-oriented:

- either implement a BIT-compatible display driver (recommended)
  - add new driver file under `components/retro-go/drivers/display/`
  - wire it in `rg_display.c` with a new `RG_SCREEN_DRIVER` option
- or adapt an existing driver if electrically/controller compatible

Also adjust launcher/app UI assumptions for small 128x128 viewport.

## 2.6 Input mapping

Map BIT buttons to retro-go keys in target `config.h`:

- physical: Up/Down/Left/Right/A/B/Menu
- virtual combos for missing keys (e.g. Start/Select/Option) if required by emulators/UI

Use `RG_GAMEPAD_GPIO_MAP` and, where needed, virtual mappings described by retro-go input model.

## 2.7 Storage backend decision

Pick one storage strategy:

1. **SD-based** (preferred for ROM capacity): wire SDSPI/SDMMC pins and use `/sd` root
2. **Flash FAT partition** (`RG_STORAGE_FLASH_PARTITION`): lower complexity but strict ROM-size limits

BIT’s current SPIFFS usage is not a drop-in replacement for retro-go ROM/save layout.

## 2.8 Audio path

Implement/choose audio path that works with BIT hardware:

- validate DAC/I2S assumptions in chosen target config
- if unavailable, provide reduced fallback audio behavior per emulator constraints

## 3) Recommended MVP Scope (to make first boot realistic)

1. Target skeleton (`bit-2-0` + registration + env)
2. Launcher-only boot on display with input navigation
3. Storage mount and ROM listing
4. Single lightweight emulator core
5. Add more cores only after memory/perf verification

Disable non-essential features early (network/updater/heavy cores) until baseline stability is proven.

## 4) Validation Checklist

- `python rg_tool.py --target bit-2-0 build launcher`
- `python rg_tool.py --target bit-2-0 build-img launcher`
- Flash image and verify:
  - display init
  - button mapping correctness
  - storage mount
  - launcher navigation
- Add one core and repeat memory/perf validation before expanding scope.

## 5) Go/No-Go Gate

Before serious implementation, confirm this explicitly:

- BIT 2.0 hardware **does** provide usable PSRAM for retro-go workload.

If not, plan for a very constrained fork (few cores, aggressive cuts) rather than a full-feature retro-go port.
