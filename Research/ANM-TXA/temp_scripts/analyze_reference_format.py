#!/usr/bin/env python3
"""
Reverse-engineer ANM binary format by analyzing a reference file.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from DayzAnimationToolsBinary.Types.Anm import Anm

# Load a reference ANM to understand the exact structure
ref_path = pathlib.Path('examples/stand_roar.anm')
if not ref_path.exists():
    # Try stand_walk_fwd_original
    ref_path = pathlib.Path('examples/stand_walk_fwd_original.anm')

if not ref_path.exists():
    print("No reference ANM found")
    sys.exit(1)

anm = Anm.CreateFromFile(str(ref_path))

print(f"File: {ref_path.name}")
print(f"Format: {anm.format}")
print(f"FPS: {anm.fps}")
print(f"numFrames: {anm.numFrames}")
print(f"Total bones: {len(anm.bones)}")
print()

# Examine first 5 bones in detail
for idx, bone in enumerate(anm.bones[:5]):
    print(f"Bone {idx}: {bone.name}")
    print(f"  posBias={bone.posBias:.10f}, posMulti={bone.posMulti:.15e}")
    print(f"  rotBias={bone.rotBias:.10f}, rotMulti={bone.rotMulti:.15e}")
    print(f"  scaleBias={bone.scaleBias:.10f}, scaleMulti={bone.scaleMulti:.15e}")
    print(f"  numFrames={bone.numFrames}")
    print(f"  posKeys={len(bone.posKeys)}, rotKeys={len(bone.rotKeys)}, scaleKeys={len(bone.scaleKeys)}")
    
    # Show first 3 and last 3 keys per channel
    if bone.posKeys:
        first3 = bone.posKeys[:3]
        last3 = bone.posKeys[-3:]
        print(f"    pos frames: {[k.frame for k in first3]} ... {[k.frame for k in last3]}")
    
    if bone.rotKeys:
        first3 = bone.rotKeys[:3]
        last3 = bone.rotKeys[-3:]
        print(f"    rot frames: {[k.frame for k in first3]} ... {[k.frame for k in last3]}")
    
    if bone.scaleKeys:
        frames = [k.frame for k in bone.scaleKeys]
        print(f"    scale frames: {frames}")
    
    print()
