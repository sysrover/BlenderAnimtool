#!/usr/bin/env python3
"""Compare original vs verify TXA files"""

with open('examples/stand_roar.txa', 'r') as f:
    original = f.read()
with open('examples/stand_roar_verify.txa', 'r') as f:
    verify = f.read()

orig_lines = original.split('\n')
verify_lines = verify.split('\n')

print(f'Original TXA: {len(orig_lines)} lines')
print(f'Verify TXA: {len(verify_lines)} lines')
print()

# Check first 30 lines (header)
print('=== HEADER COMPARISON (first 30 lines) ===')
for i in range(min(30, len(orig_lines), len(verify_lines))):
    if orig_lines[i] != verify_lines[i]:
        print(f'Line {i+1} DIFFER:')
        print(f'  Orig: {orig_lines[i][:80]}')
        print(f'  Veri: {verify_lines[i][:80]}')
    else:
        print(f'Line {i+1} OK: {orig_lines[i][:60]}')

# Find hip bone data
print('\n=== HIP BONE DATA (original) ===')
for i, line in enumerate(orig_lines):
    if 'hip' in line.lower() and '$node' in line:
        for j in range(i, min(i+25, len(orig_lines))):
            print(f'{orig_lines[j]}')
        break

print('\n=== HIP BONE DATA (verify) ===')
for i, line in enumerate(verify_lines):
    if 'hip' in line.lower() and '$node' in line:
        for j in range(i, min(i+25, len(verify_lines))):
            print(f'{verify_lines[j]}')
        break

# Count differences
diffs = sum(1 for i in range(min(len(orig_lines), len(verify_lines))) if orig_lines[i] != verify_lines[i])
print(f'\n=== SUMMARY ===')
print(f'Total line differences: {diffs}')
