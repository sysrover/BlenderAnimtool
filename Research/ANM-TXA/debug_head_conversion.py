import sys
import pathlib
sys.path.insert(0, 'p:\\ANM-TXA')

from txa_to_anm import parse_txa, Anm

# Manual step through the conversion for head node
txa = parse_txa(pathlib.Path('example2/stand_attack_0_test.txa'))
anim = Anm()
anim.num_frames = txa.num_frames
anim.fps = txa.fps

# Find head node in parsed TXA
head_node_txa = None
for node_name, node in txa.nodes.items():
    if node_name == 'head':
        head_node_txa = node
        print(f"TXA head node has rot keys: {sorted(node.q.keys())}")
        print(f"Total: {len(node.q)} keys")
        break

# Simulate the processing in txa_to_anm
q_has_keys = bool(head_node_txa.q)
print(f"q_has_keys: {q_has_keys}")
print(f"Before any modification: len(node.q)={len(head_node_txa.q)}, frames={sorted(head_node_txa.q.keys())[:5]}...")

# The duplication logic - which shouldn't apply to rot keys with many frames
if len(head_node_txa.q) == 1:
    print("Would apply rotation duplication (but we don't, only scale)")
else:
    print(f"No rotation duplication applied (has {len(head_node_txa.q)} keys)")

# Check final state
print(f"Final rot key count: {len(head_node_txa.q)}")
