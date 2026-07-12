import json
import os

import bpy
from mathutils import Vector


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-left-hand-grip-snap.json"
CONTROL_CONSTRAINT_PREFIX = "DayZ WIK Control"


BODY_OR_HELPER_OBJECTS = {
    "Female_body",
    "zMale_body",
    "EntityPosition",
    "zEntityPosition",
}


def pose_point(arm, bone_name, attr="head"):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    return Vector(getattr(pb, attr))


def nearest_weapon_point_to(needle):
    best = None
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.visible_get():
            continue
        if obj.name in BODY_OR_HELPER_OBJECTS or obj.name.startswith("z"):
            continue
        verts = obj.data.vertices
        step = int(max(1, len(verts) // 12000))
        for i in range(0, len(verts), step):
            p = obj.matrix_world @ verts[i].co
            d = (p - needle).length
            if best is None or d < best["distance"]:
                best = {
                    "object": obj.name,
                    "distance": d,
                    "point": p,
                }
    if best is None:
        raise RuntimeError("No visible weapon mesh vertices found")
    return best


def get_or_create_empty(name, location, display_type="SPHERE", size=0.045):
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
    return obj


def set_control_constraint_mute(arm, helper_name, mute):
    pb = arm.pose.bones.get(helper_name)
    if pb is None:
        raise RuntimeError(f"Missing helper bone {helper_name}")
    changed = []
    for c in pb.constraints:
        if c.name.startswith(CONTROL_CONSTRAINT_PREFIX):
            c.mute = mute
            changed.append(c.name)
    return changed


def copy_rotation_from_bone(obj, arm, bone_name):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        return
    obj.matrix_world = pb.id_data.matrix_world @ pb.matrix
    obj.location = obj.location


def place_anatomical_left_pole(arm):
    shoulder = pose_point(arm, "LeftArm", "head")
    elbow = pose_point(arm, "LeftForeArm", "head")
    wrist = pose_point(arm, "LeftHand", "head")
    line = wrist - shoulder
    if line.length < 0.0001:
        direction = Vector((-1.0, 0.0, 0.0))
    else:
        t = max(0.0, min(1.0, (elbow - shoulder).dot(line) / line.dot(line)))
        projected = shoulder + line * t
        direction = elbow - projected
        if direction.length < 0.0001:
            direction = Vector((-1.0, 0.0, 0.0))
        else:
            direction.normalize()
    pole_location = elbow + direction * 0.35
    pole = get_or_create_empty("WIK_L_Elbow_Pole", pole_location, "SINGLE_ARROW", 0.075)
    return pole


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    bpy.context.view_layer.update()

    left_hand = pose_point(arm, "LeftHand", "head")
    best = nearest_weapon_point_to(left_hand)

    target = get_or_create_empty("WIK_L_Hand_Target", best["point"], "SPHERE", 0.045)
    copy_rotation_from_bone(target, arm, "LeftHandIKTarget")
    target.location = best["point"]

    bpy.ops.object.mode_set(mode="POSE")
    changed = set_control_constraint_mute(arm, "LeftHandIKTarget", False)
    arm["dayz_weaponik_mode"] = "Manual Authoring"
    bpy.context.view_layer.update()

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    pole = place_anatomical_left_pole(arm)
    bpy.context.view_layer.update()

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    target.select_set(True)
    pole.select_set(True)
    bpy.context.view_layer.objects.active = target

    data = {
        "mode": "Manual Authoring",
        "snapped_to": {
            "object": best["object"],
            "distance_before": best["distance"],
            "point": list(best["point"]),
        },
        "unmuted_constraints": changed,
        "left_hand_after": list(pose_point(arm, "LeftHand", "head")),
        "target_after": list(target.location),
        "pole_after": list(pole.location),
        "note": "LeftHandIKTarget is now driven by WIK_L_Hand_Target. This is authoring/preview state; bake/export should write helper tracks.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
