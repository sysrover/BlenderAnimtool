import pathlib
import sys
import struct

sys.path.insert(0, 'p:/ANM-TXA')
from txa_to_anm import parse_txa
from DayzAnimationToolsBinary.Types.Anm import Anm

# Load original ANM to get HEAD metadata
orig_anm = Anm.CreateFromFile('examples/stand_turn_ls_90_original.anm')

# Parse TXA
txa = parse_txa(pathlib.Path('examples/stand_turn_ls_90.txa'))

# For each bone, use original's bias/mult values
print("Original ANM bone metadata (first 3):")
for bone in orig_anm.bones[:3]:
    print(f"{bone.name}:")
    print(f"  posBias={bone.posBias} posMulti={bone.posMulti}")
    print(f"  rotBias={bone.rotBias} rotMulti={bone.rotMulti}")
    print(f"  scaleBias={bone.scaleBias} scaleMulti={bone.scaleMulti}")
