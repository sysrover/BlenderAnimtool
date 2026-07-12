import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import convert_txa_to_anm

src = pathlib.Path('example2/stand_alerted_generated.txa')
dst = pathlib.Path('example2/stand_alerted.anm')
convert_txa_to_anm(src, dst)
print(dst)
