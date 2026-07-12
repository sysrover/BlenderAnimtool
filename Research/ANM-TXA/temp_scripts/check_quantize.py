#!/usr/bin/env python3
"""Check if quantization is producing valid encodings"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from txa_to_anm import parse_txa, _quantize_channel

txa_path = pathlib.Path("examples/stand_turn_ls_90.txa")
anim = parse_txa(txa_path)

# Check hip bone
hip = anim.nodes['hip']
print("hip node:")
print(f"  t frames: {sorted(hip.t.keys())}")
print(f"  q frames: {sorted(hip.q.keys())}")

# Quantize position
pos_frames = sorted(hip.t.items())
pos_vals = [v for _, vec in pos_frames for v in vec]
pos_bias, pos_mult, pos_enc = _quantize_channel(pos_vals)

print(f"\nPosition quantization:")
print(f"  bias: {pos_bias}")
print(f"  mult: {pos_mult:.10e}")
print(f"  spread: {(max(pos_vals) - min(pos_vals)):.10e}")
print(f"  encoded values (first 9): {pos_enc[:9]}")

# Check if any encoded values are invalid
if any(v < 0 or v > 65535 for v in pos_enc):
    print("  ❌ INVALID ENCODED VALUES!")
else:
    print("  ✓ All encoded values in valid range [0, 65535]")
