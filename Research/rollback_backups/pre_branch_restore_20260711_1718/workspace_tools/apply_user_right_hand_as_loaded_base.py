import json
import os

import bpy
from mathutils import Matrix


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN = r"P:\Animation_Weapon\Weapon_template_dayz_diag_restored.blend"
USER_JSON = os.path.join(ROOT, "anm", "right-hand-loaded-pose-delta.json")
OUT = os.path.join(ROOT, "anm", "right-hand-loaded-base-apply-check.json")
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_dayz_diag_loaded_base_right_hand_correct.blend"
ARMATURE_NAME = "_DayZ_Character"


CHECK_BONES = [
    "RightHand",
    "RightHand_Dummy",
    "RightHandIK",
    "RightHandOrigin",
    "RightForeArmDirectionOrigin",
]


def rows(m):
    return [[float(v) for v in row] for row in m]


def vlist(v):
    return [float(v.x), float(v.y), float(v.z)]


def pose_row(arm, name):
    pb = arm.pose.bones[name]
    head = arm.matrix_world @ pb.head
    tail = arm.matrix_world @ pb.tail
    return {
        "matrix_basis": rows(pb.matrix_basis),
        "head_world": vlist(head),
        "tail_world": vlist(tail),
        "direction_world": vlist((tail - head).normalized()),
    }


def max_abs_matrix_delta(a, b):
    ma = Matrix(a)
    mb = Matrix(b)
    return max(abs(float(ma[r][c] - mb[r][c])) for r in range(4) for c in range(4))


def vec_error(a, b):
    return max(abs(float(a[i] - b[i])) for i in range(3))


def main():
    with open(USER_JSON, "r", encoding="utf-8") as f:
        user = json.load(f)

    bpy.ops.wm.open_mainfile(filepath=CLEAN)
    arm = bpy.data.objects[ARMATURE_NAME]

    target_basis = Matrix(user["bones"]["RightHand"]["matrix_basis"])
    arm.pose.bones["RightHand"].matrix_basis = target_basis
    bpy.context.view_layer.update()

    after = {name: pose_row(arm, name) for name in CHECK_BONES}
    checks = {}
    max_error = 0.0
    for name, row in after.items():
        user_row = user["bones"][name]
        matrix_error = max_abs_matrix_delta(row["matrix_basis"], user_row["matrix_basis"])
        dir_error = vec_error(row["direction_world"], user_row["direction_world"])
        checks[name] = {
            "matrix_basis_max_abs_delta_vs_user": matrix_error,
            "direction_max_abs_delta_vs_user": dir_error,
            "after_direction_world": row["direction_world"],
            "user_direction_world": user_row["direction_world"],
        }
        max_error = max(max_error, matrix_error, dir_error)

    payload = {
        "source_clean": CLEAN,
        "user_reference": USER_JSON,
        "saved_as": SAVE_AS,
        "applied_bones": ["RightHand"],
        "right_hand_target_matrix_basis": rows(target_basis),
        "check_bones": checks,
        "max_error": max_error,
        "accepted": max_error < 0.0001,
        "meaning": "Setting only RightHand.matrix_basis reproduces the user-correct loaded pose for hand and inherited helpers.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return payload


RESULT = main()
