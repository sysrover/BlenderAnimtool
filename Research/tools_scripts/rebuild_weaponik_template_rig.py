import json
import os

import bpy


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-weaponik-template-rig.json"
CONTROL_COLLECTION = "DayZ WeaponIK Controls"
CONTROL_PREFIX = "WIK_"
CONTROL_CONSTRAINT_PREFIX = "DayZ WIK Control"
PREVIEW_CONSTRAINT = "DayZ WeaponIK Preview"


CONTROLS = {
    "WIK_L_Hand_Target": {
        "helper": "LeftHandIKTarget",
        "empty_type": "SPHERE",
        "display_size": 0.045,
        "copy_rotation": True,
    },
    "WIK_L_Elbow_Pole": {
        "helper": "LeftForeArmDirection",
        "empty_type": "SINGLE_ARROW",
        "display_size": 0.075,
        "copy_rotation": False,
    },
    "WIK_R_Hand_Target": {
        "helper": "RightHandOrigin",
        "empty_type": "SPHERE",
        "display_size": 0.045,
        "copy_rotation": True,
    },
    "WIK_R_Elbow_Pole": {
        "helper": "RightForeArmDirection",
        "empty_type": "SINGLE_ARROW",
        "display_size": 0.075,
        "copy_rotation": False,
    },
}


HELPER_PARENT_MAP = {
    "LeftHandIKTarget": "RightHand_Dummy",
    "LeftHandOrigin": "RightHand_Dummy",
    "LeftForeArmDirectionOrigin": "LeftHand",
    "RightForeArmDirectionOrigin": "RightHand",
    "RightHandOrigin": "RightShoulder",
    "RightForeArmDirection": "RightShoulder",
    "LeftForeArmDirection": "LeftShoulder",
}


def matrix_rows(m):
    return [list(row) for row in m]


def get_armature():
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


def ensure_collection():
    col = bpy.data.collections.get(CONTROL_COLLECTION)
    if col is None:
        col = bpy.data.collections.new(CONTROL_COLLECTION)
        bpy.context.scene.collection.children.link(col)
    return col


def link_only_to_collection(obj, col):
    if obj.name not in col.objects:
        col.objects.link(obj)
    for other in list(obj.users_collection):
        if other != col:
            other.objects.unlink(obj)


def ensure_helper_bones(arm):
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    changes = []

    if eb.get("LeftHandIKTarget") is None:
        src = eb.get("LeftHandOrigin") or eb.get("LeftHand")
        if src is None:
            raise RuntimeError("Need LeftHandOrigin or LeftHand to create LeftHandIKTarget")
        target = eb.new("LeftHandIKTarget")
        target.matrix = src.matrix.copy()
        target.length = max(src.length, 0.01)
        changes.append("created LeftHandIKTarget")

    for child_name, parent_name in HELPER_PARENT_MAP.items():
        child = eb.get(child_name)
        parent = eb.get(parent_name)
        if child is None or parent is None:
            continue
        if child.parent != parent:
            child.parent = parent
            child.use_connect = False
            changes.append(f"parented {child_name} -> {parent_name}")

    bpy.ops.object.mode_set(mode="POSE")
    return changes


def remove_old_control_objects():
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith(CONTROL_PREFIX) or obj.get("dayz_weaponik_control"):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def remove_control_constraints(arm):
    removed = []
    for pb in arm.pose.bones:
        for constraint in list(pb.constraints):
            if constraint.name.startswith(CONTROL_CONSTRAINT_PREFIX):
                removed.append(f"{pb.name}:{constraint.name}")
                pb.constraints.remove(constraint)
    return removed


def ensure_preview_ik(arm):
    def set_ik(hand_name, target_name, pole_name, pole_angle, use_tail):
        hand = arm.pose.bones.get(hand_name)
        if hand is None:
            raise RuntimeError(f"Missing {hand_name}")
        for constraint in list(hand.constraints):
            if constraint.type == "IK" and constraint.name in {
                "IK",
                "DayZ Left Hand IK",
                "DayZ Right Hand IK",
                PREVIEW_CONSTRAINT,
            }:
                hand.constraints.remove(constraint)
        constraint = hand.constraints.new(type="IK")
        constraint.name = PREVIEW_CONSTRAINT
        constraint.target = arm
        constraint.subtarget = target_name
        constraint.pole_target = arm
        constraint.pole_subtarget = pole_name
        constraint.chain_count = 5
        constraint.iterations = 500
        constraint.use_rotation = True
        constraint.use_stretch = False
        constraint.use_tail = use_tail
        constraint.pole_angle = pole_angle

    set_ik("RightHand", "RightHandOrigin", "RightForeArmDirection", 3.14159 * 45.3 / 180.0, True)
    set_ik("LeftHand", "LeftHandIKTarget", "LeftForeArmDirection", 3.14159 * -127.9 / 180.0, False)


def create_controls_from_current_helpers(arm, col):
    controls = {}
    for name, spec in CONTROLS.items():
        helper = arm.pose.bones.get(spec["helper"])
        if helper is None:
            raise RuntimeError(f"Missing helper bone {spec['helper']}")
        obj = bpy.data.objects.new(name, None)
        link_only_to_collection(obj, col)
        obj.empty_display_type = spec["empty_type"]
        obj.empty_display_size = spec["display_size"]
        obj.show_name = True
        obj.matrix_world = arm.matrix_world @ helper.matrix
        obj["dayz_weaponik_control"] = True
        obj["drives_helper_bone"] = spec["helper"]
        obj["mode_note"] = "World-space control. Use Manual Authoring mode to drive helper bones."
        controls[name] = obj
    return controls


def add_muted_manual_constraints(arm, controls):
    constraints = []
    for name, spec in CONTROLS.items():
        pb = arm.pose.bones.get(spec["helper"])
        ctrl = controls[name]
        loc = pb.constraints.new(type="COPY_LOCATION")
        loc.name = CONTROL_CONSTRAINT_PREFIX + " Copy Location"
        loc.target = ctrl
        loc.target_space = "WORLD"
        loc.owner_space = "WORLD"
        loc.influence = 1.0
        loc.mute = True
        constraints.append(f"{pb.name}:{loc.name}:muted")
        if spec.get("copy_rotation"):
            rot = pb.constraints.new(type="COPY_ROTATION")
            rot.name = CONTROL_CONSTRAINT_PREFIX + " Copy Rotation"
            rot.target = ctrl
            rot.target_space = "WORLD"
            rot.owner_space = "WORLD"
            rot.influence = 1.0
            rot.mute = True
            constraints.append(f"{pb.name}:{rot.name}:muted")
    return constraints


def set_mode_properties(arm):
    arm["dayz_weaponik_mode"] = "Imported Playback"
    arm["dayz_weaponik_modes"] = "Imported Playback: control constraints muted; Manual Authoring: unmute DayZ WIK Control constraints."


def select_controls(controls):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in controls.values():
        obj.select_set(True)
    bpy.context.view_layer.objects.active = controls["WIK_L_Hand_Target"]


def main():
    arm = get_armature()
    helper_changes = ensure_helper_bones(arm)
    removed_constraints = remove_control_constraints(arm)
    removed_objects = remove_old_control_objects()
    ensure_preview_ik(arm)
    col = ensure_collection()
    controls = create_controls_from_current_helpers(arm, col)
    manual_constraints = add_muted_manual_constraints(arm, controls)
    set_mode_properties(arm)
    bpy.context.view_layer.update()
    select_controls(controls)

    data = {
        "mode": "Imported Playback",
        "helper_changes": helper_changes,
        "removed_control_constraints": removed_constraints,
        "removed_control_objects": removed_objects,
        "manual_constraints": manual_constraints,
        "controls": {
            name: {
                "helper": spec["helper"],
                "parent": controls[name].parent.name if controls[name].parent else None,
                "matrix_world": matrix_rows(controls[name].matrix_world),
            }
            for name, spec in CONTROLS.items()
        },
        "important": [
            "Controls are world-space on purpose. Do not parent them to Weapon_Magazine/Weapon_Root; that creates an IK dependency cycle.",
            "Imported Playback mode keeps imported ANM/TXA helper tracks active.",
            "Manual Authoring mode is enabled by unmuting DayZ WIK Control constraints on helper bones.",
        ],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
