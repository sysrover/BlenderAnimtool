#!/usr/bin/env python3
"""
Debug stand_attack_0.anm by comparing original vs generated binary structure.
"""

import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def read_file_bytes(path):
    """Read entire file as bytes."""
    with open(path, 'rb') as f:
        return f.read()

def parse_anm_header(data):
    """Parse ANM header structure and return key info."""
    if len(data) < 32:
        return None
    
    pos = 0
    # FORM tag
    form_tag = data[pos:pos+4].decode('ascii', errors='ignore')
    pos += 4
    form_size_be = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    
    # ANIMSET tag
    animset_tag = data[pos:pos+7].decode('ascii', errors='ignore')
    pos += 7
    format_char = data[pos]
    pos += 1
    
    return {
        'form_tag': form_tag,
        'form_size_be': form_size_be,
        'animset_tag': animset_tag,
        'format': format_char,
    }

def find_chunk(data, chunk_tag, start_pos=0):
    """Find chunk position and size by tag."""
    tag_bytes = chunk_tag.encode('ascii')
    pos = data.find(tag_bytes, start_pos)
    if pos == -1:
        return None, None, None
    
    # Read big-endian size
    if pos + 8 > len(data):
        return None, None, None
    
    size_be = struct.unpack('>I', data[pos+4:pos+8])[0]
    return pos, size_be, pos + 8  # return (chunk_pos, chunk_size, data_start)

def dump_head_section(data):
    """Dump HEAD section structure."""
    head_pos, head_size, head_data_pos = find_chunk(data, 'HEAD')
    if head_pos is None:
        return None
    
    print(f"\n=== HEAD Chunk ===")
    print(f"Position: {head_pos}, Size: {head_size}, Data starts at: {head_data_pos}")
    
    # Parse first 3 bones to see structure
    pos = head_data_pos
    bone_idx = 0
    bones = []
    
    while pos < head_pos + 8 + head_size and bone_idx < 3:
        bone = {}
        
        # Bone name (32 bytes for AnimSet5, variable for AnimSet6)
        name_start = pos
        # Try to detect string end
        name_len = 32
        for i in range(32):
            if data[pos + i] == 0:
                name_len = i
                break
        name = data[name_start:name_start+32].split(b'\x00')[0].decode('ascii', errors='ignore')
        pos += 32
        bone['name'] = name
        
        # Read bias/mult (6 floats)
        bone['posBias'] = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        bone['posMult'] = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        bone['rotBias'] = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        bone['rotMult'] = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        bone['scaleBias'] = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        bone['scaleMult'] = struct.unpack('<f', data[pos:pos+4])[0]; pos += 4
        
        # Read frame counts (4 shorts)
        bone['numFrames'] = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        bone['numPosKeys'] = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        bone['numRotKeys'] = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        bone['numScaleKeys'] = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        
        # Flags (2 bytes for AnimSet5)
        bone['flags'] = struct.unpack('<h', data[pos:pos+2])[0]; pos += 2
        
        bones.append(bone)
        bone_idx += 1
    
    for i, bone in enumerate(bones):
        print(f"\nBone {i}: {bone['name']}")
        print(f"  posBias={bone['posBias']:.6f}, posMult={bone['posMult']:.10e}")
        print(f"  rotBias={bone['rotBias']:.6f}, rotMult={bone['rotMult']:.10e}")
        print(f"  scaleBias={bone['scaleBias']:.6f}, scaleMult={bone['scaleMult']:.10e}")
        print(f"  numFrames={bone['numFrames']}, numPosKeys={bone['numPosKeys']}, numRotKeys={bone['numRotKeys']}, numScaleKeys={bone['numScaleKeys']}")
        print(f"  flags={bone['flags']}")
    
    return bones

def compare_files(orig_path, gen_path):
    """Compare original vs generated ANM files."""
    orig = read_file_bytes(orig_path)
    gen = read_file_bytes(gen_path)
    
    print(f"Original file size: {len(orig)} bytes")
    print(f"Generated file size: {len(gen)} bytes")
    print(f"Size difference: {len(gen) - len(orig)} bytes\n")
    
    # Parse headers
    orig_header = parse_anm_header(orig)
    gen_header = parse_anm_header(gen)
    
    print("=== Header Comparison ===")
    print(f"Original header: {orig_header}")
    print(f"Generated header: {gen_header}")
    
    # Find chunks
    print("\n=== Chunk Analysis ===")
    
    # HEAD chunk
    orig_head_pos, orig_head_size, _ = find_chunk(orig, 'HEAD')
    gen_head_pos, gen_head_size, _ = find_chunk(gen, 'HEAD')
    print(f"Original HEAD: pos={orig_head_pos}, size={orig_head_size}")
    print(f"Generated HEAD: pos={gen_head_pos}, size={gen_head_size}")
    
    # DATA chunk
    orig_data_pos, orig_data_size, _ = find_chunk(orig, 'DATA')
    gen_data_pos, gen_data_size, _ = find_chunk(gen, 'DATA')
    print(f"Original DATA: pos={orig_data_pos}, size={orig_data_size}")
    print(f"Generated DATA: pos={gen_data_pos}, size={gen_data_size}")
    
    # EVNT chunk (optional)
    orig_evnt_pos, orig_evnt_size, _ = find_chunk(orig, 'EVNT')
    gen_evnt_pos, gen_evnt_size, _ = find_chunk(gen, 'EVNT')
    print(f"Original EVNT: pos={orig_evnt_pos}, size={orig_evnt_size}")
    print(f"Generated EVNT: pos={gen_evnt_pos}, size={gen_evnt_size}")
    
    # Dump HEAD sections
    print("\n=== Original HEAD Section (first 3 bones) ===")
    dump_head_section(orig)
    
    print("\n=== Generated HEAD Section (first 3 bones) ===")
    dump_head_section(gen)
    
    # Byte-level comparison of first 100 bytes
    print("\n=== First 100 bytes comparison ===")
    for i in range(min(100, len(orig), len(gen))):
        if orig[i] != gen[i]:
            print(f"Byte {i}: orig=0x{orig[i]:02x}, gen=0x{gen[i]:02x}")

if __name__ == '__main__':
    orig_path = Path(r'p:\ANM-TXA\example2\stand_attack_0_original.anm')
    gen_path = Path(r'p:\ANM-TXA\example2\stand_attack_0.anm')
    
    compare_files(orig_path, gen_path)
