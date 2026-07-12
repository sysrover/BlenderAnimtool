import importlib
import json

import bpy


ARMATURE = "_DayZ_Character"
SOURCE_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
BASE_ACTION = "p_rfl_erc_idle_ras"
CONTROL_RIG = "DAT_DayZ_Arm_FK_Controls"
OUTPUT_BLEND = r"P:\Animation_Weapon\Weapon_template_dayz_weaponik_authoring_v3.blend"
REPORT = r"C:\Users\sysro\diag\CsharpModVScode\anm\dayz-weaponik-authoring-v3-build.json"


def main():
    import DayzAnimationTools.Tools.AddSurvivorIK as weaponik

    weaponik = importlib.reload(weaponik)
    armature = bpy.data.objects.get(ARMATURE)
    base_action = bpy.data.actions.get(BASE_ACTION)
    if armature is None or armature.type != "ARMATURE":
        raise RuntimeError(f"Missing export armature {ARMATURE}")
    if base_action is None:
        raise RuntimeError(f"Missing base action {BASE_ACTION}")

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    if armature.animation_data is None:
        armature.animation_data_create()
    # Start from the known ready pose, then import a fresh official IK ANM with
    # the current importer. This prevents the template from inheriting legacy
    # pre-Action-Slot actions from earlier experiments.
    for track in list(armature.animation_data.nla_tracks):
        armature.animation_data.nla_tracks.remove(track)
    armature.animation_data.action = base_action
    bpy.context.scene["dayz_live_weaponik_solver_busy"] = True
    bpy.context.scene.frame_set(0)
    bpy.context.scene.frame_set(1)
    import_result = bpy.ops.import_scene.anm(
        filepath=SOURCE_ANM,
        files=[{"name": "aks74u.anm"}],
        fUnitScale=1.0,
        bImportTranslationKeys=True,
        bImportRotationKeys=True,
        bImportScaleKeys=True,
    )
    if "FINISHED" not in import_result:
        raise RuntimeError(f"Fresh source import failed: {sorted(import_result)}")
    source_action = armature.animation_data.action
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 1
    bpy.context.scene.frame_set(1)

    prepare_error = weaponik.refresh_weaponik_preview_constraints(armature)
    if prepare_error:
        raise RuntimeError(prepare_error)
    build_error = weaponik.bake_current_anm_to_dayz_arm_controls(armature)
    if build_error:
        raise RuntimeError(build_error)

    rig = bpy.data.objects.get(CONTROL_RIG)
    if rig is None or rig.type != "ARMATURE":
        raise RuntimeError("Control rig was not created")

    required_controls = set(weaponik.IK_EXPORT_CONTROLS.values())
    required_controls.update(
        f"FK_{bone}.{side}"
        for side, bones in weaponik.FK_ARM_BONES.items()
        for bone in bones
    )
    missing_controls = sorted(required_controls - set(rig.pose.bones.keys()))
    if missing_controls:
        raise RuntimeError("Missing controls: " + ", ".join(missing_controls))

    weaponik._set_authoring_mode_constraints(armature, "IK")
    armature["dayz_arm_authoring_mode"] = "IK_AUTHORING_CONTROLS"
    armature["dayz_weaponik_preview_shoulder_clearance"] = 0.0
    # Import/bake deliberately suppresses the live handler. The saved authoring
    # template must be left unlocked so control edits refresh the preview.
    bpy.context.scene["dayz_live_weaponik_solver_busy"] = False
    bpy.context.scene.frame_set(0)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    rig.data.show_names = False
    legacy_rig = bpy.data.objects.get("DAT_ControlRig_RefBakeV1")
    if legacy_rig is not None:
        legacy_rig.hide_set(True)
        legacy_rig.hide_viewport = True
        legacy_rig.hide_render = True

    helper_constraints = {}
    for helper, control in weaponik.IK_HELPER_CONTROLS.items():
        pose_bone = armature.pose.bones.get(helper)
        helper_constraints[helper] = [
            {
                "name": constraint.name,
                "type": constraint.type,
                "target": constraint.target.name if constraint.target else None,
                "subtarget": constraint.subtarget,
                "influence": constraint.influence,
            }
            for constraint in pose_bone.constraints
            if constraint.name.startswith(weaponik.IK_CONSTRAINT_PREFIX)
        ]

    report = {
        "output_blend": OUTPUT_BLEND,
        "source_anm": SOURCE_ANM,
        "source_action": source_action.name,
        "base_action": base_action.name,
        "export_armature": armature.name,
        "control_rig": rig.name,
        "control_count": len(rig.pose.bones),
        "missing_controls": missing_controls,
        "helper_constraints": helper_constraints,
        "scene_solver_armature": bpy.context.scene.get(
            "dayz_live_weaponik_solver_armature"
        ),
        "scene_solver_source": bpy.context.scene.get(
            "dayz_live_weaponik_solver_source"
        ),
        "scene_solver_base": bpy.context.scene.get("dayz_live_weaponik_solver_base"),
        "solver_handler": any(
            getattr(handler, "__name__", "")
            == weaponik._dayz_live_weaponik_solver_handler.__name__
            for handler in bpy.app.handlers.frame_change_post
        ),
        "solver_busy": bool(bpy.context.scene.get("dayz_live_weaponik_solver_busy", False)),
        "armature_mode": armature.get("dayz_arm_authoring_mode"),
        "preview_shoulder_clearance": float(
            armature.get("dayz_weaponik_preview_shoulder_clearance", 0.0)
        ),
        "raw_preserve": bool(source_action.get("dayz_binary_anm_raw_preserve", False)),
    }

    with open(REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    return report


RESULT = main()
