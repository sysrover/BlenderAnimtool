import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN_PATH = r"P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend"
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_controlrig_v5_proxyik.blend"
OUT_JSON = os.path.join(ROOT, "anm", "dayz-controlrig-v5-proxyik-result.json")

DAYZ = "_DayZ_Character"
CTRL = "DAT_ControlRigV5"

SIDES = {
    "L": {
        "arm": "LeftArm",
        "fore": "LeftForeArm",
        "hand": "LeftHand",
        "arm_roll": "LeftArmRoll",
        "fore_roll": "LeftForeArmRoll",
        "proxy_arm": "IK_Arm.L",
        "proxy_fore": "IK_ForeArm.L",
        "proxy_hand": "IK_Hand.L",
        "ctrl_hand": "CTRL_Hand.L",
        "ctrl_elbow": "CTRL_Elbow.L",
    },
    "R": {
        "arm": "RightArm",
        "fore": "RightForeArm",
        "hand": "RightHand",
        "arm_roll": "RightArmRoll",
        "fore_roll": "RightForeArmRoll",
        "proxy_arm": "IK_Arm.R",
        "proxy_fore": "IK_ForeArm.R",
        "proxy_hand": "IK_Hand.R",
        "ctrl_hand": "CTRL_Hand.R",
        "ctrl_elbow": "CTRL_Elbow.R",
    },
}


def object_mode():
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass


def mode_for(obj, mode):
    object_mode()
    for other in bpy.context.view_layer.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.mode_set(mode=mode)


def wh(obj, bone):
    return obj.matrix_world @ obj.pose.bones[bone].head


def wt(obj, bone):
    return obj.matrix_world @ obj.pose.bones[bone].tail


def ensure_clean():
    object_mode()
    if os.path.exists(CLEAN_PATH) and bpy.data.filepath != CLEAN_PATH:
        bpy.ops.wm.open_mainfile(filepath=CLEAN_PATH)
        object_mode()


def clear_old():
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


def copy_edit_bone_transform(dst, src):
    dst.head = src.head.copy()
    dst.tail = src.tail.copy()
    dst.roll = src.roll
    dst.use_connect = False


def pole_position(dayz, side, sd):
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
    outside = Vector((-0.32 if side == "L" else 0.32, -0.25, 0.0))
    return elbow + plane * 0.55 + outside


def make_proxy_rig(dayz):
    data = bpy.data.armatures.new(CTRL)
    rig = bpy.data.objects.new(CTRL, data)
    bpy.context.collection.objects.link(rig)
    rig.matrix_world = dayz.matrix_world.copy()
    rig.show_in_front = True
    rig["dat_role"] = "non_export_proxy_ik_control_rig"

    mode_for(dayz, "EDIT")
    source = {b.name: (b.head.copy(), b.tail.copy(), b.roll) for b in dayz.data.edit_bones}

    mode_for(rig, "EDIT")
    inv = rig.matrix_world.inverted()
    for side, sd in SIDES.items():
        src_arm = source[sd["arm"]]
        src_fore = source[sd["fore"]]
        src_hand = source[sd["hand"]]

        arm = data.edit_bones.new(sd["proxy_arm"])
        arm.head, arm.tail, arm.roll = src_arm
        arm.use_connect = False

        fore = data.edit_bones.new(sd["proxy_fore"])
        fore.head, fore.tail, fore.roll = src_fore
        fore.parent = arm
        fore.use_connect = True

        hand = data.edit_bones.new(sd["proxy_hand"])
        hand.head, hand.tail, hand.roll = src_hand
        hand.parent = fore
        hand.use_connect = True

        wrist = wh(dayz, sd["hand"])
        hand_tail = wt(dayz, sd["hand"])
        pole = pole_position(dayz, side, sd)

        ctrl_hand = data.edit_bones.new(sd["ctrl_hand"])
        ctrl_hand.head = inv @ wrist
        ctrl_hand.tail = inv @ hand_tail
        ctrl_hand.use_connect = False

        ctrl_elbow = data.edit_bones.new(sd["ctrl_elbow"])
        ctrl_elbow.head = inv @ pole
        ctrl_elbow.tail = inv @ (pole + Vector((0.0, 0.0, 0.18)))
        ctrl_elbow.use_connect = False

    mode_for(rig, "POSE")
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb["dat_role"] = "animator_visible_control" if pb.name.startswith("CTRL_") else "hidden_proxy_ik"

    for side, sd in SIDES.items():
        pb = rig.pose.bones[sd["proxy_hand"]]
        ik = pb.constraints.new(type="IK")
        ik.name = "DAT Proxy Arm IK"
        ik.target = rig
        ik.subtarget = sd["ctrl_hand"]
        ik.pole_target = rig
        ik.pole_subtarget = sd["ctrl_elbow"]
        ik.chain_count = 3
        ik.use_rotation = True
        ik.use_stretch = False
        ik.pole_angle = math.radians(-90.0)

    return rig


def add_dayz_follow(dayz, rig):
    copied = []
    # Rotation-only follow keeps DayZ bone locations/rest chain intact. This avoids
    # Blender moving roll bones as if they were true elbow joints.
    for side, sd in SIDES.items():
        for dayz_bone, proxy_bone in [
            (sd["arm"], sd["proxy_arm"]),
            (sd["fore"], sd["proxy_fore"]),
            (sd["hand"], sd["proxy_hand"]),
        ]:
            pb = dayz.pose.bones.get(dayz_bone)
            if not pb:
                continue
            c = pb.constraints.new(type="COPY_ROTATION")
            c.name = "DAT ProxyIK Follow Rotation"
            c.target = rig
            c.subtarget = proxy_bone
            c.target_space = "POSE"
            c.owner_space = "POSE"
            copied.append({"bone": dayz_bone, "proxy": proxy_bone, "type": "COPY_ROTATION"})
    return copied


def add_bake_text():
    name = "DAT_Bake_ProxyIK_ControlRig.py"
    body = r'''import bpy

DAYZ_ARMATURE = "_DayZ_Character"
EXPORT_BONES = [
    "LeftArm", "LeftForeArm", "LeftHand",
    "RightArm", "RightForeArm", "RightHand",
]

def dat_bake_proxyik_preview(action_name="DAT_Baked_ProxyIK_WeaponPose", frame_start=None, frame_end=None):
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

print("Loaded DAT ProxyIK bake helper. Call dat_bake_proxyik_preview().")
'''
    if name in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts[name])
    text = bpy.data.texts.new(name)
    text.write(body)


def visibility(dayz, rig):
    dayz_visible = {
        "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
        "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    for b in dayz.data.bones:
        b.hide = b.name not in dayz_visible
    for b in rig.data.bones:
        b.hide = not b.name.startswith("CTRL_")
    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_"):
            obj.hide_set(True)
            obj.hide_viewport = True


def main():
    ensure_clean()
    clear_old()
    dayz = bpy.data.objects.get(DAYZ)
    if not dayz or dayz.type != "ARMATURE":
        raise RuntimeError(f"{DAYZ} not found")

    rig = make_proxy_rig(dayz)
    copied = add_dayz_follow(dayz, rig)
    add_bake_text()
    visibility(dayz, rig)
    bpy.context.view_layer.update()
    mode_for(rig, "POSE")
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    result = {
        "source_clean_file": CLEAN_PATH,
        "saved_as": SAVE_PATH,
        "dayz_armature": DAYZ,
        "control_rig": CTRL,
        "visible_control_bones": [b.name for b in rig.data.bones if not b.hide],
        "hidden_proxy_bones": [b.name for b in rig.data.bones if b.hide],
        "dayz_follow_constraints": copied,
        "note": "Proxy IK rig: IK uses a clean 3-bone arm chain without DayZ roll bones. DayZ skeleton keeps rest locations and copies rotations only.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


RESULT = main()
