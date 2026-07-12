#!/usr/bin/env python3
"""
Detailed hex inspection of ANM HEAD and DATA chunks.
"""

import struct
import sys
import pathlib

def hex_dump(data, offset=0, length=None):
    """Pretty-print hex dump."""
    if length:
        data = data[:length]
    for i in range(0, len(data), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"{offset+i:06x}: {hex_str:<48} {ascii_str}")

def inspect_anm_chunks(path):
    """Extract and dump HEAD and DATA chunks."""
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"File: {path}")
    print(f"Total size: {len(data)} bytes\n")
    
    # Parse FORM header
    pos = 0
    form_marker = data[pos:pos+4]
    print(f"FORM marker: {form_marker} (should be b'FORM')")
    pos += 4
    
    form_size = struct.unpack('>I', data[pos:pos+4])[0]
    print(f"FORM size: {form_size} (0x{form_size:x})")
    pos += 4
    
    # ANIMSET version
    anim_set = data[pos:pos+7]
    print(f"ANIMSET: {anim_set}")
    pos += 7
    
    fmt_byte = data[pos]
    print(f"Format: {fmt_byte} (AnimSet{fmt_byte & 15})")
    pos += 1
    
    # Anim data len
    anim_data_size = struct.unpack('>I', data[pos:pos+4])[0]
    print(f"Anim data size: {anim_data_size} (0x{anim_data_size:x})")
    pos += 4
    
    # FPS chunk
    fps_marker = data[pos:pos+4]
    unknown = struct.unpack('>I', data[pos+4:pos+8])[0]
    fps = struct.unpack('<I', data[pos+8:pos+12])[0]
    print(f"FPS chunk: {fps_marker}, unknown={unknown}, fps={fps}")
    pos += 12
    
    print("\n" + "="*80 + "\n")
    
    # HEAD chunk
    head_marker = data[pos:pos+4]
    head_size = struct.unpack('>I', data[pos+4:pos+8])[0]
    print(f"HEAD marker: {head_marker}, size: {head_size} (0x{head_size:x})")
    head_data = data[pos+8:pos+8+head_size]
    print(f"\nHEAD data (first 256 bytes in hex):")
    hex_dump(head_data, 0, 256)
    pos += 8 + head_size
    
    print("\n" + "="*80 + "\n")
    
    # DATA chunk
    data_marker = data[pos:pos+4]
    data_size = struct.unpack('>I', data[pos+4:pos+8])[0]
    print(f"DATA marker: {data_marker}, size: {data_size} (0x{data_size:x})")
    data_chunk = data[pos+8:pos+8+data_size]
    print(f"\nDATA data (first 512 bytes in hex):")
    hex_dump(data_chunk, 0, 512)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_anm_chunks.py <anm_file>")
        sys.exit(1)
    
    path = pathlib.Path(sys.argv[1]).resolve()
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    
    inspect_anm_chunks(path)
