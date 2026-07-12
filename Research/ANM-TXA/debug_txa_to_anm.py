import sys
import pathlib
sys.path.insert(0, 'p:\\ANM-TXA')

from txa_to_anm import parse_txa

# Parse the NEW TXA
txa = parse_txa(pathlib.Path('example2/stand_attack_0_test.txa'))

for node_name, node in txa.nodes.items():
    if node_name == 'head':
        print(f"Head node AFTER parsing TXA (before txa_to_anm processing):")
        print(f"  q_has_keys at start: {bool(node.q)}")
        print(f"  q frames: {sorted(node.q.keys())}")
        print(f"  q count: {len(node.q)}")
        
        # Simulate txa_to_anm processing
        q_has_keys = bool(node.q)
        
        # Check if any modification would happen
        last_frame = txa.num_frames - 1
        print(f"  last_frame: {last_frame}")
        print(f"  Would scale duplication apply? No (only to scale, not rot)")
        
        # Check final count
        print(f"  Final q count (should stay same): {len(node.q)}")
        break
