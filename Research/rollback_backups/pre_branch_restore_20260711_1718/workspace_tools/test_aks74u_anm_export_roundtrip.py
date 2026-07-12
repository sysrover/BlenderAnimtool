import importlib
import json
import os
import sys

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_DIR = os.path.join(ROOT, "anm", "blender_roundtrip")
OUT_ANM = os.path.join(OUT_DIR, "aks74u_roundtrip_export.anm")
OUT_JSON = os.path.join(ROOT, "anm", "aks74u-anm-export-roundtrip.json")
ORIG_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"


def load_anm(path):
    import DayzAnimationToolsBinary.Types.Anm as AnmModule

    AnmModule = importlib.reload(AnmModule)
    return AnmModule.Anm.CreateFromFile(path)


def bone_summary(anm):
    result = {}
    for bone in anm.bones:
        result[bone.name] = {
            "pos": len(bone.posKeys),
            "rot": len(bone.rotKeys),
            "scale": len(bone.scaleKeys),
            "pos_frames": [int(k.frame) for k in bone.posKeys],
            "rot_frames": [int(k.frame) for k in bone.rotKeys],
        }
    return result


def is_finger(name):
    prefixes = (
        "LeftHandThumb",
        "LeftHandIndex",
        "LeftHandMiddle",
        "LeftHandRing",
        "LeftHandPinky",
        "RightHandThumb",
        "RightHandIndex",
        "RightHandMiddle",
        "RightHandRing",
        "RightHandPinky",
    )
    return name.startswith(prefixes)


def main():
    import DayzAnimationToolsBinary.Export.ExportAnm as ExportAnm
    ExportAnm = importlib.reload(ExportAnm)

    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    action = bpy.data.actions.get(ACTION_NAME)
    if action is None:
        raise RuntimeError(f"Action {ACTION_NAME!r} not found")

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 1

    os.makedirs(OUT_DIR, exist_ok=True)
    result = bpy.ops.export_scene.anm(
        filepath=OUT_ANM,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=0,
        eAnimType="IK2H",
        bSaveAll=False,
        fUnitScale=1.0,
    )

    orig = load_anm(ORIG_ANM)
    exp = load_anm(OUT_ANM)
    orig_summary = bone_summary(orig)
    exp_summary = bone_summary(exp)
    orig_names = set(orig_summary.keys())
    exp_names = set(exp_summary.keys())

    orig_fingers = sorted([name for name in orig_names if is_finger(name)])
    exp_fingers = sorted([name for name in exp_names if is_finger(name)])

    missing_fingers = sorted(set(orig_fingers) - set(exp_fingers))
    missing_helpers = sorted({
        "RightHandOrigin",
        "RightForeArmDirectionOrigin",
        "RightForeArmDirection",
        "RightHand_Dummy",
        "LeftHandOrigin",
        "LeftHandIKTarget",
        "LeftForeArmDirectionOrigin",
        "LeftForeArmDirection",
        "LeftHand_Dummy",
    } - exp_names)

    key_count_mismatches = {}
    for name in sorted(orig_names & exp_names):
        if is_finger(name) or name.endswith("_Dummy") or "Origin" in name or "Direction" in name or name == "LeftHandIKTarget":
            o = orig_summary[name]
            e = exp_summary[name]
            if (o["pos"], o["rot"], o["scale"]) != (e["pos"], e["rot"], e["scale"]):
                key_count_mismatches[name] = {"orig": o, "exported": e}

    data = {
        "export_result": sorted(list(result)),
        "source_blend": bpy.data.filepath,
        "source_action": action.name,
        "out_anm": OUT_ANM,
        "original_anm": ORIG_ANM,
        "original_bone_count": len(orig_names),
        "exported_bone_count": len(exp_names),
        "original_finger_count": len(orig_fingers),
        "exported_finger_count": len(exp_fingers),
        "missing_fingers": missing_fingers,
        "missing_helpers": missing_helpers,
        "extra_exported": sorted(exp_names - orig_names),
        "missing_exported": sorted(orig_names - exp_names),
        "key_count_mismatches": key_count_mismatches,
        "note": "Round-trip structural test for IK2H export. Numeric parity is a separate tolerance test.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
