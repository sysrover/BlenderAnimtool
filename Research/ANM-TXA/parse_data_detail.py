#!/usr/bin/env python3
"""Parse DATA section structure in detail"""
import struct

def show_data_structure(filename, label):
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    data_pos = data.find(b'DATA')
    data_start = data_pos + 8
    
    # Parse each bone's data: pos frames, pos values, scale frames, scale values, rot frames, rot values
    
    # From HEAD we know bone counts
    head_pos = data.find(b'HEAD')
    head_start = head_pos + 8
    
    pos = head_start
    bone_idx = 0
    bone_info = []
    
    # Parse HEAD to get key counts for first 2 bones
    for b in range(2):
        # Skip to key counts
        pos_bias_pos = pos
        pos += 24  # skip to numFrames
        
        num_frames = struct.unpack('<H', data[pos:pos+2])[0]
        num_pos_keys = struct.unpack('<H', data[pos+2:pos+4])[0]
        num_rot_keys = struct.unpack('<H', data[pos+4:pos+6])[0]
        num_scale_keys = struct.unpack('<H', data[pos+6:pos+8])[0]
        
        flags = data[pos+8]
        nameLen = data[pos+9]
        name = data[pos+10:pos+10+nameLen].decode('ascii', errors='ignore')
        
        bone_info.append((name, num_pos_keys, num_rot_keys, num_scale_keys))
        pos += 10 + nameLen
        
        print(f"\nBone {b}: {name}")
        print(f"  #posKeys={num_pos_keys}, #rotKeys={num_rot_keys}, #scaleKeys={num_scale_keys}")
    
    # Now parse DATA
    print(f"\n--- DATA STRUCTURE ---")
    
    # Bone 0 (Scene_Root)
    pos = data_start
    print(f"\nSceneRoot DATA at offset 0x{pos:04x}:")
    
    name, npos, nrot, nscale = bone_info[0]
    
    print(f"  Position frames ({npos} frames):")
    frame_indices = []
    for i in range(npos):
        frame = struct.unpack('<H', data[pos:pos+2])[0]
        frame_indices.append(frame)
        print(f"    Frame[{i}]: {frame} (0x{frame:04x})")
        pos += 2
    
    print(f"  Position values ({npos} frames * 3 values):")
    for i in range(npos):
        x = struct.unpack('<H', data[pos:pos+2])[0]
        y = struct.unpack('<H', data[pos+2:pos+4])[0]
        z = struct.unpack('<H', data[pos+4:pos+6])[0]
        print(f"    Value[{i}]: x=0x{x:04x} y=0x{y:04x} z=0x{z:04x}")
        pos += 6
    
    print(f"  Scale frames ({nscale} frames):")
    for i in range(nscale):
        frame = struct.unpack('<H', data[pos:pos+2])[0]
        print(f"    Frame[{i}]: {frame} (0x{frame:04x})")
        pos += 2
    
    print(f"  Scale values ({nscale} frames * 3 values):")
    for i in range(nscale):
        x = struct.unpack('<H', data[pos:pos+2])[0]
        y = struct.unpack('<H', data[pos+2:pos+4])[0]
        z = struct.unpack('<H', data[pos+4:pos+6])[0]
        print(f"    Value[{i}]: x=0x{x:04x} y=0x{y:04x} z=0x{z:04x}")
        pos += 6
    
    print(f"  Rotation frames ({nrot} frames):")
    for i in range(nrot):
        frame = struct.unpack('<H', data[pos:pos+2])[0]
        print(f"    Frame[{i}]: {frame} (0x{frame:04x})")
        pos += 2
    
    print(f"  Rotation values ({nrot} frames * 4 values):")
    for i in range(nrot):
        x = struct.unpack('<H', data[pos:pos+2])[0]
        y = struct.unpack('<H', data[pos+2:pos+4])[0]
        z = struct.unpack('<H', data[pos+4:pos+6])[0]
        w = struct.unpack('<H', data[pos+6:pos+8])[0]
        print(f"    Value[{i}]: x=0x{x:04x} y=0x{y:04x} z=0x{z:04x} w=0x{w:04x}")
        pos += 8
    
    print(f"\nBone 0 DATA ends at offset 0x{pos:04x}")
    
    # Bone 1 (hip)
    print(f"\n--- HIP BONE DATA ---")
    print(f"Hip DATA starts at offset 0x{pos:04x}:")
    
    name, npos, nrot, nscale = bone_info[1]
    print(f"  #posKeys={npos}, #rotKeys={nrot}, #scaleKeys={nscale}")
    
    print(f"  Position frames (first 5):")
    for i in range(min(5, npos)):
        frame = struct.unpack('<H', data[pos:pos+2])[0]
        print(f"    Frame[{i}]: {frame} (0x{frame:04x})")
        pos += 2
    pos += (npos - 5) * 2  # Skip remaining frames
    
    print(f"  Position values (first 2):")
    for i in range(min(2, npos)):
        x = struct.unpack('<H', data[pos:pos+2])[0]
        y = struct.unpack('<H', data[pos+2:pos+4])[0]
        z = struct.unpack('<H', data[pos+4:pos+6])[0]
        print(f"    Value[{i}]: x=0x{x:04x} y=0x{y:04x} z=0x{z:04x}")
        pos += 6
    pos += (npos - 2) * 6  # Skip remaining values

show_data_structure('examples/stand_roar_new.anm', 'OUR OUTPUT')
show_data_structure('examples/stand_walk_fwd_original.anm', 'WORKING REFERENCE')
