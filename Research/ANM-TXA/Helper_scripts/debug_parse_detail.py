#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from txa_to_anm import parse_txa
import pathlib

anim = parse_txa(pathlib.Path('examples/head_turn.txa'))
print(f'Parsed animation:')
print(f'  name: "{anim.name}"')
print(f'  fps: {anim.fps}')
print(f'  num_frames: {anim.num_frames}')

for name, node in anim.nodes.items():
    print(f'  node: "{name}"')
    if node.t:
        print(f'    t keys: {sorted(node.t.keys())}')
        for frame, val in sorted(node.t.items())[:3]:
            print(f'      {frame}: {val}')
    else:
        print(f'    t keys: None')
    
    if node.q:
        print(f'    q keys: {list(sorted(node.q.keys()))[:10]}... (total {len(node.q)})')
        for frame, val in sorted(node.q.items())[:2]:
            print(f'      {frame}: {val}')
    else:
        print(f'    q keys: None')
    
    if node.s:
        print(f'    s keys: {list(sorted(node.s.keys()))[:10]}... (total {len(node.s)})')
        for frame, val in sorted(node.s.items())[:2]:
            print(f'      {frame}: {val}')
    else:
        print(f'    s keys: None')
