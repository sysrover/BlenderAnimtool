#!/usr/bin/env python3
"""
Hex compare generated vs original stand_attack_0.anm
"""

from pathlib import Path

def hex_compare(orig_path, gen_path):
    orig = Path(orig_path).read_bytes()
    gen = Path(gen_path).read_bytes()
    
    print(f"Original size: {len(orig)} bytes")
    print(f"Generated size: {len(gen)} bytes")
    print(f"Size difference: {len(gen) - len(orig)} bytes")
    
    # Find first difference
    min_len = min(len(orig), len(gen))
    first_diff = None
    diff_count = 0
    
    for i in range(min_len):
        if orig[i] != gen[i]:
            if first_diff is None:
                first_diff = i
            diff_count += 1
    
    print(f"\nTotal differing bytes: {diff_count}")
    
    if first_diff is not None:
        print(f"First difference at byte {first_diff} (0x{first_diff:x})")
        
        # Show context around first difference
        start = max(0, first_diff - 32)
        end = min(min_len, first_diff + 32)
        
        print(f"\nContext around first difference (bytes {start}-{end}):")
        print("\nOriginal:")
        for i in range(start, end, 16):
            hex_str = ' '.join(f'{b:02x}' for b in orig[i:min(i+16, end)])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in orig[i:min(i+16, end)])
            marker = ' <--' if i <= first_diff < i+16 else ''
            print(f"{i:08x}: {hex_str:<48} {ascii_str}{marker}")
        
        print("\nGenerated:")
        for i in range(start, end, 16):
            hex_str = ' '.join(f'{b:02x}' for b in gen[i:min(i+16, end)])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in gen[i:min(i+16, end)])
            marker = ' <--' if i <= first_diff < i+16 else ''
            print(f"{i:08x}: {hex_str:<48} {ascii_str}{marker}")
    else:
        if len(orig) == len(gen):
            print("\n✓ Files are identical!")
        else:
            print(f"\n❌ Files differ only in length by {len(gen) - len(orig)} bytes")
    
    # Show first 20 differences
    if diff_count > 0:
        print(f"\nFirst 20 differences:")
        shown = 0
        for i in range(min_len):
            if orig[i] != gen[i]:
                print(f"  Byte 0x{i:08x}: orig=0x{orig[i]:02x} gen=0x{gen[i]:02x}")
                shown += 1
                if shown >= 20:
                    break

if __name__ == '__main__':
    hex_compare('example2/stand_attack_0_original.anm', 'example2/stand_attack_0.anm')
