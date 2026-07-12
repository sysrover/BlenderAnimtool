#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from DayzAnimationToolsBinary.Types.Anm import Anm

try:
    anm = Anm.CreateFromFile('examples/head_turn.anm')
    print(f'✓ ANM loaded successfully')
    print(f'  Format: {anm.format}')
    print(f'  FPS: {anm.fps}')
    print(f'  NumFrames: {anm.numFrames}')
    print(f'  NumBones: {len(anm.bones)}')
    for i, bone in enumerate(anm.bones):
        print(f'    Bone {i}: {bone.name}')
        print(f'      posKeys: {len(bone.posKeys)}')
        print(f'      rotKeys: {len(bone.rotKeys)}')
        print(f'      scaleKeys: {len(bone.scaleKeys)}')
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
