#!/usr/bin/env python3

with open('examples/head_turn_original.anm', 'rb') as f:
    data = f.read()

print('Full file dump (hex + ASCII):')
for i in range(0, len(data), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:04x}: {hex_str:<48} {ascii_str}')

print()
print('Interpreted structure:')
print(f'Marker: {data[0:4]}')
print(f'FORM size (BE): {int.from_bytes(data[4:8], "big")}')
print(f'ANIMSET: {data[8:15]}')
print(f'Format byte: {data[15]} (0x{data[15]:02x})')
print(f'Next 4 bytes: {data[16:20]}')
if data[16:20] == b'FPS\x00':
    print('  -> Found ASCII "FPS" marker')
    fps_val = int.from_bytes(data[20:24], 'little')
    print(f'  FPS value (LE): {fps_val}')
    print(f'  Next marker: {data[24:28]}')
