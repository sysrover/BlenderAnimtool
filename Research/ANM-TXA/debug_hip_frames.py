#!/usr/bin/env python3
"""Debug quantization and dedup for stand_walk_fwd hip rotations."""

import struct
import sys
import pathlib
import types
import importlib.util

BIN_BASE = pathlib.Path(__file__).resolve().parent
sys.modules.setdefault("DayzAnimationToolsBinary", types.ModuleType("DayzAnimationToolsBinary"))
sys.modules.setdefault("DayzAnimationToolsBinary.Utils", types.ModuleType("DayzAnimationToolsBinary.Utils"))
sys.modules.setdefault("DayzAnimationToolsBinary.Types", types.ModuleType("DayzAnimationToolsBinary.Types"))

def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_load_module("DayzAnimationToolsBinary.Utils.BinaryReader", BIN_BASE / "DayzAnimationToolsBinary" / "Utils" / "BinaryReader.py")
_load_module("DayzAnimationToolsBinary.Utils.Lz4Decoder", BIN_BASE / "DayzAnimationToolsBinary" / "Utils" / "Lz4Decoder.py")
anm_mod = _load_module("DayzAnimationToolsBinary.Types.Anm", BIN_BASE / "DayzAnimationToolsBinary" / "Types" / "Anm.py")

# Load reference ANM
anm = anm_mod.Anm.CreateFromFile(str(pathlib.Path("examples/stand_walk_fwd_original.anm")))

# Find hip bone
hip = None
for bone in anm.bones:
    if bone.name == "hip":
        hip = bone
        break

if hip:
    print(f"Hip bone rot keys (original):")
    print(f"  Count: {len(hip.rotKeys)}")
    print(f"  Frame indices: {[k.frame for k in hip.rotKeys]}")
    print(f"  Which frames are MISSING vs 0-49: {set(range(50)) - set(k.frame for k in hip.rotKeys)}")
else:
    print("Hip bone not found")
