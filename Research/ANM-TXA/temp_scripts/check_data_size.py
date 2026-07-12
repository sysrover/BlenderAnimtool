#!/usr/bin/env python3
"""
Calculate expected DATA size from HEAD entries and compare with actual.
"""

import struct
from pathlib import Path

def analyze_data_layout(path, label):
    """Calculate expected DATA bytes from HEAD entries."""
    with open(path, 'rb') as f:
        data = f.read()
    
    # Find HEAD chunk
    head_pos = data.find(b'HEAD')
    head_size_be = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    head_data_start = head_pos + 8
    head_data_end = head_data_start + head_size_be
    
    print(f"\n=== {label} ===")
    
    # Parse HEAD to get key counts
    pos = head_data_start
    total_pos_bytes = 0
    total_rot_bytes = 0
    total_scale_bytes = 0
    total_frame_indices = 0
    
    bone_idx = 0
    while pos < head_data_end and bone_idx < 67:
        # Read bias/mult (6 floats = 24 bytes)
        pos += 24
        
        # Read frame counts (4 shorts = 8 bytes)
        numFrames = struct.unpack('<h', data[pos:pos+2])[0]
        numPosKeys = struct.unpack('<h', data[pos+2:pos+4])[0]
        numRotKeys = struct.unpack('<h', data[pos+4:pos+6])[0]
        numScaleKeys = struct.unpack('<h', data[pos+6:pos+8])[0]
        pos += 8
        
        # Read flags and name
        flags = struct.unpack('<B', data[pos:pos+1])[0]
        nameLen = struct.unpack('<B', data[pos+1:pos+2])[0]
        pos += 2 + nameLen
        
        # Calculate DATA bytes for this bone
        # DATA layout: pos frames (uint16 each) + pos values (3 uint16 each)
        #             scale frames (uint16 each) + scale values (3 uint16 each)
        #             rot frames (uint16 each) + rot values (4 uint16 each)
        
        pos_frame_bytes = numPosKeys * 2
        pos_value_bytes = numPosKeys * 6  # 3 uint16s per key
        scale_frame_bytes = numScaleKeys * 2
        scale_value_bytes = numScaleKeys * 6  # 3 uint16s per key
        rot_frame_bytes = numRotKeys * 2
        rot_value_bytes = numRotKeys * 8  # 4 uint16s per key
        
        bone_total = pos_frame_bytes + pos_value_bytes + scale_frame_bytes + scale_value_bytes + rot_frame_bytes + rot_value_bytes
        
        total_pos_bytes += pos_frame_bytes + pos_value_bytes
        total_rot_bytes += rot_frame_bytes + rot_value_bytes
        total_scale_bytes += scale_frame_bytes + scale_value_bytes
        total_frame_indices += numPosKeys + numScaleKeys + numRotKeys
        
        if bone_idx < 3:
            print(f"Bone {bone_idx}: pos_keys={numPosKeys} ({bone_total} bytes)")
        
        bone_idx += 1
    
    expected_total = total_pos_bytes + total_rot_bytes + total_scale_bytes
    
    # Find DATA chunk to get actual size
    data_pos = data.find(b'DATA')
    data_size = struct.unpack('>I', data[data_pos+4:data_pos+8])[0]
    
    print(f"\nExpected DATA size (from HEAD): {expected_total}")
    print(f"Actual DATA size (chunk): {data_size}")
    print(f"Difference: {data_size - expected_total}")
    
    if data_size != expected_total:
        print(f"❌ MISMATCH! This will cause DeAnm Generic Error")
    else:
        print(f"✓ Match")
    
    print(f"\nBreakdown:")
    print(f"  Pos: {total_pos_bytes} bytes")
    print(f"  Scale: {total_scale_bytes} bytes")
    print(f"  Rot: {total_rot_bytes} bytes")
    print(f"  Total frame indices: {total_frame_indices}")

def main():
    analyze_data_layout('example2/stand_attack_0_original.anm', 'ORIGINAL')
    analyze_data_layout('example2/stand_attack_0.anm', 'GENERATED')

if __name__ == '__main__':
    main()
