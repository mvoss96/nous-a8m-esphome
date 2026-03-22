#!/usr/bin/env python3
"""
Extract the original MAC address from a Nous A8M stock firmware dump
and generate a calibration partition patch for use after flashing the
LibreTiny v1.0.1 bootloader.

Usage:
    python extract_mac_patch.py <stock_dump.bin>

Output:
    mac_patch_1D0000.bin  – flash this at offset 0x1D0000
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_mac_patch.py <stock_dump.bin>")
        sys.exit(1)

    dump_path = sys.argv[1]
    if not os.path.exists(dump_path):
        print(f"Error: file not found: {dump_path}")
        sys.exit(1)

    data = bytearray(open(dump_path, "rb").read())
    print(f"Loaded {len(data)} bytes from {dump_path}")

    # Search for TLV magic (0x544c5600)
    magic = bytes([0x54, 0x4C, 0x56, 0x00])
    patch_source = None
    pos = 0

    while True:
        idx = data.find(magic, pos)
        if idx == -1:
            break
        mac = data[idx+0x24:idx+0x2A]
        mac_str = ':'.join(f'{b:02X}' for b in mac)
        print(f"  TLV found at 0x{idx:06x} → MAC: {mac_str}")

        # Skip default/empty MACs
        if mac[0] not in (0xC8, 0x00, 0xFF):
            patch_source = (idx, bytes(mac))

        pos = idx + 1

    if patch_source is None:
        print("\nError: No valid original MAC found in dump!")
        print("The stock firmware may have already been overwritten.")
        print("Use generate_mac_patch.py with the MAC from your Tuya app instead.")
        sys.exit(1)

    src_offset, mac = patch_source
    mac_str = ':'.join(f'{b:02X}' for b in mac)
    print(f"\nOriginal MAC found at 0x{src_offset:06x}: {mac_str}")

    # Use the TLV sector containing the original MAC as template
    # and place it at 0x1D0000 (calibration partition)
    tlv_sector = bytearray(data[src_offset:src_offset+0x1000])

    output = "mac_patch_1D0000.bin"
    with open(output, "wb") as f:
        f.write(tlv_sector)

    print(f"\nPatch saved: {output} ({len(tlv_sector)} bytes)")
    print(f"\nFlash with:")
    print(f"  ltchiptool write <port> bk7231n 0x1D0000 {output}")


if __name__ == "__main__":
    main()
