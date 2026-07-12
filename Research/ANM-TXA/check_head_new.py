import sys
import pathlib
sys.path.insert(0, 'p:\\ANM-TXA')

from txa_to_anm import parse_txa

txa = parse_txa(pathlib.Path('example2/stand_attack_0_test.txa'))

# Find head node
for node_name, node in txa.nodes.items():
    if node_name == 'head':
        print(f"Head node from NEW TXA (stand_attack_0_test.txa):")
        print(f"  Position (t) frames: {sorted(node.t.keys())}")
        print(f"  Rotation (q) frames: {sorted(node.q.keys())[:10]}... (showing first 10)")
        print(f"  Scale (s) frames: {sorted(node.s.keys())}")
        print(f"  Total rot keys: {len(node.q)}")
        break
