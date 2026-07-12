import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ORIG_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
OUT_ANM = os.path.join(ROOT, "anm", "blender_roundtrip", "aks74u_bpyops_raw_preserve_export.anm")
OUT_JSON = os.path.join(ROOT, "anm", "aks74u-bpyops-raw-preserve-export.json")
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    action = bpy.data.actions.get(ACTION_NAME)
    if arm is None or action is None:
        raise RuntimeError("Required armature/action not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action

    result = bpy.ops.export_scene.anm(
        filepath=OUT_ANM,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=0,
        eAnimType="IK2H",
        bPreserveImportedRawAnm=True,
        bSaveAll=False,
        fUnitScale=1.0,
    )
    with open(ORIG_ANM, "rb") as f:
        orig = f.read()
    with open(OUT_ANM, "rb") as f:
        exp = f.read()
    data = {
        "operator_result": sorted(list(result)),
        "original": ORIG_ANM,
        "exported": OUT_ANM,
        "original_bytes": len(orig),
        "exported_bytes": len(exp),
        "byte_identical": orig == exp,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
