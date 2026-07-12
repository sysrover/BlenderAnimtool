import json
import os

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-safe-weaponik-lock-preview.json")
ARMATURE_NAME = "_DayZ_Character"
LEFT_TARGET_OFFSET = Vector((0.0, 0.0, -0.025))


def ensure_empty(name, location, display_type="SINGLE_ARROW", size=0.075):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        col = bpy.data.collections.get("DayZ WeaponIK Controls")
        if col is None:
            col = bpy.data.collections.new("DayZ WeaponIK Controls")
            bpy.context.scene.collection.children.link(col)
        col.objects.link(obj)
    obj.parent = None
    obj.empty_display_type = display_type
    obj.empty_display_size = size
    obj.show_name = True
    obj.location = location
    obj["dayz_weaponik_control"] = True
    obj["preview_only"] = True
    return obj


def head(arm, name):
    pb = arm.pose.bones.get(name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {name}")
    return Vector(pb.head)


def anatomical_pole(arm, shoulder, elbow, wrist, fallback):
    s = head(arm, shoulder)
    e = head(arm, elbow)
    w = head(arm, wrist)
    line = w - s
    if line.length < 0.0001:
        direction = fallback
    else:
        t = max(0.0, min(1.0, (e - s).dot(line) / line.dot(line)))
        projected = s + line * t
        direction = e - projected
        if direction.length < 0.0001:
            direction = fallback
        else:
            direction.normalize()
    return e + direction * 0.35


def remove_preview_constraints(arm):
    removed = []
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name == "DayZ WeaponIK Preview" or c.name.startswith("DayZ WIK Control"):
                removed.append(f"{pb.name}:{c.name}")
                pb.constraints.remove(c)
    return removed


def ensure_ik(arm, hand_name, target_name, pole_obj, pole_angle, chain_count, use_tail):
    hand = arm.pose.bones.get(hand_name)
    if hand is None:
        raise RuntimeError(f"Missing pose bone {hand_name}")
    c = hand.constraints.new(type="IK")
    c.name = "DayZ WeaponIK Preview"
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

    removed = remove_preview_constraints(arm)

    # Always start from the evaluated clean full-body/helper pose.
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()

    # Offset only the viewport target. Do not edit the helper action data.
    left_target = ensure_empty(
        "WIK_L_Viewport_Target",
        head(arm, "LeftHandIKTarget") + LEFT_TARGET_OFFSET,
        "SPHERE",
        0.045,
    )
    right_target = ensure_empty(
        "WIK_R_Viewport_Target",
        head(arm, "RightHandOrigin"),
        "SPHERE",
        0.045,
    )
    left_pole = ensure_empty(
        "WIK_L_Viewport_Elbow_Pole",
        anatomical_pole(arm, "LeftArm", "LeftForeArm", "LeftHand", Vector((-1.0, 0.0, 0.0))),
        "SINGLE_ARROW",
        0.075,
    )
    right_pole = ensure_empty(
        "WIK_R_Viewport_Elbow_Pole",
        anatomical_pole(arm, "RightArm", "RightForeArm", "RightHand", Vector((1.0, 0.0, 0.0))),
        "SINGLE_ARROW",
        0.075,
    )

    # Copy viewport target transforms to real helper bones via constraints.
    for helper, target in [("LeftHandIKTarget", left_target), ("RightHandOrigin", right_target)]:
        pb = arm.pose.bones.get(helper)
        loc = pb.constraints.new(type="COPY_LOCATION")
        loc.name = "DayZ WIK Control Copy Location"
        loc.target = target
        loc.owner_space = "WORLD"
        loc.target_space = "WORLD"
        rot = pb.constraints.new(type="COPY_ROTATION")
        rot.name = "DayZ WIK Control Copy Rotation"
        rot.target = target
        rot.owner_space = "WORLD"
        rot.target_space = "WORLD"

    bpy.context.view_layer.update()

    ensure_ik(arm, "LeftHand", "LeftHandIKTarget", left_pole, 3.14159 * -127.9 / 180.0, 3, False)
    ensure_ik(arm, "RightHand", "RightHandOrigin", right_pole, 3.14159 * 45.3 / 180.0, 3, True)
    bpy.context.view_layer.update()

    arm["dayz_weaponik_mode"] = "Viewport Lock Preview"

    data = {
        "mode": arm["dayz_weaponik_mode"],
        "frame": bpy.context.scene.frame_current,
        "removed": removed,
        "left_target_offset_m": list(LEFT_TARGET_OFFSET),
        "left_target": list(left_target.location),
        "right_target": list(right_target.location),
        "left_hand": list(head(arm, "LeftHand")),
        "right_hand": list(head(arm, "RightHand")),
        "note": "Preview-only lock. This uses Blender IK for viewport checking, not export truth.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
