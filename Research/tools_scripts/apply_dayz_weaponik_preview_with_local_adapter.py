import json
import os
import sys

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ADDON_ROOT = r"P:\BlenderAnimtool"
OUT = os.path.join(ROOT, "anm", "blender-dayz-local-adapter-preview.json")
ARMATURE_NAME = "_DayZ_Character"
FULL_BODY_ACTION = "p_rfl_erc_idle_ras"
HELPER_ACTION = "aks74u_helpers_only"

if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)

from DayzAnimationTools.Utils.WeaponIKSolver import IkXform, solve_weapon_ik_chain


PRIMARY_CHAIN = ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand"]
SECONDARY_CHAIN = ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"]


def ensure_clean_actions(arm):
    if arm.animation_data is None:
        arm.animation_data_create()
    helper = bpy.data.actions.get(HELPER_ACTION)
    if helper is None:
        raise RuntimeError(f"Missing helper action {HELPER_ACTION}; run create_weaponik_helper_only_action.py first")
    full = bpy.data.actions.get(FULL_BODY_ACTION)
    if full is None:
        raise RuntimeError(f"Missing full-body action {FULL_BODY_ACTION}")

    arm.animation_data.action = helper
    for tr in arm.animation_data.nla_tracks:
        for st in tr.strips:
            if st.action == full:
                tr.mute = False
                st.mute = False
                st.influence = 1.0
                st.blend_type = "REPLACE"
            else:
                tr.mute = True


def remove_preview_constraints_and_reset_basis(arm):
    removed = []
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DayZ WIK Control") or c.name == "DayZ WeaponIK Preview":
                removed.append(f"{pb.name}:{c.name}")
                pb.constraints.remove(c)
        pb.matrix_basis.identity()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()
    return removed


def pose_xform(arm, bone_name):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    return IkXform(pb.matrix.to_quaternion().normalized(), Vector(pb.head))


def object_matrix_from_xform(pb, xform):
    # Keep current pose scale. DayZ compact records carry rot+translation only.
    return Matrix.LocRotScale(xform.location, xform.rotation, pb.matrix.to_scale())


def matrix_basis_from_object_matrix(pb, desired_object_matrix):
    bone_rest = pb.bone.matrix_local
    if pb.parent is None:
        base = bone_rest
    else:
        parent_rest = pb.parent.bone.matrix_local
        base = pb.parent.matrix @ parent_rest.inverted() @ bone_rest
    return base.inverted() @ desired_object_matrix


def apply_xforms_to_chain(arm, chain, records):
    applied = {}
    for name, record in zip(chain, records):
        pb = arm.pose.bones[name]
        desired = object_matrix_from_xform(pb, record)
        pb.matrix_basis = matrix_basis_from_object_matrix(pb, desired)
        bpy.context.view_layer.update()
        applied[name] = {
            "desired_head": list(record.location),
            "actual_head": list(pb.head),
            "actual_matrix_translation": list(pb.matrix.translation),
        }
    return applied


def solve_chain(arm, chain, axis_id, target_name, helper_dir_name, helper_a_name, helper_b_name, snapshot):
    records = [pose_xform(arm, name) for name in chain]
    before = {name: list(records[i].location) for i, name in enumerate(chain)}
    target = snapshot[target_name]
    ok = solve_weapon_ik_chain(
        records,
        axis_id,
        target,
        helper_dir=snapshot[helper_dir_name].location,
        helper_a=snapshot[helper_a_name].location,
        helper_b=snapshot[helper_b_name].location,
        blend=1.0,
    )
    applied = apply_xforms_to_chain(arm, chain, records) if ok else {}
    after = {name: list(arm.pose.bones[name].head) for name in chain}
    return {
        "ok": ok,
        "target": list(target.location),
        "before": before,
        "solver_records_after": {name: list(records[i].location) for i, name in enumerate(chain)},
        "applied": applied,
        "after": after,
    }


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    ensure_clean_actions(arm)
    removed = remove_preview_constraints_and_reset_basis(arm)

    helper_names = [
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightForeArmDirectionOrigin",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
        "LeftForeArmDirectionOrigin",
    ]
    snapshot = {name: pose_xform(arm, name) for name in helper_names}

    primary = solve_chain(
        arm,
        PRIMARY_CHAIN,
        3,
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightHandOrigin",
        "RightForeArmDirectionOrigin",
        snapshot,
    )
    secondary = solve_chain(
        arm,
        SECONDARY_CHAIN,
        0,
        "LeftHandIKTarget",
        "LeftForeArmDirection",
        "LeftHandOrigin",
        "LeftForeArmDirectionOrigin",
        snapshot,
    )

    arm["dayz_weaponik_mode"] = "DayZ Local Adapter Preview"
    data = {
        "mode": arm["dayz_weaponik_mode"],
        "frame": bpy.context.scene.frame_current,
        "removed": removed,
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
        "helper_snapshot": {name: list(x.location) for name, x in snapshot.items()},
        "primary": primary,
        "secondary": secondary,
        "evidence": {
            "primary_chain": PRIMARY_CHAIN,
            "secondary_chain": SECONDARY_CHAIN,
            "chainaxis": "-x",
            "secchainaxis": "+x",
            "basis_formula": "pose = parent_pose * parent_rest^-1 * bone_rest * matrix_basis",
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
