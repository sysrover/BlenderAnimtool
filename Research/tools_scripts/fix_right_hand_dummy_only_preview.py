import json
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
SOURCE = r"P:\Animation_Weapon\Weapon_template_right_hand_preview_flip.blend"
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_right_hand_preview_dummy_only.blend"
OUT = os.path.join(ROOT, "anm", "right-hand-dummy-only-fix-result.json")
ARMATURE_NAME = "_DayZ_Character"


def vlist(v):
    return [float(v.x), float(v.y), float(v.z)]


def pose_points(arm, bone_name):
    pb = arm.pose.bones[bone_name]
    head = arm.matrix_world @ pb.head
    tail = arm.matrix_world @ pb.tail
    direction = (tail - head).normalized()
    return head, tail, direction


def dot(a, b):
    return float(a.normalized().dot(b.normalized()))


def row(arm, bone_name):
    head, tail, direction = pose_points(arm, bone_name)
    return {
        "bone": bone_name,
        "head": vlist(head),
        "tail": vlist(tail),
        "direction": vlist(direction),
        "length": float((tail - head).length),
    }


def dist(arm, a, b):
    ah, _, _ = pose_points(arm, a)
    bh, _, _ = pose_points(arm, b)
    return float((ah - bh).length)


def metrics(arm):
    _, _, rh = pose_points(arm, "RightHand")
    _, _, rhd = pose_points(arm, "RightHand_Dummy")
    _, _, rho = pose_points(arm, "RightHandOrigin")
    _, _, lhd = pose_points(arm, "LeftHand_Dummy")
    return {
        "right_hand_y": float(rh.y),
        "right_dummy_y": float(rhd.y),
        "right_dummy_vs_right_hand_dot": dot(rhd, rh),
        "right_dummy_vs_right_hand_origin_dot": dot(rhd, rho),
        "right_dummy_vs_left_dummy_dot": dot(rhd, lhd),
        "right_ik_distance_to_dummy": dist(arm, "RightHandIK", "RightHand_Dummy"),
        "right_ik_distance_to_hand": dist(arm, "RightHandIK", "RightHand"),
        "right_hand_backwards_flag": float(rh.y) < -0.25,
        "right_dummy_backwards_flag": dot(rhd, rh) < 0.0,
    }


def set_pose_tail_direction(arm, bone_name, target_dir_world):
    pb = arm.pose.bones[bone_name]
    rest_dir_arm = (pb.bone.tail_local - pb.bone.head_local).normalized()
    target_dir_arm = (arm.matrix_world.inverted().to_3x3() @ target_dir_world).normalized()
    q = rest_dir_arm.rotation_difference(target_dir_arm)
    loc = pb.matrix.to_translation()
    scale = pb.matrix.to_scale()
    pb.matrix = Matrix.LocRotScale(loc, q, scale)


def main():
    if bpy.data.filepath != SOURCE:
        bpy.ops.wm.open_mainfile(filepath=SOURCE)
    arm = bpy.data.objects[ARMATURE_NAME]
    before = {
        "rows": {n: row(arm, n) for n in ["RightHand", "RightHand_Dummy", "RightHandIK", "RightHandOrigin"]},
        "metrics": metrics(arm),
    }
    _, _, right_hand_dir = pose_points(arm, "RightHand")
    _, _, right_origin_dir = pose_points(arm, "RightHandOrigin")
    target_dir = (right_hand_dir + right_origin_dir).normalized()
    fixed = []
    if before["metrics"]["right_dummy_backwards_flag"]:
        set_pose_tail_direction(arm, "RightHand_Dummy", target_dir)
        fixed.append("RightHand_Dummy")
        bpy.context.view_layer.update()
    after = {
        "rows": {n: row(arm, n) for n in ["RightHand", "RightHand_Dummy", "RightHandIK", "RightHandOrigin"]},
        "metrics": metrics(arm),
    }
    payload = {
        "source": SOURCE,
        "saved_as": SAVE_AS,
        "fixed_pose_bones": fixed,
        "before": before,
        "after": after,
        "accepted": (
            not after["metrics"]["right_hand_backwards_flag"]
            and not after["metrics"]["right_dummy_backwards_flag"]
            and after["metrics"]["right_dummy_vs_right_hand_dot"] > 0.75
        ),
        "note": "Only RightHand_Dummy pose orientation changed; RightHandIK was not directly edited.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return payload


RESULT = main()
