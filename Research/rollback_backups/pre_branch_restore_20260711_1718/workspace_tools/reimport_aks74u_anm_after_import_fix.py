import importlib
import json
import os
import sys
from types import SimpleNamespace

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-reimport-aks74u-anm-after-import-fix.json")
ARMATURE_NAME = "_DayZ_Character"
FULL_BODY_ACTION = "p_rfl_erc_idle_ras"
IK_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
ADDON_ROOT = r"P:\BlenderAnimtool"


def set_active_armature():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    return arm


def remove_preview_state(arm):
    removed = {"constraints": [], "objects": []}
    for pb in arm.pose.bones:
        for constraint in list(pb.constraints):
            if (
                constraint.name.startswith("DayZ WIK Control")
                or constraint.name == "DayZ WeaponIK Preview"
                or constraint.name.startswith("WIK_")
            ):
                removed["constraints"].append(f"{pb.name}:{constraint.name}")
                pb.constraints.remove(constraint)

    for obj in list(bpy.data.objects):
        if (
            obj.name.startswith("WIK_")
            or obj.get("dayz_weaponik_control")
            or obj.get("dayz_weaponik_computed_pole")
        ):
            removed["objects"].append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def reset_pose_basis(arm):
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def ensure_full_body_nla(arm):
    full = bpy.data.actions.get(FULL_BODY_ACTION)
    if full is None:
        raise RuntimeError(f"Full-body action {FULL_BODY_ACTION!r} not found")
    if arm.animation_data is None:
        arm.animation_data_create()

    arm.animation_data.action = None
    has_strip = False
    for track in arm.animation_data.nla_tracks:
        track.mute = True
        for strip in track.strips:
            if strip.action == full:
                track.mute = False
                strip.mute = False
                strip.influence = 1.0
                strip.blend_type = "REPLACE"
                has_strip = True
            else:
                strip.mute = True

    if not has_strip:
        track = arm.animation_data.nla_tracks.new()
        track.name = FULL_BODY_ACTION
        strip = track.strips.new(FULL_BODY_ACTION, int(full.frame_range[0]), full)
        strip.influence = 1.0
        strip.blend_type = "REPLACE"
        strip.mute = False
        track.mute = False


def remove_old_actions():
    removed = []
    for name in ("aks74u", "aks74u_helpers_only"):
        action = bpy.data.actions.get(name)
        if action is not None:
            bpy.data.actions.remove(action)
            removed.append(name)
    return removed


def import_ik_anm(arm):
    if not os.path.exists(ADDON_ROOT):
        raise RuntimeError(f"Blender process cannot see addon root: {ADDON_ROOT}")
    if not os.path.exists(IK_ANM):
        raise RuntimeError(f"Blender process cannot see IK ANM: {IK_ANM}")
    if ADDON_ROOT not in sys.path:
        sys.path.insert(0, ADDON_ROOT)

    import DayzAnimationToolsBinary.Import.ImportAnm as ImportAnm

    ImportAnm = importlib.reload(ImportAnm)

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    dummy_self = SimpleNamespace(
        filepath=IK_ANM,
        files=[SimpleNamespace(name=os.path.basename(IK_ANM))],
    )
    result = ImportAnm.load(dummy_self, bpy.context, ImportAnm.AnmImportSettings())
    if result:
        raise RuntimeError(str(result))

    action = bpy.data.actions.get("aks74u")
    if action is None:
        raise RuntimeError("Import finished but action 'aks74u' was not created")
    return action


def summarize_action(action):
    bones = {}
    for fc in action.fcurves:
        path = fc.data_path
        prefix = 'pose.bones["'
        if path.startswith(prefix):
            name = path[len(prefix):].split('"]', 1)[0]
        else:
            name = path
        bones.setdefault(name, 0)
        bones[name] += 1
    return {
        "name": action.name,
        "frame_range": [float(action.frame_range[0]), float(action.frame_range[1])],
        "fcurves": len(action.fcurves),
        "bones": bones,
    }


def main():
    arm = set_active_armature()
    removed_preview = remove_preview_state(arm)
    ensure_full_body_nla(arm)
    reset_pose_basis(arm)
    removed_actions = remove_old_actions()
    action = import_ik_anm(arm)

    # Leave the freshly imported ANM action active; the helper-only creation
    # pass will copy only DayZ WeaponIK helper tracks from it.
    arm.animation_data.action = action
    arm["dayz_weaponik_mode"] = "ANM import fixed: raw aks74u helper source"
    bpy.context.scene.frame_set(30)
    bpy.context.view_layer.update()

    data = {
        "mode": arm["dayz_weaponik_mode"],
        "anm": IK_ANM,
        "addon_root": ADDON_ROOT,
        "removed_preview": removed_preview,
        "removed_actions": removed_actions,
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
        "action": summarize_action(action),
        "note": "This reimport uses DayzAnimationToolsBinary.Import.ImportAnm reloaded from disk after the ANM IK import patch.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
