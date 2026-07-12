import pathlib
import itertools
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from DayzAnimationToolsBinary.Types.Anm import Anm

new_path = pathlib.Path('examples/stand_walk_fwd_new.anm')
orig_path = pathlib.Path('examples/stand_walk_fwd_original.anm')

new = Anm.CreateFromFile(str(new_path))
orig = Anm.CreateFromFile(str(orig_path))

print(f'numFrames new/orig: {new.numFrames} / {orig.numFrames}')
print(f'bones new/orig: {len(new.bones)} / {len(orig.bones)}')

count_diffs = []
name_diffs = []
mult_diffs = []

for na, nb in itertools.zip_longest(new.bones, orig.bones):
    if na is None or nb is None:
        name_diffs.append((getattr(na, "name", None), getattr(nb, "name", None)))
        continue
    if na.name != nb.name:
        name_diffs.append((na.name, nb.name))
        continue
    if (len(na.posKeys), len(na.rotKeys), len(na.scaleKeys)) != (len(nb.posKeys), len(nb.rotKeys), len(nb.scaleKeys)):
        count_diffs.append((na.name, len(na.posKeys), len(nb.posKeys), len(na.rotKeys), len(nb.rotKeys), len(na.scaleKeys), len(nb.scaleKeys)))
    if (na.posBias, na.posMulti, na.rotBias, na.rotMulti, na.scaleBias, na.scaleMulti) != (
        nb.posBias, nb.posMulti, nb.rotBias, nb.rotMulti, nb.scaleBias, nb.scaleMulti
    ):
        mult_diffs.append(na.name)

print('name mismatches:', len(name_diffs))
for item in name_diffs[:5]:
    print(' name diff:', item)

print('count mismatches:', len(count_diffs))
for item in count_diffs[:10]:
    print(' count diff:', item)

print('mult mismatches:', len(mult_diffs))
for item in mult_diffs[:5]:
    print(' mult diff:', item)

print('events new/orig:', len(getattr(new, 'events', [])), len(getattr(orig, 'events', [])))
print('custProps new/orig:', len(getattr(new, 'custProps', [])), len(getattr(orig, 'custProps', [])))
