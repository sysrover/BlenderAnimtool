import sys
import pathlib
sys.path.insert(0, 'p:\\ANM-TXA')

from txa_to_anm import parse_txa

# Parse both TXAs
txa_new = parse_txa(pathlib.Path('example2/stand_attack_0_test.txa'))
txa_orig = parse_txa(pathlib.Path('example2/stand_attack_0.txa'))

for node_name in ['head']:
    node_new = txa_new.nodes[node_name]
    node_orig = txa_orig.nodes[node_name]
    
    print(f"{node_name} - NEW TXA:")
    print(f"  q frames:  {sorted(node_new.q.keys())}")
    print(f"  q count: {len(node_new.q)}")
    print()
    print(f"{node_name} - ORIGINAL TXA:")
    print(f"  q frames: {sorted(node_orig.q.keys())}")
    print(f"  q count: {len(node_orig.q)}")
