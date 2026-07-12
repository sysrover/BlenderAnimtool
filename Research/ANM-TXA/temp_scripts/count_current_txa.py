import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

txa = parse_txa(pathlib.Path('example2/stand_alerted.txa'))
pos = rot = scale = 0
has_scale = 0
for n in txa.nodes.values():
    pos += len(n.t)
    rot += len(n.q)
    scale += len(n.s)
    has_scale += 1 if n.s else 0
print(f"nodes={len(txa.nodes)} pos={pos} rot={rot} scale={scale} nodes_with_scale={has_scale}")
