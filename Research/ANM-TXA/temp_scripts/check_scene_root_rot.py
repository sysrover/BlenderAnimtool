import sys
import pathlib

sys.path.insert(0, 'p:/ANM-TXA')
from txa_to_anm import parse_txa

anim = parse_txa(pathlib.Path('examples/stand_turn_ls_90.txa'))
node = anim.nodes['Scene_Root']
print("Scene_Root rotation keys:")
for frame, val in sorted(node.q.items()):
    print(f"  frame {frame}: {val}")

if node.q:
    vals = [v for frame, vec in sorted(node.q.items()) for v in vec]
    print(f"\nAll rot values: {set(vals)}")
    print(f"Min: {min(vals)}, Max: {max(vals)}, Spread: {max(vals) - min(vals)}")
