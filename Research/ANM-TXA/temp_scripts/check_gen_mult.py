#!/usr/bin/env python3
"""Check if generated ANM mult bytes now match original"""
import struct
import pathlib

# Check generated ANM
gen_path = pathlib.Path("examples/stand_turn_ls_90.anm")
with open(gen_path, 'rb') as f:
    gen_data = f.read()

# Skip to HEAD section
pos = 4 + 4 + 8 + 4 + 4 + 4 + 4 + 4  # FORM, size, ANIMSET6, anim_data_len, FPS, const, fps, HEAD magic
head_size = struct.unpack('>I', gen_data[pos:pos+4])[0]
pos += 4

print("Generated ANM mult bytes (hip bone - 2nd):")
# Skip Scene_Root (40 bytes for bias/mult/bias/mult/bias/mult + numFrames + 3*key counts + flags + name_len + name)
pos += 24  # 6 floats = 24 bytes
pos += 2 + 2 + 2 + 2  # 4 shorts = 8 bytes
pos += 1 + 1 + 10  # flags + name_len + "Scene_Root"

# Now at hip bone
pos_mult_bytes = gen_data[pos+4:pos+8]
print(f"  posMulti bytes: {pos_mult_bytes.hex()}")
print(f"  as float: {struct.unpack('<f', pos_mult_bytes)[0]:.10e}")

print("\nOriginal ANM hip mult bytes:")
print(f"  Should be: bc62 9f3f (or similar)")
