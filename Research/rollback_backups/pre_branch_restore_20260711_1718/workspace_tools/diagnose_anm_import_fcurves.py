import json
import os
import sys

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN = r"P:\Animation_Weapon\Weapon_template_dayz_diag_restored.blend"
ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
OUT = os.path.join(ROOT, "anm", "anm-import-fcurve-diagnostic.json")
ARMATURE_NAME = "_DayZ_Character"


def ensure_addon_path():
    addon_root = os.path.join(
        os.environ["APPDATA"],
        "Blender Foundation",
        "Blender",
        "4.2",
        "scripts",
        "addons",
    )
    if addon_root not in sys.path:
        sys.path.append(addon_root)


def main():
    bpy.ops.wm.open_mainfile(filepath=CLEAN)
    arm = bpy.data.objects[ARMATURE_NAME]
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    ensure_addon_path()
    with bpy.context.temp_override(object=arm, active_object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        op_result = bpy.ops.import_scene.anm(
            "EXEC_DEFAULT",
            filepath=ANM,
            files=[{"name": os.path.basename(ANM)}],
        )
    action = arm.animation_data.action if arm.animation_data else None
    data = {
        "op_result": list(op_result),
        "action": action.name if action else None,
        "frame_range": list(action.frame_range) if action else None,
        "fcurves": [],
        "right_related": [],
    }
    if action:
        for fc in action.fcurves:
            item = {
                "data_path": fc.data_path,
                "array_index": fc.array_index,
                "keys": [float(kp.co.x) for kp in fc.keyframe_points[:10]],
                "key_count": len(fc.keyframe_points),
            }
            data["fcurves"].append(item)
            if "RightHand" in fc.data_path or "RightForeArm" in fc.data_path:
                data["right_related"].append(item)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
