import json
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ADDON_ROOT = r"P:\BlenderAnimtool"
OUT = os.path.join(ROOT, "anm", "dayz-weaponik-runtime-cache-diagnostic.json")
ARMATURE_NAME = "_DayZ_Character"

if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)

from DayzAnimationTools.Utils.WeaponIKSolver import IkXform, rotate_vector, solve_weapon_ik_chain


MTX_FIX = Matrix(((0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
PRIMARY_CHAIN = ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand"]
SECONDARY_CHAIN = ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"]


def vlist(v):
    return [float(v.x), float(v.y), float(v.z)]


def qlist(q):
    return [float(q.w), float(q.x), float(q.y), float(q.z)]


def ensure_pose_eval(arm):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()


def pose_xform(arm, name):
    pb = arm.pose.bones[name]
    return IkXform(pb.matrix.to_quaternion().normalized(), Vector(pb.head))


def txa_local_location(arm, bone_name):
    bone = arm.pose.bones[bone_name]
    mtx = bone.matrix @ MTX_FIX.inverted()

    if bone_name == "LeftHandOrigin":
        parent = arm.pose.bones["RightHand_Dummy"].matrix
        mtx = bone.matrix @ Matrix.Translation((0, bone.length, 0)).inverted() @ MTX_FIX.inverted()
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).translation
    elif bone_name == "LeftHandIKTarget":
        parent = arm.pose.bones["RightHand_Dummy"].matrix
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).translation
    elif bone_name == "RightHandOrigin":
        parent = arm.pose.bones["RightHand"].matrix
        mtx = bone.matrix @ Matrix.Translation((0, bone.length, 0)).inverted() @ MTX_FIX.inverted()
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).inverted().translation
    elif bone_name in ("LeftForeArmDirection", "LeftForeArmDirectionOrigin"):
        parent = arm.pose.bones["LeftHand"].matrix
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).translation
    elif bone_name in ("RightForeArmDirection", "RightForeArmDirectionOrigin"):
        parent = arm.pose.bones["RightHand"].matrix
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).translation
    elif bone_name == "RightHand_Dummy":
        parent = arm.pose.bones["RightHand"].matrix
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).translation
    elif bone.parent is None:
        vec = mtx.translation
    else:
        parent = bone.parent.matrix
        vec = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).translation
    return Vector(vec)


def txa_local_rotation(arm, bone_name):
    bone = arm.pose.bones[bone_name]
    mtx = bone.matrix @ MTX_FIX.inverted()

    if bone_name in ("LeftHandOrigin", "LeftHandIKTarget"):
        parent = arm.pose.bones["RightHand_Dummy"].matrix
        mtx = ((parent @ MTX_FIX.inverted()).inverted() @ mtx)
    elif bone_name == "RightHandOrigin":
        parent = arm.pose.bones["RightHand"].matrix
        mtx = ((parent @ MTX_FIX.inverted()).inverted() @ mtx).inverted()
    elif bone_name.startswith("LeftForeArm"):
        parent = arm.pose.bones["LeftHand"].matrix
        mtx = ((parent @ MTX_FIX.inverted()).inverted() @ mtx)
    elif bone_name.startswith("RightForeArm"):
        parent = arm.pose.bones["RightHand"].matrix
        mtx = ((parent @ MTX_FIX.inverted()).inverted() @ mtx)
    elif bone_name == "RightHand_Dummy":
        parent = arm.pose.bones["RightHand"].matrix
        mtx = ((parent @ MTX_FIX.inverted()).inverted() @ mtx)
    elif bone.parent is not None:
        parent = bone.parent.matrix
        mtx = ((parent @ MTX_FIX.inverted()).inverted() @ mtx)

    q = mtx.to_quaternion().normalized()
    # ExportTxa writes the negated quaternion. q and -q represent the same
    # rotation, so keep Blender's sign here for readable diagnostics.
    return q


def cached_xform(arm, name):
    return IkXform(txa_local_rotation(arm, name), txa_local_location(arm, name))


def compose(base, local):
    return IkXform(
        (base.rotation @ local.rotation).normalized(),
        base.location + rotate_vector(base.rotation, local.location),
    )


def solve_from_dayz_cache(arm):
    cache = {name: cached_xform(arm, name) for name in [
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightForeArmDirectionOrigin",
        "RightHand_Dummy",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
        "LeftForeArmDirectionOrigin",
    ]}

    primary_records = [pose_xform(arm, name) for name in PRIMARY_CHAIN]
    secondary_records = [pose_xform(arm, name) for name in SECONDARY_CHAIN]

    primary_target = compose(primary_records[-1], cache["RightHandOrigin"])
    primary_helper_dir = primary_target.location + rotate_vector(primary_target.rotation, cache["RightForeArmDirection"].location)
    primary_helper_a = primary_target.location + rotate_vector(primary_target.rotation, cache["RightHandOrigin"].location)
    primary_mid_b_local = cache["RightHandOrigin"].location + rotate_vector(
        cache["RightHandOrigin"].rotation,
        cache["RightForeArmDirectionOrigin"].location,
    )
    primary_helper_b = primary_target.location + rotate_vector(primary_target.rotation, primary_mid_b_local)

    primary_ok = solve_weapon_ik_chain(
        primary_records,
        3,
        primary_target,
        helper_dir=primary_helper_dir,
        helper_a=primary_helper_a,
        helper_b=primary_helper_b,
        blend=1.0,
    )

    weapon_base = compose(primary_target, cache["RightHand_Dummy"])
    secondary_target = compose(weapon_base, cache["LeftHandIKTarget"])
    secondary_helper_dir = secondary_target.location + rotate_vector(
        secondary_target.rotation,
        cache["LeftForeArmDirection"].location,
    )
    secondary_helper_a = weapon_base.location + rotate_vector(weapon_base.rotation, cache["LeftHandOrigin"].location)
    secondary_mid_b_local = cache["LeftHandOrigin"].location + rotate_vector(
        cache["LeftHandOrigin"].rotation,
        cache["LeftForeArmDirectionOrigin"].location,
    )
    secondary_helper_b = weapon_base.location + rotate_vector(weapon_base.rotation, secondary_mid_b_local)

    secondary_ok = solve_weapon_ik_chain(
        secondary_records,
        0,
        secondary_target,
        helper_dir=secondary_helper_dir,
        helper_a=secondary_helper_a,
        helper_b=secondary_helper_b,
        blend=1.0,
    )

    return {
        "cache": {name: {"location": vlist(x.location), "rotation": qlist(x.rotation)} for name, x in cache.items()},
        "primary": {
            "ok": primary_ok,
            "target": vlist(primary_target.location),
            "helpers": {
                "dir": vlist(primary_helper_dir),
                "a": vlist(primary_helper_a),
                "b": vlist(primary_helper_b),
            },
            "records": {name: vlist(primary_records[i].location) for i, name in enumerate(PRIMARY_CHAIN)},
        },
        "secondary": {
            "ok": secondary_ok,
            "target": vlist(secondary_target.location),
            "weapon_base": vlist(weapon_base.location),
            "helpers": {
                "dir": vlist(secondary_helper_dir),
                "a": vlist(secondary_helper_a),
                "b": vlist(secondary_helper_b),
            },
            "records": {name: vlist(secondary_records[i].location) for i, name in enumerate(SECONDARY_CHAIN)},
        },
    }


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    ensure_pose_eval(arm)
    data = {
        "frame": bpy.context.scene.frame_current,
        "mode": "offline DayZ runtime cache diagnostic; no pose applied",
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "result": solve_from_dayz_cache(arm),
        "evidence": {
            "primary_target": "RightHand current transform composed with cached ikpose_chainoffset / RightHandOrigin",
            "secondary_target": "primary target composed with ikpose_weaponoffset / RightHand_Dummy, then ikpose_secchainoffset / LeftHandIKTarget",
            "secondary_helpers": "matches Ghidra local_4b8 from secondary target basis and local_498/local_4a8 from weapon_base/local_588 basis",
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
