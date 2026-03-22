#!/usr/bin/env python3
"""
Generate a calibration partition patch for the Nous A8M with a manually
specified MAC address (e.g. from the Tuya app).

Requires a reference TLV template – either from a stock dump or from
another A8M. By default uses the built-in template derived from a known
stock image.

Usage:
    python generate_mac_patch.py <MAC>

Example:
    python generate_mac_patch.py F8:17:2D:D3:0A:40

Output:
    mac_patch_1D0000.bin  – flash this at offset 0x1D0000
"""

import sys
import struct

# Minimal TLV calibration sector template (from Nous A8M stock firmware)
# This is the structure the v1.0.1 bootloader expects at 0x1D0000.
# Only the MAC bytes at offset 0x24 are device-specific.
TLV_TEMPLATE = bytearray([
    0x54, 0x4C, 0x56, 0x00, 0xF6, 0x01, 0x00, 0x00,  # TLV header
    0x00, 0x11, 0x11, 0x11, 0x5A, 0x00, 0x00, 0x00,  # entry 0
    0x01, 0x11, 0x11, 0x11, 0x04, 0x00, 0x00, 0x00,  # entry 1
    0x4E, 0x61, 0xBC, 0x00,                          # frequency calibration
    0x02, 0x11, 0x11, 0x11, 0x06, 0x00, 0x00, 0x00,  # entry 2 (MAC, 6 bytes)
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,              # MAC placeholder
    0x03, 0x11, 0x11, 0x11, 0x04, 0x00, 0x00, 0x00,  # entry 3
    0x5E, 0x01, 0x00, 0x00,
    0x04, 0x11, 0x11, 0x11, 0x04, 0x00, 0x00, 0x00,
    0x8E, 0x15, 0x53, 0x01,
])

MAC_OFFSET = 0x24  # offset of MAC within TLV sector


def parse_mac(mac_str):
    parts = mac_str.strip().split(':')
    if len(parts) != 6:
        raise ValueError(f"Invalid MAC address: {mac_str}")
    return bytes(int(p, 16) for p in parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_mac_patch.py <MAC>")
        print("Example: python generate_mac_patch.py F8:17:2D:D3:0A:40")
        sys.exit(1)

    try:
        mac = parse_mac(sys.argv[1])
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    mac_str = ':'.join(f'{b:02X}' for b in mac)
    print(f"Generating MAC patch for: {mac_str}")

    # Build 4096-byte sector: template + 0xFF padding
    sector = bytearray(0x1000)
    sector[:] = b'\xff' * 0x1000
    sector[:len(TLV_TEMPLATE)] = TLV_TEMPLATE
    sector[MAC_OFFSET:MAC_OFFSET+6] = mac

    output = "mac_patch_1D0000.bin"
    with open(output, "wb") as f:
        f.write(sector)

    print(f"Patch saved: {output} ({len(sector)} bytes)")
    print(f"\nFlash with:")
    print(f"  ltchiptool write <port> bk7231n 0x1D0000 {output}")


if __name__ == "__main__":
    main()
