import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BASE_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_controlrig_v1.blend"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_previewrig_v5_unparented.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-refbake-previewrig-v5-unparented-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREVIEW_ARMATURE = "DAT_PreviewSkeleton"
PREVIEW_MESH = "DAT_PreviewMesh_Female_body"
PREVIEW_PREFIX = "DAT_PreviewMesh_"
CONSTRAINT_PREFIX = "DAT_NATIVE_PREVIEW_"

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


def remove_bad_handlers():
    removed = []
    for handlers in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
        for handler in list(handlers):
            name = getattr(handler, "__name__", "")
            if name in {"dat_preview_offset_follow_v2", "dat_refbake_live_follow_v1"}:
                handlers.remove(handler)
                removed.append(name)
    return removed


def clean_scene_artifacts():
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name == PREVIEW_ARMATURE or obj.name.startswith(PREVIEW_PREFIX):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    for name in (
        "DAT_NATIVE_PREVIEW_BAKE",
        "DAT_MANUAL_PREVIEW_BAKE",
        "DAT_PREVIEW_BAKE_HELPERS",
        "DAT_REFBAKE_LIVE_FOLLOW",
        "DAT_REFBAKE_HELPERS",
        "DAT_Bake_TrueJoint_ControlRig.py",
    ):
        text = bpy.data.texts.get(name)
        if text:
            bpy.data.texts.remove(text)
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
    preview.data.show_names = False
    preview.show_in_front = False
    bpy.context.view_layer.objects.active = preview
    preview.select_set(True)
    bpy.context.view_layer.update()

    bpy.ops.object.mode_set(mode="EDIT")
    for name in DRIVER_MAPPING:
        eb = preview.data.edit_bones.get(name)
        if eb:
            eb.parent = None
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="POSE")
    for pb in preview.pose.bones:
        src = export_obj.pose.bones.get(pb.name)
        if src:
            pb.matrix_basis = src.matrix_basis.copy()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    return preview


def create_preview_mesh(export_obj, preview):
    source = bpy.data.objects.get("Female_body")
    if not source:
        raise RuntimeError("Missing Female_body")
    dup = source.copy()
    dup.data = source.data
    dup.animation_data_clear()
    dup.name = PREVIEW_MESH
    bpy.context.collection.objects.link(dup)
    dup.matrix_world = source.matrix_world.copy()
    for mod in dup.modifiers:
        if mod.type == "ARMATURE" and mod.object == export_obj:
            mod.object = preview
    dup.hide_set(False)
    dup.hide_select = True
    return dup.name


def add_native_constraints(preview, rig):
    added = []
    bpy.context.view_layer.update()
    for target_bone, driver_bone in DRIVER_MAPPING.items():
        pb = preview.pose.bones.get(target_bone)
        driver = rig.pose.bones.get(driver_bone)
        if not pb or not driver:
            continue
        for con in list(pb.constraints):
            if con.name.startswith(CONSTRAINT_PREFIX):
                pb.constraints.remove(con)
        con = pb.constraints.new(type="CHILD_OF")
        con.name = CONSTRAINT_PREFIX + driver_bone
        con.target = rig
        con.subtarget = driver_bone
        con.inverse_matrix = (rig.matrix_world @ driver.matrix).inverted()
        con.influence = 1.0
        added.append({"target_bone": target_bone, "driver_bone": driver_bone})
    bpy.context.view_layer.update()
    return added


def hide_scene(export_obj, rig, preview):
    export_obj.hide_set(True)
    export_obj.hide_select = True
    preview.hide_set(True)
    preview.hide_select = True
    for name in ("Female_body", "zMale_body", "zEntityPosition", "EntityPosition"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_set(True)
            obj.hide_select = True
    for obj in bpy.data.objects:
        if obj.name == PREVIEW_MESH or obj.name in {"1", "1.001"}:
            obj.hide_set(False)
        elif obj.name.startswith(PREVIEW_PREFIX) and obj.name != PREVIEW_MESH:
            obj.hide_set(True)
    rig.hide_set(False)
    rig.hide_select = False
    rig.show_in_front = True
    rig.data.show_names = True
    for bone in rig.data.bones:
        bone.hide = not bone.name.startswith("CTRL_")
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig


def add_bake_text():
    text = bpy.data.texts.new("DAT_NATIVE_PREVIEW_BAKE")
    text.write(
        """# DAT_NATIVE_PREVIEW_BAKE
import bpy

EXPORT_ARMATURE = "_DayZ_Character"
PREVIEW_ARMATURE = "DAT_PreviewSkeleton"
DRIVEN_BONES = [
    "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
    "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
]


def apply_export_once():
    export_obj = bpy.data.objects[EXPORT_ARMATURE]
    preview = bpy.data.objects[PREVIEW_ARMATURE]
    export_inv = export_obj.matrix_world.inverted()
    bpy.context.view_layer.update()
    for name in DRIVEN_BONES:
        export_obj.pose.bones[name].matrix = export_inv @ (preview.matrix_world @ preview.pose.bones[name].matrix)
    bpy.context.view_layer.update()


def bake_export_frame(frame=None):
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    export_obj = bpy.data.objects[EXPORT_ARMATURE]
    apply_export_once()
    for name in DRIVEN_BONES:
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


def measure_deltas(export_obj, preview):
    import math

    out = []
    for name in DRIVER_MAPPING:
        ew = export_obj.matrix_world @ export_obj.pose.bones[name].matrix
        pw = preview.matrix_world @ preview.pose.bones[name].matrix
        out.append({
            "bone": name,
            "loc_delta": (pw.translation - ew.translation).length,
            "rot_delta_deg": ew.to_quaternion().rotation_difference(pw.to_quaternion()).angle * 180 / math.pi,
        })
    return out


def main():
    export_obj = bpy.data.objects.get(EXPORT_ARMATURE)
    rig = bpy.data.objects.get(CONTROL_RIG)
    if not export_obj or not rig:
        raise RuntimeError("Missing export/control rig")

    removed_handlers = remove_bad_handlers()
    removed_objects = clean_scene_artifacts()
    reset_controls(rig)
    bpy.context.view_layer.update()
    preview = create_preview_armature(export_obj)
    preview_mesh = create_preview_mesh(export_obj, preview)
    constraints = add_native_constraints(preview, rig)
    hide_scene(export_obj, rig, preview)
    add_bake_text()
    bpy.context.view_layer.update()

    result = {
        "base_blend": BASE_BLEND,
        "saved_blend": OUT_BLEND,
        "removed_handlers": removed_handlers,
        "removed_objects": removed_objects,
        "preview_mesh": preview_mesh,
        "constraints": constraints,
        "neutral_delta": measure_deltas(export_obj, preview),
        "visible_meshes": [o.name for o in bpy.data.objects if o.type == "MESH" and not o.hide_get()],
        "visible_control_bones": [b.name for b in rig.data.bones if not b.hide],
        "handlers_left": [
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
