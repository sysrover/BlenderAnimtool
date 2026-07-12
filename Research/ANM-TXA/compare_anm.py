#!/usr/bin/env python3
"""
Compare two ANM files byte-by-byte, hex dump sections.
"""

import struct
import sys
import pathlib

def dump_anm_structure(path):
    """Dump raw ANM structure."""
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"File: {path}")
    print(f"Total size: {len(data)} bytes\n")
    
    # Dump first 100 bytes in hex
    print("First 200 bytes (hex):")
    for i in range(0, min(200, len(data)), 16):
        hex_part = ' '.join(f'{data[j]:02x}' for j in range(i, min(i+16, len(data))))
        ascii_part = ''.join(chr(data[j]) if 32 <= data[j] < 127 else '.' for j in range(i, min(i+16, len(data))))
        print(f"{i:04x}: {hex_part:<48} {ascii_part}")
    
    print("\n" + "="*80 + "\n")

def compare_chunks(path1, path2):
    """Compare two ANM files."""
    with open(path1, 'rb') as f:
        data1 = f.read()
    with open(path2, 'rb') as f:
        data2 = f.read()
    
    print(f"Comparing {path1} vs {path2}")
    print(f"Sizes: {len(data1)} vs {len(data2)}")
    
    # Find first difference
    for i in range(min(len(data1), len(data2))):
        if data1[i] != data2[i]:
            print(f"\nFirst difference at byte {i} (0x{i:04x}):")
            print(f"  File 1: 0x{data1[i]:02x}")
            print(f"  File 2: 0x{data2[i]:02x}")
            print(f"  Context (file 1): {data1[max(0, i-10):i+10].hex()}")
            print(f"  Context (file 2): {data2[max(0, i-10):i+10].hex()}")
            return i
    
    if len(data1) != len(data2):
        print(f"\nFile length difference: {len(data1)} vs {len(data2)}")
        return min(len(data1), len(data2))
    
    print("\nFiles are identical!")
    return None

if __name__ == "__main__":
    path1 = pathlib.Path("examples/stand_walk_fwd_original.anm")
    path2 = pathlib.Path("examples/stand_walk_fwd_new.anm")
    
    if not path1.exists():
        print(f"File not found: {path1}")
        sys.exit(1)
    if not path2.exists():
        print(f"File not found: {path2}")
        sys.exit(1)
    
    dump_anm_structure(path1)
    dump_anm_structure(path2)
    
    print("="*80)
    print("COMPARISON")
    print("="*80)
    compare_chunks(path1, path2)
