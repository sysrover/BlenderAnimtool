import importlib
import json
import math
import os

import bpy
from mathutils import Matrix, Vector

import DayzAnimationTools.Tools.AddSurvivorIK as IK


BASE = r"P:\DZ\anims\anm\player\moves\1handed\p_1hd_erc_idle_low.anm"
IK_SOURCE = r"P:\DZ\anims\anm\player\ik\gear\box_cereal.anm"
EXPORT = r"C:\temp\dayz_ik1h_proxy_workflow\box_cereal_dayz_solve_guide_cycle.anm"
REPORT = r"P:\BlenderAnimtool\Research\anm_reports\ik1h-dayz-solve-blender-guide-roundtrip-20260711.json"
TRACE = r"P:\BlenderAnimtool\Research\anm_reports\ik1h-dayz-solve-blender-guide-export-trace-20260711.json"


def select_only(obj):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def clear_armature(arm):
    select_only(arm)
    IK._remove_old_fk_controls(arm)
    for pose_bone in arm.pose.bones:
        for constraint in list(pose_bone.constraints):
            if constraint.name.startswith(("DAT_", "DayZ")):
                pose_bone.constraints.remove(constraint)
        pose_bone.matrix_basis.identity()
    if arm.animation_data:
        arm.animation_data_clear()
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()


def import_anm(arm, path, translations, first_two=False):
    select_only(arm)
    result = bpy.ops.import_scene.anm(
        filepath=path,
        files=[{"name": os.path.basename(path)}],
        fUnitScale=1.0,
        bImportTranslationKeys=translations,
        bImportRotationKeys=True,
        bImportScaleKeys=False,
        bImportFirstTwoFramesOnly=first_two,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Import failed: {path}: {sorted(result)}")


def export_anm(arm, path):
    select_only(arm)
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
        raise RuntimeError(f"Export failed: {sorted(result)}")


def matrix_error(actual, expected):
    return {
        "location": (actual.to_translation() - expected.to_translation()).length,
        "rotation": actual.to_quaternion().rotation_difference(expected.to_quaternion()).angle,
    }


def guide_state(arm, rig):
    wrist = rig.pose.bones[IK.RIGHT_FOREARM_GUIDES["wrist"]].matrix.copy()
    elbow = rig.pose.bones[IK.RIGHT_FOREARM_GUIDES["elbow"]].matrix.copy()
    axis = (elbow.translation - wrist.translation).normalized()
    return {
        "wrist": wrist,
        "elbow": elbow,
        "axis": axis,
        "wrist_joint": arm.pose.bones["RightHand"].head.copy(),
        "elbow_joint": arm.pose.bones["RightForeArm"].head.copy(),
    }


IK = importlib.reload(IK)
arm = bpy.data.objects["_DayZ_Character"]
scene = bpy.context.scene
clear_armature(arm)
import_anm(arm, BASE, False)
import_anm(arm, IK_SOURCE, True, True)
scene.frame_set(0)
bpy.context.view_layer.update()
rig = bpy.data.objects[IK.FK_CONTROL_RIG_NAME]

target = IK._matrix_from_flat(arm["dayz_import_solved_primary_target"])
initial_decode_parent = IK._matrix_from_flat(arm[IK._proxy_decode_key(0, "RightHand")])
solved_elbow = IK._matrix_from_flat(arm["dayz_import_solved_RightForeArm"])
initial = guide_state(arm, rig)
initial_checks = {
    "wrist_target": matrix_error(arm.pose.bones["RightHand"].matrix, target),
    "elbow_after_build": (
        arm.pose.bones["RightForeArm"].matrix.translation - solved_elbow.translation
    ).length,
    "guide_wrist_joint": (initial["wrist"].translation - initial["wrist_joint"]).length,
    "guide_elbow_joint": (initial["elbow"].translation - initial["elbow_joint"]).length,
}

# Wrist twist must not affect wrist/elbow guide geometry.
hand_control = rig.pose.bones[IK.RIGHT_ANIMATOR_CONTROLS["hand"]]
elbow_control = rig.pose.bones[IK.RIGHT_ANIMATOR_CONTROLS["elbow"]]
original_hand = hand_control.matrix.copy()
original_elbow = elbow_control.matrix.copy()
twisted = original_hand @ Matrix.Rotation(math.radians(70.0), 4, "Y")
twisted.translation = original_hand.translation
hand_control.matrix = twisted
bpy.context.view_layer.update()
IK._sync_dayz_arm_from_proxy(arm, rig)
bpy.context.view_layer.update()
after_twist = guide_state(arm, rig)
twist_checks = {
    "guide_wrist_location_delta": (
        after_twist["wrist"].translation - initial["wrist"].translation
    ).length,
    "guide_elbow_location_delta": (
        after_twist["elbow"].translation - initial["elbow"].translation
    ).length,
    "guide_axis_angle_delta": after_twist["axis"].angle(initial["axis"]),
    "wrist_location_delta": (
        after_twist["wrist_joint"] - initial["wrist_joint"]
    ).length,
}

# Hand translation: both solved joints may move, guide must remain exact.
hand_control.matrix = original_hand
bpy.context.view_layer.update()
IK._sync_dayz_arm_from_proxy(arm, rig)
translated = original_hand.copy()
translated.translation += Vector((0.035, -0.015, 0.025))
hand_control.matrix = translated
bpy.context.view_layer.update()
IK._sync_dayz_arm_from_proxy(arm, rig)
bpy.context.view_layer.update()
after_hand_move = guide_state(arm, rig)
hand_move_checks = {
    "wrist_moved": (after_hand_move["wrist_joint"] - initial["wrist_joint"]).length,
    "guide_wrist_joint": (
        after_hand_move["wrist"].translation - after_hand_move["wrist_joint"]
    ).length,
    "guide_elbow_joint": (
        after_hand_move["elbow"].translation - after_hand_move["elbow_joint"]
    ).length,
}

# Pole translation: wrist remains fixed, elbow and guide follow the pole solve.
before_pole = guide_state(arm, rig)
moved_pole = original_elbow.copy()
moved_pole.translation += Vector((0.08, 0.03, 0.01))
elbow_control.matrix = moved_pole
bpy.context.view_layer.update()
IK._sync_dayz_arm_from_proxy(arm, rig)
bpy.context.view_layer.update()
after_pole = guide_state(arm, rig)
pole_checks = {
    "wrist_delta": (after_pole["wrist_joint"] - before_pole["wrist_joint"]).length,
    "elbow_delta": (after_pole["elbow_joint"] - before_pole["elbow_joint"]).length,
    "guide_wrist_joint": (
        after_pole["wrist"].translation - after_pole["wrist_joint"]
    ).length,
    "guide_elbow_joint": (
        after_pole["elbow"].translation - after_pole["elbow_joint"]
    ).length,
}

# Bake a nontrivial wrist rotation and ensure visible anatomy/guide does not jump.
edited_hand = original_hand @ Matrix.Rotation(math.radians(35.0), 4, "Y")
edited_hand.translation = original_hand.translation
hand_control.matrix = edited_hand
elbow_control.matrix = original_elbow
bpy.context.view_layer.update()
IK._sync_dayz_arm_from_proxy(arm, rig)
bpy.context.view_layer.update()
primary_names = list(IK.DAYZ_PRIMARY_SOLVER_CHAIN)
before_bake = {name: arm.pose.bones[name].matrix.copy() for name in primary_names}
guide_before_bake = guide_state(arm, rig)
bake_error = IK.bake_dayz_ik1h_controls_to_helpers(arm)
if bake_error:
    raise RuntimeError(bake_error)
bpy.context.view_layer.update()
bake_checks = {
    "anatomy": {
        name: matrix_error(arm.pose.bones[name].matrix, before_bake[name])
        for name in primary_names
    },
    "guide_wrist": matrix_error(
        rig.pose.bones[IK.RIGHT_FOREARM_GUIDES["wrist"]].matrix,
        guide_before_bake["wrist"],
    ),
    "guide_elbow": matrix_error(
        rig.pose.bones[IK.RIGHT_FOREARM_GUIDES["elbow"]].matrix,
        guide_before_bake["elbow"],
    ),
}

expected = {
    name: arm.pose.bones[name].matrix.copy()
    for name in primary_names + ["RightHand_Dummy"]
}
expected_guide = guide_state(arm, rig)
expected_target = rig.pose.bones[IK.RIGHT_ANIMATOR_CONTROLS["hand"]].matrix.copy()

# Trace every representation immediately before export.  This deliberately
# records small scalar arrays rather than relying on a large bridge response.
select_only(arm)
import DayzAnimationToolsBinary.Export.ExportAnm as ExportAnm
ExportAnm = importlib.reload(ExportAnm)

def flat_matrix(matrix):
    return [float(matrix[row][column]) for row in range(4) for column in range(4)]

origin = arm.pose.bones["RightHandOrigin"]
export_control = rig.pose.bones[IK.IK_EXPORT_CONTROLS["RightHandOrigin"]]
decode_parent = ExportAnm._ik_decode_hand_parent(arm)
export_location = ExportAnm.GetBoneLocation(origin, "IK1H")
export_rotation = ExportAnm.GetBoneRotation(origin, "IK1H")
trace = {
    "frame": int(scene.frame_current),
    "initial_solved_primary_target": flat_matrix(target),
    "initial_decode_right_hand_parent": flat_matrix(initial_decode_parent),
    "ctrl_right_hand": flat_matrix(expected_target),
    "export_control_right_hand_origin": flat_matrix(export_control.matrix),
    "main_right_hand_origin": flat_matrix(origin.matrix),
    "decode_right_hand_parent": flat_matrix(decode_parent),
    "export_get_bone_location": list(export_location),
    "export_get_bone_rotation_wxyz": list(export_rotation),
    "source_raw_right_hand_origin": {
        "frame_0": flat_matrix(IK._raw_ik_track_rel_from_action(arm.animation_data.action, "RightHandOrigin", 0)),
        "frame_1": flat_matrix(IK._raw_ik_track_rel_from_action(arm.animation_data.action, "RightHandOrigin", 1)),
    },
}
with open(TRACE, "w", encoding="utf-8") as stream:
    json.dump(trace, stream, indent=2)
export_anm(arm, EXPORT)

clear_armature(arm)
import_anm(arm, BASE, False)
import_anm(arm, EXPORT, True, True)
scene.frame_set(0)
bpy.context.view_layer.update()
cycle_rig = bpy.data.objects[IK.FK_CONTROL_RIG_NAME]
cycle_guide = guide_state(arm, cycle_rig)
cycle_target = IK._matrix_from_flat(arm["dayz_import_solved_primary_target"])
cycle_checks = {
    "primary_target": matrix_error(cycle_target, expected_target),
    "anatomy": {
        name: matrix_error(arm.pose.bones[name].matrix, expected[name])
        for name in expected
    },
    "guide_wrist": matrix_error(cycle_guide["wrist"], expected_guide["wrist"]),
    "guide_elbow": matrix_error(cycle_guide["elbow"], expected_guide["elbow"]),
}

all_errors = []
all_errors.extend(
    [initial_checks["wrist_target"]["location"], initial_checks["wrist_target"]["rotation"]]
)
all_errors.extend(
    [initial_checks["elbow_after_build"], initial_checks["guide_wrist_joint"], initial_checks["guide_elbow_joint"]]
)
all_errors.extend(twist_checks.values())
all_errors.extend(
    [hand_move_checks["guide_wrist_joint"], hand_move_checks["guide_elbow_joint"]]
)
all_errors.extend(
    [pole_checks["wrist_delta"], pole_checks["guide_wrist_joint"], pole_checks["guide_elbow_joint"]]
)
for value in bake_checks["anatomy"].values():
    all_errors.extend(value.values())
all_errors.extend(bake_checks["guide_wrist"].values())
all_errors.extend(bake_checks["guide_elbow"].values())
for value in cycle_checks["anatomy"].values():
    all_errors.extend(value.values())
all_errors.extend(cycle_checks["guide_wrist"].values())
all_errors.extend(cycle_checks["guide_elbow"].values())
all_errors.extend(cycle_checks["primary_target"].values())

result = {
    "source": IK_SOURCE,
    "export": EXPORT,
    "initial": initial_checks,
    "wrist_twist": twist_checks,
    "hand_translation": hand_move_checks,
    "pole_translation": pole_checks,
    "bake": bake_checks,
    "cycle": cycle_checks,
    "max_checked_error": max(all_errors),
    "pass": (
        max(all_errors) < 1.0e-4
        and hand_move_checks["wrist_moved"] > 1.0e-3
        and pole_checks["elbow_delta"] > 1.0e-5
    ),
}
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
print("IK1H_GUIDE_TEST=" + json.dumps(result))
