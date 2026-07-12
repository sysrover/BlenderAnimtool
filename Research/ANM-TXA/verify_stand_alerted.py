import sys
sys.path.insert(0, 'p:\\ANM-TXA')
from DayzAnimationToolsBinary.Types.Anm import Anm

orig = Anm.CreateFromFile('examples/stand_alerted.anm')
test = Anm.CreateFromFile('examples/stand_alerted_test.anm')

orig_pos = sum(len(b.posKeys) for b in orig.bones)
test_pos = sum(len(b.posKeys) for b in test.bones)
orig_rot = sum(len(b.rotKeys) for b in orig.bones)
test_rot = sum(len(b.rotKeys) for b in test.bones)
orig_scale = sum(len(b.scaleKeys) for b in orig.bones)
test_scale = sum(len(b.scaleKeys) for b in test.bones)

pos_match = orig_pos == test_pos
rot_match = orig_rot == test_rot
scale_match = orig_scale == test_scale

print(f"stand_alerted roundtrip verification:")
print(f"  PosKeys:   {orig_pos:4d} -> {test_pos:4d} {'✓' if pos_match else '✗'}")
print(f"  RotKeys:   {orig_rot:4d} -> {test_rot:4d} {'✓' if rot_match else '✗'}")
print(f"  ScaleKeys: {orig_scale:4d} -> {test_scale:4d} {'✓' if scale_match else '✗'}")
print()
print(f"Overall: {'PERFECT ✓' if pos_match and rot_match and scale_match else 'DIFFERENCES'}")
