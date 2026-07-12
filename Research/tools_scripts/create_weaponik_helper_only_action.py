import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-weaponik-helper-only-action.json")
ARMATURE_NAME = "_DayZ_Character"
SOURCE_ACTION = "aks74u"
HELPER_ACTION = "aks74u_helpers_only"

HELPER_BONES = {
    "RightHandOrigin",
    "RightForeArmDirectionOrigin",
    "RightForeArmDirection",
    "LeftHandOrigin",
    "LeftHandIKTarget",
    "LeftForeArmDirectionOrigin",
    "LeftForeArmDirection",
    "RightHand_Dummy",
    "LeftHand_Dummy",
}


def fcurve_bone_name(fc):
    path = fc.data_path
    prefix = 'pose.bones["'
    if not path.startswith(prefix):
        return None
    rest = path[len(prefix):]
    return rest.split('"]', 1)[0]


def copy_fcurve(src, dst_action):
    dst = dst_action.fcurves.new(src.data_path, index=src.array_index, action_group=src.group.name if src.group else None)
    dst.color_mode = src.color_mode
    dst.extrapolation = src.extrapolation
    dst.keyframe_points.add(len(src.keyframe_points))
    for i, src_kp in enumerate(src.keyframe_points):
        dst_kp = dst.keyframe_points[i]
        dst_kp.co = src_kp.co
        dst_kp.interpolation = src_kp.interpolation
        dst_kp.easing = src_kp.easing
        dst_kp.handle_left_type = src_kp.handle_left_type
        dst_kp.handle_right_type = src_kp.handle_right_type
        dst_kp.handle_left = src_kp.handle_left
        dst_kp.handle_right = src_kp.handle_right
    dst.update()
    return dst


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    src = bpy.data.actions.get(SOURCE_ACTION)
    if src is None:
        raise RuntimeError(f"Source action {SOURCE_ACTION!r} not found")

    old = bpy.data.actions.get(HELPER_ACTION)
    if old is not None:
        bpy.data.actions.remove(old)
    dst = bpy.data.actions.new(HELPER_ACTION)
    dst.use_fake_user = True

    copied = []
    skipped = []
    for fc in src.fcurves:
        bone = fcurve_bone_name(fc)
        if bone in HELPER_BONES:
            copy_fcurve(fc, dst)
            copied.append(f"{bone}:{fc.data_path}[{fc.array_index}]")
        else:
            skipped.append(bone or fc.data_path)

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = dst
    arm["dayz_weaponik_mode"] = "FullBody + Helper Tracks Only"

    # Make sure no preview/manual constraints are active.
    removed_constraints = []
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DayZ WIK Control") or c.name == "DayZ WeaponIK Preview":
                removed_constraints.append(f"{pb.name}:{c.name}")
                pb.constraints.remove(c)

    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()

    data = {
        "mode": arm["dayz_weaponik_mode"],
        "source": SOURCE_ACTION,
        "created": HELPER_ACTION,
        "copied_fcurves": len(copied),
        "copied_bones": sorted({item.split(":", 1)[0] for item in copied}),
        "skipped_unique": sorted({x for x in skipped if x})[:200],
        "removed_constraints": removed_constraints,
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
        "note": "Finger tracks are excluded to avoid spaghetti hands while debugging DayZ WeaponIK helper/solver preview.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
