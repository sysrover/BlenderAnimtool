#!/usr/bin/env python3
"""Compare full HEAD and DATA chunks between broken and working ANMs"""
import struct

def dump_anm_structure(filename, label):
    print(f"\n{'='*80}")
    print(f"ANALYZING: {label}")
    print(f"{'='*80}")
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Find FORM header
    if data[:4] != b'FORM':
        print(f"ERROR: Not a valid ANM file (no FORM header)")
        return
    
    form_size = struct.unpack('>I', data[4:8])[0]
    print(f"FORM size: {form_size} bytes (0x{form_size:x})")
    
    # Find FPS chunk (after ANIMSET)
    fps_pos = data.find(b'FPS\x00')
    if fps_pos > 0:
        fps_val = struct.unpack('<I', data[fps_pos+8:fps_pos+12])[0]
        print(f"FPS: {fps_val}")
    
    # Find HEAD chunk
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    head_start = head_pos + 8
    print(f"\nHEAD chunk at 0x{head_pos:04x}, size: {head_size} bytes (0x{head_size:x})")
    
    # Parse HEAD structure - iterate through bones
    print("\n--- PER-BONE METADATA (HEAD) ---")
    pos = head_start
    bone_idx = 0
    while pos < head_start + head_size:
        # Read bias/mult for pos
        pos_bias = struct.unpack('<f', data[pos:pos+4])[0]
        pos_mult_raw = struct.unpack('<f', data[pos+4:pos+8])[0]
        pos += 8
        
        # Read bias/mult for rot
        rot_bias = struct.unpack('<f', data[pos:pos+4])[0]
        rot_mult_raw = struct.unpack('<f', data[pos+4:pos+8])[0]
        pos += 8
        
        # Read bias/mult for scale
        scale_bias = struct.unpack('<f', data[pos:pos+4])[0]
        scale_mult_raw = struct.unpack('<f', data[pos+4:pos+8])[0]
        pos += 8
        
        # Read numFrames (i16)
        num_frames = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        
        # Read key counts (3x i16)
        num_pos_keys = struct.unpack('<H', data[pos:pos+2])[0]
        num_rot_keys = struct.unpack('<H', data[pos+2:pos+4])[0]
        num_scale_keys = struct.unpack('<H', data[pos+4:pos+6])[0]
        pos += 6
        
        # Read flags (u8) and nameLen (u8)
        flags = data[pos]
        nameLen = data[pos+1]
        pos += 2
        
        # Read bone name
        name = data[pos:pos+nameLen].decode('ascii', errors='ignore')
        pos += nameLen
        
        if bone_idx < 5 or bone_idx >= 65:  # Show first 5 and last 2
            print(f"\nBone {bone_idx}: '{name}'")
            print(f"  posBias={pos_bias:.6f}, posMultRaw={pos_mult_raw:.6e}")
            print(f"  rotBias={rot_bias:.6f}, rotMultRaw={rot_mult_raw:.6e}")
            print(f"  scaleBias={scale_bias:.6f}, scaleMultRaw={scale_mult_raw:.6e}")
            print(f"  numFrames={num_frames}, #posKeys={num_pos_keys}, #rotKeys={num_rot_keys}, #scaleKeys={num_scale_keys}")
        elif bone_idx == 5:
            print(f"  ... (bones 5-64 omitted) ...")
        
        bone_idx += 1
    
    # Find DATA chunk
    data_pos = data.find(b'DATA')
    data_size = struct.unpack('>I', data[data_pos+4:data_pos+8])[0]
    data_start = data_pos + 8
    print(f"\n\nDATA chunk at 0x{data_pos:04x}, size: {data_size} bytes (0x{data_size:x})")
    
    # Show first 256 bytes of DATA
    print(f"\n--- DATA CHUNK RAW (first 256 bytes) ---")
    for i in range(0, min(256, data_size), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[data_start+i:data_start+i+16])
        print(f'0x{data_start+i:04x}:  {hex_str}')

# Compare both files
dump_anm_structure('examples/stand_roar_new.anm', 'OUR OUTPUT (stand_roar_new.anm)')
dump_anm_structure('examples/stand_walk_fwd_original.anm', 'WORKING REFERENCE (stand_walk_fwd_original.anm)')
