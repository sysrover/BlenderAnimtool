import importlib
import json
import os
from types import SimpleNamespace

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-clean-imported-weaponik-reset.json")
ARMATURE_NAME = "_DayZ_Character"
AKS74U_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
CONTROL_PREFIX = "WIK_"


def remove_experimental_controls():
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith(CONTROL_PREFIX) or obj.get("dayz_weaponik_control") or obj.get("dayz_weaponik_computed_pole"):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def remove_experimental_constraints(arm):
    removed = []
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DayZ WIK Control") or c.name == "DayZ WeaponIK Preview":
                removed.append(f"{pb.name}:{c.name}")
                pb.constraints.remove(c)
    return removed


def ensure_active_armature():
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


def set_helper_parent_hierarchy(arm):
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    if eb.get("LeftHandIKTarget") is None:
        src = eb.get("LeftHandOrigin") or eb.get("LeftHand")
        target = eb.new("LeftHandIKTarget")
        target.matrix = src.matrix.copy()
        target.length = max(src.length, 0.01)

    parent_map = {
        "LeftHandIKTarget": "RightHand_Dummy",
        "LeftHandOrigin": "RightHand_Dummy",
        "LeftForeArmDirectionOrigin": "LeftHand",
        "RightForeArmDirectionOrigin": "RightHand",
        "RightHandOrigin": "RightShoulder",
        "RightForeArmDirection": "RightShoulder",
        "LeftForeArmDirection": "LeftShoulder",
    }
    changes = []
    for child_name, parent_name in parent_map.items():
        child = eb.get(child_name)
        parent = eb.get(parent_name)
        if child is not None and parent is not None and child.parent != parent:
            child.parent = parent
            child.use_connect = False
            changes.append(f"{child_name}->{parent_name}")
    bpy.ops.object.mode_set(mode="OBJECT")
    return changes


def reimport_aks74u(arm):
    if arm.animation_data is None:
        arm.animation_data_create()
    if arm.animation_data.action and arm.animation_data.action.name == "aks74u":
        arm.animation_data.action = None
    for act in list(bpy.data.actions):
        if act.name == "aks74u":
            bpy.data.actions.remove(act)

    import DayzAnimationToolsBinary.Import.ImportAnm as ImportAnm
    ImportAnm = importlib.reload(ImportAnm)
    dummy_self = SimpleNamespace(filepath=AKS74U_ANM, files=[SimpleNamespace(name=os.path.basename(AKS74U_ANM))])
    result = ImportAnm.load(dummy_self, bpy.context, ImportAnm.AnmImportSettings())
    if result:
        raise RuntimeError(result)
    if arm.animation_data:
        for track in arm.animation_data.nla_tracks:
            track.mute = False
            for strip in track.strips:
                strip.mute = False
                strip.influence = 1.0


def xform_summary(arm):
    bpy.context.view_layer.update()
    names = [
        "LeftArm",
        "LeftArmRoll",
        "LeftForeArm",
        "LeftForeArmRoll",
        "LeftHand",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
        "LeftForeArmDirectionOrigin",
        "RightHand",
        "RightHand_Dummy",
        "RightHandOrigin",
    ]
    return {
        name: list(arm.pose.bones[name].head)
        for name in names
        if arm.pose.bones.get(name) is not None
    }


def main():
    arm = ensure_active_armature()
    removed_constraints = remove_experimental_constraints(arm)
    removed_controls = remove_experimental_controls()
    hierarchy_changes = set_helper_parent_hierarchy(arm)
    reimport_aks74u(arm)
    arm["dayz_weaponik_mode"] = "Clean Imported Tracks"
    bpy.context.scene.frame_set(30)
    bpy.context.view_layer.update()
    data = {
        "mode": arm["dayz_weaponik_mode"],
        "removed_constraints": removed_constraints,
        "removed_controls": removed_controls,
        "hierarchy_changes": hierarchy_changes,
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "nla": [
            {
                "track": tr.name,
                "strip": st.name,
                "action": st.action.name if st.action else None,
                "influence": st.influence,
                "mute": st.mute,
                "track_mute": tr.mute,
            }
            for tr in arm.animation_data.nla_tracks
            for st in tr.strips
        ] if arm.animation_data else [],
        "frame30_heads": xform_summary(arm),
        "rule": "No Blender IK or manual control constraints are active. This is the clean imported DayZ helper-track state.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
