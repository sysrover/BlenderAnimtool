import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_controlrig_v1.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-refbake-controlrig-v1-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREFIX = "DAT_REFBAKE_"

SIDE_MAP = {
    "L": {
        "upper": "LeftArm",
        "fore": "LeftForeArm",
        "fore_roll": "LeftForeArmRoll",
        "hand": "LeftHand",
    },
    "R": {
        "upper": "RightArm",
        "fore": "RightForeArm",
        "fore_roll": "RightForeArmRoll",
        "hand": "RightHand",
    },
}


def remove_object(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def remove_refbake_constraints(export_obj):
    removed = []
    for pb in export_obj.pose.bones:
        for con in list(pb.constraints):
            if con.name.startswith(PREFIX):
                removed.append(f"{pb.name}:{con.name}")
                pb.constraints.remove(con)
    return removed


def pose_point(export_obj, bone_name, point):
    pb = export_obj.pose.bones[bone_name]
    if point == "head":
        return export_obj.matrix_world @ pb.head
    if point == "tail":
        return export_obj.matrix_world @ pb.tail
    raise ValueError(point)


def pose_matrix(export_obj, bone_name):
    return export_obj.matrix_world @ export_obj.pose.bones[bone_name].matrix


def safe_tail(head, tail, fallback):
    if (tail - head).length > 0.015:
        return tail
    return head + fallback.normalized() * 0.08


def pole_position(shoulder, elbow, hand, side):
    mid = (shoulder + hand) * 0.5
    pole = elbow - mid
    if pole.length < 0.03:
        pole = Vector((-0.25, 0.0, 0.0)) if side == "L" else Vector((0.25, 0.0, 0.0))
    return elbow + pole.normalized() * 0.35


def make_bone(arm_data, name, head, tail, parent=None, connected=False, hide=False):
    eb = arm_data.edit_bones.new(name)
    eb.head = head
    eb.tail = safe_tail(head, tail, Vector((0, 0, 1)))
    eb.roll = 0.0
    if parent:
        eb.parent = arm_data.edit_bones[parent]
        eb.use_connect = connected
    eb.hide = hide
    return eb


def create_control_rig(export_obj):
    arm_data = bpy.data.armatures.new(CONTROL_RIG)
    rig_obj = bpy.data.objects.new(CONTROL_RIG, arm_data)
    bpy.context.collection.objects.link(rig_obj)
    rig_obj.matrix_world = Matrix.Identity(4)
    arm_data.display_type = "STICK"
    arm_data.show_names = True

    bpy.context.view_layer.objects.active = rig_obj
    rig_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    created = []
    for side, names in SIDE_MAP.items():
        upper = names["upper"]
        fore = names["fore"]
        fore_roll = names["fore_roll"]
        hand = names["hand"]

        shoulder = pose_point(export_obj, upper, "head")
        elbow = pose_point(export_obj, fore, "head")
        wrist = pose_point(export_obj, hand, "head")
        hand_tail = pose_point(export_obj, hand, "tail")
        pole = pole_position(shoulder, elbow, wrist, side)

        make_bone(arm_data, f"MCH_UpperArm.{side}", shoulder, elbow, hide=True)
        make_bone(arm_data, f"MCH_ForeArm.{side}", elbow, wrist, parent=f"MCH_UpperArm.{side}", connected=True, hide=True)
        make_bone(arm_data, f"MCH_Hand.{side}", wrist, hand_tail, parent=f"MCH_ForeArm.{side}", connected=False, hide=True)

        hand_dir = hand_tail - wrist
        if hand_dir.length < 0.03:
            hand_dir = Vector((0, -0.1, 0)) if side == "R" else Vector((0, 0.1, 0))
        make_bone(arm_data, f"CTRL_Hand.{side}", wrist, wrist + hand_dir.normalized() * 0.18)
        make_bone(arm_data, f"CTRL_Elbow.{side}", pole, pole + Vector((0, 0, 0.12)))

        created.extend([
            f"MCH_UpperArm.{side}",
            f"MCH_ForeArm.{side}",
            f"MCH_Hand.{side}",
            f"CTRL_Hand.{side}",
            f"CTRL_Elbow.{side}",
        ])

    bpy.ops.object.mode_set(mode="POSE")
    for side in SIDE_MAP:
        fore = rig_obj.pose.bones[f"MCH_ForeArm.{side}"]
        ik = fore.constraints.new(type="IK")
        ik.name = f"{PREFIX}IK_ARM_{side}"
        ik.target = rig_obj
        ik.subtarget = f"CTRL_Hand.{side}"
        ik.pole_target = rig_obj
        ik.pole_subtarget = f"CTRL_Elbow.{side}"
        ik.chain_count = 2
        ik.use_rotation = True
        ik.use_stretch = False

        hand_copy = rig_obj.pose.bones[f"MCH_Hand.{side}"].constraints.new(type="COPY_TRANSFORMS")
        hand_copy.name = f"{PREFIX}COPY_HAND_CTRL_{side}"
        hand_copy.target = rig_obj
        hand_copy.subtarget = f"CTRL_Hand.{side}"
        hand_copy.target_space = "WORLD"
        hand_copy.owner_space = "WORLD"

        for ctrl in (rig_obj.pose.bones[f"CTRL_Hand.{side}"], rig_obj.pose.bones[f"CTRL_Elbow.{side}"]):
            ctrl.custom_shape_scale_xyz = (1.0, 1.0, 1.0)
            ctrl.color.palette = "THEME09"

    for bone in rig_obj.data.bones:
        bone.hide = bone.name.startswith("MCH_")

    rig_obj["dat_refbake_version"] = "v1"
    rig_obj["dat_export_armature"] = EXPORT_ARMATURE
    rig_obj["dat_notes"] = "Reference-style authoring rig. IK stays on this armature; export skeleton follow constraints start disabled for safe bake."
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig_obj, created


def add_export_follow_constraints(export_obj, rig_obj):
    mapping = {
        "LeftArm": "MCH_UpperArm.L",
        "LeftForeArm": "MCH_ForeArm.L",
        "LeftHand": "MCH_Hand.L",
        "RightArm": "MCH_UpperArm.R",
        "RightForeArm": "MCH_ForeArm.R",
        "RightHand": "MCH_Hand.R",
    }
    added = []
    for export_bone, driver_bone in mapping.items():
        pb = export_obj.pose.bones.get(export_bone)
        if not pb:
            continue
        con = pb.constraints.new(type="COPY_TRANSFORMS")
        con.name = f"{PREFIX}FOLLOW_{driver_bone}"
        con.target = rig_obj
        con.subtarget = driver_bone
        con.target_space = "WORLD"
        con.owner_space = "WORLD"
        con.influence = 0.0
        added.append({"export_bone": export_bone, "driver_bone": driver_bone, "influence": con.influence})
    return added


def driver_mapping():
    return {
        "LeftArm": "MCH_UpperArm.L",
        "LeftForeArm": "MCH_ForeArm.L",
        "LeftHand": "MCH_Hand.L",
        "RightArm": "MCH_UpperArm.R",
        "RightForeArm": "MCH_ForeArm.R",
        "RightHand": "MCH_Hand.R",
    }


def matrix_rows(matrix):
    return [list(row) for row in matrix]


def store_bake_offsets(export_obj, rig_obj):
    offsets = {}
    bpy.context.view_layer.update()
    for export_bone, driver_bone in driver_mapping().items():
        export_world = export_obj.matrix_world @ export_obj.pose.bones[export_bone].matrix
        driver_world = rig_obj.matrix_world @ rig_obj.pose.bones[driver_bone].matrix
        offsets[export_bone] = {
            "driver_bone": driver_bone,
            "offset": matrix_rows(export_world @ driver_world.inverted()),
        }
    rig_obj["dat_refbake_offsets_json"] = json.dumps(offsets)
    return offsets


def add_helper_text():
    text = bpy.data.texts.get("DAT_REFBAKE_HELPERS") or bpy.data.texts.new("DAT_REFBAKE_HELPERS")
    text.clear()
    text.write(
        """# DAT_REFBAKE_HELPERS
import json
import bpy
from mathutils import Matrix

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig_RefBakeV1"
PREFIX = "DAT_REFBAKE_"


def set_export_follow(influence):
    export_obj = bpy.data.objects[EXPORT_ARMATURE]
    for pb in export_obj.pose.bones:
        for con in pb.constraints:
            if con.name.startswith(PREFIX + "FOLLOW_"):
                con.influence = influence
    bpy.context.view_layer.update()


def bake_visible_arm_frame(frame=None):
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    export_obj = bpy.data.objects[EXPORT_ARMATURE]
    rig_obj = bpy.data.objects[CONTROL_RIG]
    offsets = json.loads(rig_obj["dat_refbake_offsets_json"])
    for export_bone, info in offsets.items():
        driver_bone = info["driver_bone"]
        offset = Matrix(info["offset"])
        driver_world = rig_obj.matrix_world @ rig_obj.pose.bones[driver_bone].matrix
        target_world = offset @ driver_world
        pb = export_obj.pose.bones[export_bone]
        pb.matrix = export_obj.matrix_world.inverted() @ target_world
        pb.keyframe_insert("location")
        if pb.rotation_mode == "QUATERNION":
            pb.keyframe_insert("rotation_quaternion")
        elif pb.rotation_mode == "AXIS_ANGLE":
            pb.keyframe_insert("rotation_axis_angle")
        else:
            pb.keyframe_insert("rotation_euler")
    bpy.context.view_layer.update()


def bake_visible_arm_range(start=None, end=None):
    scene = bpy.context.scene
    if start is None:
        start = scene.frame_start
    if end is None:
        end = scene.frame_end
    original_frame = scene.frame_current
    set_export_follow(1.0)
    for frame in range(int(start), int(end) + 1):
        bake_visible_arm_frame(frame)
    set_export_follow(0.0)
    scene.frame_set(original_frame)


def apply_controls_to_export_once():
    bake_visible_arm_frame()


# Use:
# set_export_follow(1.0)  # preview skeleton follows controls
# set_export_follow(0.0)  # safe/edit imported ANM normally
# bake_visible_arm_frame() # key current frame from controls into export skeleton
# bake_visible_arm_range() # bake scene frame range, then disable follow constraints
# apply_controls_to_export_once() # apply current controls without enabling raw constraints
"""
    )


def main():
    export_obj = bpy.data.objects.get(EXPORT_ARMATURE)
    if not export_obj or export_obj.type != "ARMATURE":
        raise RuntimeError(f"Missing export armature {EXPORT_ARMATURE}")

    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    removed_constraints = remove_refbake_constraints(export_obj)
    remove_object(CONTROL_RIG)

    rig_obj, created_bones = create_control_rig(export_obj)
    bake_offsets = store_bake_offsets(export_obj, rig_obj)
    follow_constraints = add_export_follow_constraints(export_obj, rig_obj)
    add_helper_text()

    bpy.context.view_layer.update()

    validation = {
        "export_file_before_save": bpy.data.filepath,
        "control_rig": CONTROL_RIG,
        "created_bones": created_bones,
        "removed_old_constraints": removed_constraints,
        "follow_constraints": follow_constraints,
        "bake_offsets": bake_offsets,
        "active_export_follow_constraints": [
            f"{pb.name}:{con.name}:{con.influence}"
            for pb in export_obj.pose.bones
            for con in pb.constraints
            if con.name.startswith(PREFIX + "FOLLOW_") and con.influence > 0.0
        ],
        "control_ik_constraints": [
            f"{pb.name}:{con.name}:{con.type}:{con.influence}"
            for pb in rig_obj.pose.bones
            for con in pb.constraints
            if con.name.startswith(PREFIX)
        ],
    }

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    validation["saved_blend"] = OUT_BLEND
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2)

    return validation


RESULT = main()
