#!/usr/bin/env python3
"""
Deep diagnostic comparison: original vs generated stand_attack_0.anm
Looking for structural issues that DeAnm detects.
"""

import struct
from pathlib import Path

def hexdump(data, start=0, length=128):
    """Return hex dump of bytes."""
    lines = []
    for i in range(0, min(length, len(data) - start), 16):
        offset = start + i
        hex_part = ' '.join(f'{b:02x}' for b in data[offset:offset+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:offset+16])
        lines.append(f'{offset:08x}: {hex_part:<48} {ascii_part}')
    return '\n'.join(lines)

def check_evnt_chunk(path, label):
    """Check EVNT chunk structure."""
    with open(path, 'rb') as f:
        data = f.read()
    
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        print(f"{label}: No EVNT chunk")
        return
    
    print(f"\n=== {label} EVNT Chunk ===")
    size_be = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    print(f"Position: {evnt_pos}, Size: {size_be}")
    
    pos = evnt_pos + 8
    num_events = struct.unpack('<H', data[pos:pos+2])[0]
    print(f"Number of events: {num_events}")
    
    pos += 2
    for i in range(min(5, num_events)):
        frame = struct.unpack('<I', data[pos:pos+4])[0]
        pos += 4
        
        name_len = struct.unpack('<I', data[pos:pos+4])[0]
        pos += 4
        name = data[pos:pos+name_len].decode('utf-8', errors='ignore')
        pos += name_len
        
        user_str_len = struct.unpack('<I', data[pos:pos+4])[0]
        pos += 4
        user_str = data[pos:pos+user_str_len].decode('utf-8', errors='ignore')
        pos += user_str_len
        
        user_int = struct.unpack('<I', data[pos:pos+4])[0]
        pos += 4
        
        print(f"  Event {i}: frame={frame}, name='{name}', user='{user_str}', int={user_int}")

def check_quantization(path, label):
    """Check for NaN/Inf in quantization parameters."""
    with open(path, 'rb') as f:
        data = f.read()
    
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    pos = head_pos + 8
    end = pos + head_size
    
    print(f"\n=== {label} Quantization Check ===")
    issues = 0
    bone_idx = 0
    
    while pos < end and bone_idx < 67:
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
        name = data[pos:pos+nameLen].decode('ascii', errors='ignore'); pos += nameLen
        
        # Check for NaN/Inf
        import math
        for val, fname in [(posBias, 'posBias'), (posMult, 'posMult'),
                           (rotBias, 'rotBias'), (rotMult, 'rotMult'),
                           (scaleBias, 'scaleBias'), (scaleMult, 'scaleMult')]:
            if math.isnan(val) or math.isinf(val):
                print(f"  Bone {bone_idx} ({name}): {fname}={val} ❌ INVALID")
                issues += 1
        
        # Check for negative frame counts
        if numFrames < 0 or numPosKeys < 0 or numRotKeys < 0 or numScaleKeys < 0:
            print(f"  Bone {bone_idx} ({name}): negative key count ❌ INVALID")
            issues += 1
        
        bone_idx += 1
    
    if issues == 0:
        print("✓ All quantization values valid")
    else:
        print(f"❌ Found {issues} invalid values")

def check_data_alignment(path, label):
    """Check DATA chunk byte alignment and consistency."""
    with open(path, 'rb') as f:
        data = f.read()
    
    data_pos = data.find(b'DATA')
    data_size = struct.unpack('>I', data[data_pos+4:data_pos+8])[0]
    data_start = data_pos + 8
    data_end = data_start + data_size
    
    print(f"\n=== {label} DATA Alignment ===")
    print(f"DATA chunk: pos={data_pos}, size={data_size}")
    print(f"DATA starts at byte {data_start}, ends at byte {data_end}")
    print(f"File size: {len(data)}")
    
    # Find next chunk
    next_chunk_pos = len(data)
    for chunk in [b'EVNT', b'CPRP', b'FORM', b'ANIM']:
        pos = data.find(chunk, data_end)
        if pos >= 0:
            next_chunk_pos = min(next_chunk_pos, pos)
            print(f"Next chunk '{chunk.decode()}' at {pos}")
    
    if next_chunk_pos > data_end:
        gap = next_chunk_pos - data_end
        print(f"Gap after DATA: {gap} bytes")
        if gap > 0 and gap < 20:
            print(f"  Hex: {data[data_end:next_chunk_pos].hex()}")

def compare_anm_structure(orig_path, gen_path):
    """Compare original vs generated in detail."""
    orig = Path(orig_path).read_bytes()
    gen = Path(gen_path).read_bytes()
    
    print("="*70)
    print("STAND_ATTACK_0 DETAILED COMPARISON")
    print("="*70)
    
    check_quantization(orig_path, "ORIGINAL")
    check_quantization(gen_path, "GENERATED")
    
    check_evnt_chunk(orig_path, "ORIGINAL")
    check_evnt_chunk(gen_path, "GENERATED")
    
    check_data_alignment(orig_path, "ORIGINAL")
    check_data_alignment(gen_path, "GENERATED")
    
    # Compare first DATA bytes
    orig_data_pos = orig.find(b'DATA') + 8
    gen_data_pos = gen.find(b'DATA') + 8
    
    print(f"\n=== First 64 bytes of DATA section ===")
    print("ORIGINAL:")
    print(hexdump(orig, orig_data_pos, 64))
    print("\nGENERATED:")
    print(hexdump(gen, gen_data_pos, 64))
    
    # Check CPRP chunk
    print(f"\n=== Custom Properties Chunk ===")
    orig_cprp = orig.find(b'CPRP')
    gen_cprp = gen.find(b'CPRP')
    print(f"Original has CPRP: {orig_cprp >= 0}")
    print(f"Generated has CPRP: {gen_cprp >= 0}")

if __name__ == '__main__':
    compare_anm_structure('example2/stand_attack_0_original.anm', 'example2/stand_attack_0.anm')
