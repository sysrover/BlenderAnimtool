import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

from DayzAnimationTools.Tools import AddSurvivorIK
from DayzAnimationToolsBinary.Types.Anm import Anm


ARMATURE = "_DayZ_Character"
BASE_ANM = r"P:\BlenderAnimtool\examples\p_1hd_erc_idle_low.anm"
IK_ANM = os.environ.get("DAYZ_IK1H_TEST_ANM", r"P:\BlenderAnimtool\examples\ik\apple.anm")
IK_NAME = os.path.splitext(os.path.basename(IK_ANM))[0]
OUT_ANM = rf"C:\temp\dayz_ik1h_proxy_workflow\{IK_NAME}_proxy_edited.anm"
CYCLE_ANM = rf"C:\temp\dayz_ik1h_proxy_workflow\{IK_NAME}_proxy_cycle.anm"
REPORT = rf"C:\Users\sysro\diag\CsharpModVScode\anm\dayz-ik1h-proxy-{IK_NAME}.json"


def select_only(obj):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def import_anm(obj, path, translation):
    select_only(obj)
    result = bpy.ops.import_scene.anm(
        filepath=path,
        files=[{"name": os.path.basename(path)}],
        fUnitScale=1.0,
        bImportTranslationKeys=translation,
        bImportRotationKeys=True,
        bImportScaleKeys=False,
        bImportFirstTwoFramesOnly=False,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Import failed for {path}: {sorted(result)}")
    return obj.animation_data.action


def world_head(obj, bone_name):
    return obj.matrix_world @ obj.pose.bones[bone_name].head


def world_tail(obj, bone_name):
    return obj.matrix_world @ obj.pose.bones[bone_name].tail


def distance(a, b):
    return float((a - b).length)


def decoded_tracks(path):
    animation = Anm.CreateFromFile(path)
    return {
        "format": animation.format.name,
        "frames": int(animation.numFrames),
        "fps": int(animation.fps),
        "tracks": [bone.name for bone in animation.bones],
    }


def decoded_position_tracks(path):
    animation = Anm.CreateFromFile(path)
    return sorted(bone.name for bone in animation.bones if len(bone.posKeys) > 0)


def decoded_values(path):
    animation = Anm.CreateFromFile(path)
    values = {}
    for bone in animation.bones:
        values[bone.name] = {
            "position": {
                int(key.frame): [float(x * bone.posMulti + bone.posBias) for x in key.data]
                for key in bone.posKeys
            },
            "rotation": {
                int(key.frame): [float(x * bone.rotMulti + bone.rotBias) for x in key.data]
                for key in bone.rotKeys
            },
        }
    return values


def held(keys, frame, identity):
    candidates = [key for key in keys if key <= frame]
    return keys[max(candidates)] if candidates else identity


def compare_values(left, right):
    maximum = 0.0
    worst = None
    missing = sorted(set(left) - set(right))
    for name in sorted(set(left).intersection(right)):
        for channel, identity in (("position", [0.0, 0.0, 0.0]), ("rotation", [0.0, 0.0, 0.0, 1.0])):
            for frame in (0, 1):
                a = held(left[name][channel], frame, identity)
                b = held(right[name][channel], frame, identity)
                if channel == "rotation":
                    error = min(
                        max(abs(a[i] - b[i]) for i in range(4)),
                        max(abs(a[i] + b[i]) for i in range(4)),
                    )
                else:
                    error = max(abs(a[i] - b[i]) for i in range(3))
                if error > maximum:
                    maximum = error
                    worst = {"track": name, "channel": channel, "frame": frame, "error": error}
    return {"max_error": maximum, "worst": worst, "missing": missing}


def main():
    arm = bpy.data.objects.get(ARMATURE)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature {ARMATURE}")
    if arm.animation_data is None:
        arm.animation_data_create()
    for track in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(track)
    arm.animation_data.action = None

    base_action = import_anm(arm, BASE_ANM, translation=False)
    ik_action = import_anm(arm, IK_ANM, translation=True)
    if ik_action.get("dayz_weaponik_base_action") != base_action.name:
        raise RuntimeError("IK import did not remember the active base action")

    scene = bpy.context.scene
    scene.frame_set(1)
    raw_pose_before_controls = {
        name: world_head(arm, name).copy()
        for name in ("RightArm", "RightForeArm", "RightHand")
    }
    error = AddSurvivorIK.bake_current_anm_to_dayz_arm_controls(arm)
    if error:
        raise RuntimeError(error)
    rig = bpy.data.objects.get(AddSurvivorIK.FK_CONTROL_RIG_NAME)
    if rig is None:
        raise RuntimeError("Control rig was not created")
    rig_name = rig.name

    required = {
        "CTRL_RightHand",
        "CTRL_RightElbow",
        AddSurvivorIK.RIGHT_PROXY_BONES["arm"],
        AddSurvivorIK.RIGHT_PROXY_BONES["forearm"],
        AddSurvivorIK.RIGHT_PROXY_BONES["hand"],
    }
    missing = sorted(required - set(rig.pose.bones.keys()))
    if missing:
        raise RuntimeError("Missing controls/proxy bones: " + ", ".join(missing))

    hand_ctrl = rig.pose.bones["CTRL_RightHand"]
    elbow_ctrl = rig.pose.bones["CTRL_RightElbow"]
    proxy_arm = AddSurvivorIK.RIGHT_PROXY_BONES["arm"]
    proxy_fore = AddSurvivorIK.RIGHT_PROXY_BONES["forearm"]
    proxy_hand = AddSurvivorIK.RIGHT_PROXY_BONES["hand"]
    bpy.context.view_layer.update()

    default_pose_error = max(
        distance(world_head(arm, name), raw_pose_before_controls[name])
        for name in raw_pose_before_controls
    )

    base = {
        "target": world_head(rig, "CTRL_RightHand"),
        "wrist": world_tail(rig, proxy_fore),
        "dayz_hand": world_head(arm, "RightHand"),
        "elbow": world_head(rig, proxy_fore),
        "upper_len": distance(world_head(rig, proxy_arm), world_tail(rig, proxy_arm)),
        "lower_len": distance(world_head(rig, proxy_fore), world_tail(rig, proxy_fore)),
        "hand_rot": (rig.matrix_world @ rig.pose.bones[proxy_hand].matrix).to_quaternion(),
        "dayz_hand_rot": (arm.matrix_world @ arm.pose.bones["RightHand"].matrix).to_quaternion(),
        "arm_roll_rot": (arm.matrix_world @ arm.pose.bones["RightArmRoll"].matrix).to_quaternion(),
        "forearm_roll_rot": (arm.matrix_world @ arm.pose.bones["RightForeArmRoll"].matrix).to_quaternion(),
        "arm_roll_scale": (arm.matrix_world @ arm.pose.bones["RightArmRoll"].matrix).to_scale(),
        "forearm_roll_scale": (arm.matrix_world @ arm.pose.bones["RightForeArmRoll"].matrix).to_scale(),
    }

    hand_ctrl.location.x += 0.03
    bpy.context.view_layer.update()
    hand_move = {
        "control_delta": distance(world_head(rig, "CTRL_RightHand"), base["target"]),
        "proxy_wrist_delta": distance(world_tail(rig, proxy_fore), base["wrist"]),
        "dayz_hand_delta": distance(world_head(arm, "RightHand"), base["dayz_hand"]),
        "target_error": distance(world_tail(rig, proxy_fore), world_head(rig, "CTRL_RightHand")),
        "upper_length_error": abs(distance(world_head(rig, proxy_arm), world_tail(rig, proxy_arm)) - base["upper_len"]),
        "lower_length_error": abs(distance(world_head(rig, proxy_fore), world_tail(rig, proxy_fore)) - base["lower_len"]),
        "arm_roll_angle": float(base["arm_roll_rot"].rotation_difference(
            (arm.matrix_world @ arm.pose.bones["RightArmRoll"].matrix).to_quaternion()
        ).angle),
        "forearm_roll_angle": float(base["forearm_roll_rot"].rotation_difference(
            (arm.matrix_world @ arm.pose.bones["RightForeArmRoll"].matrix).to_quaternion()
        ).angle),
        "arm_roll_scale_error": distance(
            base["arm_roll_scale"],
            (arm.matrix_world @ arm.pose.bones["RightArmRoll"].matrix).to_scale(),
        ),
        "forearm_roll_scale_error": distance(
            base["forearm_roll_scale"],
            (arm.matrix_world @ arm.pose.bones["RightForeArmRoll"].matrix).to_scale(),
        ),
    }
    hand_ctrl.location.x -= 0.03
    bpy.context.view_layer.update()

    wrist_before_elbow = world_tail(rig, proxy_fore)
    target_before_elbow = world_head(rig, "CTRL_RightHand")
    elbow_before = world_head(rig, proxy_fore)
    elbow_ctrl.location.z += 0.10
    bpy.context.view_layer.update()
    elbow_move = {
        "proxy_elbow_delta": distance(world_head(rig, proxy_fore), elbow_before),
        "proxy_wrist_delta": distance(world_tail(rig, proxy_fore), wrist_before_elbow),
        "control_target_delta": distance(world_head(rig, "CTRL_RightHand"), target_before_elbow),
        "target_error": distance(world_tail(rig, proxy_fore), world_head(rig, "CTRL_RightHand")),
    }
    elbow_ctrl.location.z -= 0.10
    bpy.context.view_layer.update()

    wrist_before_rotation = world_tail(rig, proxy_fore)
    hand_ctrl.rotation_mode = "QUATERNION"
    old_rotation = hand_ctrl.rotation_quaternion.copy()
    hand_ctrl.rotation_quaternion = Quaternion((0.0, 1.0, 0.0), math.radians(15.0)) @ old_rotation
    bpy.context.view_layer.update()
    rotated = (rig.matrix_world @ rig.pose.bones[proxy_hand].matrix).to_quaternion()
    dayz_rotated = (arm.matrix_world @ arm.pose.bones["RightHand"].matrix).to_quaternion()
    wrist_rotation = {
        "proxy_hand_angle": float(base["hand_rot"].rotation_difference(rotated).angle),
        "dayz_hand_angle": float(base["dayz_hand_rot"].rotation_difference(dayz_rotated).angle),
        "proxy_to_dayz_angle_error": float(rotated.rotation_difference(dayz_rotated).angle),
        "proxy_wrist_delta": distance(world_tail(rig, proxy_fore), wrist_before_rotation),
    }

    # Deliberately leave the control edit unkeyed. Bake must commit the visible
    # pose before its frame sampling instead of resetting it to older keys.
    visible_control_rotation = hand_ctrl.rotation_quaternion.copy()
    visible_dayz_rotation = (arm.matrix_world @ arm.pose.bones["RightHand"].matrix).to_quaternion()

    bake_error = AddSurvivorIK.bake_dayz_ik1h_controls_to_helpers(arm)
    if bake_error:
        raise RuntimeError(bake_error)
    wrist_rotation["bake_control_reset_error"] = float(
        visible_control_rotation.rotation_difference(hand_ctrl.rotation_quaternion).angle
    )
    wrist_rotation["bake_dayz_reset_error"] = float(
        visible_dayz_rotation.rotation_difference(
            (arm.matrix_world @ arm.pose.bones["RightHand"].matrix).to_quaternion()
        ).angle
    )
    baked_action_name = arm.get("dayz_ik1h_controls_baked_action")
    required_helper_names = {
        "RightHandOrigin", "RightForeArmDirection",
        "RightForeArmDirectionOrigin", "RightHand_Dummy",
    }
    helper_bake_keys = {}
    for helper_name in sorted(required_helper_names):
        channel_frames = {}
        prefix = f'pose.bones["{helper_name}"].'
        for curve in arm.animation_data.action.fcurves:
            if curve.data_path.startswith(prefix):
                channel_frames.setdefault(curve.data_path[len(prefix):], set()).update(
                    int(round(point.co.x)) for point in curve.keyframe_points
                )
        helper_bake_keys[helper_name] = {
            channel: sorted(frames) for channel, frames in channel_frames.items()
        }
    helpers_have_two_frame_tr = all(
        helper_bake_keys[name].get("location") == [0, 1]
        and helper_bake_keys[name].get("rotation_quaternion") == [0, 1]
        for name in required_helper_names
    )

    os.makedirs(os.path.dirname(OUT_ANM), exist_ok=True)
    select_only(arm)
    result = bpy.ops.export_scene.anm(
        filepath=OUT_ANM,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=30,
        eAnimType="IK1H",
        bSaveAll=False,
        bPreserveImportedRawAnm=False,
        fUnitScale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Export failed: {sorted(result)}")
    export = decoded_tracks(OUT_ANM)
    position_tracks = decoded_position_tracks(OUT_ANM)
    # Corpus ground truth: every track present in an IK1H ANM has a position
    # channel. The whitelist already excludes non-IK skeleton bones.
    required_position_tracks = set(export["tracks"])
    unexpected_position_tracks = sorted(set(position_tracks) - required_position_tracks)
    missing_position_tracks = sorted(required_position_tracks - set(position_tracks))

    # Numeric re-import/re-export cycle.  Remove authoring constraints so the
    # second export proves the serialized helper data itself is stable.
    for pose_bone in arm.pose.bones:
        for constraint in list(pose_bone.constraints):
            if constraint.name.startswith((
                AddSurvivorIK.FK_CONSTRAINT_PREFIX,
                AddSurvivorIK.IK_CONSTRAINT_PREFIX,
                AddSurvivorIK.IK_PREVIEW_CONSTRAINT_PREFIX,
            )):
                pose_bone.constraints.remove(constraint)
    bpy.data.objects.remove(rig, do_unlink=True)
    for track in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(track)
    arm.animation_data.action = base_action
    cycle_action = import_anm(arm, OUT_ANM, translation=True)
    cycle_action["dayz_binary_anm_raw_preserve"] = False
    scene.frame_set(0)
    bpy.context.view_layer.update()
    parsed_cycle_source = Anm.CreateFromFile(OUT_ANM)
    raw_origin = next(bone for bone in parsed_cycle_source.bones if bone.name == "RightHandOrigin")
    raw_rot_key = raw_origin.rotKeys[0]
    raw_rot_values = [float(x * raw_origin.rotMulti + raw_origin.rotBias) for x in raw_rot_key.data]
    raw_pos_key = raw_origin.posKeys[0]
    raw_pos_values = Vector(float(x * raw_origin.posMulti + raw_origin.posBias) for x in raw_pos_key.data)
    imported_rot = Quaternion((-raw_rot_values[3], raw_rot_values[0], raw_rot_values[1], raw_rot_values[2])).normalized()
    mtx_fix = Matrix(((0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    expected_rel_rotation = imported_rot.inverted().to_matrix().to_4x4()
    expected_object = (
        arm.pose.bones["RightHand"].matrix
        @ mtx_fix.inverted()
        @ expected_rel_rotation
        @ Matrix.Translation(-raw_pos_values)
        @ mtx_fix
        @ Matrix.Translation((0, arm.pose.bones["RightHandOrigin"].length, 0))
    )
    expected_object_rotation = expected_object.to_quaternion()
    actual_object_rotation = arm.pose.bones["RightHandOrigin"].matrix.to_quaternion()
    helper = arm.pose.bones["RightHandOrigin"]
    saved_basis = helper.matrix_basis.copy()
    helper.matrix = expected_object
    bpy.context.view_layer.update()
    setter_basis_rotation = helper.matrix_basis.to_quaternion()
    helper.matrix_basis = saved_basis
    bpy.context.view_layer.update()
    keyed_components = []
    for axis in range(4):
        curve = next(curve for curve in cycle_action.fcurves if curve.data_path == 'pose.bones["RightHandOrigin"].rotation_quaternion' and curve.array_index == axis)
        keyed_components.append(curve.evaluate(0))
    keyed_basis_rotation = Quaternion(keyed_components)
    from DayzAnimationToolsBinary.Export.ExportAnm import GetBoneRotation
    sampled_rotation = GetBoneRotation(arm.pose.bones["RightHandOrigin"], "IK1H")
    cycle_debug = {
        "import_object_rotation_error": float(expected_object_rotation.rotation_difference(actual_object_rotation).angle),
        "raw_to_export_rotation_error": float(imported_rot.rotation_difference(sampled_rotation).angle),
        "setter_to_keyed_basis_error": float(setter_basis_rotation.rotation_difference(keyed_basis_rotation).angle),
        "imported_raw_quaternion_wxyz": list(imported_rot),
        "sampled_quaternion_wxyz": list(sampled_rotation),
    }
    select_only(arm)
    result = bpy.ops.export_scene.anm(
        filepath=CYCLE_ANM,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=30,
        eAnimType="IK1H",
        bSaveAll=False,
        bPreserveImportedRawAnm=False,
        fUnitScale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Cycle export failed: {sorted(result)}")
    roundtrip = compare_values(decoded_values(OUT_ANM), decoded_values(CYCLE_ANM))

    allowed = {
        "RightHand", "RightHand_Dummy", "RightHandOrigin",
        "RightForeArmDirection", "RightForeArmDirectionOrigin",
    }
    allowed.update(name for name in export["tracks"] if name.startswith("RightHand"))
    left_tracks = [name for name in export["tracks"] if name.startswith("Left")]
    report = {
        "base_action": base_action.name,
        "ik_action": ik_action.name,
        "remembered_base": ik_action.get("dayz_weaponik_base_action"),
        "preview_backend": arm.get("dayz_weaponik_preview_backend"),
        "control_rig": rig_name,
        "missing_controls": missing,
        "default_pose_error": default_pose_error,
        "hand_move": hand_move,
        "elbow_move": elbow_move,
        "wrist_rotation": wrist_rotation,
        "baked_action": baked_action_name,
        "helper_bake_keys": helper_bake_keys,
        "helpers_have_two_frame_tr": helpers_have_two_frame_tr,
        "helper_constraints": {
            name: [constraint.name for constraint in arm.pose.bones[name].constraints]
            for name in ("RightHandOrigin", "RightForeArmDirection", "RightForeArmDirectionOrigin", "RightHand_Dummy")
        },
        "export": export,
        "position_tracks": position_tracks,
        "unexpected_position_tracks": unexpected_position_tracks,
        "missing_position_tracks": missing_position_tracks,
        "roundtrip": roundtrip,
        "cycle_debug": cycle_debug,
        "left_tracks": left_tracks,
        "output_anm": OUT_ANM,
        "pass": (
            hand_move["proxy_wrist_delta"] > 0.005
            and default_pose_error < 1.0e-4
            and hand_move["dayz_hand_delta"] > 0.005
            and hand_move["target_error"] < 0.001
            and hand_move["upper_length_error"] < 1.0e-5
            and hand_move["lower_length_error"] < 1.0e-5
            and hand_move["arm_roll_angle"] > 1.0e-4
            and hand_move["forearm_roll_angle"] > 1.0e-4
            and hand_move["arm_roll_scale_error"] < 1.0e-5
            and hand_move["forearm_roll_scale_error"] < 1.0e-5
            and elbow_move["proxy_elbow_delta"] > 0.001
            and elbow_move["proxy_wrist_delta"] < 0.001
            and elbow_move["control_target_delta"] < 1.0e-6
            and wrist_rotation["proxy_hand_angle"] > math.radians(5.0)
            and wrist_rotation["dayz_hand_angle"] > math.radians(5.0)
            and wrist_rotation["proxy_to_dayz_angle_error"] < 1.0e-4
            and wrist_rotation["proxy_wrist_delta"] < 0.001
            and wrist_rotation["bake_control_reset_error"] < 1.0e-4
            and wrist_rotation["bake_dayz_reset_error"] < 1.0e-4
            and baked_action_name == ik_action.name
            and helpers_have_two_frame_tr
            and not left_tracks
            and not unexpected_position_tracks
            and not missing_position_tracks
            and not roundtrip["missing"]
            and roundtrip["max_error"] < 5.0e-4
        ),
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, default=lambda value: list(value))
    print("IK1H_PROXY_RESULT " + json.dumps({"pass": report["pass"], "report": REPORT, "output": OUT_ANM}))


main()
