import json
import math
import os

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN_PATH = r"P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_controlrig_v3_refstyle.blend"
OUT_JSON = os.path.join(ROOT, "anm", "dayz-controlrig-v3-refstyle-result.json")

DAYZ = "_DayZ_Character"
CTRL = "DAT_ControlRigV3"

SIDES = {
    "L": {
        "upper": "LeftArm",
        "upper_roll": "LeftArmRoll",
        "fore": "LeftForeArm",
        "fore_roll": "LeftForeArmRoll",
        "hand": "LeftHand",
        "ctrl_hand": "CTRL_Hand.L",
        "ctrl_elbow": "CTRL_Elbow.L",
        "drv_upper": "DRV_UpperArm.L",
        "drv_fore": "DRV_ForeArm.L",
        "drv_hand": "DRV_Hand.L",
    },
    "R": {
        "upper": "RightArm",
        "upper_roll": "RightArmRoll",
        "fore": "RightForeArm",
        "fore_roll": "RightForeArmRoll",
        "hand": "RightHand",
        "ctrl_hand": "CTRL_Hand.R",
        "ctrl_elbow": "CTRL_Elbow.R",
        "drv_upper": "DRV_UpperArm.R",
        "drv_fore": "DRV_ForeArm.R",
        "drv_hand": "DRV_Hand.R",
    },
}


def mode(name):
    if bpy.context.mode != name:
        bpy.ops.object.mode_set(mode=name)


def ensure_object_mode():
    try:
        mode("OBJECT")
    except Exception:
        pass


def activate(obj):
    ensure_object_mode()
    for other in bpy.context.view_layer.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def world_head(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].head


def world_tail(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].tail


def ensure_clean_scene():
    ensure_object_mode()
    if os.path.exists(CLEAN_PATH) and bpy.data.filepath != CLEAN_PATH:
        bpy.ops.wm.open_mainfile(filepath=CLEAN_PATH)
        ensure_object_mode()


def pole_position(dayz, side, sd):
    shoulder = world_head(dayz, sd["upper"])
    elbow = world_head(dayz, sd["fore"])
    wrist = world_head(dayz, sd["hand"])
    axis = wrist - shoulder
    if axis.length < 0.0001:
        axis = Vector((0, -1, 0))
    axis.normalize()
    bend = elbow - shoulder
    plane = bend - axis * bend.dot(axis)
    if plane.length < 0.0001:
        plane = Vector((-1 if side == "L" else 1, -0.2, 0.0))
    plane.normalize()
    outside = Vector((-0.22 if side == "L" else 0.22, -0.20, 0.0))
    return elbow + plane * 0.45 + outside


def remove_old_preview_constraints(dayz):
    removed = []
    for pb in dayz.pose.bones:
        for c in list(pb.constraints):
            if (
                c.name.startswith("DAT Preview")
                or c.name.startswith("DAT RefStyle")
                or c.name.startswith("DayZ WeaponIK Preview")
            ):
                removed.append({"bone": pb.name, "constraint": c.name, "type": c.type})
                pb.constraints.remove(c)
    return removed


def make_control_rig(dayz):
    ensure_object_mode()
    old = bpy.data.objects.get(CTRL)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    data = bpy.data.armatures.new(CTRL)
    rig = bpy.data.objects.new(CTRL, data)
    bpy.context.collection.objects.link(rig)
    rig.matrix_world = dayz.matrix_world.copy()
    rig.show_in_front = True
    rig["dat_role"] = "non_export_authoring_control_rig"

    activate(rig)
    mode("EDIT")
    inv = rig.matrix_world.inverted()

    for side, sd in SIDES.items():
        shoulder = world_head(dayz, sd["upper"])
        elbow = world_head(dayz, sd["fore"])
        wrist = world_head(dayz, sd["hand"])
        hand_tail = world_tail(dayz, sd["hand"])
        pole = pole_position(dayz, side, sd)

        upper = data.edit_bones.new(sd["drv_upper"])
        upper.head = inv @ shoulder
        upper.tail = inv @ elbow
        upper.use_connect = False

        fore = data.edit_bones.new(sd["drv_fore"])
        fore.head = inv @ elbow
        fore.tail = inv @ wrist
        fore.parent = upper
        fore.use_connect = True

        hand = data.edit_bones.new(sd["drv_hand"])
        hand.head = inv @ wrist
        hand.tail = inv @ hand_tail
        hand.parent = fore
        hand.use_connect = True

        ctrl_hand = data.edit_bones.new(sd["ctrl_hand"])
        ctrl_hand.head = inv @ wrist
        ctrl_hand.tail = inv @ hand_tail
        ctrl_hand.use_connect = False

        ctrl_elbow = data.edit_bones.new(sd["ctrl_elbow"])
        ctrl_elbow.head = inv @ pole
        ctrl_elbow.tail = inv @ (pole + Vector((0.0, 0.0, 0.18)))
        ctrl_elbow.use_connect = False

    mode("POSE")
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        if pb.name.startswith("CTRL_"):
            pb["dat_role"] = "animator_visible_control"
            pb.custom_shape_scale_xyz = (1.0, 1.0, 1.0)
        else:
            pb["dat_role"] = "hidden_mechanism"

    for side, sd in SIDES.items():
        hand_pb = rig.pose.bones[sd["drv_hand"]]
        ik = hand_pb.constraints.new(type="IK")
        ik.name = "DAT RefStyle Arm IK"
        ik.target = rig
        ik.subtarget = sd["ctrl_hand"]
        ik.pole_target = rig
        ik.pole_subtarget = sd["ctrl_elbow"]
        ik.chain_count = 3
        ik.use_rotation = True
        ik.use_stretch = False
        ik.pole_angle = math.radians(-90.0)

        copy_rot = hand_pb.constraints.new(type="COPY_ROTATION")
        copy_rot.name = "DAT RefStyle Hand Rotation"
        copy_rot.target = rig
        copy_rot.subtarget = sd["ctrl_hand"]
        copy_rot.target_space = "WORLD"
        copy_rot.owner_space = "WORLD"

    return rig


def add_export_follow_constraints(dayz, rig):
    made = []
    for side, sd in SIDES.items():
        mapping = [
            (sd["upper"], sd["drv_upper"]),
            (sd["fore"], sd["drv_fore"]),
            (sd["hand"], sd["drv_hand"]),
        ]
        if sd["upper_roll"] in dayz.pose.bones:
            mapping.append((sd["upper_roll"], sd["drv_upper"]))
        if sd["fore_roll"] in dayz.pose.bones:
            mapping.append((sd["fore_roll"], sd["drv_fore"]))

        for dayz_bone, driver_bone in mapping:
            pb = dayz.pose.bones.get(dayz_bone)
            if not pb:
                continue
            con = pb.constraints.new(type="COPY_TRANSFORMS")
            con.name = "DAT RefStyle Follow ControlRig"
            con.target = rig
            con.subtarget = driver_bone
            con.target_space = "WORLD"
            con.owner_space = "WORLD"
            made.append({"bone": dayz_bone, "driver": driver_bone})
    return made


def add_bake_text():
    body = r'''import bpy

DAYZ_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRigV3"
EXPORT_BONES = [
    "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
    "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
]

def dat_bake_refstyle_preview(action_name="DAT_Baked_RefStyle_WeaponPose", frame_start=None, frame_end=None):
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

print("Loaded DAT RefStyle bake helper. Call dat_bake_refstyle_preview().")
'''
    name = "DAT_Bake_RefStyle_ControlRig.py"
    if name in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts[name])
    text = bpy.data.texts.new(name)
    text.write(body)


def set_visibility(dayz, rig):
    visible_dayz = {
        "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
        "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    for b in dayz.data.bones:
        b.hide = b.name not in visible_dayz
    for b in rig.data.bones:
        b.hide = not b.name.startswith("CTRL_")

    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_"):
            obj.hide_set(True)
            obj.hide_viewport = True


def main():
    ensure_clean_scene()
    dayz = bpy.data.objects.get(DAYZ)
    if dayz is None or dayz.type != "ARMATURE":
        raise RuntimeError(f"{DAYZ} armature not found")

    activate(dayz)
    removed = remove_old_preview_constraints(dayz)
    rig = make_control_rig(dayz)
    made = add_export_follow_constraints(dayz, rig)
    add_bake_text()
    set_visibility(dayz, rig)

    bpy.context.view_layer.update()
    ensure_object_mode()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    result = {
        "source_clean_file": CLEAN_PATH,
        "saved_as": SAVE_PATH,
        "dayz_armature": DAYZ,
        "control_rig": CTRL,
        "removed_preview_constraints": removed,
        "copy_follow_constraints": made,
        "visible_control_bones": [b.name for b in rig.data.bones if not b.hide],
        "hidden_mechanism_bones": [b.name for b in rig.data.bones if b.hide],
        "note": "Reference-style two-armature authoring rig: controls and IK live on DAT_ControlRigV3; DayZ skeleton follows/bakes and stays free of direct IK controls.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


RESULT = main()
