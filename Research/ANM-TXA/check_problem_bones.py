import sys
sys.path.insert(0, 'p:\\ANM-TXA')

from DayzAnimationToolsBinary.Types.Anm import Anm

orig = Anm.CreateFromFile('example2/stand_attack_0_original.anm')

# Check the problematic bones
for bone in orig.bones:
    if bone.name in ['righttopindex', 'righttopindex1', 'righttopthumb', 'righttopthumb1']:
        print(f"{bone.name}:")
        print(f"  rotKeys: {len(bone.rotKeys)}")
        print(f"  rotKey frames: {[k.frame for k in bone.rotKeys]}")
