import json
import os

import bpy
from mathutils import Matrix, Vector


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-weaponik-computed-poles.json"
COLLECTION = "DayZ WeaponIK Controls"
PREVIEW_CONSTRAINT = "DayZ WeaponIK Preview"


def ensure_collection():
    col = bpy.data.collections.get(COLLECTION)
    if col is None:
        col = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(col)
    return col


def link_only(obj, col):
    if obj.name not in col.objects:
        col.objects.link(obj)
    for other in list(obj.users_collection):
        if other != col:
            other.objects.unlink(obj)


def world_matrix(arm, bone_name):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    return arm.matrix_world @ pb.matrix


def computed_pole_matrix(arm, origin_name, direction_name):
    origin = world_matrix(arm, origin_name)
    direction = world_matrix(arm, direction_name)
    # DayZDiag helper FUN_1400e1a30 uses originTranslation + originRotation * directionTranslation.
    local_direction = direction.translation
    pole_world = origin.translation + (origin.to_3x3() @ local_direction)
    out = origin.copy()
    out.translation = pole_world
    return out


def make_empty(name, matrix, display_type="SINGLE_ARROW", size=0.08):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
    col = ensure_collection()
    link_only(obj, col)
    obj.parent = None
    obj.empty_display_type = display_type
    obj.empty_display_size = size
    obj.show_name = True
    obj.matrix_world = matrix
    obj["dayz_weaponik_computed_pole"] = True
    return obj


def ensure_hand_ik(arm, hand_name, target_name, pole_obj, pole_angle, use_tail, chain_count):
    hand = arm.pose.bones.get(hand_name)
    if hand is None:
        raise RuntimeError(f"Missing {hand_name}")
    for c in list(hand.constraints):
        if c.type == "IK" and c.name in {"IK", "DayZ Left Hand IK", "DayZ Right Hand IK", PREVIEW_CONSTRAINT}:
            hand.constraints.remove(c)
    c = hand.constraints.new(type="IK")
    c.name = PREVIEW_CONSTRAINT
    c.target = arm
    c.subtarget = target_name
    c.pole_target = pole_obj
    c.pole_subtarget = ""
    c.chain_count = chain_count
    c.iterations = 500
    c.use_rotation = True
    c.use_stretch = False
    c.use_tail = use_tail
    c.pole_angle = pole_angle
    return c


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.context.view_layer.update()

    left_pole = make_empty(
        "WIK_L_Computed_Elbow_Pole",
        computed_pole_matrix(arm, "LeftForeArmDirectionOrigin", "LeftForeArmDirection"),
    )
    right_pole = make_empty(
        "WIK_R_Computed_Elbow_Pole",
        computed_pole_matrix(arm, "RightForeArmDirectionOrigin", "RightForeArmDirection"),
    )

    bpy.ops.object.mode_set(mode="POSE")
    left_ik = ensure_hand_ik(
        arm,
        "LeftHand",
        "LeftHandIKTarget",
        left_pole,
        3.14159 * -127.9 / 180.0,
        use_tail=False,
        chain_count=3,
    )
    right_ik = ensure_hand_ik(
        arm,
        "RightHand",
        "RightHandOrigin",
        right_pole,
        3.14159 * 45.3 / 180.0,
        use_tail=True,
        chain_count=3,
    )
    bpy.context.view_layer.update()

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in [left_pole, right_pole]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = left_pole

    data = {
        "left_pole": list(left_pole.matrix_world.translation),
        "right_pole": list(right_pole.matrix_world.translation),
        "left_ik": {
            "target": left_ik.subtarget,
            "pole_target": left_ik.pole_target.name,
            "chain_count": left_ik.chain_count,
            "use_tail": left_ik.use_tail,
        },
        "right_ik": {
            "target": right_ik.subtarget,
            "pole_target": right_ik.pole_target.name,
            "chain_count": right_ik.chain_count,
            "use_tail": right_ik.use_tail,
        },
        "note": "Computed pole follows DayZDiag origin + originRotation * direction rule for Blender preview.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
