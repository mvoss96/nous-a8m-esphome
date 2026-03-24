# Nous A8M – ESPHome Conversion Guide

> **Tested firmware:** `oem_bk7231n_matter_socket:2.0.4`  
> **Chip:** Tuya T34 / BK7231N  
> **Issue:** [libretiny#335](https://github.com/libretiny-eu/libretiny/issues/335)

---

## The Problem

Nous A8M Plugs with matter support ship with a Tuya bootloader v3.0.0 instead of v1.0.1. This mismatch causes two practical issues observed during conversion attempts:

1. OTA updates appear to succeed but never get applied — the v3.0 bootloader layout is incompatible with the runtime the v1.0.1-based flow expects, so the partition swap does not occur.
2. Devices flashed without adjusting for the different layout show an incorrect MAC (example: `C8:47:8C:00:00:00`) because calibration/userdata TLVs were read from the wrong offsets.

## Solution
- Flash the bkboot `1.0.1` bootloader to the device (required for proper OTA behavior). Example using `ltchiptool`:

```bash
ltchiptool write <port> bk7231n 0x0 bk7231n-1.0.1-encrypted-tuya.bin --length 0x11000
```

- Configure ESPHome to use the correct calibration offset. Add this to your YAML (`Nous-A8M.yaml`):

```yaml
esphome:
  platformio_options:
    board_flash.calibration: "0x1E3000+0x1000"
```

## Deprecated:

Previosly i thought i had to manually extract the MAC from the stock firmware and patch it into the ESPHome build. With the corrected calibration offset and the `generic-bk7231n-qfn32-tuya` board configuration, this is generally not necessary: flashing ESPHome over a stock firmware dump should preserve or restore the expected MAC behavior. The old scripts remain in `scripts/`s but are not required for the conversion.

## Prerequisites

- [ltchiptool](https://github.com/libretiny-eu/ltchiptool) installed
- USB-UART adapter (3.3V)
- UART access to the device (TX1/RX1 pins)
- [bk7231n-1.0.1-encrypted-tuya bootloader](https://github.com/libretiny-eu/libretiny/releases)
- The original MAC address of your device (from the Tuya app or by reading the stock flash)

---

## Quick fix (minimal changes)

If you want the shortest path to a working ESPHome build for the `generic-bk7231n-qfn32-tuya` board, update only the calibration offset in your YAML. This is the only `platformio_options` entry you generally need to change:

```yaml
esphome:
  platformio_options:
    board_flash.calibration: "0x1E3000+0x1000"
```

Flash the `bkboot 1.0.1` bootloader separately if you want OTA support; otherwise build and flash ESPHome as described below.


## Step-by-Step Guide

### Step 1 – Read the stock firmware (IMPORTANT – do this first!)

Before doing anything else, create a full backup of the stock firmware:

```bash
ltchiptool read <port> bk7231n stock_backup.bin
```

This backup allows you to extract the original MAC address later (see Step 3).

### Step 2 – Flash the v1.0.1 bootloader

Download `bk7231n-1.0.1-encrypted-tuya.zip` from the LibreTiny releases and flash it:

```bash
ltchiptool write <port> bk7231n 0x0 bk7231n-1.0.1-encrypted-tuya.bin --length 0x11000
```

### Step 3 – MAC handling (usually not required)

With the corrected calibration offset (`0x1E3000`) and the `generic-bk7231n-qfn32-tuya` board configuration, extracting and patching the MAC is generally not necessary: flashing ESPHome over a stock firmware dump should preserve or restore the expected MAC behavior.

If you still need the original MAC for any reason, the old scripts remain in `scripts/` and can extract or build a MAC patch from a dump or a known MAC. These scripts are provided for legacy/edge cases and are not required for the standard conversion flow.


### Step 4 – Flash ESPHome

Build your ESPHome firmware using the provided `Nous-A8M.yaml` (adjust substitutions for each device). Flash via UART as before:

```bash
ltchiptool write <port> bk7231n 0x11000 firmware.uf2
```


## ESPHome Configuration

See [`Nous-A8M.yaml`](Nous-A8M.yaml) for the full configuration. For the `generic-bk7231n-qfn32-tuya` board the only `platformio_options` entry you must change is the calibration offset. Add this to your YAML:

```yaml
esphome:
  platformio_options:
    board_flash.calibration: "0x1E3000+0x1000"
```

Notes:

- `board_build.bkboot_version` is a build-time setting and does not replace the device bootloader; flashing the `1.0.1` bootloader must still be done separately if you require OTA support.
- The BK7231N download/OTA offset commonly defaults to `0x12A000` and matches observed dumps.
- `kvs` stores LibreTiny/ESPHome runtime configuration (e.g., last-used Wi‑Fi); for this board the default `kvs` location does not overlap with `0x1E3000`, so you normally do not need to modify it.

---

## Recovering an Already-Converted Device

If you have already flashed ESPHome **without** the correct `platformio_options`:

1. The MAC address may be corrupted (`C8:47:8C:00:00:00`)
2. WiFi may not connect reliably

Fix:
1. Add the `platformio_options` to your YAML and reflash via UART
2. Read the current flash to recover the MAC:
   ```bash
   ltchiptool read <port> bk7231n current.bin
   python scripts/extract_mac_patch.py current.bin
   ```
   The original MAC should survive at `0x1E3024` even after conversion
---

## Credits

- [kuba2k2](https://github.com/kuba2k2) – LibreTiny maintainer, diagnosed the bootloader issue

---

## Legacy tools

These helper scripts are provided for edge cases where you must extract or patch a MAC from a full dump. For the normal conversion flow they are not required.

| Script | Description |
|--------|-------------|
| [`scripts/extract_mac_patch.py`](scripts/extract_mac_patch.py) | Extracts MAC from a dump and generates a patch |
| [`scripts/generate_mac_patch.py`](scripts/generate_mac_patch.py) | Generates a MAC patch from a provided MAC address |
