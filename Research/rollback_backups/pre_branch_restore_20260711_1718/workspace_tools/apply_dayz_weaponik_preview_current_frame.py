import json
import os
import sys

import bpy
from mathutils import Matrix


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ADDON_ROOT = r"P:\BlenderAnimtool"
OUT = os.path.join(ROOT, "anm", "blender-dayz-solver-preview-current-frame.json")
ARMATURE_NAME = "_DayZ_Character"

if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)

from DayzAnimationTools.Utils.WeaponIKSolver import IkXform, solve_weapon_ik_chain


PRIMARY_CHAIN = ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand"]
SECONDARY_CHAIN = ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"]


def pose_xform(arm, bone_name):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    m = pb.matrix.copy()
    return IkXform(m.to_quaternion().normalized(), pb.head.copy())


def pose_pos(arm, bone_name):
    return pose_xform(arm, bone_name).location


def apply_xform(arm, bone_name, xform):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    scale = pb.matrix.to_scale()
    pb.matrix = Matrix.LocRotScale(xform.location, xform.rotation, scale)


def mute_preview_constraints(arm):
    changed = []
    for pb in arm.pose.bones:
        for c in pb.constraints:
            if c.type == "IK" and c.name == "DayZ WeaponIK Preview":
                c.mute = True
                changed.append(f"{pb.name}:{c.name}")
            if c.name.startswith("DayZ WIK Control"):
                c.mute = True
                changed.append(f"{pb.name}:{c.name}")
    return changed


def reset_pose_basis(arm):
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()


def solve_chain(arm, chain, axis_id, target_bone, helper_dir, helper_a, helper_b, blend, snapshot=None):
    records = [pose_xform(arm, name) for name in chain]
    before = {name: list(records[i].location) for i, name in enumerate(chain)}
    snapshot = snapshot or {}
    target = snapshot.get(target_bone, pose_xform(arm, target_bone))
    ok = solve_weapon_ik_chain(
        records,
        axis_id,
        target,
        helper_dir=snapshot.get(helper_dir, pose_xform(arm, helper_dir)).location if helper_dir else None,
        helper_a=snapshot.get(helper_a, pose_xform(arm, helper_a)).location if helper_a else None,
        helper_b=snapshot.get(helper_b, pose_xform(arm, helper_b)).location if helper_b else None,
        blend=blend,
    )
    if ok:
        for name, xform in zip(chain, records):
            apply_xform(arm, name, xform)
    after = {name: list(pose_xform(arm, name).location) for name in chain}
    return {"ok": ok, "before": before, "after": after, "target": list(target.location)}


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.context.view_layer.update()

    muted = mute_preview_constraints(arm)
    reset_pose_basis(arm)
    bpy.context.view_layer.update()

    bpy.ops.object.mode_set(mode="POSE")

    helper_snapshot = {
        name: pose_xform(arm, name)
        for name in [
            "RightHandOrigin",
            "RightForeArmDirection",
            "RightForeArmDirectionOrigin",
            "LeftHandIKTarget",
            "LeftHandOrigin",
            "LeftForeArmDirection",
            "LeftForeArmDirectionOrigin",
        ]
        if arm.pose.bones.get(name) is not None
    }

    primary = solve_chain(
        arm,
        PRIMARY_CHAIN,
        3,  # -x, confirmed player chainaxis
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightHandOrigin",
        "RightForeArmDirectionOrigin",
        1.0,
        snapshot=helper_snapshot,
    )
    bpy.context.view_layer.update()
    secondary = solve_chain(
        arm,
        SECONDARY_CHAIN,
        0,  # +x, confirmed player secchainaxis
        "LeftHandIKTarget",
        "LeftForeArmDirection",
        "LeftHandOrigin",
        "LeftForeArmDirectionOrigin",
        1.0,
        snapshot=helper_snapshot,
    )
    bpy.context.view_layer.update()

    arm["dayz_weaponik_mode"] = "DayZDiag Solver Preview"

    data = {
        "frame": bpy.context.scene.frame_current,
        "muted_constraints": muted,
        "primary_chain": primary,
        "secondary_chain": secondary,
        "mode": arm["dayz_weaponik_mode"],
        "evidence": {
            "chain": PRIMARY_CHAIN,
            "secchain": SECONDARY_CHAIN,
            "chainaxis": "-x",
            "secchainaxis": "+x",
            "source": "DayZDiag FUN_1401093e0 remap and FUN_1400e1be0 solver model",
        },
        "note": "This applies the DayZDiag-style solver to the current Blender frame and mutes Blender IK preview constraints.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
