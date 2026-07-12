#!/usr/bin/env python3
"""
Inspect ANM binary format details to debug encoder vs. reference.
"""

import struct
import sys
import pathlib

BIN_BASE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BIN_BASE))

from DayzAnimationToolsBinary.Utils.BinaryReader import BinaryReader
from DayzAnimationToolsBinary.Types.Anm import Anm

def inspect_anm_head(path):
    """Dump HEAD section of ANM file in detail."""
    with open(path, 'rb') as f:
        data = f.read()
    
    br = BinaryReader(data)
    br.Seek(4)  # FORM
    form_size = br.ReadInt32BE()
    print(f"FORM size: {form_size}")
    
    br.Seek(7)  # ANIMSET
    fmt = br.ReadCharParseInt()
    print(f"Format: AnimSet{fmt}")
    
    br.Seek(4)  # size
    br.Seek(8)  # constant
    fps = br.ReadInt32()
    print(f"FPS: {fps}")
    
    br.Seek(4)  # HEAD tag
    head_size = br.ReadInt32BE()
    print(f"HEAD size: {head_size}")
    
    head_start = br.GetPos()
    print(f"\nHEAD starts at byte {head_start}")
    
    anm = Anm.CreateFromFile(str(path))
    
    for i, bone in enumerate(anm.bones):
        print(f"\nBone {i}: {bone.name}")
        print(f"  posBias={bone.posBias}, posMulti={bone.posMulti:.15e}")
        print(f"  rotBias={bone.rotBias}, rotMulti={bone.rotMulti:.15e}")
        print(f"  scaleBias={bone.scaleBias}, scaleMulti={bone.scaleMulti:.15e}")
        print(f"  numFrames={bone.numFrames}")
        print(f"  #posKeys={len(bone.posKeys)}, #rotKeys={len(bone.rotKeys)}, #scaleKeys={len(bone.scaleKeys)}")
        print(f"  flags={bone.flags}")
        if bone.posKeys:
            print(f"    pos frames: {[k.frame for k in bone.posKeys[:5]]}{' ...' if len(bone.posKeys) > 5 else ''}")
        if bone.rotKeys:
            print(f"    rot frames: {[k.frame for k in bone.rotKeys[:5]]}{' ...' if len(bone.rotKeys) > 5 else ''}")
        if bone.scaleKeys:
            print(f"    scale frames: {[k.frame for k in bone.scaleKeys[:5]]}{' ...' if len(bone.scaleKeys) > 5 else ''}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_anm_format.py <anm_file>")
        sys.exit(1)
    
    path = pathlib.Path(sys.argv[1]).resolve()
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    
    inspect_anm_head(path)
