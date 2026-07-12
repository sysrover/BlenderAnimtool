import sys, pathlib
sys.path.insert(0, 'p:/ANM-TXA')
from txa_to_anm import convert_txa_to_anm

if __name__ == '__main__':
    inp = pathlib.Path('examples/stand_alerted.txa')
    outp = pathlib.Path('examples/stand_alerted.anm')
    convert_txa_to_anm(inp, outp)
