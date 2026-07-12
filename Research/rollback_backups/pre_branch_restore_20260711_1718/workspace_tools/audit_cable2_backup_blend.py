import json
import os

import bpy


def matrix_values(matrix):
    return [float(value) for row in matrix for value in row]


def action_summary(obj):
    action = obj.animation_data.action if obj and obj.animation_data else None
    if action is None:
        return None
    keyed = set()
    for curve in action.fcurves:
        marker = 'pose.bones["'
        if marker in curve.data_path:
            keyed.add(curve.data_path.split(marker, 1)[1].split('"', 1)[0])
    return {"name": action.name, "range": list(action.frame_range), "keyed_bones": sorted(keyed)}


arm = bpy.data.objects.get("_DayZ_Character")
rig = bpy.data.objects.get("DAT_DayZ_Arm_FK_Controls")
report = {
    "file": bpy.data.filepath,
    "objects": [obj.name for obj in bpy.data.objects],
    "arm_action": action_summary(arm),
    "rig_action": action_summary(rig),
    "arm": {},
    "rig": {},
}
if arm:
    for name in (
        "RightHand",
        "RightHandOrigin",
        "RightForeArmDirectionOrigin",
        "RightForeArmDirection",
        "RightHand_Dummy",
    ):
        bone = arm.pose.bones.get(name)
        if bone:
            report["arm"][name] = matrix_values(bone.matrix)
    report["finger_matrices"] = {
        bone.name: matrix_values(bone.matrix)
        for bone in arm.pose.bones
        if bone.name.startswith("RightHand")
        and bone.name not in {"RightHand", "RightHandOrigin", "RightHand_Dummy"}
    }
if rig:
    for name in (
        "CTRL_RightHand",
        "CTRL_RightElbow",
        "IK_RightHandOrigin.R",
        "IK_RightElbowOrigin.R",
        "IK_RightElbow.R",
        "IK_RightHandDummy.R",
    ):
        bone = rig.pose.bones.get(name)
        if bone:
            report["rig"][name] = matrix_values(bone.matrix)
output = r"P:\BlenderAnimtool\Research\anm_reports\cable2-backup-authored-pose-20260711.json"
os.makedirs(os.path.dirname(output), exist_ok=True)
with open(output, "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
print("CABLE2_BACKUP_AUDIT=" + json.dumps(report))
