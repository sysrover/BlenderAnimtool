#!/usr/bin/env python3
"""Detailed byte-by-byte comparison of HEAD and DATA chunks"""
import struct

def analyze_anm(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    head_start = head_pos + 8
    
    data_pos = data.find(b'DATA')
    data_size = struct.unpack('>I', data[data_pos+4:data_pos+8])[0]
    data_start = data_pos + 8
    
    return data, head_start, head_size, data_start, data_size

ours, our_head_start, our_head_size, our_data_start, our_data_size = analyze_anm('examples/stand_roar_new.anm')
ref, ref_head_start, ref_head_size, ref_data_start, ref_data_size = analyze_anm('examples/stand_walk_fwd_original.anm')

print("="*80)
print("HEAD CHUNK BYTE-BY-BYTE COMPARISON")
print("="*80)

# Compare HEAD byte by byte (both have same size so can compare)
head_compare_size = min(our_head_size, ref_head_size)
diffs = []
for i in range(head_compare_size):
    our_b = ours[our_head_start + i]
    ref_b = ref[ref_head_start + i]
    if our_b != ref_b:
        diffs.append((i, our_b, ref_b))

if diffs:
    print(f"\nFound {len(diffs)} byte differences in HEAD (first 20):")
    for offset, our_byte, ref_byte in diffs[:20]:
        # Try to decode context
        print(f"  Offset 0x{offset:04x}: ours=0x{our_byte:02x} ({our_byte:3d})  vs  ref=0x{ref_byte:02x} ({ref_byte:3d})")
else:
    print("\nHEAD chunks are IDENTICAL!")

print("\n" + "="*80)
print("DATA CHUNK BYTE-BY-BYTE COMPARISON")
print("="*80)

# Compare first 500 bytes of DATA
data_compare_size = min(500, our_data_size, ref_data_size)
data_diffs = []
for i in range(data_compare_size):
    our_b = ours[our_data_start + i]
    ref_b = ref[ref_data_start + i]
    if our_b != ref_b:
        data_diffs.append((i, our_b, ref_b))

if data_diffs:
    print(f"\nFound {len(data_diffs)} byte differences in first {data_compare_size} bytes of DATA:")
    for offset, our_byte, ref_byte in data_diffs[:15]:
        print(f"  Offset 0x{offset:04x}: ours=0x{our_byte:02x}  vs  ref=0x{ref_byte:02x}")
else:
    print(f"\nFirst {data_compare_size} bytes of DATA are IDENTICAL!")

# Check DATA structure by parsing Scene_Root data
print("\n" + "="*80)
print("DATA SECTION STRUCTURE ANALYSIS")
print("="*80)

def parse_scene_root_data(data, data_start):
    """Parse Scene_Root data from DATA chunk"""
    pos = data_start
    
    # Scene_Root pos frames: 1 frame (frame 0)
    print(f"\nScene_Root position frames:")
    frame_idx = struct.unpack('<H', data[pos:pos+2])[0]
    print(f"  Frame: {frame_idx}")
    pos += 2
    
    # Scene_Root pos values: 1 frame * 3 values
    print(f"Scene_Root position values:")
    for i in range(1):
        x = struct.unpack('<H', data[pos:pos+2])[0]
        y = struct.unpack('<H', data[pos+2:pos+4])[0]
        z = struct.unpack('<H', data[pos+4:pos+6])[0]
        print(f"  Frame {i}: x=0x{x:04x} y=0x{y:04x} z=0x{z:04x}")
        pos += 6
    
    # Scene_Root scale frames: 1 frame (frame 0)
    print(f"\nScene_Root scale frames:")
    frame_idx = struct.unpack('<H', data[pos:pos+2])[0]
    print(f"  Frame: {frame_idx}")
    pos += 2
    
    # Scene_Root scale values: 1 frame * 3 values
    print(f"Scene_Root scale values:")
    for i in range(1):
        x = struct.unpack('<H', data[pos:pos+2])[0]
        y = struct.unpack('<H', data[pos+2:pos+4])[0]
        z = struct.unpack('<H', data[pos+4:pos+6])[0]
        print(f"  Frame {i}: x=0x{x:04x} y=0x{y:04x} z=0x{z:04x}")
        pos += 6
    
    # Scene_Root rot frames: 0 frames (no rotation keys)
    print(f"\nScene_Root rotation frames: 0 (none expected)")
    
    return pos

print("\nOUR OUTPUT:")
our_pos = parse_scene_root_data(ours, our_data_start)

print("\n\nWORKING REFERENCE:")
ref_pos = parse_scene_root_data(ref, ref_data_start)

print("\n" + "="*80)
print("HIP BONE DATA ANALYSIS (first few keyframes)")
print("="*80)

def parse_hip_data(data, data_start):
    """Skip to hip bone (second bone) and show first few frames"""
    pos = data_start
    
    # Skip Scene_Root data
    # Scene_Root: 1 posFrame + 1*3 posVals + 1 scaleFrame + 1*3 scaleVals + 0 rotFrames
    pos += 2 + 6 + 2 + 6  # = 16 bytes
    
    print(f"\nStarting at offset 0x{pos:04x} (where hip data should be)")
    
    # Hip pos frames: 69 frames (from compare_formats.py)
    print(f"Hip position frames (first 10):")
    for i in range(10):
        frame_idx = struct.unpack('<H', data[pos:pos+2])[0]
        print(f"  Frame {i}: {frame_idx}")
        pos += 2
    
    return pos

print("\nOUR OUTPUT HIP:")
parse_hip_data(ours, our_data_start)

print("\n\nWORKING REFERENCE HIP:")
parse_hip_data(ref, ref_data_start)
