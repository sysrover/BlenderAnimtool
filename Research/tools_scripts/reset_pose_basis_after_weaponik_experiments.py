import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-reset-pose-basis-after-weaponik.json")
ARMATURE_NAME = "_DayZ_Character"


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "POSE":
        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)
        bpy.ops.object.mode_set(mode="POSE")

    reset = []
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
        reset.append(pb.name)

    scene = bpy.context.scene
    scene.frame_set(scene.frame_current)
    bpy.context.view_layer.update()

    names = [
        "LeftArm",
        "LeftForeArm",
        "LeftHand",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
        "RightHand",
        "RightHand_Dummy",
        "RightHandOrigin",
    ]
    data = {
        "frame": scene.frame_current,
        "reset_count": len(reset),
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "heads": {
            name: list(arm.pose.bones[name].head)
            for name in names
            if arm.pose.bones.get(name) is not None
        },
        "mode": "Pose basis reset; animation re-evaluated",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
