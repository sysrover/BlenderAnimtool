import json
import os

import bpy
from mathutils import Matrix


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BASE_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_controlrig_v1.blend"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_previewrig_v3_manual.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-refbake-previewrig-v3-manual-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREVIEW_ARMATURE = "DAT_PreviewSkeleton"
PREVIEW_MESH = "DAT_PreviewMesh_Female_body"
PREVIEW_PREFIX = "DAT_PreviewMesh_"

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


def rows(m):
    return [list(row) for row in m]


def remove_handlers():
    removed = []
    for handlers in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
        for handler in list(handlers):
            name = getattr(handler, "__name__", "")
            if name in {"dat_preview_offset_follow_v2", "dat_refbake_live_follow_v1"}:
                handlers.remove(handler)
                removed.append(name)
    return removed


def clean_preview_objects():
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name == PREVIEW_ARMATURE or obj.name.startswith(PREVIEW_PREFIX):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def reset_controls(rig):
    for name in ("CTRL_Hand.L", "CTRL_Elbow.L", "CTRL_Hand.R", "CTRL_Elbow.R"):
        pb = rig.pose.bones.get(name)
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
    preview.hide_set(True)
    preview.hide_select = True
    preview.show_in_front = False
    preview.data.show_names = False
    bpy.context.view_layer.update()
    for pb in preview.pose.bones:
        src = export_obj.pose.bones.get(pb.name)
        if src:
            pb.matrix_basis = src.matrix_basis.copy()
    return preview


def create_one_preview_mesh(export_obj, preview_obj):
    source = bpy.data.objects.get("Female_body")
    if not source:
        raise RuntimeError("Missing Female_body preview source")
    dup = source.copy()
    dup.data = source.data
    dup.animation_data_clear()
    dup.name = PREVIEW_MESH
    bpy.context.collection.objects.link(dup)
    dup.matrix_world = source.matrix_world.copy()
    for mod in dup.modifiers:
        if mod.type == "ARMATURE" and mod.object == export_obj:
            mod.object = preview_obj
    dup.hide_set(False)
    dup.hide_select = True
    return dup.name


def compute_offsets(target_obj, rig):
    bpy.context.view_layer.update()
    offsets = {}
    for target_bone, driver_bone in DRIVER_MAPPING.items():
        target_pb = target_obj.pose.bones.get(target_bone)
        driver_pb = rig.pose.bones.get(driver_bone)
        if not target_pb or not driver_pb:
            continue
        target_world = target_obj.matrix_world @ target_pb.matrix
        driver_world = rig.matrix_world @ driver_pb.matrix
        offsets[target_bone] = {
            "driver_bone": driver_bone,
            "offset": rows(target_world @ driver_world.inverted()),
        }
    rig["dat_preview_offsets_json"] = json.dumps(offsets)
    return offsets


def apply_offsets(target_obj, rig):
    offsets = json.loads(rig["dat_preview_offsets_json"])
    target_inv = target_obj.matrix_world.inverted()
    for target_bone, info in offsets.items():
        pb = target_obj.pose.bones.get(target_bone)
        driver_pb = rig.pose.bones.get(info["driver_bone"])
        if not pb or not driver_pb:
            continue
        pb.matrix = target_inv @ (Matrix(info["offset"]) @ (rig.matrix_world @ driver_pb.matrix))


def hide_non_authoring_scene(export_obj, rig, preview_obj):
    export_obj.hide_set(True)
    export_obj.hide_select = True
    preview_obj.hide_set(True)
    preview_obj.hide_select = True
    rig.hide_set(False)
    rig.hide_select = False
    rig.show_in_front = True
    rig.data.show_names = True
    for bone in rig.data.bones:
        bone.hide = not bone.name.startswith("CTRL_")

    for obj in bpy.data.objects:
        if obj.name == PREVIEW_MESH:
            obj.hide_set(False)
            obj.hide_select = True
        elif obj.name in {"Female_body", "zMale_body", "zEntityPosition"}:
            obj.hide_set(True)
            obj.hide_select = True
        elif obj.name.startswith(PREVIEW_PREFIX) and obj.name != PREVIEW_MESH:
            obj.hide_set(True)

    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig


def add_helper_text():
    text = bpy.data.texts.get("DAT_MANUAL_PREVIEW_BAKE") or bpy.data.texts.new("DAT_MANUAL_PREVIEW_BAKE")
    text.clear()
    text.write(
        """# DAT_MANUAL_PREVIEW_BAKE
# This version is intentionally manual: no depsgraph live handler.
# Move CTRL_Hand/CTRL_Elbow, then run preview_once().
# When it looks correct, run apply_export_once() or bake_export_range().
import json
import bpy
from mathutils import Matrix

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREVIEW_ARMATURE = "DAT_PreviewSkeleton"


def _apply_offsets(target_obj):
    rig = bpy.data.objects[CONTROL_RIG]
    offsets = json.loads(rig["dat_preview_offsets_json"])
    target_inv = target_obj.matrix_world.inverted()
    for target_bone, info in offsets.items():
        pb = target_obj.pose.bones.get(target_bone)
        driver_pb = rig.pose.bones.get(info["driver_bone"])
        if pb and driver_pb:
            pb.matrix = target_inv @ (Matrix(info["offset"]) @ (rig.matrix_world @ driver_pb.matrix))
    bpy.context.view_layer.update()


def preview_once():
    _apply_offsets(bpy.data.objects[PREVIEW_ARMATURE])


def apply_export_once():
    _apply_offsets(bpy.data.objects[EXPORT_ARMATURE])


def bake_export_frame(frame=None):
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    export_obj = bpy.data.objects[EXPORT_ARMATURE]
    apply_export_once()
    for name in json.loads(bpy.data.objects[CONTROL_RIG]["dat_preview_offsets_json"]).keys():
        pb = export_obj.pose.bones[name]
        pb.keyframe_insert("location")
        if pb.rotation_mode == "QUATERNION":
            pb.keyframe_insert("rotation_quaternion")
        elif pb.rotation_mode == "AXIS_ANGLE":
            pb.keyframe_insert("rotation_axis_angle")
        else:
            pb.keyframe_insert("rotation_euler")


def bake_export_range(start=None, end=None):
    scene = bpy.context.scene
    if start is None:
        start = scene.frame_start
    if end is None:
        end = scene.frame_end
    current = scene.frame_current
    for frame in range(int(start), int(end) + 1):
        bake_export_frame(frame)
    scene.frame_set(current)
"""
    )


def main():
    export_obj = bpy.data.objects.get(EXPORT_ARMATURE)
    rig = bpy.data.objects.get(CONTROL_RIG)
    if not export_obj or not rig:
        raise RuntimeError("Missing export armature or control rig")

    removed_handlers = remove_handlers()
    removed_preview = clean_preview_objects()
    for name in ("DAT_REFBAKE_LIVE_FOLLOW", "DAT_PREVIEW_BAKE_HELPERS"):
        text = bpy.data.texts.get(name)
        if text:
            bpy.data.texts.remove(text)

    reset_controls(rig)
    bpy.context.view_layer.update()
    preview = create_preview_armature(export_obj)
    preview_mesh = create_one_preview_mesh(export_obj, preview)
    offsets = compute_offsets(preview, rig)
    apply_offsets(preview, rig)
    rig["dat_preview_live_enabled"] = False
    hide_non_authoring_scene(export_obj, rig, preview)
    add_helper_text()
    bpy.context.view_layer.update()

    result = {
        "base_blend": BASE_BLEND,
        "saved_blend": OUT_BLEND,
        "removed_handlers": removed_handlers,
        "removed_preview": removed_preview,
        "preview_mesh": preview_mesh,
        "driven_bones": list(offsets.keys()),
        "visible_control_bones": [b.name for b in rig.data.bones if not b.hide],
        "manual_helper": "DAT_MANUAL_PREVIEW_BAKE",
        "live_handlers_left": [
            getattr(h, "__name__", "")
            for h in bpy.app.handlers.depsgraph_update_post + bpy.app.handlers.frame_change_post
            if getattr(h, "__name__", "") in {"dat_preview_offset_follow_v2", "dat_refbake_live_follow_v1"}
        ],
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    return result


RESULT = main()
