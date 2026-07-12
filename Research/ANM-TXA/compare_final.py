#!/usr/bin/env python3
"""
Compare original vs final rebuilt stand_attack_0.anm
"""

import sys
from pathlib import Path

sys.path.insert(0, 'p:\\ANM-TXA')

from DayzAnimationToolsBinary.Types.Anm import Anm

def analyze_anm(path, label):
    """Load and analyze ANM file."""
    try:
        anm = Anm.CreateFromFile(str(path))
        print(f"\n=== {label} ===")
        print(f"Format: AnimSet{anm.format.value}")
        print(f"FPS: {anm.fps}")
        print(f"Num Frames: {anm.numFrames}")
        print(f"Num Bones: {len(anm.bones)}")
        total_pos = sum(len(b.posKeys) for b in anm.bones)
        total_rot = sum(len(b.rotKeys) for b in anm.bones)
        total_scale = sum(len(b.scaleKeys) for b in anm.bones)
        print(f"Total PosKeys: {total_pos}")
        print(f"Total RotKeys: {total_rot}")
        print(f"Total ScaleKeys: {total_scale}")
        
        print(f"\nFirst 10 bones:")
        for i, bone in enumerate(anm.bones[:10]):
            print(f"  {i}: {bone.name:<20} | pos={len(bone.posKeys):4d} rot={len(bone.rotKeys):4d} scale={len(bone.scaleKeys):4d}")
        
        return anm
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def main():
    orig_path = Path(r'p:\ANM-TXA\example2\stand_attack_0_original.anm')
    final_path = Path(r'p:\ANM-TXA\example2\stand_attack_0_final.anm')
    
    orig = analyze_anm(orig_path, "ORIGINAL stand_attack_0_original.anm")
    final = analyze_anm(final_path, "FINAL stand_attack_0_final.anm")
    
    if orig and final:
        print(f"\n=== COMPARISON ===")
        total_pos_diff = 0
        total_rot_diff = 0
        total_scale_diff = 0
        
        for i, (b1, b2) in enumerate(zip(orig.bones, final.bones)):
            pos_diff = len(b2.posKeys) - len(b1.posKeys)
            rot_diff = len(b2.rotKeys) - len(b1.rotKeys)
            scale_diff = len(b2.scaleKeys) - len(b1.scaleKeys)
            
            if pos_diff != 0 or rot_diff != 0 or scale_diff != 0:
                print(f"  {b1.name:<20} | pos{pos_diff:+3d} rot{rot_diff:+3d} scale{scale_diff:+3d}")
            
            total_pos_diff += pos_diff
            total_rot_diff += rot_diff
            total_scale_diff += scale_diff
        
        print(f"\nTotal key differences:")
        print(f"  PosKeys:   {total_pos_diff:+d}")
        print(f"  RotKeys:   {total_rot_diff:+d}")
        print(f"  ScaleKeys: {total_scale_diff:+d}")

if __name__ == '__main__':
    main()
