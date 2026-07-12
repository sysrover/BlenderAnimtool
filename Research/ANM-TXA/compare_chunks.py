#!/usr/bin/env python3
"""Compare ANM files chunk by chunk."""

import pathlib
import struct

def parse_anm_chunks(data):
    """Parse ANM chunks without using reader."""
    pos = 0
    
    # FORM
    form_tag = data[pos:pos+4]
    pos += 4
    form_size_be = struct.unpack('>i', data[pos:pos+4])[0]
    pos += 4
    print(f"FORM size: {form_size_be}")
    
    # ANIMSET
    anim_tag = data[pos:pos+7]
    pos += 7
    fmt = data[pos]
    pos += 1
    print(f"Format: {fmt}")
    
    # Anim data len
    anim_data_len_be = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    print(f"Anim data len: {anim_data_len_be}")
    
    # FPS section
    fps_tag = data[pos:pos+4]
    pos += 4
    unknown = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    fps = struct.unpack('<i', data[pos:pos+4])[0]
    pos += 4
    print(f"FPS: {fps}")
    
    # HEAD chunk
    head_tag = data[pos:pos+4]
    pos += 4
    head_size_be = struct.unpack('>i', data[pos:pos+4])[0]
    pos += 4
    head_start = pos
    print(f"\nHEAD chunk: size={head_size_be}, starts at byte {head_start}")
    
    # Show first bone in HEAD
    print("First bone HEAD data (first 64 bytes):")
    first_bone_head = data[head_start:head_start+64]
    for i, b in enumerate(first_bone_head):
        if i % 16 == 0:
            print(f"  {i:2d}: ", end="")
        print(f"{b:02x} ", end="")
        if (i + 1) % 16 == 0:
            print()
    print()
    
    pos = head_start + head_size_be
    
    # DATA chunk
    data_tag = data[pos:pos+4]
    pos += 4
    data_size_be = struct.unpack('>i', data[pos:pos+4])[0]
    pos += 4
    data_start = pos
    print(f"\nDATA chunk: size={data_size_be}, starts at byte {data_start}")
    print(f"First 128 bytes of DATA:")
    first_data = data[data_start:data_start+128]
    for i, b in enumerate(first_data):
        if i % 16 == 0:
            print(f"  {i:3d}: ", end="")
        print(f"{b:02x} ", end="")
        if (i + 1) % 16 == 0:
            print()
    print()

with open("examples/stand_walk_fwd_original.anm", 'rb') as f:
    orig_data = f.read()

with open("test_walk_new.anm", 'rb') as f:
    new_data = f.read()

print("="*60)
print("ORIGINAL")
print("="*60)
parse_anm_chunks(orig_data)

print("\n" + "="*60)
print("GENERATED")
print("="*60)
parse_anm_chunks(new_data)
