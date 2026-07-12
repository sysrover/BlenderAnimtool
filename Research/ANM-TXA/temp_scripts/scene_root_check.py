#!/usr/bin/env python3
import struct

def get_scene_root_info(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    head_pos = data.find(b'HEAD')
    head_size = struct.unpack('>I', data[head_pos+4:head_pos+8])[0]
    pos = head_pos + 8
    
    # First bone is Scene_Root
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
    
    return {
        'posMult': posMult,
        'rotMult': rotMult,
        'scaleMult': scaleMult,
        'numFrames': numFrames,
        'numPosKeys': numPosKeys,
        'numRotKeys': numRotKeys,
        'numScaleKeys': numScaleKeys
    }

orig = get_scene_root_info('example2/stand_attack_0_original.anm')
gen = get_scene_root_info('example2/stand_attack_0.anm')

print('Scene_Root comparison:')
for key in ['numFrames', 'numPosKeys', 'numRotKeys', 'numScaleKeys', 'posMult', 'rotMult', 'scaleMult']:
    o = orig[key]
    g = gen[key]
    match = '✓' if o == g else '❌'
    print(f'  {key}: orig={o} gen={g} {match}')
