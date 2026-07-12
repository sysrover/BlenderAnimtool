import importlib
import json
import os

import bpy
from mathutils import Matrix

import DayzAnimationTools.Tools.AddSurvivorIK as IK


BASE = r"P:\DZ\anims\anm\player\moves\1handed\p_1hd_erc_idle_low.anm"
IK_ANM = r"P:\UARP_Items_3\ANM\cable2_rebuilt_importfix_20260711.anm"
DESIRED = r"P:\BlenderAnimtool\Research\anm_reports\cable2-backup-authored-pose-20260711.json"
REPORT = r"P:\BlenderAnimtool\Research\anm_reports\cable2-rebuilt-roundtrip-20260711.json"


def matrix(values):
    return Matrix([values[index:index + 4] for index in range(0, 16, 4)])


def errors(actual, expected):
    return {
        "location": (actual.to_translation() - expected.to_translation()).length,
        "rotation_radians": actual.to_quaternion().rotation_difference(expected.to_quaternion()).angle,
    }


def select_arm(arm):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.hide_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm


def import_anm(arm, path, translation, first_two):
    select_arm(arm)
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
        raise RuntimeError(f"Import failed for {path}: {sorted(result)}")


IK = importlib.reload(IK)
arm = bpy.data.objects["_DayZ_Character"]
select_arm(arm)
IK._remove_old_fk_controls(arm)
if arm.animation_data:
    arm.animation_data_clear()
for pose_bone in arm.pose.bones:
    pose_bone.matrix_basis.identity()
bpy.context.view_layer.update()

import_anm(arm, BASE, False, False)
import_anm(arm, IK_ANM, True, True)
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
build_error = IK.bake_current_anm_to_dayz_arm_controls(arm)
if build_error:
    raise RuntimeError(build_error)
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

rig = bpy.data.objects[IK.FK_CONTROL_RIG_NAME]
desired = json.load(open(DESIRED, "r", encoding="utf-8"))
checks = {}
for name in ("CTRL_RightHand", "CTRL_RightElbow", "IK_RightHandDummy.R"):
    checks[name] = errors(
        rig.matrix_world @ rig.pose.bones[name].matrix,
        matrix(desired["rig"][name]),
    )

# The corrected import invariant: both origin controls use the same displayed
# rotation, while the positional vector retains the ANM's real small offset.
rho = rig.pose.bones["IK_RightHandOrigin.R"].matrix
rfdo = rig.pose.bones["IK_RightElbowOrigin.R"].matrix
checks["origin_rotation_difference_radians"] = rho.to_quaternion().rotation_difference(
    rfdo.to_quaternion()
).angle

result = {
    "source": IK_ANM,
    "build_error": build_error,
    "checks": checks,
    "pass": (
        checks["CTRL_RightHand"]["location"] < 1.0e-4
        and checks["CTRL_RightHand"]["rotation_radians"] < 1.0e-4
        and checks["IK_RightHandDummy.R"]["location"] < 1.0e-4
        and checks["IK_RightHandDummy.R"]["rotation_radians"] < 1.0e-4
        and checks["origin_rotation_difference_radians"] < 1.0e-4
    ),
}
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
print("CABLE2_ROUNDTRIP=" + json.dumps(result))
