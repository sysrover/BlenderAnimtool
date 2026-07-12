import json
import os

import bpy

from DayzAnimationToolsBinary.Types.Anm import Anm


ARMATURE = "_DayZ_Character"
RIG = "DAT_DayZ_Arm_FK_Controls"
CONTROL = "IK_LeftHandTarget.L"
TRACK = "LeftHandIKTarget"
BASELINE = r"C:\temp\aks74u_control_baseline.anm"
CHANGED = r"C:\temp\aks74u_control_changed.anm"
REPORT = r"C:\Users\sysro\diag\CsharpModVScode\anm\weaponik-control-to-anm.json"


def decoded_positions(path):
    animation = Anm.CreateFromFile(path)
    bone = next(item for item in animation.bones if item.name == TRACK)
    return {
        int(key.frame): [
            float(key.data[index] * bone.posMulti + bone.posBias)
            for index in range(3)
        ]
        for key in bone.posKeys
    }


def export(path):
    return bpy.ops.export_scene.anm(
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


def main():
    armature = bpy.data.objects[ARMATURE]
    rig = bpy.data.objects[RIG]
    old_active = bpy.context.view_layer.objects.active
    old_selected = list(bpy.context.selected_objects)
    old_rig_action = rig.animation_data.action
    test_action = old_rig_action.copy()
    test_action.name = "DAT_CONTROL_TO_ANM_TEST"

    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.context.scene.frame_set(1)
        baseline_result = export(BASELINE)

        rig.animation_data.action = test_action
        path = f'pose.bones["{CONTROL}"].location'
        changed_points = []
        for curve in test_action.fcurves:
            if curve.data_path != path or curve.array_index != 0:
                continue
            for point in curve.keyframe_points:
                if int(round(point.co.x)) == 1:
                    point.co.y += 0.02
                    changed_points.append([point.co.x, point.co.y])
        if not changed_points:
            raise RuntimeError(f"No frame-1 location X key found for {CONTROL}")
        bpy.context.scene.frame_set(0)
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        changed_result = export(CHANGED)

        baseline = decoded_positions(BASELINE)
        changed = decoded_positions(CHANGED)
        delta = {
            str(frame): [changed[frame][i] - baseline[frame][i] for i in range(3)]
            for frame in sorted(set(baseline) & set(changed))
        }
        report = {
            "baseline_result": sorted(baseline_result),
            "changed_result": sorted(changed_result),
            "control": CONTROL,
            "track": TRACK,
            "changed_control_keys": changed_points,
            "baseline_track": baseline,
            "changed_track": changed,
            "track_delta": delta,
            "baseline_size": os.path.getsize(BASELINE),
            "changed_size": os.path.getsize(CHANGED),
        }
        with open(REPORT, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
        return report
    finally:
        rig.animation_data.action = old_rig_action
        if test_action.name in bpy.data.actions:
            bpy.data.actions.remove(test_action)
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in old_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        bpy.context.view_layer.objects.active = old_active


RESULT = main()
