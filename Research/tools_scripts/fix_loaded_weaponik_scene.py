import bpy


ARMATURE_NAME = "_DayZ_Character"


def fix_weaponik_scene():
    result = {"changes": [], "warnings": []}
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm

    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones

    if eb.get("LeftHandIKTarget") is None:
        src = eb.get("LeftHandOrigin") or eb.get("LeftHand")
        if src is None:
            raise RuntimeError("Need LeftHandOrigin or LeftHand to create LeftHandIKTarget")
        target = eb.new("LeftHandIKTarget")
        target.matrix = src.matrix.copy()
        target.length = max(src.length, 0.01)
        result["changes"].append(f"created LeftHandIKTarget from {src.name}")

    parent_map = {
        "LeftHandIKTarget": "RightHand_Dummy",
        "LeftHandOrigin": "RightHand_Dummy",
        "LeftForeArmDirectionOrigin": "LeftHand",
        "RightForeArmDirectionOrigin": "RightHand",
        "RightHandOrigin": "RightShoulder",
        "RightForeArmDirection": "RightShoulder",
        "LeftForeArmDirection": "LeftShoulder",
    }
    for child_name, parent_name in parent_map.items():
        child = eb.get(child_name)
        parent = eb.get(parent_name)
        if child is None:
            result["warnings"].append(f"missing helper {child_name}")
            continue
        if parent is None:
            result["warnings"].append(f"missing parent {parent_name} for {child_name}")
            continue
        if child.parent != parent:
            child.parent = parent
            child.use_connect = False
            result["changes"].append(f"parented {child_name} -> {parent_name}")

    bpy.ops.object.mode_set(mode="POSE")
    pb = arm.pose.bones
    required = (
        "RightHand",
        "RightHandOrigin",
        "RightForeArmDirection",
        "LeftHand",
        "LeftHandIKTarget",
        "LeftForeArmDirection",
    )
    missing = [name for name in required if pb.get(name) is None]
    if missing:
        raise RuntimeError("Missing required pose bones after edit: " + ", ".join(missing))

    def ensure_preview(hand_name, target_name, pole_name, pole_angle, use_tail=True):
        hand = pb[hand_name]
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
        result["changes"].append(f"set {hand_name} IK target={target_name} pole={pole_name}")

    ensure_preview("RightHand", "RightHandOrigin", "RightForeArmDirection", 3.14159 * 45.3 / 180.0)
    ensure_preview("LeftHand", "LeftHandIKTarget", "LeftForeArmDirection", 3.14159 * -127.9 / 180.0, use_tail=False)

    bpy.ops.object.mode_set(mode="OBJECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.context.view_layer.update()
    return result


RESULT = fix_weaponik_scene()
print("CODEX_WEAPONIK_SCENE_FIX_OK", RESULT)
