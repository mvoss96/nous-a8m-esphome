# Nous A8M – ESPHome Conversion Guide

> **Tested firmware:** `oem_bk7231n_matter_socket:2.0.4`  
> **Chip:** Tuya T34 / BK7231N  
> **Issue:** [libretiny#335](https://github.com/libretiny-eu/libretiny/issues/335)

---

## The Problem

The Nous A8M is a Matter-enabled smart plug using a **BK7231N** chip with Tuya bootloader **v3.0.0**.  
LibreTiny only supports bootloader **v1.0.1**, which causes two issues after conversion:

1. **OTA updates appear successful but never apply** – the bootloader does not perform the partition swap.
2. **Wrong MAC address** (`C8:47:8C:00:00:00`) after flashing – the v1.0.1 bootloader does not understand the v3.0 flash layout and cannot read the original MAC.

### Root Cause: Flash Layout

The v3.0 bootloader uses a different flash layout than what LibreTiny expects by default:

| Partition    | Stock offset | Size     |
|-------------|-------------|----------|
| bootloader  | `0x000000`  | 64K      |
| app         | `0x010000`  | ~1.5MB   |
| calibration | `0x1D0000`  | `0x3000` |
| net         | `0x1D3000`  | `0x2000` |
| kvs         | `0x1D5000`  | `0x9000` |
| userdata    | `0x1E3000`  | `0x12000`|
| tuya        | `0x1F5000`  | `0xA000` |

The original MAC address is stored in the **userdata TLV** at `0x1E3024`.  
After flashing the v1.0.1 bootloader, the calibration TLV at `0x1D0000` gets a default MAC of `C8:47:8C:00:00:00`.

---

## Prerequisites

- [ltchiptool](https://github.com/libretiny-eu/ltchiptool) installed
- USB-UART adapter (3.3V)
- UART access to the device (TX1/RX1 pins)
- [bk7231n-1.0.1-encrypted-tuya bootloader](https://github.com/libretiny-eu/libretiny/releases)
- The original MAC address of your device (from the Tuya app or by reading the stock flash)

---

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

### Step 3 – Extract and patch the MAC address

The original MAC is stored in the **userdata partition at `0x1E3024`** and survives both the
bootloader replacement and the ESPHome flash as long as ESPHome was flashed with the correct
`platformio_options` (which keep the KVS away from that region). This means the MAC can be
extracted from **any dump** of the device, even after conversion.

Use the provided script to extract the original MAC and generate a patch file:

```bash
python scripts/extract_mac_patch.py <your_dump.bin>
```

This will output the original MAC and create `mac_patch_1D0000.bin`.

Flash the MAC patch:

```bash
ltchiptool write <port> bk7231n 0x1D0000 mac_patch_1D0000.bin
```

If you have no dump at all, find the MAC in the **Nous app** (Device Info) and use:

```bash
python scripts/generate_mac_patch.py F8:17:2D:D3:0A:40
```

### Step 4 – Flash ESPHome

Build your ESPHome firmware using the provided `Nous-A8M.yaml` (adjust substitutions for each device).

Flash via UART:

```bash
ltchiptool write <port> bk7231n 0x11000 firmware.uf2
```

## ESPHome Configuration

See [`Nous-A8M.yaml`](Nous-A8M.yaml) for the full configuration.

The critical part is the `platformio_options` section which tells LibreTiny the correct flash layout:

```yaml
esphome:
  platformio_options:
    board_build.bkboot_version: "1.0.1-bk7231n"
    board_flash.calibration: "0x1D0000+0x3000"
    board_flash.net:          "0x1D3000+0x2000"
    board_flash.kvs:          "0x1D5000+0x9000"
    board_flash.userdata:     "0x1E3000+0x12000"
    board_flash.tuya:         "0x1F5000+0xA000"
```

## Scripts

| Script | Description |
|--------|-------------|
| [`scripts/extract_mac_patch.py`](scripts/extract_mac_patch.py) | Extracts MAC from a stock dump and generates a patch file |
| [`scripts/generate_mac_patch.py`](scripts/generate_mac_patch.py) | Generates a MAC patch from a manually specified MAC address |

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