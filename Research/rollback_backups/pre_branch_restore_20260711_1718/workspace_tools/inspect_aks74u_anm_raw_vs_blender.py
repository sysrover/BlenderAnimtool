import importlib
import json
import os
import sys

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "aks74u-anm-raw-vs-blender.json")
ADDON_ROOT = r"P:\BlenderAnimtool"
IK_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u_helpers_only"

HELPER_BONES = [
    "RightHandOrigin",
    "RightForeArmDirectionOrigin",
    "RightForeArmDirection",
    "RightHand_Dummy",
    "LeftHandOrigin",
    "LeftHandIKTarget",
    "LeftForeArmDirectionOrigin",
    "LeftForeArmDirection",
    "LeftHand_Dummy",
]


def add_addon_path():
    if not os.path.exists(ADDON_ROOT):
        raise RuntimeError(f"Missing addon root in Blender process: {ADDON_ROOT}")
    if ADDON_ROOT not in sys.path:
        sys.path.insert(0, ADDON_ROOT)


def load_raw_anm():
    add_addon_path()
    import DayzAnimationToolsBinary.Types.Anm as AnmModule

    AnmModule = importlib.reload(AnmModule)
    return AnmModule.Anm.CreateFromFile(IK_ANM)


def decode_keys(anm_bone):
    pos = {}
    rot = {}
    for key in anm_bone.posKeys:
        pos[str(key.frame)] = [
            float(key.data[i] * anm_bone.posMulti + anm_bone.posBias)
            for i in range(3)
        ]
    for key in anm_bone.rotKeys:
        # Match ImportAnm raw decode: Quaternion((-w, x, y, z)).
        rot[str(key.frame)] = [
            float(-1.0 * (key.data[3] * anm_bone.rotMulti + anm_bone.rotBias)),
            float(key.data[0] * anm_bone.rotMulti + anm_bone.rotBias),
            float(key.data[1] * anm_bone.rotMulti + anm_bone.rotBias),
            float(key.data[2] * anm_bone.rotMulti + anm_bone.rotBias),
        ]
    return {
        "posMulti": float(anm_bone.posMulti),
        "posBias": float(anm_bone.posBias),
        "rotMulti": float(anm_bone.rotMulti),
        "rotBias": float(anm_bone.rotBias),
        "pos": pos,
        "rot_import_quat": rot,
        "pos_key_count": len(anm_bone.posKeys),
        "rot_key_count": len(anm_bone.rotKeys),
    }


def fcurve_value(action, bone, prop, index, frame):
    data_path = f'pose.bones["{bone}"].{prop}'
    fc = action.fcurves.find(data_path, index=index)
    if fc is None:
        return None
    return float(fc.evaluate(frame))


def blender_action_values(frame):
    action = bpy.data.actions.get(ACTION_NAME)
    if action is None:
        raise RuntimeError(f"Missing action {ACTION_NAME!r}")
    out = {}
    for bone in HELPER_BONES:
        loc = [fcurve_value(action, bone, "location", i, frame) for i in range(3)]
        rot = [fcurve_value(action, bone, "rotation_quaternion", i, frame) for i in range(4)]
        out[bone] = {"location": loc, "rotation_quaternion": rot}
    return out


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature {ARMATURE_NAME!r}")
    anm = load_raw_anm()
    raw = {}
    for bone in anm.bones:
        if bone.name in HELPER_BONES:
            raw[bone.name] = decode_keys(bone)
    data = {
        "anm": IK_ANM,
        "numFrames": int(anm.numFrames),
        "raw_helper_bones": raw,
        "blender_action_values_frame_0": blender_action_values(0),
        "blender_action_values_frame_1": blender_action_values(1),
        "note": "Raw values are decoded from binary .anm before Blender pose-space conversion; Blender values are fcurves after ImportAnm conversion.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
