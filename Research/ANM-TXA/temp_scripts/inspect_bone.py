import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from anm_to_txa import load_anm

bone = sys.argv[1] if len(sys.argv) > 1 else 'leftindex'
for label, path in [('new', 'example2/stand_alerted_from_txa.anm'), ('orig', 'example2/stand_alerted_original.anm')]:
    anm = load_anm(pathlib.Path(path))
    node = next((b for b in anm.bones if b.name == bone), None)
    if not node:
        print(label, bone, 'not found')
        continue
    print(label, bone, 'pos', len(node.posKeys), 'rot', len(node.rotKeys), 'scale', len(node.scaleKeys))
