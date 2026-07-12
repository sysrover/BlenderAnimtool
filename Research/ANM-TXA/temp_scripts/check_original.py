#!/usr/bin/env python3
import struct
with open('examples/stand_turn_ls_90_original.anm', 'rb') as f:
    data = f.read()

pos = 0
form_size = struct.unpack('>I', data[4:8])[0]
print(f'FORM size: {form_size}, total file: {len(data)}')
pos = 12

anim_data_len = struct.unpack('>I', data[12:16])[0]
print(f'anim_data_len: {anim_data_len}')
pos = 16 + 4 + 4 + 4  # skip FPS\x00, unknown, fps value

print(f'At offset {pos:04x} (HEAD magic):')
print(f'  {data[pos:pos+4]} = {data[pos:pos+4]}')
pos += 4

head_size = struct.unpack('>I', data[pos:pos+4])[0]
print(f'HEAD size: {head_size}')
pos += 4

print(f'\nFirst bone Scene_Root at offset {pos:04x}:')
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

print(f'  posBias={pos_bias}, posMulti={pos_mult:.10e}')
print(f'  rotBias={rot_bias}, rotMulti={rot_mult:.10e}')
print(f'  scaleBias={scale_bias}, scaleMulti={scale_mult:.10e}')
print(f'  (rotMulti as stored: {rot_mult})')
print(f'  When read with * SCALE_FACTOR: {rot_mult * 1.525902e-05}')
