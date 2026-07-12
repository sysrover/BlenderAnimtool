#!/usr/bin/env python3
"""Debug reference ANM loading"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from txa_to_anm import _load_anm_for_reference

ref_path = pathlib.Path("examples/stand_turn_ls_90_original.anm")
ref_anm = _load_anm_for_reference(ref_path)

print(f"Loaded {len(ref_anm.bones)} bones from reference ANM")
print()

# Show first 5 bones
for i, bone in enumerate(ref_anm.bones[:5]):
    print(f"[{i}] {bone.name}:")
    print(f"  posMulti: {bone.posMulti}")
    print(f"  rotMulti: {bone.rotMulti}")
    print(f"  scaleMulti: {bone.scaleMulti}")
    print()
