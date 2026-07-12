import json
import math
import os

import bpy
from mathutils import Matrix


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "right-hand-loaded-pose-delta.json")
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_dayz_diag_right_hand_user_correct.blend"
ARMATURE_NAME = "_DayZ_Character"

INTEREST = [
    "RightShoulder",
    "RightArm",
    "RightArmRoll",
    "RightForeArm",
    "RightForeArmRoll",
    "RightHand",
    "RightHand_Dummy",
    "RightHandIK",
    "RightHandOrigin",
    "RightForeArmDirection",
    "RightForeArmDirectionOrigin",
    "LeftHand",
    "LeftHand_Dummy",
]


def matrix_rows(m):
    return [[float(v) for v in row] for row in m]


def vec_list(v):
    return [float(v.x), float(v.y), float(v.z)]


def quat_list(q):
    return [float(q.w), float(q.x), float(q.y), float(q.z)]


def euler_deg(q):
    e = q.to_euler("XYZ")
    return [float(math.degrees(v)) for v in (e.x, e.y, e.z)]


def pose_row(arm, name):
    pb = arm.pose.bones[name]
    head = arm.matrix_world @ pb.head
    tail = arm.matrix_world @ pb.tail
    direction = (tail - head).normalized()
    basis_quat = pb.matrix_basis.to_quaternion()
    pose_quat = pb.matrix.to_quaternion()
    rest_quat = pb.bone.matrix_local.to_quaternion()
    return {
        "name": name,
        "parent": pb.parent.name if pb.parent else None,
        "head_world": vec_list(head),
        "tail_world": vec_list(tail),
        "direction_world": vec_list(direction),
        "length": float((tail - head).length),
        "matrix_basis": matrix_rows(pb.matrix_basis),
        "basis_quat": quat_list(basis_quat),
        "basis_euler_xyz_deg": euler_deg(basis_quat),
        "pose_quat": quat_list(pose_quat),
        "pose_euler_xyz_deg": euler_deg(pose_quat),
        "rest_quat": quat_list(rest_quat),
        "constraints": [
            {
                "name": c.name,
                "type": c.type,
                "target": c.target.name if getattr(c, "target", None) else None,
                "subtarget": getattr(c, "subtarget", ""),
                "influence": getattr(c, "influence", None),
            }
            for c in pb.constraints
        ],
    }


def rel_delta(parent_row, child_row):
    parent = Matrix(parent_row["matrix_basis"])
    child = Matrix(child_row["matrix_basis"])
    delta = parent.inverted_safe() @ child
    q = delta.to_quaternion()
    return {
        "matrix": matrix_rows(delta),
        "quat": quat_list(q),
        "euler_xyz_deg": euler_deg(q),
    }


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature {ARMATURE_NAME}")

    rows = {name: pose_row(arm, name) for name in INTEREST if name in arm.pose.bones}
    right_chain = ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand", "RightHand_Dummy"]
    deltas = {}
    for parent, child in zip(right_chain, right_chain[1:]):
        if parent in rows and child in rows:
            deltas[f"{parent}->{child}"] = rel_delta(rows[parent], rows[child])

    payload = {
        "file": bpy.data.filepath,
        "saved_reference_pose_as": SAVE_AS,
        "frame": int(bpy.context.scene.frame_current),
        "mode": bpy.context.mode,
        "active_object": bpy.context.object.name if bpy.context.object else None,
        "selected_objects": [o.name for o in bpy.context.selected_objects],
        "bones": rows,
        "right_chain_basis_deltas": deltas,
        "interpretation": {
            "purpose": "Snapshot of user-corrected right hand loaded pose. Use matrix_basis/quaternion deltas to reproduce this as default loaded pose without changing DayZ skeleton names.",
            "do_not_apply_to_rest_skeleton_yet": True,
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return payload


RESULT = main()
