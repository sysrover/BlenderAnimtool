import importlib
import json
import os
import sys

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-safe-weaponik-addon-operator-test.json")
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_aks74u_anm_safe_authoring.blend"


def main():
    import DayzAnimationTools.Tools.AddSurvivorIK as AddSurvivorIK
    AddSurvivorIK = importlib.reload(AddSurvivorIK)

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

    result = AddSurvivorIK.refresh_weaponik_preview_constraints(arm)
    if result:
        raise RuntimeError(result)

    unsafe_constraints = []
    for pb in arm.pose.bones:
        for c in pb.constraints:
            if (
                c.name == "DayZ WeaponIK Preview"
                or c.name.startswith("DayZ WIK Control")
                or c.name in ("DayZ Left Hand IK", "DayZ Right Hand IK")
            ):
                unsafe_constraints.append(f"{pb.name}:{c.name}")

    finger_visible = []
    for bone in arm.data.bones:
        if bone.name.startswith("LeftHand") or bone.name.startswith("RightHand"):
            if not getattr(bone, "hide", False):
                finger_visible.append(bone.name)

    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    data = {
        "saved": SAVE_PATH,
        "addon_module": getattr(AddSurvivorIK, "__file__", None),
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
        "mode": arm.get("dayz_weaponik_mode", ""),
        "unsafe_constraints": unsafe_constraints,
        "finger_visible_count": len(finger_visible),
        "finger_visible": sorted(finger_visible),
        "action_fcurves": len(action.fcurves),
        "note": "Tests the patched addon operator path: safe ANM authoring mode, no Blender IK preview constraints.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
