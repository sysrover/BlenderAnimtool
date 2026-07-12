#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from DayzAnimationToolsBinary.Types.Anm import Anm

try:
    anm = Anm.CreateFromFile(sys.argv[1] if len(sys.argv) > 1 else 'examples/stand_alerted.anm')
    print(f'✓ ANM loaded successfully')
    print(f'  Format: {anm.format}')
    print(f'  FPS: {anm.fps}')
    print(f'  NumFrames: {anm.numFrames}')
    print(f'  NumBones: {len(anm.bones)}')
    
    # Show entityposition if it exists
    for i, bone in enumerate(anm.bones):
        if 'entityposition' in bone.name.lower():
            print(f'\n  Bone {i}: {bone.name}')
            print(f'    posKeys: {len(bone.posKeys)}')
            print(f'    rotKeys: {len(bone.rotKeys)}')
            print(f'    scaleKeys: {len(bone.scaleKeys)}')
            if bone.posKeys:
                print(f'      First pos key: frame {bone.posKeys[0].frame}, data {bone.posKeys[0].data}')
            if bone.rotKeys:
                print(f'      First rot key: frame {bone.rotKeys[0].frame}, data {bone.rotKeys[0].data}')
            break
    else:
        print(f'\nNo entityposition bone found. First 5 bones:')
        for i, bone in enumerate(anm.bones[:5]):
            print(f'  Bone {i}: {bone.name}')
            print(f'    posKeys: {len(bone.posKeys)}, rotKeys: {len(bone.rotKeys)}, scaleKeys: {len(bone.scaleKeys)}')
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
