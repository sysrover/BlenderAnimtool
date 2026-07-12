#!/usr/bin/env python3
"""Debug with detailed print statements"""
import sys
import pathlib

# Patch _write_anm to add debug output
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Read the current txa_to_anm.py to see the _write_anm signature
with open("txa_to_anm.py", "r") as f:
    content = f.read()
    
# Check if ref_anm is used in _write_anm
if "ref_anm" in content:
    print("✓ ref_anm parameter found in txa_to_anm.py")
    
    # Find the line that uses ref_bones_by_name
    if "ref_bones_by_name" in content:
        print("✓ ref_bones_by_name found")
    else:
        print("✗ ref_bones_by_name NOT found")
    
    # Check if reference values are being assigned
    if "ref_bone.posMulti" in content:
        print("✓ ref_bone attributes found")
    else:
        print("✗ ref_bone attributes NOT found")
else:
    print("✗ ref_anm parameter NOT found in _write_anm")

# Now try conversion with instrumentation
from txa_to_anm import convert_txa_to_anm

print("\nConverting with reference ANM...")
convert_txa_to_anm(
    pathlib.Path("examples/stand_turn_ls_90.txa"),
    pathlib.Path("examples/stand_turn_ls_90_debug.anm"),
    pathlib.Path("examples/stand_turn_ls_90_original.anm")
)
print("Done!")
