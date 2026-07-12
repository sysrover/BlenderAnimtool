import sys
sys.path.insert(0, 'p:\\ANM-TXA')

from DayzAnimationToolsBinary.Types.Anm import Anm

# Load original ANM
anm = Anm.CreateFromFile(r'example2\stand_attack_0_original.anm')

# Find head bone
for i, bone in enumerate(anm.bones):
    if bone.name == 'head':
        print(f"Head bone (index {i}):")
        print(f"  posKeys count: {len(bone.posKeys)}")
        print(f"  rotKeys count: {len(bone.rotKeys)}")
        print(f"  scaleKeys count: {len(bone.scaleKeys)}")
        print(f"  rotKey frames: {[k.frame for k in bone.rotKeys]}")
        break
