import json
import os

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
REPORT = os.path.join(ROOT, "anm", "dayz-refbake-live-follow-v1-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
HANDLER_NAME = "dat_refbake_live_follow_v1"


def remove_existing_handler():
    removed = 0
    for handlers in (
        bpy.app.handlers.depsgraph_update_post,
        bpy.app.handlers.frame_change_post,
    ):
        for handler in list(handlers):
            if getattr(handler, "__name__", "") == HANDLER_NAME:
                handlers.remove(handler)
                removed += 1
    return removed


def apply_offset_follow():
    export_obj = bpy.data.objects.get(EXPORT_ARMATURE)
    rig_obj = bpy.data.objects.get(CONTROL_RIG)
    if not export_obj or not rig_obj:
        return False
    if not bool(rig_obj.get("dat_live_follow_enabled", True)):
        return False
    offsets_json = rig_obj.get("dat_refbake_offsets_json", "")
    if not offsets_json:
        return False

    offsets = json.loads(offsets_json)
    export_inv = export_obj.matrix_world.inverted()
    for export_bone, info in offsets.items():
        pb = export_obj.pose.bones.get(export_bone)
        driver_pb = rig_obj.pose.bones.get(info["driver_bone"])
        if not pb or not driver_pb:
            continue
        offset = Matrix(info["offset"])
        driver_world = rig_obj.matrix_world @ driver_pb.matrix
        pb.matrix = export_inv @ (offset @ driver_world)
    return True


@persistent
def dat_refbake_live_follow_v1(scene, depsgraph=None):
    guard = getattr(bpy.types.Scene, "_dat_refbake_live_follow_guard", False)
    if guard:
        return
    bpy.types.Scene._dat_refbake_live_follow_guard = True
    try:
        apply_offset_follow()
    finally:
        bpy.types.Scene._dat_refbake_live_follow_guard = False


def add_text_block():
    text = bpy.data.texts.get("DAT_REFBAKE_LIVE_FOLLOW") or bpy.data.texts.new("DAT_REFBAKE_LIVE_FOLLOW")
    text.clear()
    text.write(
        """# DAT_REFBAKE_LIVE_FOLLOW
# Run this text after reopening the file if live controls stop updating.
import json
import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"


def apply_offset_follow():
    export_obj = bpy.data.objects.get(EXPORT_ARMATURE)
    rig_obj = bpy.data.objects.get(CONTROL_RIG)
    if not export_obj or not rig_obj or not bool(rig_obj.get("dat_live_follow_enabled", True)):
        return
    offsets = json.loads(rig_obj["dat_refbake_offsets_json"])
    export_inv = export_obj.matrix_world.inverted()
    for export_bone, info in offsets.items():
        pb = export_obj.pose.bones.get(export_bone)
        driver_pb = rig_obj.pose.bones.get(info["driver_bone"])
        if pb and driver_pb:
            pb.matrix = export_inv @ (Matrix(info["offset"]) @ (rig_obj.matrix_world @ driver_pb.matrix))


@persistent
def dat_refbake_live_follow_v1(scene, depsgraph=None):
    if getattr(bpy.types.Scene, "_dat_refbake_live_follow_guard", False):
        return
    bpy.types.Scene._dat_refbake_live_follow_guard = True
    try:
        apply_offset_follow()
    finally:
        bpy.types.Scene._dat_refbake_live_follow_guard = False


for handlers in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
    for handler in list(handlers):
        if getattr(handler, "__name__", "") == "dat_refbake_live_follow_v1":
            handlers.remove(handler)
bpy.app.handlers.depsgraph_update_post.append(dat_refbake_live_follow_v1)
bpy.app.handlers.frame_change_post.append(dat_refbake_live_follow_v1)
apply_offset_follow()
print("DAT_REFBAKE_LIVE_FOLLOW_READY")
"""
    )
    return text.name


def main():
    rig_obj = bpy.data.objects.get(CONTROL_RIG)
    if not rig_obj:
        raise RuntimeError(f"Missing {CONTROL_RIG}")
    removed = remove_existing_handler()
    rig_obj["dat_live_follow_enabled"] = True
    text_name = add_text_block()
    bpy.app.handlers.depsgraph_update_post.append(dat_refbake_live_follow_v1)
    bpy.app.handlers.frame_change_post.append(dat_refbake_live_follow_v1)
    applied = apply_offset_follow()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)

    result = {
        "file": bpy.data.filepath,
        "removed_old_handlers": removed,
        "live_follow_enabled": bool(rig_obj.get("dat_live_follow_enabled", False)),
        "applied_once": applied,
        "text_block": text_name,
        "depsgraph_handlers": [
            getattr(h, "__name__", "")
            for h in bpy.app.handlers.depsgraph_update_post
            if getattr(h, "__name__", "") == HANDLER_NAME
        ],
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


RESULT = main()
