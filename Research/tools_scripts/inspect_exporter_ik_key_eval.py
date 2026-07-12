import importlib
import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "exporter-ik-key-eval.json")
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"
NAMES = [
    "LeftHandIKTarget",
    "LeftHandOrigin",
    "RightHandOrigin",
    "LeftForeArmDirection",
    "RightForeArmDirection",
]


class DummySelf:
    eAnimType = "IK2H"
    fUnitScale = 1.0


def main():
    import DayzAnimationToolsBinary.Export.ExportAnm as ExportAnm
    ExportAnm = importlib.reload(ExportAnm)
    ExportAnm.g_scale = 1.0

    arm = bpy.data.objects.get(ARMATURE_NAME)
    action = bpy.data.actions.get(ACTION_NAME)
    if arm is None or action is None:
        raise RuntimeError("Missing armature/action")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action

    data = {}
    for frame in (0, 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        data[str(frame)] = {}
        for name in NAMES:
            pb = arm.pose.bones.get(name)
            if pb is None:
                data[str(frame)][name] = None
                continue
            loc = ExportAnm.GetBoneLocation(pb, "IK2H")
            rot = ExportAnm.GetBoneRotation(pb, "IK2H")
            data[str(frame)][name] = {
                "export_loc": [float(loc.x), float(loc.y), float(loc.z)],
                "export_rot_key": [float(-rot.x), float(-rot.y), float(-rot.z), float(rot.w)],
                "pose_location": [float(pb.location.x), float(pb.location.y), float(pb.location.z)],
                "pose_rotation_quaternion": [float(x) for x in pb.rotation_quaternion],
                "should_skip": bool(ExportAnm.ShouldSkipBone(pb.bone, DummySelf())),
            }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
