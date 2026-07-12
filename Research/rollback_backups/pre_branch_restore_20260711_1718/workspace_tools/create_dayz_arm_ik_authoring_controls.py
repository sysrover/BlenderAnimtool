import json
import math
import os

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-arm-ik-authoring-controls.json")
ARMATURE_NAME = "_DayZ_Character"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_arm_ik_controls.blend"

CONTROL_BONES = {
    "DAT_CTRL_L_Hand": "LeftHand",
    "DAT_CTRL_R_Hand": "RightHand",
}

POLE_BONES = {
    "DAT_CTRL_L_Elbow": ("LeftArm", "LeftForeArm", "LeftHand"),
    "DAT_CTRL_R_Elbow": ("RightArm", "RightForeArm", "RightHand"),
}

EXPORT_SKIP_PREFIXES = ("DAT_CTRL_", "WIK_")


def ensure_mode(mode):
    if bpy.context.mode != mode:
        bpy.ops.object.mode_set(mode=mode)


def vec_from_matrix(m):
    return Vector((m[0][3], m[1][3], m[2][3]))


def bone_world_head(arm, bone_name):
    pb = arm.pose.bones[bone_name]
    return arm.matrix_world @ pb.head


def bone_world_tail(arm, bone_name):
    pb = arm.pose.bones[bone_name]
    return arm.matrix_world @ pb.tail


def make_edit_bone(arm, name, head_world, tail_world, parent_name=None):
    eb = arm.data.edit_bones.get(name)
    if eb is None:
        eb = arm.data.edit_bones.new(name)
    inv = arm.matrix_world.inverted()
    eb.head = inv @ head_world
    eb.tail = inv @ tail_world
    eb.roll = 0.0
    eb.use_connect = False
    eb.parent = arm.data.edit_bones.get(parent_name) if parent_name else None
    return eb


def pole_position(arm, upper_name, fore_name, hand_name, side):
    shoulder = bone_world_head(arm, upper_name)
    elbow = bone_world_head(arm, fore_name)
    hand = bone_world_head(arm, hand_name)
    arm_dir = (hand - shoulder)
    if arm_dir.length < 0.0001:
        arm_dir = Vector((0, -1, 0))
    arm_dir.normalize()
    # Remove the along-arm component and push the pole forward/outside.
    bend = elbow - shoulder
    plane = bend - arm_dir * bend.dot(arm_dir)
    if plane.length < 0.0001:
        plane = Vector((-1.0 if side == "L" else 1.0, -0.25, 0.0))
    plane.normalize()
    side_vec = Vector((-0.18 if side == "L" else 0.18, -0.18, 0.0))
    return elbow + plane * 0.28 + side_vec


def clear_constraint(pb, name):
    for c in list(pb.constraints):
        if (
            c.name == name
            or c.name.startswith("DAT Arm Authoring")
            or c.name.startswith("DayZ WeaponIK Preview")
            or c.name.startswith("DayZ WIK Control")
            or c.name in {"DayZ Left Hand IK", "DayZ Right Hand IK"}
        ):
            pb.constraints.remove(c)


def remove_old_weaponik_preview_constraints(arm):
    removed = []
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if (
                c.name.startswith("DayZ WeaponIK Preview")
                or c.name.startswith("DayZ WIK Control")
                or c.name in {"DayZ Left Hand IK", "DayZ Right Hand IK"}
            ):
                removed.append({"bone": pb.name, "constraint": c.name})
                pb.constraints.remove(c)
    return removed


def add_ik(pb, target_name, pole_name, pole_angle):
    clear_constraint(pb, "DAT Arm Authoring IK")
    c = pb.constraints.new(type="IK")
    c.name = "DAT Arm Authoring IK"
    c.target = bpy.context.object
    c.subtarget = target_name
    c.pole_target = bpy.context.object
    c.pole_subtarget = pole_name
    c.pole_angle = pole_angle
    c.chain_count = 2
    c.use_rotation = True
    c.use_stretch = False
    c.influence = 1.0
    return c


def add_copy(pb, target_name, loc=True, rot=True):
    for c in list(pb.constraints):
        if c.name.startswith("DAT Auto Follow"):
            pb.constraints.remove(c)
    if loc:
        c = pb.constraints.new(type="COPY_LOCATION")
        c.name = "DAT Auto Follow Location"
        c.target = bpy.context.object
        c.subtarget = target_name
        c.target_space = "POSE"
        c.owner_space = "POSE"
        c.influence = 1.0
    if rot:
        c = pb.constraints.new(type="COPY_ROTATION")
        c.name = "DAT Auto Follow Rotation"
        c.target = bpy.context.object
        c.subtarget = target_name
        c.target_space = "POSE"
        c.owner_space = "POSE"
        c.influence = 1.0


def hide_all_except_authoring(arm):
    keep = {
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand",
        "DAT_CTRL_L_Hand", "DAT_CTRL_R_Hand", "DAT_CTRL_L_Elbow", "DAT_CTRL_R_Elbow",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    for b in arm.data.bones:
        b.hide = b.name not in keep
        b.select = b.name in CONTROL_BONES or b.name in POLE_BONES
    if arm.data.bones.get("DAT_CTRL_L_Hand"):
        arm.data.bones.active = arm.data.bones["DAT_CTRL_L_Hand"]


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")

    ensure_mode("OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    arm.show_in_front = True
    arm.data.display_type = "BBONE"

    # Hide viewport-only custom shape library.
    coll = bpy.data.collections.get("BoneShapes")
    if coll:
        coll.hide_viewport = True
    hidden_shapes = []
    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_"):
            obj.hide_set(True)
            obj.hide_viewport = True
            hidden_shapes.append(obj.name)

    ensure_mode("EDIT")
    created = []

    for ctrl_name, hand_name in CONTROL_BONES.items():
        if hand_name not in arm.pose.bones:
            continue
        head = bone_world_head(arm, hand_name)
        tail = head + Vector((0.0, 0.0, 0.12))
        make_edit_bone(arm, ctrl_name, head, tail)
        created.append(ctrl_name)

    for ctrl_name, (upper, fore, hand) in POLE_BONES.items():
        if not all(name in arm.pose.bones for name in (upper, fore, hand)):
            continue
        side = "L" if "_L_" in ctrl_name else "R"
        head = pole_position(arm, upper, fore, hand, side)
        tail = head + Vector((0.0, 0.0, 0.10))
        make_edit_bone(arm, ctrl_name, head, tail)
        created.append(ctrl_name)

    ensure_mode("POSE")
    removed_old_constraints = remove_old_weaponik_preview_constraints(arm)
    for name in created:
        pb = arm.pose.bones.get(name)
        if pb:
            pb.rotation_mode = "QUATERNION"
            pb.custom_shape = None
            pb.color.palette = "THEME09"

    if "LeftHand" in arm.pose.bones:
        add_ik(arm.pose.bones["LeftHand"], "DAT_CTRL_L_Hand", "DAT_CTRL_L_Elbow", math.radians(-90.0))
    if "RightHand" in arm.pose.bones:
        add_ik(arm.pose.bones["RightHand"], "DAT_CTRL_R_Hand", "DAT_CTRL_R_Elbow", math.radians(90.0))

    # Technical DayZ helper bones should follow the authoring controls and stay hidden.
    follow_map = {
        "LeftHandIKTarget": "DAT_CTRL_L_Hand",
        "LeftHandOrigin": "DAT_CTRL_L_Hand",
        "LeftHandIK": "DAT_CTRL_L_Hand",
        "LeftHand_Dummy": "DAT_CTRL_L_Hand",
        "LeftForeArmDirection": "DAT_CTRL_L_Elbow",
        "LeftForeArmDirectionOrigin": "DAT_CTRL_L_Elbow",
        "RightHandOrigin": "DAT_CTRL_R_Hand",
        "RightHandIK": "DAT_CTRL_R_Hand",
        "RightHand_Dummy": "DAT_CTRL_R_Hand",
        "RightForeArmDirection": "DAT_CTRL_R_Elbow",
        "RightForeArmDirectionOrigin": "DAT_CTRL_R_Elbow",
    }
    followed = []
    for bone_name, target_name in follow_map.items():
        if bone_name in arm.pose.bones and target_name in arm.pose.bones:
            add_copy(arm.pose.bones[bone_name], target_name, loc=True, rot=True)
            followed.append(bone_name)

    hide_all_except_authoring(arm)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    visible = [b.name for b in arm.data.bones if not b.hide]
    data = {
        "file_saved_as": SAVE_PATH,
        "created_or_updated_controls": sorted(created),
        "auto_follow_helper_bones": sorted(followed),
        "visible_bones": sorted(visible),
        "visible_bones_count": len(visible),
        "hidden_shape_objects": sorted(hidden_shapes),
        "removed_old_weaponik_preview_constraints": removed_old_constraints,
        "note": "Move DAT_CTRL_* hand bones for arm IK and DAT_CTRL_* elbow bones for pole direction. Technical DayZ helper bones are hidden and constrained to controls.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
