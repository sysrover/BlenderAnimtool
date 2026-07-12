import json
import math
import os

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN = r"P:\Animation_Weapon\Weapon_template_dayz_diag_restored.blend"
USER_JSON = os.path.join(ROOT, "anm", "right-hand-loaded-pose-delta.json")
OUT = os.path.join(ROOT, "anm", "right-hand-clean-vs-user-correction.json")
ARMATURE_NAME = "_DayZ_Character"

INTEREST = [
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
]


def q_from_rows(rows):
    return Matrix(rows).to_quaternion()


def q_list(q):
    return [float(q.w), float(q.x), float(q.y), float(q.z)]


def euler_deg(q):
    e = q.to_euler("XYZ")
    return [float(math.degrees(v)) for v in (e.x, e.y, e.z)]


def angle_deg(q):
    return float(math.degrees(q.angle))


def matrix_rows(m):
    return [[float(v) for v in row] for row in m]


def vec_list(v):
    return [float(v.x), float(v.y), float(v.z)]


def pose_data(arm, name):
    pb = arm.pose.bones[name]
    head = arm.matrix_world @ pb.head
    tail = arm.matrix_world @ pb.tail
    return {
        "matrix_basis": matrix_rows(pb.matrix_basis),
        "basis_quat": q_list(pb.matrix_basis.to_quaternion()),
        "basis_euler_xyz_deg": euler_deg(pb.matrix_basis.to_quaternion()),
        "head_world": vec_list(head),
        "tail_world": vec_list(tail),
        "direction_world": vec_list((tail - head).normalized()),
    }


def main():
    with open(USER_JSON, "r", encoding="utf-8") as f:
        user = json.load(f)

    bpy.ops.wm.open_mainfile(filepath=CLEAN)
    arm = bpy.data.objects[ARMATURE_NAME]
    clean = {name: pose_data(arm, name) for name in INTEREST if name in arm.pose.bones}

    diff = {}
    changed = []
    for name, clean_row in clean.items():
        if name not in user["bones"]:
            continue
        qc = q_from_rows(clean_row["matrix_basis"])
        qu = q_from_rows(user["bones"][name]["matrix_basis"])
        delta = qc.inverted() @ qu
        loc_c = Matrix(clean_row["matrix_basis"]).to_translation()
        loc_u = Matrix(user["bones"][name]["matrix_basis"]).to_translation()
        loc_delta = loc_u - loc_c
        row = {
            "bone": name,
            "rotation_delta_quat": q_list(delta),
            "rotation_delta_euler_xyz_deg": euler_deg(delta),
            "rotation_delta_angle_deg": angle_deg(delta),
            "location_delta": vec_list(loc_delta),
            "location_delta_len": float(loc_delta.length),
            "clean_basis_euler_xyz_deg": clean_row["basis_euler_xyz_deg"],
            "user_basis_euler_xyz_deg": user["bones"][name]["basis_euler_xyz_deg"],
            "clean_direction_world": clean_row["direction_world"],
            "user_direction_world": user["bones"][name]["direction_world"],
        }
        diff[name] = row
        if row["rotation_delta_angle_deg"] > 0.1 or row["location_delta_len"] > 0.0001:
            changed.append(name)

    payload = {
        "clean": CLEAN,
        "user_reference_json": USER_JSON,
        "changed_bones": changed,
        "diff": diff,
        "recommended_loaded_pose_apply_bones": [
            name for name in changed
            if name in {
                "RightHand",
                "RightHand_Dummy",
                "RightHandOrigin",
                "RightForeArmDirection",
                "RightForeArmDirectionOrigin",
            }
        ],
        "addon_suspicion": {
            "file": r"%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationToolsBinary\Import\ImportAnm.py",
            "right_hand_origin_rotation_uses_inverted_rot": True,
            "right_hand_origin_translation_uses_negative_trans": True,
            "reason": "Right side helper decode is asymmetric; user-corrected pose changes RightHandOrigin/RightForeArmDirection helpers in the same area.",
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload


RESULT = main()
