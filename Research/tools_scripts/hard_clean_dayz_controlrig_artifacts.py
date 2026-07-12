import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend"
OUT_JSON = os.path.join(ROOT, "anm", "hard-clean-controlrig-artifacts.json")


def object_mode():
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass


def main():
    object_mode()
    removed_objects = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith("DAT_ControlRig") or obj.name.startswith("DAT_CTRL"):
            removed_objects.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    removed_constraints = []
    for obj in bpy.data.objects:
        if obj.type != "ARMATURE":
            continue
        for pb in obj.pose.bones:
            for c in list(pb.constraints):
                if (
                    c.name.startswith("DAT ")
                    or c.name.startswith("DAT_")
                    or c.name.startswith("DayZ WeaponIK Preview")
                    or c.name.startswith("WIK ")
                ):
                    removed_constraints.append({
                        "armature": obj.name,
                        "bone": pb.name,
                        "constraint": c.name,
                        "type": c.type,
                    })
                    pb.constraints.remove(c)

    dayz = bpy.data.objects.get("_DayZ_Character")
    visible = []
    if dayz and dayz.type == "ARMATURE":
        keep = {
            "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
            "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
            "LeftHandOrigin", "LeftHandIK", "LeftHandIKTarget", "LeftHand_Dummy",
            "LeftForeArmDirection", "LeftForeArmDirectionOrigin",
            "RightHandOrigin", "RightHandIK", "RightHand_Dummy",
            "RightForeArmDirection", "RightForeArmDirectionOrigin",
            "Weapon_Root", "Weapon_Trigger", "Weapon_Magazine", "Weapon_Bolt",
        }
        for b in dayz.data.bones:
            b.hide = b.name not in keep
        visible = sorted([b.name for b in dayz.data.bones if not b.hide])

    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)
    result = {
        "saved_as": SAVE_PATH,
        "removed_objects": removed_objects,
        "removed_constraints": removed_constraints,
        "visible_bones": visible,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


RESULT = main()
