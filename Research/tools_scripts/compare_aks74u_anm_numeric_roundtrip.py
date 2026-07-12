import json
import math
import os
import sys


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "aks74u-anm-numeric-roundtrip.json")
ORIG_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
EXP_ANM = os.path.join(ROOT, "anm", "blender_roundtrip", "aks74u_roundtrip_export.anm")
ADDON_ROOT = r"C:\Users\sysro\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationToolsBinary"

if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)

from Types.Anm import Anm


def decoded_bone_keys(bone):
    pos = {}
    rot = {}
    for k in bone.posKeys:
        pos[int(k.frame)] = [
            float(k.data[i] * bone.posMulti + bone.posBias)
            for i in range(3)
        ]
    for k in bone.rotKeys:
        rot[int(k.frame)] = [
            float(k.data[i] * bone.rotMulti + bone.rotBias)
            for i in range(4)
        ]
    return pos, rot


def diff_vec(a, b):
    return max(abs(a[i] - b[i]) for i in range(len(a)))


def main():
    orig = Anm.CreateFromFile(ORIG_ANM)
    exp = Anm.CreateFromFile(EXP_ANM)
    orig_bones = {b.name: b for b in orig.bones}
    exp_bones = {b.name: b for b in exp.bones}
    common = sorted(set(orig_bones) & set(exp_bones))
    per_bone = {}
    max_pos = 0.0
    max_rot = 0.0
    worst = []
    for name in common:
        opos, orot = decoded_bone_keys(orig_bones[name])
        epos, erot = decoded_bone_keys(exp_bones[name])
        frames = sorted(set(opos) & set(epos))
        bone_max_pos = 0.0
        for frame in frames:
            d = diff_vec(opos[frame], epos[frame])
            bone_max_pos = max(bone_max_pos, d)
            max_pos = max(max_pos, d)
        frames = sorted(set(orot) & set(erot))
        bone_max_rot = 0.0
        for frame in frames:
            d = diff_vec(orot[frame], erot[frame])
            bone_max_rot = max(bone_max_rot, d)
            max_rot = max(max_rot, d)
        per_bone[name] = {
            "pos_common_frames": sorted(set(opos) & set(epos)),
            "rot_common_frames": sorted(set(orot) & set(erot)),
            "pos_missing_in_export": sorted(set(opos) - set(epos)),
            "rot_missing_in_export": sorted(set(orot) - set(erot)),
            "pos_extra_in_export": sorted(set(epos) - set(opos)),
            "rot_extra_in_export": sorted(set(erot) - set(orot)),
            "max_pos_abs_diff": bone_max_pos,
            "max_rot_abs_diff": bone_max_rot,
        }
        if bone_max_pos > 1e-3 or bone_max_rot > 1e-3 or per_bone[name]["pos_missing_in_export"] or per_bone[name]["rot_missing_in_export"]:
            worst.append({"bone": name, **per_bone[name]})

    data = {
        "original": ORIG_ANM,
        "exported": EXP_ANM,
        "bone_count_original": len(orig_bones),
        "bone_count_exported": len(exp_bones),
        "missing_bones": sorted(set(orig_bones) - set(exp_bones)),
        "extra_bones": sorted(set(exp_bones) - set(orig_bones)),
        "max_pos_abs_diff_common_frames": max_pos,
        "max_rot_abs_diff_common_frames": max_rot,
        "worst_or_missing": worst,
        "note": "Decoded float comparison on common frames. Missing frame keys are reported separately from numeric error.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
