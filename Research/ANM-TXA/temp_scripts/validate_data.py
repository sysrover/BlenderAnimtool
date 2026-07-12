#!/usr/bin/env python3
"""
Validate DATA chunk against HEAD entries to find the mismatch.
"""

import struct
from pathlib import Path

def validate_data_section(path, label):
    """Parse HEAD and verify DATA section matches exactly."""
    with open(path, 'rb') as f:
        data = f.read()
    
    # Find HEAD and DATA chunks
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    head_start = head_pos + 8
    head_end = head_start + head_size
    
    data_pos = data.find(b'DATA')
    data_size = struct.unpack('>I', data[data_pos+4:data_pos+8])[0]
    data_start = data_pos + 8
    
    print(f"\n=== {label} ===")
    print(f"Expected DATA size from HEAD: needs calculation")
    
    # Parse HEAD entries
    pos = head_start
    bone_idx = 0
    data_offset = 0
    expected_data_size = 0
    bones_info = []
    
    while pos < head_end and bone_idx < 67:
        pos += 24  # Skip bias/mult
        
        numFrames = struct.unpack('<h', data[pos:pos+2])[0]
        numPosKeys = struct.unpack('<h', data[pos+2:pos+4])[0]
        numRotKeys = struct.unpack('<h', data[pos+4:pos+6])[0]
        numScaleKeys = struct.unpack('<h', data[pos+6:pos+8])[0]
        pos += 8
        
        flags = struct.unpack('<B', data[pos:pos+1])[0]
        nameLen = struct.unpack('<B', data[pos+1:pos+2])[0]
        name = data[pos+2:pos+2+nameLen].decode('ascii', errors='ignore')
        pos += 2 + nameLen
        
        # Calculate DATA bytes for this bone
        pos_frame_bytes = numPosKeys * 2
        pos_value_bytes = numPosKeys * 6  # 3 uint16 per key
        scale_frame_bytes = numScaleKeys * 2
        scale_value_bytes = numScaleKeys * 6
        rot_frame_bytes = numRotKeys * 2
        rot_value_bytes = numRotKeys * 8  # 4 uint16 per key
        
        bone_data_size = pos_frame_bytes + pos_value_bytes + scale_frame_bytes + scale_value_bytes + rot_frame_bytes + rot_value_bytes
        expected_data_size += bone_data_size
        
        bones_info.append({
            'name': name,
            'pos_keys': numPosKeys,
            'rot_keys': numRotKeys,
            'scale_keys': numScaleKeys,
            'data_bytes': bone_data_size,
            'data_offset': data_offset
        })
        
        data_offset += bone_data_size
        bone_idx += 1
    
    print(f"Expected DATA size: {expected_data_size}")
    print(f"Actual DATA size: {data_size}")
    print(f"Match: {expected_data_size == data_size}")
    
    if expected_data_size != data_size:
        print(f"❌ MISMATCH of {data_size - expected_data_size} bytes")
        print(f"\nBones with > 0 keys (first 10):")
        for i, b in enumerate(bones_info[:10]):
            if b['pos_keys'] > 0 or b['rot_keys'] > 0 or b['scale_keys'] > 0:
                print(f"{i}: {b['name']:20s} | data_offset={b['data_offset']:5d} size={b['data_bytes']:5d} (pos={b['pos_keys']} rot={b['rot_keys']} scale={b['scale_keys']})")
        
        # Find where the mismatch starts
        print(f"\nScanning for first DATA mismatch...")
        
        # Try to reconstruct what DATA should look like
        pos = head_start
        bone_idx = 0
        expected_data_pos = 0
        
        while pos < head_end and bone_idx < 67:
            pos += 24  # Skip bias/mult
            numFrames = struct.unpack('<h', data[pos:pos+2])[0]
            numPosKeys = struct.unpack('<h', data[pos+2:pos+4])[0]
            numRotKeys = struct.unpack('<h', data[pos+4:pos+6])[0]
            numScaleKeys = struct.unpack('<h', data[pos+6:pos+8])[0]
            pos += 8
            
            flags = struct.unpack('<B', data[pos:pos+1])[0]
            nameLen = struct.unpack('<B', data[pos+1:pos+2])[0]
            name = data[pos+2:pos+2+nameLen].decode('ascii', errors='ignore')
            pos += 2 + nameLen
            
            # Positions
            pos_frame_bytes = numPosKeys * 2
            pos_value_bytes = numPosKeys * 6
            
            # Scales
            scale_frame_bytes = numScaleKeys * 2
            scale_value_bytes = numScaleKeys * 6
            
            # Rotations
            rot_frame_bytes = numRotKeys * 2
            rot_value_bytes = numRotKeys * 8
            
            actual_pos = data_start + expected_data_pos
            
            # Check if first key byte matches expected
            if numPosKeys > 0 and actual_pos + 1 < len(data):
                first_key = struct.unpack('<H', data[actual_pos:actual_pos+2])[0]
                if bone_idx < 3 or numPosKeys > 40:
                    print(f"  Bone {bone_idx:2d} ({name:20s}): pos_keys={numPosKeys:2d}, first_frame_idx={first_key}")
            
            expected_data_pos += pos_frame_bytes + pos_value_bytes + scale_frame_bytes + scale_value_bytes + rot_frame_bytes + rot_value_bytes
            bone_idx += 1
    else:
        print("✓ DATA size matches HEAD")

# Compare both
validate_data_section('example2/stand_attack_0_original.anm', 'ORIGINAL')
validate_data_section('example2/stand_attack_0.anm', 'GENERATED')
