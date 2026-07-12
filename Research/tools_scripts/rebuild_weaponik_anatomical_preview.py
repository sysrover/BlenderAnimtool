import json
import os

import bpy
from mathutils import Vector


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-weaponik-anatomical-preview.json"
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


def ensure_empty(name, position, display_type="SINGLE_ARROW", size=0.08):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
    link_only(obj, ensure_collection())
    obj.parent = None
    obj.empty_display_type = display_type
    obj.empty_display_size = size
    obj.show_name = True
    obj.location = position
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj["dayz_weaponik_control"] = True
    obj["dayz_weaponik_anatomical_pole"] = True
    return obj


def point(arm, bone_name, attr="head"):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    return Vector(getattr(pb, attr))


def anatomical_pole(arm, shoulder_name, elbow_name, wrist_name, fallback_side):
    shoulder = point(arm, shoulder_name, "head")
    elbow = point(arm, elbow_name, "head")
    wrist = point(arm, wrist_name, "head")
    line = wrist - shoulder
    if line.length < 0.0001:
        return elbow + fallback_side
    t = max(0.0, min(1.0, (elbow - shoulder).dot(line) / line.dot(line)))
    projected = shoulder + line * t
    direction = elbow - projected
    if direction.length < 0.0001:
        direction = fallback_side
    else:
        direction.normalize()
    return elbow + direction * 0.45


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

    left_pole_pos = anatomical_pole(
        arm,
        "LeftArm",
        "LeftForeArm",
        "LeftHand",
        Vector((-0.45, 0.0, 0.0)),
    )
    right_pole_pos = anatomical_pole(
        arm,
        "RightArm",
        "RightForeArm",
        "RightHand",
        Vector((0.45, 0.0, 0.0)),
    )
    left_pole = ensure_empty("WIK_L_Elbow_Pole", left_pole_pos)
    right_pole = ensure_empty("WIK_R_Elbow_Pole", right_pole_pos)

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

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in [left_pole, right_pole]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = left_pole

    data = {
        "left_pole": list(left_pole.location),
        "right_pole": list(right_pole.location),
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
        "note": "Blender preview uses anatomical elbow pole controls and chain_count=3 to avoid pulling upper arms into the face.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
