#!/usr/bin/env python3
"""
Deep binary comparison of original vs generated stand_attack_0.anm
Looking for structural differences that cause DeAnm failure.
"""

import struct
from pathlib import Path

def read_file(path):
    with open(path, 'rb') as f:
        return f.read()

def parse_anm_structure(data, label):
    """Parse ANM structure to compare HEAD/DATA layout."""
    pos = 0
    
    # FORM chunk
    form_tag = data[pos:pos+4]
    pos += 4
    form_size_be = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    print(f"\n=== {label} ===")
    print(f"FORM size: {form_size_be} + 8 = {form_size_be + 8} (file size: {len(data)})")
    
    # ANIMSET tag
    animset = data[pos:pos+7]
    pos += 7
    format_byte = data[pos]
    pos += 1
    print(f"Format: {format_byte} (AnimSet{format_byte})")
    
    # Skip to HEAD chunk
    head_pos = data.find(b'HEAD', pos)
    if head_pos < 0:
        print("ERROR: No HEAD chunk found!")
        return
    
    pos = head_pos + 4
    head_size_be = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    head_data_start = pos
    head_data_end = head_pos + 8 + head_size_be
    
    print(f"HEAD: pos={head_pos}, size={head_size_be}, ends at {head_data_end}")
    
    # DATA chunk
    data_pos = data.find(b'DATA', head_data_end)
    if data_pos < 0:
        print("ERROR: No DATA chunk found!")
        return
    
    pos = data_pos + 4
    data_size_be = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    data_data_start = pos
    data_data_end = data_pos + 8 + data_size_be
    
    print(f"DATA: pos={data_pos}, size={data_size_be}, ends at {data_data_end}")
    
    # Count bytes in DATA for each bone
    print(f"\nExpected total DATA bytes (excluding padding): {data_size_be}")
    print(f"Actual file size: {len(data)}")
    
    # EVNT chunk
    evnt_pos = data.find(b'EVNT', data_data_end)
    if evnt_pos >= 0:
        pos = evnt_pos + 4
        evnt_size_be = struct.unpack('>I', data[pos:pos+4])[0]
        print(f"EVNT: pos={evnt_pos}, size={evnt_size_be}")
    else:
        print("EVNT: Not found")
    
    # Sample first few bones' HEAD entries
    print(f"\nFirst 2 bones HEAD entries:")
    pos = head_data_start
    for b_idx in range(2):
        print(f"\n Bone {b_idx}:")
        posBias = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        posMult = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        rotBias = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        rotMult = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        scaleBias = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        scaleMult = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        numFrames = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        numPosKeys = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        numRotKeys = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        numScaleKeys = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        flags = struct.unpack('<B', data[pos:pos+1])[0]; pos += 1
        nameLen = struct.unpack('<B', data[pos:pos+1])[0]; pos += 1
        name = data[pos:pos+nameLen].decode('ascii', errors='ignore')
        pos += nameLen
        
        print(f"   name={name}, numFrames={numFrames}")
        print(f"   keys: pos={numPosKeys}, rot={numRotKeys}, scale={numScaleKeys}")
        print(f"   mult: pos={posMult:.2e}, rot={rotMult:.2e}, scale={scaleMult:.2e}")

def main():
    orig = read_file('example2/stand_attack_0_original.anm')
    gen = read_file('example2/stand_attack_0.anm')
    
    parse_anm_structure(orig, "ORIGINAL")
    parse_anm_structure(gen, "GENERATED")
    
    # Byte-level comparison
    print("\n=== Byte Differences ===")
    diff_count = 0
    for i in range(min(len(orig), len(gen))):
        if orig[i] != gen[i]:
            if diff_count < 20:
                print(f"Byte {i}: orig=0x{orig[i]:02x}, gen=0x{gen[i]:02x}")
            diff_count += 1
    
    print(f"\nTotal differing bytes: {diff_count}")
    if len(orig) != len(gen):
        print(f"Length difference: {len(gen) - len(orig)} bytes")

if __name__ == '__main__':
    main()
