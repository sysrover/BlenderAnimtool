#!/usr/bin/env python3
import struct

def get_bone_headers(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    pos = head_pos + 8
    end = pos + head_size
    
    bones = []
    while pos < end:
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
        
        bones.append({
            'name': name,
            'posBias': posBias, 'posMult': posMult,
            'rotBias': rotBias, 'rotMult': rotMult,
            'scaleBias': scaleBias, 'scaleMult': scaleMult,
            'numPosKeys': numPosKeys, 'numRotKeys': numRotKeys, 'numScaleKeys': numScaleKeys
        })
    
    return bones

orig_bones = get_bone_headers('example2/stand_attack_0_original.anm')
gen_bones = get_bone_headers('example2/stand_attack_0.anm')

print('Bones with different scale keys:')
for i, (o, g) in enumerate(zip(orig_bones, gen_bones)):
    if o['numScaleKeys'] != g['numScaleKeys']:
        print(f'{i}: {o["name"]:20s} | orig scale={o["numScaleKeys"]} gen scale={g["numScaleKeys"]}')
