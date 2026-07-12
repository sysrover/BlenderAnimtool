import sys
sys.path.insert(0, 'p:\\ANM-TXA')

from DayzAnimationToolsBinary.Types.Anm import Anm
from txa_to_anm import parse_txa
import pathlib

orig = Anm.CreateFromFile('example2/stand_attack_0_original.anm')
final = Anm.CreateFromFile('example2/stand_attack_0_final.anm')
txa = parse_txa(pathlib.Path('example2/stand_attack_0_test.txa'))

bones_to_check = ['righttopindex', 'lefteye', 'head']

for bone_name in bones_to_check:
    # Original
    for bone_orig in orig.bones:
        if bone_orig.name == bone_name:
            break
    
    # Final
    for bone_final in final.bones:
        if bone_final.name == bone_name:
            break
    
    # TXA
    txa_node = txa.nodes.get(bone_name)
    
    print(f"\n{bone_name}:")
    print(f"  Original rot keys: {len(bone_orig.rotKeys)}")
    print(f"  Final rot keys: {len(bone_final.rotKeys)}")
    print(f"  TXA rot frames: {len(txa_node.q) if txa_node else 'N/A'}")
    if txa_node:
        print(f"    Frames: {sorted(txa_node.q.keys())[:10]}...")
