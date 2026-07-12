#!/usr/bin/env python3
"""Debug roundtrip: compare what goes in vs what comes out."""

import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from txa_to_anm import parse_txa

# Parse original TXA
orig = parse_txa(pathlib.Path("examples/stand_walk_fwd.txa"))

# Count frames per node
for node_name in sorted(list(orig.nodes.keys())[:3]):
    node = orig.nodes[node_name]
    print(f"\n{node_name}:")
    print(f"  #t frames: {len(node.t)} - {sorted(node.t.keys())[:10]}...")
    print(f"  #q frames: {len(node.q)} - {sorted(node.q.keys())[:10]}...")
    print(f"  #s frames: {len(node.s)} - {sorted(node.s.keys())[:10]}...")
    
    # Check if dynamic
    last_frame = orig.num_frames - 1
    t_frames = sorted(node.t.keys())
    q_frames = sorted(node.q.keys())
    t_dynamic = any(f not in (0, last_frame) for f in t_frames)
    q_dynamic = any(f not in (0, last_frame) for f in q_frames)
    print(f"  t_dynamic: {t_dynamic}, q_dynamic: {q_dynamic}")
