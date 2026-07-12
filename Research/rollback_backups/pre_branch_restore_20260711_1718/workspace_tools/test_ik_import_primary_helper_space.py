import json
import os

import bpy
from mathutils import Matrix, Quaternion, Vector

from DayzAnimationTools.Tools import AddSurvivorIK as IK


ARMATURE = "_DayZ_Character"
BASE = r"P:\DZ\anims\anm\player\moves\1handed\p_1hd_erc_idle_low.anm"
IK_ANM = r"P:\DZ\anims\anm\player\ik\gear\box_cereal.anm"
REPORT = r"P:\BlenderAnimtool\Research\anm_reports\ik-import-primary-helper-space-20260711.json"
AXIS_FIX = Matrix(((0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))


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
        bImportTranslationKeys=translation,
        bImportRotationKeys=True,
        bImportScaleKeys=False,
        bImportFirstTwoFramesOnly=first_two,
        fUnitScale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Import failed: {path}: {sorted(result)}")
    return obj.animation_data.action


def held(values, frame, default):
    keys = [int(key) for key in values if int(key) <= frame]
    return values[str(max(keys))] if keys else default


def raw_track_matrix(action, name, frame):
    tracks = json.loads(action["dayz_binary_anm_track_keys_json"])
    track = tracks[name]
    pos = held(track.get("pos", {}), frame, [0.0, 0.0, 0.0])
    raw = held(track.get("rot", {}), frame, [0.0, 0.0, 0.0, 1.0])
    quat = Quaternion((-float(raw[3]), float(raw[0]), float(raw[1]), float(raw[2])))
    return Matrix.Translation(Vector(tuple(float(value) for value in pos))) @ quat.to_matrix().to_4x4()


def matrix_error(left, right):
    return {
        "location": float((left.to_translation() - right.to_translation()).length),
        "rotation": float(left.to_quaternion().rotation_difference(right.to_quaternion()).angle),
    }


def main():
    arm = bpy.data.objects[ARMATURE]
    import_anm(arm, BASE, translation=False, first_two=False)
    action = import_anm(arm, IK_ANM, translation=True, first_two=True)

    errors = {}
    scene = bpy.context.scene
    for frame in (0, 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        origin = arm.pose.bones["RightHandOrigin"]
        primary = origin.matrix @ Matrix.Translation((0.0, -origin.length, 0.0))
        errors[str(frame)] = {}
        for name in ("RightForeArmDirectionOrigin", "RightForeArmDirection"):
            raw_rel = raw_track_matrix(action, name, frame)
            expected = primary @ AXIS_FIX.inverted() @ raw_rel @ AXIS_FIX
            actual = arm.pose.bones[name].matrix.copy()
            errors[str(frame)][name] = matrix_error(expected, actual)

    max_location = max(
        value["location"]
        for frame in errors.values()
        for value in frame.values()
    )
    max_rotation = max(
        value["rotation"]
        for frame in errors.values()
        for value in frame.values()
    )
    report = {
        "base": BASE,
        "ik": IK_ANM,
        "errors": errors,
        "max_location_error": max_location,
        "max_rotation_error": max_rotation,
        "pass": max_location < 1.0e-5 and max_rotation < 1.0e-4,
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print("IK_IMPORT_PRIMARY_HELPER_RESULT", json.dumps(report))
    if not report["pass"]:
        raise RuntimeError(json.dumps(report))


if __name__ == "__main__":
    main()
