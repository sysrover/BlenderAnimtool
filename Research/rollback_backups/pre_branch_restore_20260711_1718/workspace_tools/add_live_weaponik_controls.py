import json
import os

import bpy
from mathutils import Matrix


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-weaponik-controls.json"


CONTROL_SPECS = {
    "WIK_L_Hand_Target": {
        "bone": "LeftHandIKTarget",
        "copy_to": "LeftHandIKTarget",
        "parent_bone": "Weapon_Magazine",
        "empty_type": "SPHERE",
        "display_size": 0.045,
        "copy_rotation": True,
    },
    "WIK_L_Elbow_Pole": {
        "bone": "LeftForeArmDirection",
        "copy_to": "LeftForeArmDirection",
        "parent_bone": None,
        "empty_type": "SINGLE_ARROW",
        "display_size": 0.075,
        "copy_rotation": False,
    },
    "WIK_R_Hand_Target": {
        "bone": "RightHandOrigin",
        "copy_to": "RightHandOrigin",
        "parent_bone": None,
        "empty_type": "SPHERE",
        "display_size": 0.045,
        "copy_rotation": True,
    },
    "WIK_R_Elbow_Pole": {
        "bone": "RightForeArmDirection",
        "copy_to": "RightForeArmDirection",
        "parent_bone": None,
        "empty_type": "SINGLE_ARROW",
        "display_size": 0.075,
        "copy_rotation": False,
    },
}


def world_matrix_of_pose_bone(arm, bone_name):
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {bone_name}")
    return arm.matrix_world @ pb.matrix


def ensure_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def link_to_collection(obj, col):
    if obj.name not in col.objects:
        col.objects.link(obj)
    for other in list(obj.users_collection):
        if other != col:
            try:
                other.objects.unlink(obj)
            except RuntimeError:
                pass


def create_or_update_empty(arm, col, name, spec):
    source_matrix = world_matrix_of_pose_bone(arm, spec["bone"])
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
    link_to_collection(obj, col)

    obj.empty_display_type = spec["empty_type"]
    obj.empty_display_size = spec["display_size"]
    obj.show_name = True
    obj["dayz_weaponik_control"] = True
    obj["drives_helper_bone"] = spec["copy_to"]

    # Preserve the current imported helper transform when parenting the control.
    obj.parent = None
    obj.matrix_world = source_matrix
    parent_bone = spec.get("parent_bone")
    if parent_bone:
        if arm.pose.bones.get(parent_bone) is None:
            raise RuntimeError(f"Missing parent bone {parent_bone} for {name}")
        mw = obj.matrix_world.copy()
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = parent_bone
        obj.matrix_world = mw

    return obj


def remove_named_constraints(pb, prefix):
    for constraint in list(pb.constraints):
        if constraint.name.startswith(prefix):
            pb.constraints.remove(constraint)


def constrain_helper_to_control(arm, helper_name, control, copy_rotation):
    pb = arm.pose.bones.get(helper_name)
    if pb is None:
        raise RuntimeError(f"Missing helper pose bone {helper_name}")

    remove_named_constraints(pb, "DayZ WIK Control")

    loc = pb.constraints.new(type="COPY_LOCATION")
    loc.name = "DayZ WIK Control Copy Location"
    loc.target = control
    loc.target_space = "WORLD"
    loc.owner_space = "WORLD"
    loc.influence = 1.0

    if copy_rotation:
        rot = pb.constraints.new(type="COPY_ROTATION")
        rot.name = "DayZ WIK Control Copy Rotation"
        rot.target = control
        rot.target_space = "WORLD"
        rot.owner_space = "WORLD"
        rot.influence = 1.0


def ensure_hand_ik_constraint(arm, hand_name, target_name, pole_name, pole_angle, use_tail):
    hand = arm.pose.bones.get(hand_name)
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
    constraint.iterations = 500
    constraint.pole_angle = pole_angle


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    col = ensure_collection("DayZ WeaponIK Controls")
    controls = {}
    for name, spec in CONTROL_SPECS.items():
        controls[name] = create_or_update_empty(arm, col, name, spec)

    bpy.ops.object.mode_set(mode="POSE")
    for name, spec in CONTROL_SPECS.items():
        constrain_helper_to_control(
            arm,
            spec["copy_to"],
            controls[name],
            spec.get("copy_rotation", False),
        )

    ensure_hand_ik_constraint(
        arm,
        "RightHand",
        "RightHandOrigin",
        "RightForeArmDirection",
        3.14159 * 45.3 / 180.0,
        use_tail=True,
    )
    ensure_hand_ik_constraint(
        arm,
        "LeftHand",
        "LeftHandIKTarget",
        "LeftForeArmDirection",
        3.14159 * -127.9 / 180.0,
        use_tail=False,
    )

    bpy.context.view_layer.update()

    data = {
        "controls": {
            name: {
                "helper": spec["copy_to"],
                "parent": controls[name].parent.name if controls[name].parent else None,
                "parent_bone": controls[name].parent_bone if controls[name].parent_bone else None,
                "matrix_world": [list(row) for row in controls[name].matrix_world],
            }
            for name, spec in CONTROL_SPECS.items()
        },
        "usage": [
            "Move WIK_L_Hand_Target to place the left hand on the weapon.",
            "Move WIK_L_Elbow_Pole to control left elbow direction.",
            "Move WIK_R_Hand_Target to adjust the right-hand weapon anchor.",
            "Move WIK_R_Elbow_Pole to control right elbow direction.",
        ],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
