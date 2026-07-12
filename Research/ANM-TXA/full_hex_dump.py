#!/usr/bin/env python3
"""Full hex dump of ANM file - FORM header through all chunks."""

import struct
import sys
import pathlib

def full_hex_dump(path):
    """Complete hex inspection of ANM file."""
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"File: {path}")
    print(f"Total size: {len(data)} bytes\n")
    
    # Full hex dump
    print("FULL HEX DUMP:")
    for i in range(0, min(len(data), 1024), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"{i:06x}: {hex_str:<48} {ascii_str}")
    
    if len(data) > 1024:
        print(f"\n... ({len(data) - 1024} more bytes) ...\n")
        # Show DATA section start
        data_pos = data.find(b'DATA')
        if data_pos >= 0:
            print(f"\nDATA section at offset 0x{data_pos:x}:")
            for i in range(data_pos, min(data_pos + 256, len(data)), 16):
                hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
                print(f"{i:06x}: {hex_str:<48} {ascii_str}")

if __name__ == "__main__":
    full_hex_dump(pathlib.Path("examples/stand_roar_new.anm"))
