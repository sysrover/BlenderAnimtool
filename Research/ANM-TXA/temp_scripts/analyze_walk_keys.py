import pathlib
import sys
import itertools

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from DayzAnimationToolsBinary.Types.Anm import Anm

bones_of_interest = [
    'hip',
    'lefteye',
    'righteye',
    'pin_lookat',
    'leftindex1','leftindex2','leftmiddle1','leftmiddle2','leftpink1','leftpink2'
]

new = Anm.CreateFromFile('examples/stand_walk_fwd_new.anm')
orig = Anm.CreateFromFile('examples/stand_walk_fwd_original.anm')

print('numFrames', new.numFrames, orig.numFrames)
print('---')
for name in bones_of_interest:
    nb = next((b for b in new.bones if b.name==name), None)
    ob = next((b for b in orig.bones if b.name==name), None)
    if nb is None or ob is None:
        print(name, 'missing', nb is None, ob is None)
        continue
    print(name)
    print(' new counts', len(nb.posKeys), len(nb.rotKeys), len(nb.scaleKeys))
    print(' orig counts', len(ob.posKeys), len(ob.rotKeys), len(ob.scaleKeys))
    def frames(seq):
        return [k.frame for k in seq]
    print(' new frames pos first10', frames(nb.posKeys)[:10])
    print(' orig frames pos first10', frames(ob.posKeys)[:10])
    print(' new frames rot last10', frames(nb.rotKeys)[-10:])
    print(' orig frames rot last10', frames(ob.rotKeys)[-10:])
    print(' new frames scale', frames(nb.scaleKeys))
    print(' orig frames scale', frames(ob.scaleKeys))
    print('---')
