import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

path = pathlib.Path('example2/stand_alerted_original.txa')
if len(sys.argv) > 1:
    path = pathlib.Path(sys.argv[1])
txa = parse_txa(path)
print('TXA path', path)
for name in ['leftbrow','lefteye','leftarm','leftforearm','rightforearm','lefttopindex1','rightring2']:
    node = txa.nodes[name]
    print(name, 'pos', len(node.t), 'rot', len(node.q), 'scale', len(node.s))
