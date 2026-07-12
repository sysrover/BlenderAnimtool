import sys
sys.path.insert(0, 'p:\\ANM-TXA')

from DayzAnimationToolsBinary.Types.Anm import Anm

orig = Anm.CreateFromFile('example2/stand_attack_0_original.anm')
roundtrip2 = Anm.CreateFromFile('example2/stand_attack_0_roundtrip2.anm')

print(f"COMPARISON: Original vs Roundtrip2 (ANM->TXA->ANM without frame collapsing)")
print(f"============================================================")

total_pos_diff = 0
total_rot_diff = 0
total_scale_diff = 0
mismatches = []

for i, (b1, b2) in enumerate(zip(orig.bones, roundtrip2.bones)):
    pos_diff = len(b2.posKeys) - len(b1.posKeys)
    rot_diff = len(b2.rotKeys) - len(b1.rotKeys)
    scale_diff = len(b2.scaleKeys) - len(b1.scaleKeys)
    
    if pos_diff != 0 or rot_diff != 0 or scale_diff != 0:
        mismatches.append((b1.name, pos_diff, rot_diff, scale_diff))
    
    total_pos_diff += pos_diff
    total_rot_diff += rot_diff
    total_scale_diff += scale_diff

if mismatches:
    print(f"\nBones with differences ({len(mismatches)}):")
    for name, pos, rot, scale in mismatches:
        print(f"  {name:<20} | pos{pos:+3d} rot{rot:+3d} scale{scale:+3d}")
else:
    print(f"\nAll bones match perfectly!")

print(f"\nTotal key differences:")
print(f"  PosKeys:   {total_pos_diff:+d}")
print(f"  RotKeys:   {total_rot_diff:+d}")
print(f"  ScaleKeys: {total_scale_diff:+d}")
print(f"\nOverall: {'PERFECT MATCH ✓✓✓' if total_pos_diff == 0 and total_rot_diff == 0 and total_scale_diff == 0 else 'DIFFERENCES FOUND'}")
