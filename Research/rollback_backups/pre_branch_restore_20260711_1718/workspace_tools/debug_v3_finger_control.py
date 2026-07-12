import json

import bpy


armature = bpy.data.objects["_DayZ_Character"]
rig = bpy.data.objects["DAT_DayZ_Arm_FK_Controls"]
scene = bpy.context.scene
scene["dayz_live_weaponik_solver_busy"] = True
source = armature.pose.bones["RightHandRing3"]
control = rig.pose.bones["IK_RightHandRing3"]
constraint = next(item for item in source.constraints if item.name.startswith("DAT_IK_AUTHOR_"))


def quat_values(quaternion):
    return [float(value) for value in quaternion]


def evaluate():
    scene.frame_set(1)
    scene.frame_set(0)
    bpy.context.view_layer.update()


constraint.influence = 1.0
evaluate()
active = {
    "source_world": quat_values(source.matrix.to_quaternion()),
    "source_basis": quat_values(source.rotation_quaternion),
    "control_world": quat_values(control.matrix.to_quaternion()),
    "control_basis": quat_values(control.rotation_quaternion),
}

author_constraints = [
    item
    for pose_bone in armature.pose.bones
    for item in pose_bone.constraints
    if item.name.startswith("DAT_IK_AUTHOR_")
]
for item in author_constraints:
    item.influence = 0.0
evaluate()
raw = {
    "source_world": quat_values(source.matrix.to_quaternion()),
    "source_basis": quat_values(source.rotation_quaternion),
}
expected_basis = control.bone.convert_local_to_pose(
    source.matrix,
    control.bone.matrix_local,
    invert=True,
)

print("FINGER_DEBUG " + json.dumps({
    "active": active,
    "raw": raw,
    "expected_control_basis": quat_values(expected_basis.to_quaternion()),
    "constraint": {
        "type": constraint.type,
        "owner_space": constraint.owner_space,
        "target_space": constraint.target_space,
        "mix_mode": getattr(constraint, "mix_mode", None),
        "use_x": getattr(constraint, "use_x", None),
        "use_y": getattr(constraint, "use_y", None),
        "use_z": getattr(constraint, "use_z", None),
    },
    "author_constraint_count": len(author_constraints),
    "armature_action_slot": getattr(armature.animation_data, "action_slot_handle", None),
    "control_action_slot": getattr(rig.animation_data, "action_slot_handle", None),
}))
