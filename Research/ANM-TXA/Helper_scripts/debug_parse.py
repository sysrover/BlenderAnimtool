#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from txa_to_anm import parse_txa
import pathlib

anim = parse_txa(pathlib.Path('examples/head_turn.txa'))
print(f'Animation name: {anim.name}')
print(f'FPS: {anim.fps}')
print(f'Num frames: {anim.num_frames}')
print(f'Nodes: {list(anim.nodes.keys())}')
for name, node in anim.nodes.items():
    print(f'  {name}:')
    print(f'    pos_bias={node.pos_bias}, pos_mult={node.pos_mult}')
    print(f'    rot_bias={node.rot_bias}, rot_mult={node.rot_mult}')
    print(f'    scale_bias={node.scale_bias}, scale_mult={node.scale_mult}')
    print(f'    #t keys: {len(node.t) if node.t else 0}')
    print(f'    #q keys: {len(node.q) if node.q else 0}')
    print(f'    #s keys: {len(node.s) if node.s else 0}')
print(f'Events: {len(anim.events)}')
print(f'Custom props: {len(anim.cust_props)}')
