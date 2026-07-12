#!/usr/bin/env python3
"""Compare exact mult values in original binary"""
import struct
import pathlib

# Read original ANM binary
orig_path = pathlib.Path("examples/stand_turn_ls_90_original.anm")
with open(orig_path, "rb") as f:
    data = f.read()

# Jump to HEAD section (skip FORM, ANIMSET, etc.)
pos = 4 + 4 + 8 + 4 + 4 + 4  # FORM + size + ANIMSET6 + anim_data_len + FPS\x00 + const + fps
head_magic = data[pos:pos+4]
pos += 4
head_size = struct.unpack('>I', data[pos:pos+4])[0]
pos += 4

# Read first two bones
print("Original ANM binary HEAD values:")
print(f"\nFirst bone (Scene_Root):")
pos_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
pos_mult_raw = data[pos:pos+4]
pos_mult = struct.unpack('<f', pos_mult_raw)[0]
pos += 4
rot_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
rot_mult_raw = data[pos:pos+4]
rot_mult = struct.unpack('<f', rot_mult_raw)[0]
pos += 4
scale_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
scale_mult = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4

print(f"  posMulti (raw bytes): {pos_mult_raw.hex()} = {pos_mult}")
print(f"  rotMulti (raw bytes): {rot_mult_raw.hex()} = {rot_mult}")
print(f"  When reader does: mult * SCALE_FACTOR (1.525902e-05):")
print(f"    posMulti becomes: {pos_mult * 1.525902e-05}")
print(f"    rotMulti becomes: {rot_mult * 1.525902e-05}")

# Skip to second bone
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
name = data[pos:pos+name_len].decode('ascii')
pos += name_len

print(f"\nSecond bone (hip):")
pos_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
pos_mult_raw = data[pos:pos+4]
pos_mult = struct.unpack('<f', pos_mult_raw)[0]
pos += 4
rot_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
rot_mult_raw = data[pos:pos+4]
rot_mult = struct.unpack('<f', rot_mult_raw)[0]
pos += 4
scale_bias = struct.unpack('<f', data[pos:pos+4])[0]
pos += 4
scale_mult = struct.unpack('<f', data[pos:pos+4])[0]

print(f"  posMulti (raw bytes): {pos_mult_raw.hex()} = {pos_mult}")
print(f"  rotMulti (raw bytes): {rot_mult_raw.hex()} = {rot_mult}")
print(f"  When reader does: mult * SCALE_FACTOR (1.525902e-05):")
print(f"    posMulti becomes: {pos_mult * 1.525902e-05}")
print(f"    rotMulti becomes: {rot_mult * 1.525902e-05}")
