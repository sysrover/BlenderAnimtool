import sys
import pathlib
sys.path.insert(0, 'p:\\ANM-TXA')

from txa_to_anm import parse_txa

txa = parse_txa(pathlib.Path('example2/stand_attack_0_roundtrip.txa'))

# Check the problematic bones
for node_name in ['righttopindex', 'righttopindex1', 'righttopthumb', 'righttopthumb1']:
    if node_name in txa.nodes:
        node = txa.nodes[node_name]
        print(f"{node_name}:")
        print(f"  q frames: {sorted(node.q.keys())}")
        print(f"  count: {len(node.q)}")
