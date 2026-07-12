import json
import os
import sys

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ADDON_ROOT = r"P:\BlenderAnimtool"
OUT = os.path.join(ROOT, "anm", "dayz-weaponik-anm-runtime-cache-diagnostic.json")
ARMATURE_NAME = "_DayZ_Character"
FULL_BODY_ACTION = "p_rfl_erc_idle_ras"
HELPER_ACTION = "aks74u_helpers_only"

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


def ensure_actions(arm):
    if arm.animation_data is None:
        arm.animation_data_create()

    helper = bpy.data.actions.get(HELPER_ACTION)
    if helper is None:
        raise RuntimeError(f"Missing helper action {HELPER_ACTION!r}; import the weapon .anm first")

    full = bpy.data.actions.get(FULL_BODY_ACTION)
    if full is None:
        raise RuntimeError(f"Missing full-body action {FULL_BODY_ACTION!r}")

    arm.animation_data.action = helper
    has_full_strip = False
    for track in arm.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.action == full:
                has_full_strip = True
                track.mute = False
                strip.mute = False
                strip.influence = 1.0
                strip.blend_type = "REPLACE"
            elif strip.action != helper:
                track.mute = True

    if not has_full_strip:
        track = arm.animation_data.nla_tracks.new()
        track.name = FULL_BODY_ACTION
        strip = track.strips.new(FULL_BODY_ACTION, int(full.frame_range[0]), full)
        strip.influence = 1.0
        strip.blend_type = "REPLACE"

    for pb in arm.pose.bones:
        for constraint in list(pb.constraints):
            if constraint.name.startswith("DayZ WIK Control") or constraint.name == "DayZ WeaponIK Preview":
                pb.constraints.remove(constraint)
        pb.matrix_basis.identity()

    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()


def pose_xform(arm, name):
    pb = arm.pose.bones[name]
    return IkXform(pb.matrix.to_quaternion().normalized(), Vector(pb.head))


def anm_local_matrix(arm, bone_name):
    """Mirror DayzAnimationToolsBinary ExportAnm IK relative-space rules.

    This is intentionally different from the TXA importer/exporter path.
    The live source is imported .anm, so the cached runtime vectors must be
    read back in ANM-space before emulating DayZDiag case 0x0c.
    """
    pb = arm.pose.bones[bone_name]

    if bone_name in ("LeftHandOrigin", "LeftHandIKTarget"):
        parent = arm.pose.bones["RightHand_Dummy"].matrix
        return MTX_FIX @ parent.inverted() @ pb.matrix @ MTX_FIX.inverted()

    if bone_name == "RightHandOrigin":
        parent = arm.pose.bones["RightHand"].matrix
        tail = Matrix.Translation((0, pb.length, 0))
        return MTX_FIX @ parent.inverted() @ (pb.matrix @ tail.inverted()) @ MTX_FIX.inverted()

    if bone_name == "LeftForeArmDirection":
        parent = arm.pose.bones["LeftHand"].matrix
        tail = Matrix.Translation((0, arm.pose.bones["LeftHand"].length, 0))
        return MTX_FIX @ parent.inverted() @ (pb.matrix @ tail.inverted()) @ MTX_FIX.inverted()

    if bone_name == "RightForeArmDirection":
        parent = arm.pose.bones["RightHand"].matrix
        return MTX_FIX @ parent.inverted() @ pb.matrix @ MTX_FIX.inverted()

    if bone_name == "LeftForeArmDirectionOrigin":
        parent = arm.pose.bones["LeftHand"].matrix
        return MTX_FIX @ parent.inverted() @ pb.matrix @ MTX_FIX.inverted()

    if bone_name == "RightForeArmDirectionOrigin":
        parent = arm.pose.bones["RightHand"].matrix
        return MTX_FIX @ parent.inverted() @ pb.matrix @ MTX_FIX.inverted()

    if bone_name == "RightHand_Dummy":
        parent = arm.pose.bones["RightHand"].matrix
        return MTX_FIX @ parent.inverted() @ pb.matrix @ MTX_FIX.inverted()

    if pb.parent is not None:
        return (pb.parent.matrix @ MTX_FIX.inverted()).inverted() @ (pb.matrix @ MTX_FIX.inverted())
    return pb.matrix @ MTX_FIX.inverted()


def anm_cached_xform(arm, bone_name):
    local = anm_local_matrix(arm, bone_name)
    loc = Vector(local.translation)
    if bone_name == "RightHandOrigin":
        # ExportAnm stores RightHandOrigin translation negated.
        loc = -loc
    q = local.to_quaternion().normalized()
    # ExportAnm writes rotation keys as (-x, -y, -z, w). DayZDiag receives
    # that raw ANM quaternion, so mirror the exporter handedness here.
    return IkXform(type(q)((q.w, -q.x, -q.y, -q.z)).normalized(), loc)


def compose(base, local):
    return IkXform(
        (base.rotation @ local.rotation).normalized(),
        base.location + rotate_vector(base.rotation, local.location),
    )


def solve_from_anm_cache(arm):
    names = [
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightForeArmDirectionOrigin",
        "RightHand_Dummy",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
        "LeftForeArmDirectionOrigin",
    ]
    cache = {name: anm_cached_xform(arm, name) for name in names}

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
    ensure_actions(arm)
    data = {
        "frame": bpy.context.scene.frame_current,
        "mode": "offline ANM-space DayZ runtime cache diagnostic; no pose applied",
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "result": solve_from_anm_cache(arm),
        "evidence": {
            "source": "DayzAnimationToolsBinary ExportAnm ANM-space IK rules plus DayZDiag case 0x0c composition",
            "note": "This is for imported .anm actions, not TXA-space helper actions.",
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
