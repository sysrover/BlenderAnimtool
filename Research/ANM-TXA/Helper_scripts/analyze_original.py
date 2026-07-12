#!/usr/bin/env python3

with open('examples/head_turn_original.anm', 'rb') as f:
    original = f.read()

# Reconstruct structure analysis
print('Byte-by-byte analysis:')
print(f'0-3: FORM = {original[0:4]}')
print(f'4-7: FORM size = 0x{int.from_bytes(original[4:8], "big"):08x} = {int.from_bytes(original[4:8], "big")} bytes')
print(f'8-14: ANIMSET = {original[8:15]}')
print(f'15: format = {original[15]} (0x{original[15]:02x})')
print(f'16-19: unknown/anim_data_len = 0x{int.from_bytes(original[16:20], "big"):08x} = {int.from_bytes(original[16:20], "big")} bytes')
print(f'20-23: FPS marker = {original[20:24]}')
print(f'24-27: FPS value = 0x{int.from_bytes(original[24:28], "little"):08x} = {int.from_bytes(original[24:28], "little")} (little-endian)')
print(f'28-31: HEAD marker = {original[28:32]}')
print(f'32-35: HEAD size = 0x{int.from_bytes(original[32:36], "big"):08x} = {int.from_bytes(original[32:36], "big")} bytes')

# Find DATA marker
data_pos = original.find(b'DATA')
print(f'DATA marker at offset 0x{data_pos:02x} ({data_pos})')
print(f'DATA size = 0x{int.from_bytes(original[data_pos+4:data_pos+8], "big"):08x}')

file_size = len(original)
print(f'\nTotal file size: {file_size} bytes')
print(f'FORM size + 8 (for FORM marker and size field) = {int.from_bytes(original[4:8], "big") + 8}')
