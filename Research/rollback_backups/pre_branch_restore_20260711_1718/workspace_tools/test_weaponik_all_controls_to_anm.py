import json
import os

import bpy

from DayzAnimationTools.Tools import AddSurvivorIK
from DayzAnimationToolsBinary.Types.Anm import Anm


ARMATURE = "_DayZ_Character"
RIG = "DAT_DayZ_Arm_FK_Controls"
OUTPUT_DIR = r"C:\temp\dayz_weaponik_control_matrix"
REPORT = r"C:\Users\sysro\diag\CsharpModVScode\anm\weaponik-all-controls-to-anm.json"


def decoded_animation(path):
    animation = Anm.CreateFromFile(path)
    result = {}
    for bone in animation.bones:
        result[bone.name] = {
            "position": {
                int(key.frame): [
                    float(value * bone.posMulti + bone.posBias) for value in key.data
                ]
                for key in bone.posKeys
            },
            "rotation": {
                int(key.frame): [
                    float(value * bone.rotMulti + bone.rotBias) for value in key.data
                ]
                for key in bone.rotKeys
            },
        }
    return result


def export(path):
    result = bpy.ops.export_scene.anm(
        filepath=path,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=30,
        eAnimType="IK2H",
        bSaveAll=False,
        bPreserveImportedRawAnm=False,
        fUnitScale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"ANM export failed: {sorted(result)}")


def changed_channels(baseline, changed, epsilon=1.0e-7):
    result = {}
    for bone_name in sorted(set(baseline) | set(changed)):
        bone_changes = []
        for channel in ("position", "rotation"):
            left = baseline.get(bone_name, {}).get(channel, {})
            right = changed.get(bone_name, {}).get(channel, {})
            for frame in sorted(set(left) | set(right)):
                a = left.get(frame)
                b = right.get(frame)
                if a is None or b is None:
                    bone_changes.append({"channel": channel, "frame": frame, "delta": None})
                    continue
                delta = [b[index] - a[index] for index in range(min(len(a), len(b)))]
                if len(a) != len(b) or any(abs(value) > epsilon for value in delta):
                    bone_changes.append({"channel": channel, "frame": frame, "delta": delta})
        if bone_changes:
            result[bone_name] = bone_changes
    return result


def perturb_frame_one(action, control, is_finger):
    property_name = "rotation_quaternion" if is_finger else "location"
    array_index = 1 if is_finger else 0
    data_path = f'pose.bones["{control}"].{property_name}'
    for curve in action.fcurves:
        if curve.data_path != data_path or curve.array_index != array_index:
            continue
        for point in curve.keyframe_points:
            if int(round(point.co.x)) == 1:
                amount = 0.03 if is_finger else 0.02
                point.co.y += amount
                return {
                    "data_path": data_path,
                    "array_index": array_index,
                    "amount": amount,
                }
    raise RuntimeError(f"No frame-1 key for {data_path}[{array_index}]")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    armature = bpy.data.objects[ARMATURE]
    rig = bpy.data.objects[RIG]
    old_active = bpy.context.view_layer.objects.active
    old_selected = list(bpy.context.selected_objects)
    old_rig_action = rig.animation_data.action
    scene = bpy.context.scene
    preview_busy_was_set = "dayz_live_weaponik_solver_busy" in scene
    preview_busy = scene.get("dayz_live_weaponik_solver_busy", False)

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    armature.hide_set(False)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    scene["dayz_live_weaponik_solver_busy"] = True
    bpy.context.scene.frame_set(1)

    baseline_path = os.path.join(OUTPUT_DIR, "baseline.anm")
    export(baseline_path)
    baseline = decoded_animation(baseline_path)
    results = {}

    try:
        for source_track, control in AddSurvivorIK.IK_EXPORT_CONTROLS.items():
            test_action = old_rig_action.copy()
            test_action.name = f"DAT_TEST_{control}"
            try:
                is_finger = source_track in AddSurvivorIK.IK_FINGER_CONTROLS
                perturbation = perturb_frame_one(test_action, control, is_finger)
                rig.animation_data.action = test_action
                bpy.context.scene.frame_set(0)
                bpy.context.scene.frame_set(1)
                bpy.context.view_layer.update()
                changed_path = os.path.join(OUTPUT_DIR, f"{source_track}.anm")
                export(changed_path)
                changes = changed_channels(baseline, decoded_animation(changed_path))
                changed_tracks = sorted(changes)
                results[source_track] = {
                    "control": control,
                    "kind": "finger" if is_finger else "helper",
                    "perturbation": perturbation,
                    "changed_tracks": changed_tracks,
                    "expected_track_changed": source_track in changes,
                    "only_expected_track_changed": changed_tracks == [source_track],
                    "changes": changes,
                    "file_size": os.path.getsize(changed_path),
                }
            finally:
                rig.animation_data.action = old_rig_action
                if test_action.name in bpy.data.actions:
                    bpy.data.actions.remove(test_action)

        report = {
            "baseline": baseline_path,
            "control_count": len(AddSurvivorIK.IK_EXPORT_CONTROLS),
            "passed_expected_track": sum(
                item["expected_track_changed"] for item in results.values()
            ),
            "passed_isolation": sum(
                item["only_expected_track_changed"] for item in results.values()
            ),
            "results": results,
        }
        with open(REPORT, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
        return report
    finally:
        rig.animation_data.action = old_rig_action
        if preview_busy_was_set:
            scene["dayz_live_weaponik_solver_busy"] = preview_busy
        elif "dayz_live_weaponik_solver_busy" in scene:
            del scene["dayz_live_weaponik_solver_busy"]
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in old_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        bpy.context.view_layer.objects.active = old_active


RESULT = main()
