#!/usr/bin/env python3
import sys

# Read both files
with open('examples/head_turn_original.anm', 'rb') as f:
    original = f.read()

with open('examples/head_turn.anm', 'rb') as f:
    generated = f.read()

print(f'Original size: {len(original)}')
print(f'Generated size: {len(generated)}')
print(f'Difference: {len(generated) - len(original)} bytes')
print()

# Compare headers
print('Header comparison (first 100 bytes):')
for i in range(0, min(100, len(original), len(generated)), 16):
    o_hex = ' '.join(f'{b:02x}' for b in original[i:i+16])
    g_hex = ' '.join(f'{b:02x}' for b in generated[i:i+16])
    match = '✓' if original[i:i+16] == generated[i:i+16] else '✗'
    print(f'{i:04x}: {match}')
    print(f'  O: {o_hex}')
    print(f'  G: {g_hex}')

# Find first difference
print()
print('First difference:')
for i in range(min(len(original), len(generated))):
    if original[i] != generated[i]:
        print(f'At byte {i} (0x{i:04x}):')
        print(f'  Original: 0x{original[i]:02x}')
        print(f'  Generated: 0x{generated[i]:02x}')
        print(f'  Context (original): {original[max(0,i-8):i+8].hex()}')
        print(f'  Context (generated): {generated[max(0,i-8):i+8].hex()}')
        break
else:
    if len(original) != len(generated):
        print(f'Files are identical up to byte {min(len(original), len(generated))}, but sizes differ')
    else:
        print('Files are identical!')
