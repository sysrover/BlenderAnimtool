#!/usr/bin/env python3
"""Debug TXA parsing to see what frames are captured"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from txa_to_anm import parse_txa

txa_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("examples/stand_turn_ls_90.txa")
anim = parse_txa(txa_path)

print(f"Animation: {anim.name if anim.name else '(empty)'}")
print(f"FPS: {anim.fps}, Frames: {anim.num_frames}")
print(f"Nodes: {len(anim.nodes)}")
print()

for name, node in list(anim.nodes.items())[:5]:
    print(f"{name}:")
    print(f"  t frames: {sorted(node.t.keys())} (count: {len(node.t)})")
    if node.t:
        print(f"    [0]: {node.t[0]}")
        print(f"    [29]: {node.t.get(29, 'N/A')}")
    print(f"  q frames: {sorted(node.q.keys())[:10]}... (count: {len(node.q)})")
    if node.q:
        print(f"    [0]: {node.q[0]}")
        print(f"    [29]: {node.q.get(29, 'N/A')}")
    print(f"  s frames: {sorted(node.s.keys())} (count: {len(node.s)})")
    print()
