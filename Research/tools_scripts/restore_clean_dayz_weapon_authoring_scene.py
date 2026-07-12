import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-restore-clean-authoring.json")
ARMATURE_NAME = "_DayZ_Character"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend"


BAD_CONSTRAINT_PREFIXES = (
    "DAT Arm Authoring",
    "DAT Auto Follow",
    "DayZ WeaponIK Preview",
    "DayZ WIK Control",
)
BAD_CONSTRAINT_NAMES = {
    "DayZ Left Hand IK",
    "DayZ Right Hand IK",
}
BAD_BONE_PREFIXES = (
    "DAT_CTRL_",
    "WIK_",
)


def ensure_mode(mode):
    if bpy.context.mode != mode:
        bpy.ops.object.mode_set(mode=mode)


def remove_bad_constraints(arm):
    removed = []
    ensure_mode("POSE")
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name in BAD_CONSTRAINT_NAMES or any(c.name.startswith(prefix) for prefix in BAD_CONSTRAINT_PREFIXES):
                removed.append({"bone": pb.name, "constraint": c.name, "type": c.type})
                pb.constraints.remove(c)
    return removed


def remove_bad_bones(arm):
    removed = []
    ensure_mode("EDIT")
    for eb in list(arm.data.edit_bones):
        if any(eb.name.startswith(prefix) for prefix in BAD_BONE_PREFIXES):
            removed.append(eb.name)
            arm.data.edit_bones.remove(eb)
    return removed


def apply_safe_visibility(arm):
    keep_exact = {
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand",
        "LeftHandIK", "LeftHandOrigin", "LeftHandIKTarget", "LeftHand_Dummy",
        "LeftForeArmDirection", "LeftForeArmDirectionOrigin",
        "RightHandIK", "RightHandOrigin", "RightHand_Dummy",
        "RightForeArmDirection", "RightForeArmDirectionOrigin",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    ensure_mode("OBJECT")
    visible = []
    for b in arm.data.bones:
        b.hide = b.name not in keep_exact
        b.select = False
        if not b.hide:
            visible.append(b.name)
    return visible


def hide_shape_library():
    hidden = []
    coll = bpy.data.collections.get("BoneShapes")
    if coll:
        coll.hide_viewport = True
    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_"):
            obj.hide_set(True)
            obj.hide_viewport = True
            hidden.append(obj.name)
    return hidden


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")

    ensure_mode("OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm

    removed_constraints = remove_bad_constraints(arm)
    removed_bones = remove_bad_bones(arm)
    visible = apply_safe_visibility(arm)
    hidden_shapes = hide_shape_library()

    ensure_mode("POSE")
    bpy.context.view_layer.update()
    arm.show_in_front = True
    arm.data.display_type = "BBONE"

    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    data = {
        "file_saved_as": SAVE_PATH,
        "removed_constraints": removed_constraints,
        "removed_control_bones": removed_bones,
        "visible_bones": sorted(visible),
        "visible_bones_count": len(visible),
        "hidden_shape_objects": sorted(hidden_shapes),
        "note": "Restored safe state: no Blender IK authoring constraints and no DAT_CTRL bones. Technical DayZ helpers are visible only for inspection.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
