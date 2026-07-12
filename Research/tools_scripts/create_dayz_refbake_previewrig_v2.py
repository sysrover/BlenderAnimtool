import json
import os

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_previewrig_v2.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-refbake-previewrig-v2-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREVIEW_ARMATURE = "DAT_PreviewSkeleton"
PREVIEW_MESH_PREFIX = "DAT_PreviewMesh_"
HANDLER_NAME = "dat_preview_offset_follow_v2"


DRIVER_MAPPING = {
    "LeftArm": "MCH_UpperArm.L",
    "LeftArmRoll": "MCH_UpperArm.L",
    "LeftForeArm": "MCH_ForeArm.L",
    "LeftForeArmRoll": "MCH_ForeArm.L",
    "LeftHand": "MCH_Hand.L",
    "RightArm": "MCH_UpperArm.R",
    "RightArmRoll": "MCH_UpperArm.R",
    "RightForeArm": "MCH_ForeArm.R",
    "RightForeArmRoll": "MCH_ForeArm.R",
    "RightHand": "MCH_Hand.R",
}


def rows(matrix):
    return [list(row) for row in matrix]


def remove_handler():
    removed = 0
    for handlers in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
        for handler in list(handlers):
            if getattr(handler, "__name__", "") == HANDLER_NAME:
                handlers.remove(handler)
                removed += 1
    return removed


def remove_old_preview():
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name == PREVIEW_ARMATURE or obj.name.startswith(PREVIEW_MESH_PREFIX):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def clear_control_transforms(rig_obj):
    for name in ("CTRL_Hand.L", "CTRL_Elbow.L", "CTRL_Hand.R", "CTRL_Elbow.R"):
        pb = rig_obj.pose.bones.get(name)
        if not pb:
            continue
        pb.location = (0, 0, 0)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


def create_preview_armature(export_obj):
    data = export_obj.data.copy()
    data.name = PREVIEW_ARMATURE + "_Data"
    preview = bpy.data.objects.new(PREVIEW_ARMATURE, data)
    bpy.context.collection.objects.link(preview)
    preview.matrix_world = export_obj.matrix_world.copy()
    preview.show_in_front = False
    preview.hide_select = True
    preview.hide_set(True)
    data.show_names = False
    data.display_type = "STICK"
    bpy.context.view_layer.update()
    for pb in preview.pose.bones:
        src = export_obj.pose.bones.get(pb.name)
        if src:
            pb.matrix_basis = src.matrix_basis.copy()
    return preview


def create_preview_meshes(export_obj, preview_obj):
    created = []
    hidden_originals = []
    for obj in list(bpy.data.objects):
        if obj.type != "MESH" or obj.name.startswith(PREVIEW_MESH_PREFIX):
            continue
        armature_mods = [m for m in obj.modifiers if m.type == "ARMATURE" and m.object == export_obj]
        if not armature_mods:
            continue
        dup = obj.copy()
        dup.data = obj.data
        dup.animation_data_clear()
        dup.name = PREVIEW_MESH_PREFIX + obj.name
        bpy.context.collection.objects.link(dup)
        dup.matrix_world = obj.matrix_world.copy()
        for mod in dup.modifiers:
            if mod.type == "ARMATURE" and mod.object == export_obj:
                mod.object = preview_obj
        dup.hide_set(False)
        dup.hide_select = True
        obj.hide_set(True)
        obj.hide_select = True
        created.append(dup.name)
        hidden_originals.append(obj.name)
    return created, hidden_originals


def compute_offsets(target_obj, rig_obj):
    offsets = {}
    bpy.context.view_layer.update()
    for target_bone, driver_bone in DRIVER_MAPPING.items():
        target_pb = target_obj.pose.bones.get(target_bone)
        driver_pb = rig_obj.pose.bones.get(driver_bone)
        if not target_pb or not driver_pb:
            continue
        target_world = target_obj.matrix_world @ target_pb.matrix
        driver_world = rig_obj.matrix_world @ driver_pb.matrix
        offsets[target_bone] = {
            "driver_bone": driver_bone,
            "offset": rows(target_world @ driver_world.inverted()),
        }
    rig_obj["dat_preview_offsets_json"] = json.dumps(offsets)
    return offsets


def apply_offsets_to_armature(target_obj, rig_obj):
    offsets = json.loads(rig_obj.get("dat_preview_offsets_json", "{}"))
    target_inv = target_obj.matrix_world.inverted()
    for target_bone, info in offsets.items():
        pb = target_obj.pose.bones.get(target_bone)
        driver_pb = rig_obj.pose.bones.get(info["driver_bone"])
        if not pb or not driver_pb:
            continue
        driver_world = rig_obj.matrix_world @ driver_pb.matrix
        pb.matrix = target_inv @ (Matrix(info["offset"]) @ driver_world)


@persistent
def dat_preview_offset_follow_v2(scene, depsgraph=None):
    if getattr(bpy.types.Scene, "_dat_preview_offset_follow_guard", False):
        return
    bpy.types.Scene._dat_preview_offset_follow_guard = True
    try:
        rig_obj = bpy.data.objects.get(CONTROL_RIG)
        preview_obj = bpy.data.objects.get(PREVIEW_ARMATURE)
        if rig_obj and preview_obj and bool(rig_obj.get("dat_preview_live_enabled", True)):
            apply_offsets_to_armature(preview_obj, rig_obj)
    finally:
        bpy.types.Scene._dat_preview_offset_follow_guard = False


def add_helper_text():
    text = bpy.data.texts.get("DAT_PREVIEW_BAKE_HELPERS") or bpy.data.texts.new("DAT_PREVIEW_BAKE_HELPERS")
    text.clear()
    text.write(
        """# DAT_PREVIEW_BAKE_HELPERS
import json
import bpy
from mathutils import Matrix

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREVIEW_ARMATURE = "DAT_PreviewSkeleton"


def _apply_offsets(target_obj):
    rig_obj = bpy.data.objects[CONTROL_RIG]
    offsets = json.loads(rig_obj["dat_preview_offsets_json"])
    target_inv = target_obj.matrix_world.inverted()
    for target_bone, info in offsets.items():
        pb = target_obj.pose.bones.get(target_bone)
        driver_pb = rig_obj.pose.bones.get(info["driver_bone"])
        if pb and driver_pb:
            pb.matrix = target_inv @ (Matrix(info["offset"]) @ (rig_obj.matrix_world @ driver_pb.matrix))


def apply_controls_to_preview():
    _apply_offsets(bpy.data.objects[PREVIEW_ARMATURE])
    bpy.context.view_layer.update()


def apply_controls_to_export_once():
    _apply_offsets(bpy.data.objects[EXPORT_ARMATURE])
    bpy.context.view_layer.update()


def bake_controls_to_export_frame(frame=None):
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    export_obj = bpy.data.objects[EXPORT_ARMATURE]
    apply_controls_to_export_once()
    for name in json.loads(bpy.data.objects[CONTROL_RIG]["dat_preview_offsets_json"]).keys():
        pb = export_obj.pose.bones[name]
        pb.keyframe_insert("location")
        if pb.rotation_mode == "QUATERNION":
            pb.keyframe_insert("rotation_quaternion")
        elif pb.rotation_mode == "AXIS_ANGLE":
            pb.keyframe_insert("rotation_axis_angle")
        else:
            pb.keyframe_insert("rotation_euler")


def bake_controls_to_export_range(start=None, end=None):
    scene = bpy.context.scene
    if start is None:
        start = scene.frame_start
    if end is None:
        end = scene.frame_end
    original = scene.frame_current
    for frame in range(int(start), int(end) + 1):
        bake_controls_to_export_frame(frame)
    scene.frame_set(original)


# Move CTRL_Hand/CTRL_Elbow bones for live preview.
# Use apply_controls_to_export_once() or bake_controls_to_export_frame/range()
# when the preview pose is correct and you want to write it to _DayZ_Character.
"""
    )
    return text.name


def install_handler():
    remove_handler()
    bpy.app.handlers.depsgraph_update_post.append(dat_preview_offset_follow_v2)
    bpy.app.handlers.frame_change_post.append(dat_preview_offset_follow_v2)


def set_view(export_obj, rig_obj, preview_obj):
    export_obj.hide_set(True)
    export_obj.hide_select = True
    export_obj.show_in_front = False
    export_obj.data.show_names = False
    preview_obj.hide_set(True)
    preview_obj.hide_select = True
    if rig_obj:
        rig_obj.hide_set(False)
        rig_obj.hide_select = False
        rig_obj.show_in_front = True
        rig_obj.data.show_names = True
        for bone in rig_obj.data.bones:
            bone.hide = not bone.name.startswith("CTRL_")
        bpy.context.view_layer.objects.active = rig_obj
        for obj in bpy.context.scene.objects:
            obj.select_set(False)
        rig_obj.select_set(True)


def main():
    export_obj = bpy.data.objects.get(EXPORT_ARMATURE)
    rig_obj = bpy.data.objects.get(CONTROL_RIG)
    if not export_obj:
        raise RuntimeError(f"Missing {EXPORT_ARMATURE}")
    if not rig_obj:
        raise RuntimeError(f"Missing {CONTROL_RIG}; run create_dayz_refbake_controlrig_v1.py first")

    removed_handlers = remove_handler()
    removed_preview = remove_old_preview()
    clear_control_transforms(rig_obj)
    bpy.context.view_layer.update()

    preview_obj = create_preview_armature(export_obj)
    preview_meshes, hidden_originals = create_preview_meshes(export_obj, preview_obj)
    offsets = compute_offsets(preview_obj, rig_obj)
    rig_obj["dat_preview_live_enabled"] = True
    add_helper_text()
    install_handler()
    apply_offsets_to_armature(preview_obj, rig_obj)
    set_view(export_obj, rig_obj, preview_obj)
    bpy.context.view_layer.update()

    result = {
        "source_file": bpy.data.filepath,
        "saved_blend": OUT_BLEND,
        "removed_handlers": removed_handlers,
        "removed_preview": removed_preview,
        "preview_armature": PREVIEW_ARMATURE,
        "preview_meshes": preview_meshes,
        "hidden_original_meshes": hidden_originals,
        "driven_bones": list(offsets.keys()),
        "visible_control_bones": [b.name for b in rig_obj.data.bones if not b.hide],
        "live_preview_enabled": bool(rig_obj.get("dat_preview_live_enabled", False)),
        "helper_text": "DAT_PREVIEW_BAKE_HELPERS",
    }

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    return result


RESULT = main()
