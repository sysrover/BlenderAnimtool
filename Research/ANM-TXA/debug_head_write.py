#!/usr/bin/env python3
"""Debug script to check what HEAD bytes we're writing for Scene_Root."""

import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from txa_to_anm import parse_txa, _write_anm, SCALE_FACTOR

# Load stand_roar.txa
txa_path = pathlib.Path("examples/stand_roar.txa")
if not txa_path.exists():
    print(f"File not found: {txa_path}")
    sys.exit(1)

anim = parse_txa(txa_path)

# Get Scene_Root node
scene_root = anim.nodes.get("Scene_Root")
if scene_root is None:
    print("Scene_Root not found")
    print(f"Available nodes: {list(anim.nodes.keys())}")
    sys.exit(1)

print("Scene_Root data:")
print(f"  Translations: {dict(scene_root.t)}")
print(f"  Rotations: {dict(scene_root.q)}")
print(f"  Scales: {dict(scene_root.s)}")
print()

# Simulate HEAD writing
from txa_to_anm import _quantize_channel

# Check what we'd write for Scene_Root
q_has_keys = bool(scene_root.q)
print(f"q_has_keys: {q_has_keys}")

rot_frames = sorted(scene_root.q.items())
print(f"rot_frames from TXA: {rot_frames}")

if not q_has_keys:
    if "Scene_Root" == "Scene_Root":
        # Scene_Root needs identity quaternion at frame 0
        rot_frames = [(0, (0.0, 0.0, 0.0, 1.0))]
        # Quantize: identity quat [0, 0, 0, 1] stays as [0, 0, 0, 65535] after encoding
        rot_vals = [0.0, 0.0, 0.0, 1.0]
        rot_bias, rot_mult, rot_enc = _quantize_channel(rot_vals)
        print(f"Scene_Root rotation (forced):")
        print(f"  rot_frames: {rot_frames}")
        print(f"  rot_bias: {rot_bias}")
        print(f"  rot_mult: {rot_mult}")
        print(f"  rot_enc: {rot_enc}")
        print(f"  rot_mult / SCALE_FACTOR: {rot_mult / SCALE_FACTOR if rot_mult != 0 else 0.0}")
