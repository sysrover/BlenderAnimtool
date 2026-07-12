import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-save-anm-full-import-copy.json")
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_aks74u_anm_full_import.blend"
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"


def main():
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
    arm["dayz_weaponik_mode"] = "Full imported aks74u ANM with finger tracks"
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    data = {
        "saved": SAVE_PATH,
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
        "frame": bpy.context.scene.frame_current,
        "mode": arm["dayz_weaponik_mode"],
        "action_fcurves": len(action.fcurves),
        "note": "Saved as a separate copy with full imported .anm action, including finger tracks.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
