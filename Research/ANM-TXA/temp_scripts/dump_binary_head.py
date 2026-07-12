#!/usr/bin/env python3
"""Read the binary ANM and dump HEAD values"""
import struct
import sys
import pathlib

anm_path = pathlib.Path("examples/stand_turn_ls_90.anm")

with open(anm_path, "rb") as f:
    data = f.read()

# Parse FORM header
pos = 0
form_magic = data[pos:pos+4]
pos += 4
form_size_be = struct.unpack('>I', data[pos:pos+4])[0]
pos += 4
print(f"FORM magic: {form_magic}")
print(f"FORM size: {form_size_be} (total file size: {len(data)})")

# Skip ANIMSET6
print(f"Next: {data[pos:pos+8]}")
pos += 8  # "ANIMSET6"

# Now we're at anim_data_len
anim_data_len_be = struct.unpack('>I', data[pos:pos+4])[0]
pos += 4
print(f"anim_data_len: {anim_data_len_be}")

# Skip FPS\x00
print(f"Next: {data[pos:pos+4]}")
pos += 4

# Unknown constant
const = struct.unpack('>I', data[pos:pos+4])[0]
pos += 4
print(f"Unknown const: {const}")

# FPS value
fps = struct.unpack('<I', data[pos:pos+4])[0]
pos += 4
print(f"FPS: {fps}")

# Now HEAD chunk should start
head_magic = data[pos:pos+4]
pos += 4
print(f"\nHEAD magic: {head_magic}")

head_size_be = struct.unpack('>I', data[pos:pos+4])[0]
pos += 4
print(f"HEAD size: {head_size_be}")

# Read first bone HEAD entry
print(f"\nFirst bone (Scene_Root) HEAD:")
pos_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
pos_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
rot_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
rot_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
scale_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
scale_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4

print(f"  posBias: {pos_bias}, posMulti: {pos_mult}")
print(f"  rotBias: {rot_bias}, rotMulti: {rot_mult}")
print(f"  scaleBias: {scale_bias}, scaleMulti: {scale_mult}")

# Read second bone (hip)
num_frames = struct.unpack('<h', data[pos:pos+2])[0]
pos += 2
num_pos_keys = struct.unpack('<h', data[pos:pos+2])[0]
pos += 2
num_rot_keys = struct.unpack('<h', data[pos:pos+2])[0]
pos += 2
num_scale_keys = struct.unpack('<h', data[pos:pos+2])[0]
pos += 2
flags = struct.unpack('<B', data[pos:pos+1])[0]
pos += 1
name_len = struct.unpack('<B', data[pos:pos+1])[0]
pos += 1

print(f"  numFrames: {num_frames}, posKeys: {num_pos_keys}, rotKeys: {num_rot_keys}, scaleKeys: {num_scale_keys}")

# Skip past first bone name and read second bone
name = data[pos:pos+name_len].decode('ascii')
pos += name_len
print(f"  name: '{name}'")

print(f"\nSecond bone (hip) HEAD:")
pos_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
pos_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
rot_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
rot_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
scale_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
scale_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4

print(f"  posBias: {pos_bias}, posMulti: {pos_mult}")
print(f"  rotBias: {rot_bias}, rotMulti: {rot_mult}")
print(f"  scaleBias: {scale_bias}, scaleMulti: {scale_mult}")
