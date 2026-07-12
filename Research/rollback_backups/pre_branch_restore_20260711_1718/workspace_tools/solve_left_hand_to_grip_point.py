import json
import os

import bpy
from mathutils import Vector


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-left-hand-grip-solve.json"


def point(arm, bone_name):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    return Vector(pb.head)


def nearest_weapon_point(needle):
    best = None
    skip = {"Female_body", "zMale_body", "EntityPosition", "zEntityPosition"}
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.visible_get() or obj.name in skip or obj.name.startswith("z"):
            continue
        step = int(max(1, len(obj.data.vertices) // 12000))
        for i in range(0, len(obj.data.vertices), step):
            p = obj.matrix_world @ obj.data.vertices[i].co
            d = (p - needle).length
            if best is None or d < best["distance"]:
                best = {"object": obj.name, "point": p, "distance": d}
    if best is None:
        raise RuntimeError("No weapon mesh found")
    return best


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    target = bpy.data.objects.get("WIK_L_Hand_Target")
    if target is None:
        raise RuntimeError("WIK_L_Hand_Target not found")

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()

    desired_info = nearest_weapon_point(point(arm, "LeftHand"))
    desired = desired_info["point"]
    iterations = []
    for _ in range(8):
        bpy.context.view_layer.update()
        hand = point(arm, "LeftHand")
        err = desired - hand
        iterations.append({
            "hand": list(hand),
            "target": list(target.location),
            "error": list(err),
            "error_len": err.length,
        })
        if err.length < 0.005:
            break
        target.location = target.location + err

    bpy.context.view_layer.update()
    final_hand = point(arm, "LeftHand")
    data = {
        "desired_weapon_point": {
            "object": desired_info["object"],
            "point": list(desired),
        },
        "final_hand": list(final_hand),
        "final_target": list(target.location),
        "final_error": (desired - final_hand).length,
        "iterations": iterations,
        "note": "Target is solver-compensated so the visible hand reaches the weapon point.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
