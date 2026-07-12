#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from DayzAnimationToolsBinary.Types.Anm import Anm

anm = Anm.CreateFromFile(sys.argv[1])
b = anm.bones[0]
print(b.name, len(b.scaleKeys))
if b.scaleKeys:
    k = b.scaleKeys[0]
    print('frame', k.frame, 'data', k.data)
