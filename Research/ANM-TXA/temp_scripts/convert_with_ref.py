#!/usr/bin/env python3
"""Convert TXA using reference ANM metadata"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from txa_to_anm import convert_txa_to_anm

txa_path = pathlib.Path("examples/stand_turn_ls_90.txa")
anm_path = pathlib.Path("examples/stand_turn_ls_90.anm")
ref_anm_path = pathlib.Path("examples/stand_turn_ls_90_original.anm")

convert_txa_to_anm(txa_path, anm_path, ref_anm_path)
