import json
import os
import re

import bpy
from mathutils import Matrix, Vector

from DayzAnimationTools.Tools import AddSurvivorIK as IK
from DayzAnimationToolsBinary.Types.Anm import Anm


ARMATURE = "_DayZ_Character"
BASE = r"P:\DZ\anims\anm\player\moves\1handed\p_1hd_erc_idle_low.anm"
TOY = r"P:\UARP_Items_2\Anm\toy_ik.anm"
OUT = r"C:\temp\dayz_ik1h_proxy_workflow\toy_ik_lift_baked.anm"
CYCLE = r"C:\temp\dayz_ik1h_proxy_workflow\toy_ik_lift_cycle.anm"
BLEND = r"C:\temp\dayz_ik1h_proxy_workflow\toy_ik_lift_reimported.blend"
REPORT = r"P:\BlenderAnimtool\Research\anm_reports\toy-ik-lift-bake-roundtrip-20260711.json"
LIFT = Vector((0.0, 0.0, 0.06))


def select_only(obj):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def import_anm(obj, path, translation, first_two):
    select_only(obj)
    result = bpy.ops.import_scene.anm(
        filepath=path,
        files=[{"name": os.path.basename(path)}],
        fUnitScale=1.0,
        bImportTranslationKeys=translation,
        bImportRotationKeys=True,
        bImportScaleKeys=False,
        bImportFirstTwoFramesOnly=first_two,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Import failed: {path}: {sorted(result)}")
    return obj.animation_data.action


def export_anm(obj, path):
    select_only(obj)
    result = bpy.ops.export_scene.anm(
        filepath=path,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=30,
        eAnimType="IK1H",
        bSaveAll=False,
        fUnitScale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Export failed: {path}: {sorted(result)}")


def world_head(obj, name):
    return obj.matrix_world @ obj.pose.bones[name].head


def world_matrix(obj, name):
    return obj.matrix_world @ obj.pose.bones[name].matrix


def matrix_error(left, right):
    location = (left.to_translation() - right.to_translation()).length
    rotation = left.to_quaternion().rotation_difference(right.to_quaternion()).angle
    scale = (left.to_scale() - right.to_scale()).length
    return {"location": float(location), "rotation": float(rotation), "scale": float(scale)}


def flat_matrix(matrix):
    return [float(matrix[row][column]) for row in range(4) for column in range(4)]


def decoded(path):
    animation = Anm.CreateFromFile(path)
    return {
        bone.name: {
            "pos": {int(key.frame): [float(v * bone.posMulti + bone.posBias) for v in key.data] for key in bone.posKeys},
            "rot": {int(key.frame): [float(v * bone.rotMulti + bone.rotBias) for v in key.data] for key in bone.rotKeys},
        }
        for bone in animation.bones
    }


def held(values, frame, identity):
    frames = [key for key in values if key <= frame]
    return values[max(frames)] if frames else identity


def decoded_error(left, right):
    maximum = 0.0
    worst = None
    missing = sorted(set(left) - set(right))
    extra = sorted(set(right) - set(left))
    for name in sorted(set(left).intersection(right)):
        for channel, identity in (("pos", [0.0, 0.0, 0.0]), ("rot", [0.0, 0.0, 0.0, 1.0])):
            for frame in (0, 1):
                a = held(left[name][channel], frame, identity)
                b = held(right[name][channel], frame, identity)
                if channel == "rot":
                    error = min(
                        max(abs(a[i] - b[i]) for i in range(4)),
                        max(abs(a[i] + b[i]) for i in range(4)),
                    )
                else:
                    error = max(abs(a[i] - b[i]) for i in range(3))
                if error > maximum:
                    maximum = error
                    worst = {"track": name, "channel": channel, "frame": frame, "error": error}
    return {"max_error": maximum, "worst": worst, "missing": missing, "extra": extra}


def clear_authoring(arm):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    IK._remove_old_fk_controls(arm)
    if arm.animation_data:
        arm.animation_data.action = None
        for track in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(track)
        arm.animation_data_clear()
    for key in list(bpy.context.scene.keys()):
        if str(key).startswith("dayz_"):
            del bpy.context.scene[key]
    for key in list(arm.keys()):
        if str(key).startswith("dayz_"):
            del arm[key]
    for pose_bone in arm.pose.bones:
        pose_bone.matrix_basis = Matrix.Identity(4)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()


def helper_key_frames(action):
    names = {
        "RightHandOrigin", "RightForeArmDirection",
        "RightForeArmDirectionOrigin", "RightHand_Dummy",
    }
    result = {name: {} for name in names}
    for curve in action.fcurves:
        match = re.match(r'pose\.bones\["([^"]+)"\]\.(.+)', curve.data_path)
        if not match or match.group(1) not in names:
            continue
        result[match.group(1)].setdefault(match.group(2), set()).update(
            int(round(point.co.x)) for point in curve.keyframe_points
        )
    return {name: {channel: sorted(frames) for channel, frames in channels.items()} for name, channels in result.items()}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    arm = bpy.data.objects.get(ARMATURE)
    if arm is None:
        raise RuntimeError(f"Missing {ARMATURE}")
    clear_authoring(arm)

    base = import_anm(arm, BASE, translation=False, first_two=False)
    toy = import_anm(arm, TOY, translation=True, first_two=True)
    bpy.context.scene.frame_set(0)
    raw_initial_hand = world_matrix(arm, "RightHand").copy()
    build_error = IK.bake_current_anm_to_dayz_arm_controls(arm)
    if build_error:
        raise RuntimeError(build_error)
    rig = bpy.data.objects[IK.FK_CONTROL_RIG_NAME]
    hand_control = rig.pose.bones["CTRL_RightHand"]
    dummy_control = rig.pose.bones[IK.IK_EXPORT_CONTROLS["RightHand_Dummy"]]
    dummy_control_visible_after_build = not dummy_control.bone.hide

    before_lift = world_head(arm, "RightHand").copy()
    control_before = world_head(rig, "CTRL_RightHand").copy()
    lifted_control_matrix = hand_control.matrix.copy()
    lifted_control_matrix.translation += LIFT
    hand_control.matrix = lifted_control_matrix
    # Leave a weapon-dummy rotation deliberately unkeyed. Bake must commit this
    # visible control just like the hand and elbow controls before frame_set().
    dummy_edited_matrix = dummy_control.matrix.copy()
    dummy_edited_matrix @= Matrix.Rotation(0.2, 4, "X")
    dummy_control.matrix = dummy_edited_matrix
    # Direct finger edits are also commonly left unkeyed before pressing Bake.
    index_control = arm.pose.bones["RightHandIndex1"]
    index_edited_matrix = index_control.matrix.copy()
    index_edited_matrix @= Matrix.Rotation(0.12, 4, "X")
    index_control.matrix = index_edited_matrix
    bpy.context.view_layer.update()
    # Explicit sync makes the test independent of depsgraph handler scheduling.
    IK._sync_dayz_arm_from_proxy(arm, rig)
    bpy.context.view_layer.update()

    lifted_control = world_head(rig, "CTRL_RightHand").copy()
    lifted_control_world = rig.matrix_world @ hand_control.matrix.copy()
    lifted_hand = world_head(arm, "RightHand").copy()
    expected = {
        name: world_matrix(arm, name).copy()
        for name in (
            "RightHand", "RightHandOrigin", "RightForeArmDirection",
            "RightForeArmDirectionOrigin", "RightHand_Dummy",
            "RightHandIndex1", "RightHandIndex2", "RightHandIndex3",
        )
    }

    bake_error = IK.bake_dayz_ik1h_controls_to_helpers(arm)
    if bake_error:
        raise RuntimeError(bake_error)
    after_bake = {name: world_matrix(arm, name).copy() for name in expected}
    dummy_bake_error = matrix_error(expected["RightHand_Dummy"], after_bake["RightHand_Dummy"])
    encoded_target_after_bake = IK._right_hand_target_world_from_imported_origin(arm)
    encoded_target_after_bake_error = float(
        (encoded_target_after_bake.to_translation() - lifted_control).length
    )
    IK._restore_dayz_proxy_base_pose(arm)
    encoded_base_hand_matrix = world_matrix(arm, "RightHand").copy()
    encoded_base_origin_matrix = world_matrix(arm, "RightHandOrigin").copy()
    encoded_target_in_base = IK._right_hand_target_world_from_imported_origin(arm)
    encoded_target_in_base_error = float(
        (encoded_target_in_base.to_translation() - lifted_control).length
    )
    IK._sync_dayz_arm_from_proxy(arm, rig)
    bpy.context.view_layer.update()
    visible_names = {"RightHand", "RightHandIndex1", "RightHandIndex2", "RightHandIndex3"}
    bake_pose_errors = {name: matrix_error(expected[name], after_bake[name]) for name in visible_names}
    baked_action = arm.animation_data.action
    baked_helper_keys = helper_key_frames(baked_action)

    export_anm(arm, OUT)
    first_values = decoded(OUT)
    first_tracks = sorted(first_values)
    first_position_tracks = sorted(name for name, data in first_values.items() if data["pos"])
    # Import/reimport symmetry alone can hide an inverse-basis bug. DayZ consumes
    # RightHandOrigin after inverting it in the IK-pose cache loader:
    # target = currentEnd * axisFix^-1 * inverse(rawOffset) * axisFix.
    axis_fix = Matrix(((0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    decode_hand_values = arm.get(IK._proxy_decode_key(0, "RightHand"))
    decode_hand_matrix = IK._matrix_from_flat(decode_hand_values)
    expected_runtime_inverse = (
        axis_fix
        @ decode_hand_matrix.inverted()
        @ (arm.matrix_world.inverted() @ lifted_control_world)
        @ axis_fix.inverted()
    )
    expected_runtime_rel = expected_runtime_inverse.inverted()
    actual_runtime_pos = held(first_values["RightHandOrigin"]["pos"], 0, [0.0, 0.0, 0.0])
    actual_runtime_rot = held(first_values["RightHandOrigin"]["rot"], 0, [0.0, 0.0, 0.0, 1.0])
    expected_runtime_q = expected_runtime_rel.to_quaternion()
    expected_runtime_rot = [
        -expected_runtime_q.x,
        -expected_runtime_q.y,
        -expected_runtime_q.z,
        expected_runtime_q.w,
    ]
    runtime_position_error = max(
        abs(actual_runtime_pos[index] - expected_runtime_rel.translation[index])
        for index in range(3)
    )
    runtime_rotation_error = min(
        max(abs(actual_runtime_rot[index] - expected_runtime_rot[index]) for index in range(4)),
        max(abs(actual_runtime_rot[index] + expected_runtime_rot[index]) for index in range(4)),
    )

    clear_authoring(arm)
    re_base = import_anm(arm, BASE, translation=False, first_two=False)
    re_toy = import_anm(arm, OUT, translation=True, first_two=True)
    bpy.context.scene.frame_set(0)
    raw_reimport = {name: world_matrix(arm, name).copy() for name in expected}
    reimport_base_hand_matrix = raw_reimport["RightHand"].copy()
    reimport_base_origin_matrix = raw_reimport["RightHandOrigin"].copy()
    raw_hand_cycle_error = matrix_error(raw_initial_hand, raw_reimport["RightHand"])
    decoded_target_before_rebuild = IK._right_hand_target_world_from_imported_origin(arm)
    decoded_target_before_rebuild_error = float(
        (decoded_target_before_rebuild.to_translation() - lifted_control).length
    )
    capture_before_rebuild_error = IK._capture_dayz_proxy_base_pose(arm)
    if capture_before_rebuild_error:
        raise RuntimeError(capture_before_rebuild_error)
    if not IK._restore_dayz_proxy_base_pose(arm):
        raise RuntimeError("Could not restore proxy base before rebuild diagnostic")
    decoded_target_in_base_before_rebuild = IK._right_hand_target_world_from_imported_origin(arm)
    decoded_target_in_base_before_rebuild_error = float(
        (decoded_target_in_base_before_rebuild.to_translation() - lifted_control).length
    )
    rebuild_error = IK.bake_current_anm_to_dayz_arm_controls(arm)
    if rebuild_error:
        raise RuntimeError(rebuild_error)
    re_rig = bpy.data.objects[IK.FK_CONTROL_RIG_NAME]
    rebuilt = {name: world_matrix(arm, name).copy() for name in expected}

    # Helper matrices are intentionally re-encoded during Bake. Compare the
    # reimport against the baked matrices, while comparing visible hand/fingers
    # against the pre-Bake edited pose.
    raw_reimport_errors = {
        name: matrix_error(
            expected[name] if name in visible_names else after_bake[name],
            raw_reimport[name],
        )
        for name in expected
    }
    rebuilt_errors = {
        name: matrix_error(
            expected[name] if name in visible_names else after_bake[name],
            rebuilt[name],
        )
        for name in expected
    }
    reimport_control_error = float((world_head(re_rig, "CTRL_RightHand") - lifted_control).length)
    reimport_hand_error = float((world_head(arm, "RightHand") - lifted_hand).length)

    # Re-bake and re-export the reimported result for a decoded numeric cycle.
    second_bake_error = IK.bake_dayz_ik1h_controls_to_helpers(arm)
    if second_bake_error:
        raise RuntimeError(second_bake_error)
    export_anm(arm, CYCLE)
    cycle = decoded_error(first_values, decoded(CYCLE))

    bpy.ops.wm.save_as_mainfile(filepath=BLEND, check_existing=False)

    max_bake_location = max(value["location"] for value in bake_pose_errors.values())
    max_bake_rotation = max(value["rotation"] for value in bake_pose_errors.values())
    max_raw_location = max(value["location"] for value in raw_reimport_errors.values())
    max_raw_rotation = max(value["rotation"] for value in raw_reimport_errors.values())
    max_rebuilt_location = max(value["location"] for value in rebuilt_errors.values())
    max_rebuilt_rotation = max(value["rotation"] for value in rebuilt_errors.values())
    visible_names = ("RightHand", "RightHandIndex1", "RightHandIndex2", "RightHandIndex3")
    max_visible_rebuilt_location = max(rebuilt_errors[name]["location"] for name in visible_names)
    max_visible_rebuilt_rotation = max(rebuilt_errors[name]["rotation"] for name in visible_names)
    all_tracks_have_position = set(first_tracks) == set(first_position_tracks)
    helpers_two_frame = all(
        baked_helper_keys[name].get("location") == [0, 1]
        and baked_helper_keys[name].get("rotation_quaternion") == [0, 1]
        for name in baked_helper_keys
    )

    report = {
        "base": BASE,
        "toy": TOY,
        "output": OUT,
        "cycle_output": CYCLE,
        "saved_blend": BLEND,
        "remembered_base": toy.get("dayz_weaponik_base_action"),
        "dummy_control_visible_after_build": dummy_control_visible_after_build,
        "unkeyed_dummy_bake_error": dummy_bake_error,
        "lift_requested": list(LIFT),
        "control_lift": list(lifted_control - control_before),
        "dayz_hand_lift": list(lifted_hand - before_lift),
        "bake_pose_errors": bake_pose_errors,
        "max_bake_location_error": max_bake_location,
        "max_bake_rotation_error": max_bake_rotation,
        "encoded_target_after_bake_error": encoded_target_after_bake_error,
        "encoded_target_in_base_error": encoded_target_in_base_error,
        "encoded_base_hand_matrix": flat_matrix(encoded_base_hand_matrix),
        "encoded_base_origin_matrix": flat_matrix(encoded_base_origin_matrix),
        "encoded_target_in_base_matrix": flat_matrix(encoded_target_in_base),
        "baked_helper_keys": baked_helper_keys,
        "helpers_two_frame": helpers_two_frame,
        "tracks": first_tracks,
        "position_tracks": first_position_tracks,
        "all_tracks_have_position": all_tracks_have_position,
        "runtime_right_hand_origin_position_error": runtime_position_error,
        "runtime_right_hand_origin_rotation_error": runtime_rotation_error,
        "raw_reimport_errors": raw_reimport_errors,
        "max_raw_reimport_location_error": max_raw_location,
        "max_raw_reimport_rotation_error": max_raw_rotation,
        "raw_hand_cycle_error": raw_hand_cycle_error,
        "reimport_base_hand_matrix": flat_matrix(reimport_base_hand_matrix),
        "reimport_base_origin_matrix": flat_matrix(reimport_base_origin_matrix),
        "decoded_target_before_rebuild_matrix": flat_matrix(decoded_target_before_rebuild),
        "decoded_target_before_rebuild_error": decoded_target_before_rebuild_error,
        "decoded_target_in_base_before_rebuild_matrix": flat_matrix(decoded_target_in_base_before_rebuild),
        "decoded_target_in_base_before_rebuild_error": decoded_target_in_base_before_rebuild_error,
        "rebuilt_errors": rebuilt_errors,
        "max_rebuilt_location_error": max_rebuilt_location,
        "max_rebuilt_rotation_error": max_rebuilt_rotation,
        "max_visible_rebuilt_location_error": max_visible_rebuilt_location,
        "max_visible_rebuilt_rotation_error": max_visible_rebuilt_rotation,
        "reimport_control_error": reimport_control_error,
        "reimport_hand_error": reimport_hand_error,
        "decoded_cycle": cycle,
        "pass": (
            toy.get("dayz_weaponik_base_action") == base.name
            and dummy_control_visible_after_build
            and abs((lifted_control - control_before).z - LIFT.z) < 1.0e-5
            # The proxy is a fixed-length Blender two-bone preview, not the
            # five-record DayZ solver; sub-millimetre endpoint drift is allowed.
            and abs((lifted_hand - before_lift).z - LIFT.z) < 1.0e-3
            and max_bake_location < 1.0e-4
            and max_bake_rotation < 1.0e-4
            and dummy_bake_error["location"] < 1.0e-4
            and dummy_bake_error["rotation"] < 1.0e-4
            and helpers_two_frame
            and all_tracks_have_position
            and runtime_position_error < 5.0e-4
            and runtime_rotation_error < 5.0e-4
            # Raw/helper Blender world matrices are graph representations and
            # legitimately change when their parent hand basis is reconstructed.
            # The authoritative checks are raw RightHand cycling, visible anatomy,
            # control target and decoded ANM channels.
            and raw_hand_cycle_error["location"] < 0.002
            and raw_hand_cycle_error["rotation"] < 0.01
            and max_visible_rebuilt_location < 0.002
            and max_visible_rebuilt_rotation < 0.01
            and reimport_control_error < 0.002
            and reimport_hand_error < 0.002
            and not cycle["missing"]
            and not cycle["extra"]
            and cycle["max_error"] < 5.0e-4
        ),
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print("TOY_IK_LIFT_RESULT " + json.dumps({"pass": report["pass"], "report": REPORT, "blend": BLEND}))


main()
