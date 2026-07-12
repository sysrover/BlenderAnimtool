import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from anm_to_txa import load_anm

anm = load_anm(pathlib.Path('example2/stand_alerted_original.anm'))
for b in anm.bones:
    if b.name in {'leftindex','leftarm','leftforearm','Scene_Root','entityposition'}:
        print(b.name, len(b.posKeys), len(b.rotKeys), len(b.scaleKeys))
