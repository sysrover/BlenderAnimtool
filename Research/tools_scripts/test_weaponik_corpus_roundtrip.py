import hashlib
import json
import os
import sys

import bpy

from DayzAnimationTools.Tools import AddSurvivorIK
from DayzAnimationToolsBinary.Types.Anm import Anm


ARMATURE = "_DayZ_Character"
BASE_ACTION = "p_rfl_erc_idle_ras"
CONTROL_RIG = "DAT_DayZ_Arm_FK_Controls"
OUTPUT_ROOT = r"C:\temp\dayz_weaponik_corpus"
REPORT_ROOT = r"C:\Users\sysro\diag\CsharpModVScode\anm"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decoded(path):
    animation = Anm.CreateFromFile(path)
    result = {"format": animation.format.name, "fps": int(animation.fps), "bones": {}}
    for bone in animation.bones:
        result["bones"][bone.name] = {
            "position": {
                int(key.frame): [float(x * bone.posMulti + bone.posBias) for x in key.data]
                for key in bone.posKeys
            },
            "rotation": {
                int(key.frame): [float(x * bone.rotMulti + bone.rotBias) for x in key.data]
                for key in bone.rotKeys
            },
        }
    return result


def held_value(keys, frame, identity):
    candidates = [key for key in keys if key <= frame]
    if not candidates:
        return identity
    return keys[max(candidates)]


def compare(left, right, track_names=None):
    tracks = set(left["bones"]) if track_names is None else set(track_names)
    missing = sorted(name for name in tracks if name not in right["bones"])
    maximum = 0.0
    worst = None
    for name in sorted(tracks - set(missing)):
        for channel, identity in (("position", [0.0, 0.0, 0.0]), ("rotation", [0.0, 0.0, 0.0, 1.0])):
            akeys = left["bones"][name][channel]
            bkeys = right["bones"][name][channel]
            for frame in (0, 1):
                a = held_value(akeys, frame, identity)
                b = held_value(bkeys, frame, identity)
                if channel == "rotation":
                    direct = max(abs(a[i] - b[i]) for i in range(4))
                    negated = max(abs(a[i] + b[i]) for i in range(4))
                    error = min(direct, negated)
                else:
                    error = max(abs(a[i] - b[i]) for i in range(3))
                if error > maximum:
                    maximum = error
                    worst = {"track": name, "channel": channel, "frame": frame, "error": error}
    return {"max_error": maximum, "worst": worst, "missing_tracks": missing}


def select_armature(armature):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    armature.hide_set(False)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature


def reset_to_base(armature):
    if armature.animation_data is None:
        armature.animation_data_create()
    for track in list(armature.animation_data.nla_tracks):
        armature.animation_data.nla_tracks.remove(track)
    armature.animation_data.action = bpy.data.actions[BASE_ACTION]
    for pose_bone in armature.pose.bones:
        for constraint in pose_bone.constraints:
            if constraint.name.startswith((AddSurvivorIK.FK_CONSTRAINT_PREFIX, AddSurvivorIK.IK_CONSTRAINT_PREFIX, AddSurvivorIK.IK_PREVIEW_CONSTRAINT_PREFIX)):
                constraint.influence = 0.0
    bpy.context.scene.frame_set(0)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()


def import_anm(armature, path):
    select_armature(armature)
    result = bpy.ops.import_scene.anm(
        filepath=path,
        files=[{"name": os.path.basename(path)}],
        fUnitScale=1.0,
        bImportTranslationKeys=True,
        bImportRotationKeys=True,
        bImportScaleKeys=True,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Import failed: {sorted(result)}")
    return armature.animation_data.action


def export_anm(armature, path, preserve_raw):
    select_armature(armature)
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
        bPreserveImportedRawAnm=preserve_raw,
        fUnitScale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Export failed: {sorted(result)}")


def perturb_left_target(rig):
    action = rig.animation_data.action
    path = 'pose.bones["IK_LeftHandTarget.L"].location'
    for curve in action.fcurves:
        if curve.data_path == path and curve.array_index == 0:
            for point in curve.keyframe_points:
                if int(round(point.co.x)) == 1:
                    before = float(point.co.y)
                    point.co.y += 0.01
                    return {"before": before, "after": float(point.co.y)}
    raise RuntimeError("No editable LeftHand target X key at frame 1")


def main(source_path):
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    name = os.path.splitext(os.path.basename(source_path))[0]
    armature = bpy.data.objects[ARMATURE]
    scene = bpy.context.scene
    scene["dayz_live_weaponik_solver_busy"] = True

    reset_to_base(armature)
    imported = import_anm(armature, source_path)
    source = decoded(source_path)

    raw_path = os.path.join(OUTPUT_ROOT, f"{name}_raw.anm")
    export_anm(armature, raw_path, True)

    imported["dayz_binary_anm_raw_preserve"] = False
    sampled_path = os.path.join(OUTPUT_ROOT, f"{name}_sampled.anm")
    export_anm(armature, sampled_path, False)
    sampled = decoded(sampled_path)

    bake_error = AddSurvivorIK.bake_current_anm_to_dayz_arm_controls(armature)
    if bake_error:
        raise RuntimeError(bake_error)
    rig = bpy.data.objects[CONTROL_RIG]
    control_edit = perturb_left_target(rig)
    bpy.context.scene.frame_set(0)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    edit_runtime = {
        "control_location": list(rig.pose.bones["IK_LeftHandTarget.L"].location),
        "control_world": list(rig.pose.bones["IK_LeftHandTarget.L"].matrix.translation),
        "source_world": list(armature.pose.bones["LeftHandIKTarget"].matrix.translation),
        "constraints": [
            {
                "name": constraint.name,
                "enabled": constraint.enabled,
                "influence": constraint.influence,
            }
            for constraint in armature.pose.bones["LeftHandIKTarget"].constraints
        ],
    }
    imported["dayz_binary_anm_raw_preserve"] = False
    edited_path = os.path.join(OUTPUT_ROOT, f"{name}_edited.anm")
    export_anm(armature, edited_path, False)
    edited = decoded(edited_path)

    source_left = sampled["bones"]["LeftHandIKTarget"]
    edited_left = edited["bones"]["LeftHandIKTarget"]
    left_delta = compare(
        {"bones": {"LeftHandIKTarget": source_left}},
        {"bones": {"LeftHandIKTarget": edited_left}},
        ["LeftHandIKTarget"],
    )

    reset_to_base(armature)
    cycle_action = import_anm(armature, edited_path)
    cycle_action["dayz_binary_anm_raw_preserve"] = False
    cycle_path = os.path.join(OUTPUT_ROOT, f"{name}_cycle.anm")
    export_anm(armature, cycle_path, False)
    cycle = decoded(cycle_path)

    report = {
        "source": source_path,
        "source_format": source["format"],
        "source_fps": source["fps"],
        "source_sha256": sha256(source_path),
        "raw_sha256": sha256(raw_path),
        "raw_exact": sha256(source_path) == sha256(raw_path),
        "sampled_compare": compare(source, sampled, source["bones"].keys()),
        "control_edit": control_edit,
        "control_action_slot": getattr(rig.animation_data, "action_slot_handle", None),
        "edit_runtime": edit_runtime,
        "edited_left_target_delta": left_delta,
        "edit_detected": left_delta["max_error"] > 1.0e-4,
        "cycle_compare": compare(edited, cycle, edited["bones"].keys()),
        "paths": {"raw": raw_path, "sampled": sampled_path, "edited": edited_path, "cycle": cycle_path},
    }
    report_path = os.path.join(REPORT_ROOT, f"weaponik-corpus-{name}.json")
    with open(report_path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print("CORPUS_RESULT " + json.dumps({
        "name": name,
        "raw_exact": report["raw_exact"],
        "sampled_max_error": report["sampled_compare"]["max_error"],
        "edit_detected": report["edit_detected"],
        "cycle_max_error": report["cycle_compare"]["max_error"],
        "report": report_path,
    }))


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise RuntimeError("Pass source ANM path after --")
main(args[0])
