import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-arm-authoring-view.json")
ARMATURE_NAME = "_DayZ_Character"


VISIBLE_EXACT = {
    "LeftShoulder",
    "LeftArm",
    "LeftForeArm",
    "LeftHand",
    "RightShoulder",
    "RightArm",
    "RightForeArm",
    "RightHand",
    "LeftHandIK",
    "LeftHandOrigin",
    "LeftHandIKTarget",
    "LeftHand_Dummy",
    "LeftForeArmDirection",
    "LeftForeArmDirectionOrigin",
    "RightHandIK",
    "RightHandOrigin",
    "RightHand_Dummy",
    "RightForeArmDirection",
    "RightForeArmDirectionOrigin",
}

VISIBLE_PREFIXES = (
    # Keep weapon attach bones because arm/hand controls are authored against weapon space.
    "Weapon_",
)

HIDE_PREFIXES = (
    "LeftHandThumb",
    "LeftHandIndex",
    "LeftHandMiddle",
    "LeftHandRing",
    "LeftHandPinky",
    "RightHandThumb",
    "RightHandIndex",
    "RightHandMiddle",
    "RightHandRing",
    "RightHandPinky",
)


def should_show_bone(name):
    if name in VISIBLE_EXACT:
        return True
    if any(name.startswith(prefix) for prefix in VISIBLE_PREFIXES):
        return True
    # Fingers remain animated/exportable, but hidden in the clean arm-control view.
    if any(name.startswith(prefix) for prefix in HIDE_PREFIXES):
        return False
    return False


def main():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    hidden_shape_objects = []
    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_") or (obj.parent and obj.parent.name == "BoneShapes"):
            obj.hide_set(True)
            obj.hide_viewport = True
            hidden_shape_objects.append(obj.name)

    coll = bpy.data.collections.get("BoneShapes")
    if coll is not None:
        coll.hide_viewport = True

    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")

    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    arm.show_in_front = True
    arm.data.display_type = "BBONE"

    visible_bones = []
    hidden_bones = []
    for bone in arm.data.bones:
        show = should_show_bone(bone.name)
        bone.hide = not show
        bone.select = False
        if show:
            visible_bones.append(bone.name)
        else:
            hidden_bones.append(bone.name)

    for name in VISIBLE_EXACT:
        pb = arm.pose.bones.get(name)
        if pb:
            pb.bone.select = True
    if arm.data.bones.get("LeftHandIKTarget"):
        arm.data.bones.active = arm.data.bones["LeftHandIKTarget"]
    elif arm.data.bones.get("LeftHand"):
        arm.data.bones.active = arm.data.bones["LeftHand"]

    bpy.ops.object.mode_set(mode="POSE")
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

    save_path = r"P:\Animation_Weapon\Weapon_template_arm_authoring_view.blend"
    bpy.ops.wm.save_as_mainfile(filepath=save_path)

    data = {
        "file_saved_as": save_path,
        "hidden_shape_collection": coll is not None,
        "hidden_shape_objects_count": len(hidden_shape_objects),
        "visible_bones_count": len(visible_bones),
        "hidden_bones_count": len(hidden_bones),
        "visible_bones": sorted(visible_bones),
        "note": "Viewport-only arm authoring preset. Hidden bones are not removed and still exist for import/export.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
