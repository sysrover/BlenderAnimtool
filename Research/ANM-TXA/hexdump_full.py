#!/usr/bin/env python3
"""Full HEAD and DATA hexdump comparison"""
import struct

def hexdump_chunks(filename, label):
    print(f"\n{'='*100}")
    print(f"{label}")
    print(f"{'='*100}\n")
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Find FORM header
    print(f"File size: {len(data)} bytes (0x{len(data):x})")
    
    if data[:4] != b'FORM':
        print("ERROR: Not valid ANM format")
        return
    
    form_size = struct.unpack('>I', data[4:8])[0]
    print(f"FORM size: {form_size} (0x{form_size:x})")
    
    # Find ANIMSET version
    animset_pos = data.find(b'ANIMSET')
    version = data[animset_pos + 7]
    print(f"AnimSet version: {version}")
    
    # Find FPS chunk
    fps_pos = data.find(b'FPS\x00')
    if fps_pos > 0:
        fps_val = struct.unpack('<I', data[fps_pos+8:fps_pos+12])[0]
        print(f"FPS chunk at 0x{fps_pos:04x}: fps={fps_val}")
    
    # Find HEAD chunk
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    head_start = head_pos + 8
    print(f"\nHEAD chunk at 0x{head_pos:04x}, size={head_size} (0x{head_size:x})")
    print(f"HEAD content starts at 0x{head_start:04x}, ends at 0x{head_start+head_size:04x}\n")
    
    # Full HEAD hexdump
    print("--- HEAD CHUNK (complete) ---")
    for i in range(0, min(head_size, 2048), 32):
        hex_str = ' '.join(f'{b:02x}' for b in data[head_start+i:head_start+i+32])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[head_start+i:head_start+i+32])
        print(f'0x{head_start+i:04x}:  {hex_str:<97} | {ascii_str}')
    
    if head_size > 2048:
        print(f"... ({head_size - 2048} bytes omitted) ...")
        i = head_size - 256
        hex_str = ' '.join(f'{b:02x}' for b in data[head_start+i:head_start+i+256])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[head_start+i:head_start+i+256])
        print(f'0x{head_start+i:04x}:  {hex_str:<97}')
        print(f'         {ascii_str}')
    
    # Find DATA chunk
    data_pos = data.find(b'DATA')
    data_size = struct.unpack('>I', data[data_pos+4:data_pos+8])[0]
    data_start = data_pos + 8
    print(f"\n\nDATA chunk at 0x{data_pos:04x}, size={data_size} (0x{data_size:x})")
    print(f"DATA content starts at 0x{data_start:04x}, ends at 0x{data_start+data_size:04x}\n")
    
    # First 512 bytes of DATA
    print("--- DATA CHUNK (first 512 bytes) ---")
    for i in range(0, min(512, data_size), 32):
        hex_str = ' '.join(f'{b:02x}' for b in data[data_start+i:data_start+i+32])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[data_start+i:data_start+i+32])
        print(f'0x{data_start+i:04x}:  {hex_str:<97} | {ascii_str}')
    
    # Check if there are EVNT or CPRP chunks
    evnt_pos = data.find(b'EVNT')
    if evnt_pos > 0:
        evnt_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
        print(f"\n\nEVNT chunk at 0x{evnt_pos:04x}, size={evnt_size}")
    else:
        print("\n\nNo EVNT chunk found")
    
    cprp_pos = data.find(b'CPRP')
    if cprp_pos > 0:
        cprp_size = struct.unpack('>I', data[cprp_pos+4:cprp_pos+8])[0]
        print(f"CPRP chunk at 0x{cprp_pos:04x}, size={cprp_size}")
    else:
        print("No CPRP chunk found")

hexdump_chunks('examples/stand_roar_new.anm', 'OUR OUTPUT (stand_roar_new.anm)')
hexdump_chunks('examples/stand_walk_fwd_original.anm', 'WORKING REFERENCE (stand_walk_fwd_original.anm)')
