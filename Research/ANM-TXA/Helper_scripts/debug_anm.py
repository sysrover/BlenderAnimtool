#!/usr/bin/env python3
import sys

with open(sys.argv[1] if len(sys.argv) > 1 else 'examples/head_turn.anm', 'rb') as f:
    data = f.read()

print('First 128 bytes (hex):')
for i in range(0, min(128, len(data)), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f'{i:04x}: {hex_str:<48} {ascii_str}')

print()
print('Header breakdown:')
print(f'Marker: {data[0:4]}')
print(f'FORM size: {int.from_bytes(data[4:8], "big")}')
print(f'ANIMSET: {data[8:15]}')
print(f'Format byte: {data[15]}')
print(f'Anim data len: {int.from_bytes(data[16:20], "big")}')
print(f'Constant: {data[20:28].hex()}')
print(f'FPS: {int.from_bytes(data[28:32], "little")}')
print(f'HEAD marker: {data[32:36]}')
print(f'HEAD size: {int.from_bytes(data[36:40], "big")}')

print(f'\nTotal file size: {len(data)} bytes')
