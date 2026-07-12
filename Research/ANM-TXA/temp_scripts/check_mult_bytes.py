#!/usr/bin/env python3
"""Check what mult value we're writing vs what we should write"""
import struct
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from txa_to_anm import _load_anm_for_reference

ref_anm = _load_anm_for_reference(pathlib.Path("examples/stand_turn_ls_90_original.anm"))

# Check first few bones
SCALE_FACTOR = 1.525902e-05

for i, bone in enumerate(ref_anm.bones[:3]):
    print(f"{i}. {bone.name}:")
    
    # What the reader gave us
    print(f"  posMulti (after * SCALE_FACTOR): {bone.posMulti:.10e}")
    
    # What we need to write to binary
    binary_mult = bone.posMulti / SCALE_FACTOR
    print(f"  Binary mult (posMulti / SCALE_FACTOR): {binary_mult:.10e}")
    
    # As float32 bytes (little endian)
    bytes_le = struct.pack('<f', binary_mult)
    print(f"  Bytes (little endian): {bytes_le.hex()}")
    
    # What our quantization would give
    from txa_to_anm import parse_txa, _quantize_channel
    anim = parse_txa(pathlib.Path("examples/stand_turn_ls_90.txa"))
    txa_bone = anim.nodes[bone.name]
    pos_frames = sorted(txa_bone.t.items())
    pos_vals = [v for _, vec in pos_frames for v in vec]
    pos_bias, pos_mult, pos_enc = _quantize_channel(pos_vals)
    print(f"  Computed mult (from TXA): {pos_mult:.10e}")
    bytes_le_computed = struct.pack('<f', pos_mult)
    print(f"  Bytes (computed): {bytes_le_computed.hex()}")
    print()
