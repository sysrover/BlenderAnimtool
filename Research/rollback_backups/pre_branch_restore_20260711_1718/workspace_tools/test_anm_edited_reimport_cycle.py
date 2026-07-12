import json

import bpy


ARMATURE = "_DayZ_Character"
SOURCE_ACTION = "aks74u"
EXPORTED_ANM = r"C:\temp\aks74u_sampled_edited_test2.anm"
IMPORTED_NAME = "aks74u_sampled_edited_test2"
REPORT = r"C:\Users\sysro\diag\CsharpModVScode\anm\aks74u-edited-reimport-cycle.json"
HELPERS = (
    "LeftHandIKTarget",
    "RightHandOrigin",
    "LeftForeArmDirection",
    "RightForeArmDirection",
)


def values(action, bone, prop, count):
    path = f'pose.bones["{bone}"].{prop}'
    result = []
    for index in range(count):
        curve = next(
            (
                fc
                for fc in action.fcurves
                if fc.data_path == path and fc.array_index == index
            ),
            None,
        )
        result.append([curve.evaluate(frame) if curve else None for frame in (0, 1)])
    return result


def main():
    armature = bpy.data.objects[ARMATURE]
    old_active = bpy.context.view_layer.objects.active
    old_selected = list(bpy.context.selected_objects)
    old_action = armature.animation_data.action
    old_tracks = {track.as_pointer() for track in armature.animation_data.nla_tracks}

    desired = bpy.data.actions[SOURCE_ACTION].copy()
    desired.name = "DAT_DESIRED_EDIT_COMPARE"
    desired["dayz_binary_anm_raw_preserve"] = False
    for curve in desired.fcurves:
        if "LeftHandIKTarget" not in curve.data_path or not curve.data_path.endswith(
            ".location"
        ):
            continue
        for point in curve.keyframe_points:
            if int(round(point.co.x)) == 1:
                point.co.y += 0.01

    imported = None
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        armature.animation_data.action = desired

        result = bpy.ops.import_scene.anm(
            filepath=EXPORTED_ANM,
            files=[{"name": "aks74u_sampled_edited_test2.anm"}],
            fUnitScale=1.0,
            bImportTranslationKeys=True,
            bImportRotationKeys=True,
            bImportScaleKeys=True,
        )
        imported = armature.animation_data.action
        report = {
            "result": sorted(result),
            "imported": imported.name if imported else None,
            "format": imported.get("dayz_binary_anm_format") if imported else None,
            "bones": {},
        }
        for bone in HELPERS:
            report["bones"][bone] = {
                "desired_location": values(desired, bone, "location", 3),
                "imported_location": values(imported, bone, "location", 3),
                "desired_rotation": values(desired, bone, "rotation_quaternion", 4),
                "imported_rotation": values(imported, bone, "rotation_quaternion", 4),
            }
        with open(REPORT, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
        return report
    finally:
        armature.animation_data.action = old_action
        for track in list(armature.animation_data.nla_tracks):
            if track.as_pointer() not in old_tracks:
                armature.animation_data.nla_tracks.remove(track)
        if imported is not None and imported.name in bpy.data.actions:
            bpy.data.actions.remove(imported)
        if desired.name in bpy.data.actions:
            bpy.data.actions.remove(desired)
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in old_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        bpy.context.view_layer.objects.active = old_active


RESULT = main()
