import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

nodes = parse_txa(pathlib.Path('example2/stand_alerted.txa')).nodes
for name in ['leftarm','leftforearm','leftindex','Scene_Root','entityposition']:
    n = nodes[name]
    print(name, len(n.t), len(n.q), len(n.s))
