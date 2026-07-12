#!/usr/bin/env python3
"""
Use actual ANM reader to compare original vs generated stand_attack_0.anm
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load the ANM reader
from anm_to_txa import load_anm

def analyze_anm(path, label):
    """Load and analyze ANM file."""
    try:
        anm = load_anm(path)
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
        
        print(f"\nFirst 5 bones:")
        for i, bone in enumerate(anm.bones[:5]):
            print(f"  {i}: {bone.name:20s} | pos={len(bone.posKeys):4d} rot={len(bone.rotKeys):4d} scale={len(bone.scaleKeys):4d}")
        
        # Check for anomalies
        print(f"\nQuant Analysis (first 3 bones):")
        for i, bone in enumerate(anm.bones[:3]):
            print(f"  {i}: {bone.name:20s}")
            print(f"      posBias={bone.posBias:.6f}, posMult={bone.posMulti:.10e}")
            print(f"      rotBias={bone.rotBias:.6f}, rotMult={bone.rotMulti:.10e}")
            print(f"      scaleBias={bone.scaleBias:.6f}, scaleMult={bone.scaleMulti:.10e}")
        
        return anm
    except Exception as e:
        print(f"\n!!! ERROR reading {label}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    orig_path = Path(r'p:\ANM-TXA\example2\stand_attack_0_original.anm')
    gen_path = Path(r'p:\ANM-TXA\example2\stand_attack_0.anm')
    
    orig = analyze_anm(orig_path, "ORIGINAL stand_attack_0.anm")
    gen = analyze_anm(gen_path, "GENERATED stand_attack_0.anm")
    
    if orig and gen:
        print("\n=== COMPARISON ===")
        if orig.numFrames != gen.numFrames:
            print(f"❌ numFrames differ: orig={orig.numFrames}, gen={gen.numFrames}")
        else:
            print(f"✓ numFrames match: {orig.numFrames}")
        
        if orig.fps != gen.fps:
            print(f"❌ FPS differ: orig={orig.fps}, gen={gen.fps}")
        else:
            print(f"✓ FPS match: {orig.fps}")
        
        if len(orig.bones) != len(gen.bones):
            print(f"❌ Bone count differ: orig={len(orig.bones)}, gen={len(gen.bones)}")
        else:
            print(f"✓ Bone count match: {len(orig.bones)}")
            
            # Compare per-bone key counts
            print(f"\nPer-bone key count differences:")
            total_pos_diff = 0
            total_rot_diff = 0
            total_scale_diff = 0
            
            for i, (orig_bone, gen_bone) in enumerate(zip(orig.bones, gen.bones)):
                pos_diff = len(gen_bone.posKeys) - len(orig_bone.posKeys)
                rot_diff = len(gen_bone.rotKeys) - len(orig_bone.rotKeys)
                scale_diff = len(gen_bone.scaleKeys) - len(orig_bone.scaleKeys)
                
                if pos_diff != 0 or rot_diff != 0 or scale_diff != 0:
                    print(f"  {i}: {gen_bone.name:20s} | pos{pos_diff:+5d} rot{rot_diff:+5d} scale{scale_diff:+5d}")
                
                total_pos_diff += pos_diff
                total_rot_diff += rot_diff
                total_scale_diff += scale_diff
            
            print(f"\nTotal key differences:")
            print(f"  PosKeys:   {total_pos_diff:+d}")
            print(f"  RotKeys:   {total_rot_diff:+d}")
            print(f"  ScaleKeys: {total_scale_diff:+d}")

if __name__ == '__main__':
    main()
