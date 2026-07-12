import os, sys
addons_dir = r"C:\Users\sysro\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons"
if addons_dir not in sys.path:
    sys.path.insert(0, addons_dir)
from DayzAnimationToolsBinary.Types.Anm import Anm

root = os.path.join(addons_dir, "DayzAnimationToolsBinary")
# Support both 'example' and 'Examples' dirs
example_dir = None
for cand in ("example", "Examples"):
    p = os.path.join(root, cand)
    if os.path.isdir(p):
        example_dir = p
        break
if example_dir is None:
    example_dir = os.path.join(root, "example")

print("Example dir:", example_dir)
try:
    files = [f for f in os.listdir(example_dir) if f.lower().endswith('.anm')]
    print("ANM files:", files)
except Exception as e:
    print("listdir failed:", repr(e))

orig_name = 'aks74u.anm'
exp_candidates = ['aksu74u_exported.anm', 'aks74u_exported.anm']
orig_path = os.path.join(example_dir, orig_name)
exp_path = None
for nm in exp_candidates:
    p = os.path.join(example_dir, nm)
    if os.path.exists(p):
        exp_path = p
        break

print("original:", orig_path, os.path.exists(orig_path))
print("exported:", exp_path, (os.path.exists(exp_path) if exp_path else None))

if not os.path.exists(orig_path) or not exp_path or not os.path.exists(exp_path):
    raise FileNotFoundError("Missing expected ANM test files in example/ directory.")

orig = Anm.CreateFromFile(orig_path)
exp = Anm.CreateFromFile(exp_path)

IK_BONES = ['RightHandOrigin','RightForeArmDirection','LeftHandOrigin','LeftForeArmDirection']

def summarize(anm):
    idx = {b.name: b for b in anm.bones}
    summary = {}
    for nm in IK_BONES:
        b = idx.get(nm)
        if not b:
            summary[nm] = None
            continue
        def decomp_pos(k):
            return (
                k.data[0]*b.posMulti + b.posBias,
                k.data[1]*b.posMulti + b.posBias,
                k.data[2]*b.posMulti + b.posBias,
            )
        def decomp_rot(k):
            return (
                k.data[0]*b.rotMulti + b.rotBias,
                k.data[1]*b.rotMulti + b.rotBias,
                k.data[2]*b.rotMulti + b.rotBias,
                k.data[3]*b.rotMulti + b.rotBias,
            )
        summary[nm] = {
            'pos_frames': [k.frame for k in b.posKeys],
            'rot_frames': [k.frame for k in b.rotKeys],
            'pos_count': len(b.posKeys),
            'rot_count': len(b.rotKeys),
            'pos_first2': [decomp_pos(k) for k in b.posKeys[:2]],
            'rot_first2': [decomp_rot(k) for k in b.rotKeys[:2]],
        }
    return summary

s_orig = summarize(orig)
s_exp = summarize(exp)

import json
print("orig summary:")
print(json.dumps(s_orig, indent=2))
print("exported summary:")
print(json.dumps(s_exp, indent=2))

# Quick diff hints
for nm in IK_BONES:
    o = s_orig.get(nm)
    e = s_exp.get(nm)
    if o is None or e is None:
        print(nm, "missing in", "orig" if o is None else "exported")
        continue
    if o['rot_frames'] != e['rot_frames']:
        print(nm, "rot_frames differ:", o['rot_frames'], "vs", e['rot_frames'])
    if o['pos_frames'] != e['pos_frames']:
        print(nm, "pos_frames differ:", o['pos_frames'], "vs", e['pos_frames'])
    # compare first rot values roughly
    def round4(v):
        return tuple(round(x,4) for x in v)
    if o['rot_first2'] and e['rot_first2']:
        if round4(o['rot_first2'][0]) != round4(e['rot_first2'][0]):
            print(nm, "rot[0] differs:", round4(o['rot_first2'][0]), "vs", round4(e['rot_first2'][0]))
        if len(o['rot_first2'])>1 and len(e['rot_first2'])>1:
            if round4(o['rot_first2'][1]) != round4(e['rot_first2'][1]):
                print(nm, "rot[1] differs:", round4(o['rot_first2'][1]), "vs", round4(e['rot_first2'][1]))
    if o['pos_first2'] and e['pos_first2']:
        if round4(o['pos_first2'][0]) != round4(e['pos_first2'][0]):
            print(nm, "pos[0] differs:", round4(o['pos_first2'][0]), "vs", round4(e['pos_first2'][0]))
        if len(o['pos_first2'])>1 and len(e['pos_first2'])>1:
            if round4(o['pos_first2'][1]) != round4(e['pos_first2'][1]):
                print(nm, "pos[1] differs:", round4(o['pos_first2'][1]), "vs", round4(e['pos_first2'][1]))
