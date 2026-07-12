#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from DayzAnimationToolsBinary.Types.Anm import Anm

anm = Anm.CreateFromFile(sys.argv[1])
print(f"NumBones: {len(anm.bones)}")
for i,b in enumerate(anm.bones[:10]):
    print(i, b.name, len(b.posKeys), len(b.rotKeys), len(b.scaleKeys))
