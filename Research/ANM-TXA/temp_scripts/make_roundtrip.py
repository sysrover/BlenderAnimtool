import sys
import pathlib

sys.path.insert(0, 'p:/ANM-TXA')
from txa_to_anm import convert_txa_to_anm

# Convert the original TXA back
inp = pathlib.Path('examples/stand_turn_ls_90.txa').resolve()
outp = pathlib.Path('examples/stand_turn_ls_90_roundtrip.anm').resolve()
convert_txa_to_anm(inp, outp)
print(f"Wrote {outp}")
