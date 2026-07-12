import json
import math
import os

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN_PATH = r"P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_controlrig_v4_fullclone.blend"
OUT_JSON = os.path.join(ROOT, "anm", "dayz-controlrig-v4-fullclone-result.json")

DAYZ = "_DayZ_Character"
CTRL = "DAT_ControlRigV4"

SIDES = {
    "L": {
        "arm": "LeftArm",
        "arm_roll": "LeftArmRoll",
        "fore": "LeftForeArm",
        "fore_roll": "LeftForeArmRoll",
        "hand": "LeftHand",
        "hand_ctrl": "CTRL_Hand.L",
        "elbow_ctrl": "CTRL_Elbow.L",
    },
    "R": {
        "arm": "RightArm",
        "arm_roll": "RightArmRoll",
        "fore": "RightForeArm",
        "fore_roll": "RightForeArmRoll",
        "hand": "RightHand",
        "hand_ctrl": "CTRL_Hand.R",
        "elbow_ctrl": "CTRL_Elbow.R",
    },
}


def mode(name):
    if bpy.context.mode != name:
        bpy.ops.object.mode_set(mode=name)


def mode_for(obj, name):
    if bpy.context.mode == name and bpy.context.object == obj:
        return
    for other in bpy.context.view_layer.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        if bpy.context.mode != name:
            bpy.ops.object.mode_set(mode=name)


def object_mode():
    try:
        mode("OBJECT")
    except Exception:
        pass


def activate(obj):
    object_mode()
    for other in bpy.context.view_layer.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()


def wh(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].head


def wt(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].tail


def ensure_clean():
    object_mode()
    if os.path.exists(CLEAN_PATH) and bpy.data.filepath != CLEAN_PATH:
        bpy.ops.wm.open_mainfile(filepath=CLEAN_PATH)
        object_mode()


def remove_old():
    object_mode()
    for obj in list(bpy.data.objects):
        if obj.name.startswith("DAT_ControlRig"):
            bpy.data.objects.remove(obj, do_unlink=True)
    dayz = bpy.data.objects.get(DAYZ)
    if dayz:
        for pb in dayz.pose.bones:
            for c in list(pb.constraints):
                if c.name.startswith("DAT ") or c.name.startswith("DayZ WeaponIK Preview"):
                    pb.constraints.remove(c)


def pole_pos(dayz, side, sd):
    shoulder = wh(dayz, sd["arm"])
    elbow = wh(dayz, sd["fore"])
    wrist = wh(dayz, sd["hand"])
    axis = wrist - shoulder
    if axis.length < 0.0001:
        axis = Vector((0.0, -1.0, 0.0))
    axis.normalize()
    bend = elbow - shoulder
    plane = bend - axis * bend.dot(axis)
    if plane.length < 0.0001:
        plane = Vector((-1.0 if side == "L" else 1.0, -0.2, 0.0))
    plane.normalize()
    outside = Vector((-0.28 if side == "L" else 0.28, -0.20, 0.0))
    return elbow + plane * 0.45 + outside


def duplicate_dayz_as_control(dayz):
    object_mode()
    ctrl_data = dayz.data.copy()
    ctrl_data.name = CTRL
    ctrl = bpy.data.objects.new(CTRL, ctrl_data)
    bpy.context.collection.objects.link(ctrl)
    ctrl.matrix_world = dayz.matrix_world.copy()
    ctrl.show_in_front = True
    ctrl["dat_role"] = "non_export_full_dayz_clone_control_rig"

    mode_for(ctrl, "EDIT")
    inv = ctrl.matrix_world.inverted()
    for side, sd in SIDES.items():
        wrist = wh(dayz, sd["hand"])
        hand_tail = wt(dayz, sd["hand"])
        pole = pole_pos(dayz, side, sd)

        hand = ctrl.data.edit_bones.new(sd["hand_ctrl"])
        hand.head = inv @ wrist
        hand.tail = inv @ hand_tail
        hand.use_connect = False
        hand.parent = None

        elbow = ctrl.data.edit_bones.new(sd["elbow_ctrl"])
        elbow.head = inv @ pole
        elbow.tail = inv @ (pole + Vector((0.0, 0.0, 0.18)))
        elbow.use_connect = False
        elbow.parent = None

    mode_for(ctrl, "POSE")
    for pb in ctrl.pose.bones:
        pb.rotation_mode = "QUATERNION"
        if pb.name.startswith("CTRL_"):
            pb["dat_role"] = "animator_visible_control"
        else:
            pb["dat_role"] = "hidden_dayz_clone_mechanism"

    for side, sd in SIDES.items():
        pb = ctrl.pose.bones.get(sd["hand"])
        if not pb:
            continue
        c = pb.constraints.new(type="IK")
        c.name = "DAT FullClone Arm IK"
        c.target = ctrl
        c.subtarget = sd["hand_ctrl"]
        c.pole_target = ctrl
        c.pole_subtarget = sd["elbow_ctrl"]
        # Full DayZ chain includes Hand, ForeArmRoll, ForeArm, ArmRoll, Arm.
        c.chain_count = 5
        c.use_rotation = True
        c.use_stretch = False
        c.pole_angle = math.radians(-90.0)

    return ctrl


def add_export_copy(dayz, ctrl):
    copied = []
    object_mode()
    for side, sd in SIDES.items():
        for bone in [sd["arm"], sd["arm_roll"], sd["fore"], sd["fore_roll"], sd["hand"]]:
            pb = dayz.pose.bones.get(bone)
            if not pb:
                continue
            c = pb.constraints.new(type="COPY_TRANSFORMS")
            c.name = "DAT FullClone Follow"
            c.target = ctrl
            c.subtarget = bone
            c.target_space = "POSE"
            c.owner_space = "POSE"
            copied.append({"bone": bone, "target": bone})
    return copied


def add_bake_text():
    name = "DAT_Bake_FullClone_ControlRig.py"
    body = r'''import bpy

DAYZ_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRigV4"
EXPORT_BONES = [
    "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
    "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
]

def dat_bake_fullclone_preview(action_name="DAT_Baked_FullClone_WeaponPose", frame_start=None, frame_end=None):
    arm = bpy.data.objects[DAYZ_ARMATURE]
    scene = bpy.context.scene
    if frame_start is None:
        frame_start = scene.frame_start
    if frame_end is None:
        frame_end = scene.frame_end
    action = bpy.data.actions.new(action_name)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for name in EXPORT_BONES:
            pb = arm.pose.bones.get(name)
            if not pb:
                continue
            pb.keyframe_insert("location", frame=frame)
            pb.keyframe_insert("rotation_quaternion", frame=frame)
            pb.keyframe_insert("scale", frame=frame)
    return action

print("Loaded DAT full-clone bake helper. Call dat_bake_fullclone_preview().")
'''
    if name in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts[name])
    text = bpy.data.texts.new(name)
    text.write(body)


def visibility(dayz, ctrl):
    dayz_visible = {
        "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
        "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    for b in dayz.data.bones:
        b.hide = b.name not in dayz_visible
    for b in ctrl.data.bones:
        b.hide = not b.name.startswith("CTRL_")
    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_"):
            obj.hide_set(True)
            obj.hide_viewport = True


def main():
    ensure_clean()
    remove_old()
    dayz = bpy.data.objects.get(DAYZ)
    if not dayz or dayz.type != "ARMATURE":
        raise RuntimeError(f"{DAYZ} not found")

    ctrl = duplicate_dayz_as_control(dayz)
    copied = add_export_copy(dayz, ctrl)
    add_bake_text()
    visibility(dayz, ctrl)
    bpy.context.view_layer.update()
    mode_for(ctrl, "POSE")
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    result = {
        "source_clean_file": CLEAN_PATH,
        "saved_as": SAVE_PATH,
        "dayz_armature": DAYZ,
        "control_rig": CTRL,
        "control_rig_bone_count": len(ctrl.data.bones),
        "visible_control_bones": [b.name for b in ctrl.data.bones if not b.hide],
        "copy_follow_constraints": copied,
        "note": "Full clone control rig: DAT_ControlRigV4 has the same DayZ rest skeleton plus four visible controls. IK runs on the clone; export skeleton follows matching clone bones in pose space.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


RESULT = main()
