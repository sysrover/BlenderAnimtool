import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import convert_txa_to_anm

src = pathlib.Path('example2/stand_alerted_original.txa')
dst = pathlib.Path('example2/stand_alerted_from_txa.anm')
convert_txa_to_anm(src, dst)
print(dst)
