import sys
sys.path.insert(0, 'p:\\ANM-TXA')

from DayzAnimationToolsBinary.Types.Anm import Anm

orig = Anm.CreateFromFile('example2/stand_attack_0_original.anm')

# Find righttopindex bone
for bone in orig.bones:
    if bone.name == 'righttopindex':
        print(f"righttopindex bone from original ANM:")
        print(f"  rotKeys count: {len(bone.rotKeys)}")
        print(f"  rotKey frames: {[k.frame for k in bone.rotKeys]}")
        
        # Check if frames 28-42 have actual data
        for i, key in enumerate(bone.rotKeys):
            if key.frame >= 26:
                print(f"    Key {i}: frame={key.frame}, data={key.data}")
        break
