import importlib
import os
from types import SimpleNamespace

import bpy


ARMATURE_NAME = "_DayZ_Character"
AKS74U_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-ak-import-diagnostic-repaired.json"


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


def ensure_helper_hierarchy(arm):
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones

    if eb.get("LeftHandIKTarget") is None:
        src = eb.get("LeftHandOrigin") or eb.get("LeftHand")
        if src is None:
            raise RuntimeError("Need LeftHandOrigin or LeftHand to create LeftHandIKTarget")
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
        if child is None:
            changes.append(f"missing {child_name}")
            continue
        if parent is None:
            changes.append(f"missing parent {parent_name} for {child_name}")
            continue
        if child.parent != parent:
            child.parent = parent
            child.use_connect = False
            changes.append(f"parented {child_name} -> {parent_name}")

    bpy.ops.object.mode_set(mode="POSE")
    return changes


def ensure_preview_constraints(arm):
    pb = arm.pose.bones

    def set_ik(hand_name, target_name, pole_name, pole_angle, use_tail=True):
        hand = pb.get(hand_name)
        if hand is None:
            raise RuntimeError(f"Missing {hand_name}")
        for constraint in list(hand.constraints):
            if constraint.type == "IK" and constraint.name in {
                "IK",
                "DayZ Left Hand IK",
                "DayZ Right Hand IK",
                "DayZ WeaponIK Preview",
            }:
                hand.constraints.remove(constraint)
        constraint = hand.constraints.new(type="IK")
        constraint.name = "DayZ WeaponIK Preview"
        constraint.target = arm
        constraint.subtarget = target_name
        constraint.pole_target = arm
        constraint.pole_subtarget = pole_name
        constraint.chain_count = 5
        constraint.use_rotation = True
        constraint.use_stretch = False
        constraint.use_tail = use_tail
        constraint.pole_angle = pole_angle

    set_ik("RightHand", "RightHandOrigin", "RightForeArmDirection", 3.14159 * 45.3 / 180.0)
    set_ik("LeftHand", "LeftHandIKTarget", "LeftForeArmDirection", 3.14159 * -127.9 / 180.0, use_tail=False)


def reload_aks74u_action(arm):
    if not os.path.exists(AKS74U_ANM):
        raise RuntimeError(f"ANM not found: {AKS74U_ANM}")

    if arm.animation_data is None:
        arm.animation_data_create()

    if arm.animation_data.action and arm.animation_data.action.name == "aks74u":
        arm.animation_data.action = None

    for action in list(bpy.data.actions):
        if action.name == "aks74u":
            bpy.data.actions.remove(action)

    import DayzAnimationToolsBinary.Import.ImportAnm as ImportAnm
    ImportAnm = importlib.reload(ImportAnm)

    dummy_self = SimpleNamespace(
        filepath=AKS74U_ANM,
        files=[SimpleNamespace(name=os.path.basename(AKS74U_ANM))],
    )
    result = ImportAnm.load(dummy_self, bpy.context, ImportAnm.AnmImportSettings())
    if result:
        raise RuntimeError(result)

    if arm.animation_data:
        for track in arm.animation_data.nla_tracks:
            track.mute = False
            for strip in track.strips:
                strip.mute = False
                strip.influence = 1.0


def world_translation(obj, pose_bone_name):
    pb = obj.pose.bones[pose_bone_name]
    return list((obj.matrix_world @ pb.matrix).translation)


def dump_state(arm):
    scene = bpy.context.scene
    frames = [0, 1, 10, 30]
    bones = [
        "RightHand",
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightHand_Dummy",
        "Weapon_Root",
        "LeftHand",
        "LeftHandOrigin",
        "LeftHandIKTarget",
        "LeftForeArmDirection",
    ]
    data = {
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "nla": [],
        "frames": {},
    }
    if arm.animation_data:
        for track in arm.animation_data.nla_tracks:
            for strip in track.strips:
                data["nla"].append({
                    "track": track.name,
                    "strip": strip.name,
                    "action": strip.action.name if strip.action else None,
                    "influence": strip.influence,
                    "mute": strip.mute,
                    "track_mute": track.mute,
                })
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        data["frames"][str(frame)] = {
            name: world_translation(arm, name)
            for name in bones
            if arm.pose.bones.get(name) is not None
        }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, indent=2)
    return data


def main():
    arm = ensure_active_armature()
    hierarchy_changes = ensure_helper_hierarchy(arm)
    ensure_preview_constraints(arm)
    reload_aks74u_action(arm)
    data = dump_state(arm)
    return {"hierarchy_changes": hierarchy_changes, "diagnostic": OUT, "state": data}


RESULT = main()
