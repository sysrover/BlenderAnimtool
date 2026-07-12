#!/usr/bin/env python3
"""
Compare HEAD sections: original ANM vs regenerated ANM
This helps identify which bones/channels are being quantized differently
"""
import sys
import pathlib
import struct

BIN_BASE = pathlib.Path(__file__).resolve().parent.parent

# Import the ANM reader
sys.path.insert(0, str(BIN_BASE))
from DayzAnimationToolsBinary.Types.Anm import Anm

def extract_head_from_anm(anm_path):
    """Load ANM and extract HEAD bias/mult values per bone"""
    anm = Anm.CreateFromFile(str(anm_path))
    head_data = []
    for i, bone in enumerate(anm.bones):
        head_data.append({
            'index': i,
            'name': bone.name,
            'posBias': bone.posBias,
            'posMulti': bone.posMulti,
            'rotBias': bone.rotBias,
            'rotMulti': bone.rotMulti,
            'scaleBias': bone.scaleBias,
            'scaleMulti': bone.scaleMulti,
            'numFrames': bone.numFrames,
            'posKeys': len(bone.posKeys),
            'rotKeys': len(bone.rotKeys),
            'scaleKeys': len(bone.scaleKeys),
        })
    return head_data

def compare_heads(original_path, generated_path):
    """Compare HEAD sections of two ANMs"""
    orig = extract_head_from_anm(original_path)
    gen = extract_head_from_anm(generated_path)
    
    print(f"Original: {len(orig)} bones")
    print(f"Generated: {len(gen)} bones")
    print()
    
    diffs = []
    for i in range(min(len(orig), len(gen))):
        o = orig[i]
        g = gen[i]
        
        if o['name'] != g['name']:
            print(f"[{i}] NAME MISMATCH: '{o['name']}' vs '{g['name']}'")
            diffs.append(i)
            continue
        
        issues = []
        
        # Check bias/mult values (allow small float error)
        for param in ['posBias', 'posMulti', 'rotBias', 'rotMulti', 'scaleBias', 'scaleMulti']:
            ov = o[param]
            gv = g[param]
            err = abs(ov - gv)
            if err > 1e-6:
                issues.append(f"{param}: {ov:.9f} vs {gv:.9f} (diff: {err:.2e})")
        
        # Check key counts
        for param in ['posKeys', 'rotKeys', 'scaleKeys']:
            if o[param] != g[param]:
                issues.append(f"{param}: {o[param]} vs {g[param]}")
        
        if issues:
            diffs.append(i)
            print(f"[{i}] {o['name']}:")
            for issue in issues:
                print(f"  - {issue}")
    
    if not diffs:
        print("✓ All HEAD sections match!")
    else:
        print(f"\n❌ {len(diffs)} bones differ")
        return False
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python compare_head.py <original.anm> <generated.anm>")
        sys.exit(1)
    
    orig_p = pathlib.Path(sys.argv[1]).resolve()
    gen_p = pathlib.Path(sys.argv[2]).resolve()
    
    if not orig_p.exists() or not gen_p.exists():
        print(f"Error: files not found")
        sys.exit(1)
    
    ok = compare_heads(orig_p, gen_p)
    sys.exit(0 if ok else 1)
