import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

def counts(path):
    txa = parse_txa(path)
    pos = rot = scale = 0
    for n in txa.nodes.values():
        pos += len(n.t)
        rot += len(n.q)
        scale += len(n.s)
    return len(txa.nodes), pos, rot, scale

orig = pathlib.Path('example2/stand_attack_0.txa')
rt = pathlib.Path('example2/stand_attack_0_from_anm.txa')
print('orig', counts(orig))
print('rt  ', counts(rt))
