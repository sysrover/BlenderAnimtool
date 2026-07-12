import struct
import pathlib
import sys

sys.path.insert(0, 'p:/ANM-TXA')
from DayzAnimationToolsBinary.Types.Anm import Anm, SCALE_FACTOR


def inspect_head(path):
    anm = Anm.CreateFromFile(str(path))
    print(f"\n{path.name}:")
    for bone in anm.bones[:3]:  # First 3 bones
        print(f"  {bone.name}:")
        print(f"    posMulti={bone.posMulti:.15e} (stored would be {bone.posMulti / SCALE_FACTOR:.15e})")
        print(f"    rotMulti={bone.rotMulti:.15e} (stored would be {bone.rotMulti / SCALE_FACTOR:.15e})")
        print(f"    scaleMulti={bone.scaleMulti:.15e} (stored would be {bone.scaleMulti / SCALE_FACTOR:.15e})")
        print(f"    posBias={bone.posBias}")
        print(f"    rotBias={bone.rotBias}")
        print(f"    scaleBias={bone.scaleBias}")
        break


if __name__ == '__main__':
    inspect_head(pathlib.Path('examples/stand_turn_ls_90_original.anm'))
    inspect_head(pathlib.Path('examples/stand_turn_ls_90.anm'))
