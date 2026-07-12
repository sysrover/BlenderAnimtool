import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "right-hand-selfcheck-and-fix.json")
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_right_hand_preview_dummy_aligned.blend"

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


def bone_row(arm, bone_name):
    head, tail, direction = pose_points(arm, bone_name)
    return {
        "bone": bone_name,
        "head": vlist(head),
        "tail": vlist(tail),
        "direction": vlist(direction),
        "length": float((tail - head).length),
        "constraints": [c.name for c in arm.pose.bones[bone_name].constraints],
    }


def snapshot(arm):
    names = [
        "LeftHand",
        "RightHand",
        "LeftHand_Dummy",
        "RightHand_Dummy",
        "RightHandIK",
        "RightHandOrigin",
        "RightForeArm",
        "RightForeArmDirection",
    ]
    rows = {name: bone_row(arm, name) for name in names if name in arm.pose.bones}

    lh = Vector(rows["LeftHand"]["direction"])
    rh = Vector(rows["RightHand"]["direction"])
    lhd = Vector(rows["LeftHand_Dummy"]["direction"])
    rhd = Vector(rows["RightHand_Dummy"]["direction"])
    rho = Vector(rows["RightHandOrigin"]["direction"])

    # DayZ right side is not a simple X mirror in this file. Rest data shows
    # right arm/hand is closest to left mirrored across Y and Z.
    mirror_yz_lh = Vector((lh.x, -lh.y, -lh.z))
    mirror_yz_lhd = Vector((lhd.x, -lhd.y, -lhd.z))

    metrics = {
        "right_hand_vs_left_raw_dot": dot(rh, lh),
        "right_hand_vs_left_mirror_yz_dot": dot(rh, mirror_yz_lh),
        "right_dummy_vs_left_dummy_raw_dot": dot(rhd, lhd),
        "right_dummy_vs_left_dummy_mirror_yz_dot": dot(rhd, mirror_yz_lhd),
        "right_dummy_vs_right_hand_dot": dot(rhd, rh),
        "right_dummy_vs_right_hand_origin_dot": dot(rhd, rho),
        "right_hand_y": float(rh.y),
        "right_dummy_y": float(rhd.y),
    }
    metrics["right_hand_backwards_flag"] = metrics["right_hand_y"] < -0.25
    metrics["right_dummy_backwards_flag"] = metrics["right_dummy_vs_right_hand_dot"] < 0.0
    return rows, metrics


def set_pose_tail_direction(arm, bone_name, target_dir_world):
    pb = arm.pose.bones[bone_name]
    rest_dir_arm = (pb.bone.tail_local - pb.bone.head_local).normalized()
    target_dir_arm = (arm.matrix_world.inverted().to_3x3() @ target_dir_world).normalized()
    q = rest_dir_arm.rotation_difference(target_dir_arm)
    # Keep translation from current evaluated pose; replace orientation only.
    loc = pb.matrix.to_translation()
    scale = pb.matrix.to_scale()
    pb.matrix = Matrix.LocRotScale(loc, q, scale)


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature {ARMATURE_NAME}")

    before_rows, before_metrics = snapshot(arm)

    # If the hand itself is already forward but the dummy/IK child points opposite,
    # align dummy/IK visible direction to the hand/origin direction. This avoids
    # editing rest skeleton and avoids reintroducing IK constraints.
    _, _, right_hand_dir = pose_points(arm, "RightHand")
    _, _, right_origin_dir = pose_points(arm, "RightHandOrigin")
    target_dir = (right_hand_dir + right_origin_dir).normalized()

    fixed = []
    if before_metrics["right_dummy_backwards_flag"]:
        for name in ("RightHand_Dummy", "RightHandIK"):
            if name in arm.pose.bones:
                set_pose_tail_direction(arm, name, target_dir)
                fixed.append(name)
        bpy.context.view_layer.update()

    after_rows, after_metrics = snapshot(arm)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    payload = {
        "source_file": bpy.data.filepath,
        "saved_as": SAVE_AS,
        "fixed_pose_bones": fixed,
        "before": {"rows": before_rows, "metrics": before_metrics},
        "after": {"rows": after_rows, "metrics": after_metrics},
        "verdict": {
            "right_hand_itself_ok": not after_metrics["right_hand_backwards_flag"],
            "right_dummy_aligned_with_hand": after_metrics["right_dummy_vs_right_hand_dot"] > 0.75,
            "all_right": (not after_metrics["right_hand_backwards_flag"])
            and after_metrics["right_dummy_vs_right_hand_dot"] > 0.75,
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return payload


RESULT = main()
