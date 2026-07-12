import importlib
import json
import os
import sys

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN = r"P:\Animation_Weapon\Weapon_template_dayz_diag_restored.blend"
ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
OUT = os.path.join(ROOT, "anm", "patched-importer-right-hand-offset-check.json")
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_aks74u_patched_importer_offset.blend"
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


def vlist(v):
    return [float(v.x), float(v.y), float(v.z)]


def pose_dir(arm, bone_name):
    pb = arm.pose.bones[bone_name]
    head = arm.matrix_world @ pb.head
    tail = arm.matrix_world @ pb.tail
    return vlist((tail - head).normalized())


def main():
    bpy.ops.wm.open_mainfile(filepath=CLEAN)
    arm = bpy.data.objects[ARMATURE_NAME]
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    ensure_addon_path()
    import DayzAnimationToolsBinary.Import.ImportAnm as ImportAnm
    importlib.reload(ImportAnm)

    with bpy.context.temp_override(object=arm, active_object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        op_result = bpy.ops.import_scene.anm(
            "EXEC_DEFAULT",
            filepath=ANM,
            files=[{"name": os.path.basename(ANM)}],
        )

    action = arm.animation_data.action
    before_has_right_hand = any(
        fc.data_path == 'pose.bones["RightHand"].rotation_quaternion'
        for fc in action.fcurves
    )
    ImportAnm.ApplyRightHandLoadedOffset(arm, action, bpy.context.scene)
    after_has_right_hand = any(
        fc.data_path == 'pose.bones["RightHand"].rotation_quaternion'
        for fc in action.fcurves
    )

    samples = {}
    for frame in range(int(bpy.context.scene.frame_start), int(bpy.context.scene.frame_end) + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        samples[str(frame)] = {
            "RightHand": pose_dir(arm, "RightHand"),
            "RightHand_Dummy": pose_dir(arm, "RightHand_Dummy"),
            "RightHandIK": pose_dir(arm, "RightHandIK"),
            "RightForeArmDirectionOrigin": pose_dir(arm, "RightForeArmDirectionOrigin"),
        }

    data = {
        "op_result": list(op_result),
        "anm": ANM,
        "saved_as": SAVE_AS,
        "action": action.name,
        "before_has_right_hand_rotation_track": before_has_right_hand,
        "after_has_right_hand_rotation_track": after_has_right_hand,
        "offset_action_property": bool(action.get("dayz_right_hand_loaded_offset_applied", False)),
        "frame_range": [int(bpy.context.scene.frame_start), int(bpy.context.scene.frame_end)],
        "samples": samples,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return data


RESULT = main()
