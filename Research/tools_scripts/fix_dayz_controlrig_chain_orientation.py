import json
import os

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "dayz-controlrig-chain-orientation-fix.json")
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_separate_controlrig_v2.blend"
DAYZ = "_DayZ_Character"
CTRL = "DAT_ControlRig"

SIDES = {
    "L": {
        "hand": "LeftHand",
        "fore": "LeftForeArm",
        "arm": "LeftArm",
        "hand_ctrl": "CTRL_Hand.L",
        "elbow_ctrl": "CTRL_Elbow.L",
    },
    "R": {
        "hand": "RightHand",
        "fore": "RightForeArm",
        "arm": "RightArm",
        "hand_ctrl": "CTRL_Hand.R",
        "elbow_ctrl": "CTRL_Elbow.R",
    },
}


def mode(name):
    if bpy.context.mode != name:
        bpy.ops.object.mode_set(mode=name)


def world_head(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].head


def world_tail(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].tail


def elbow_pole(arm, side, sd):
    shoulder = world_head(arm, sd["arm"])
    elbow = world_head(arm, sd["fore"])
    hand = world_head(arm, sd["hand"])
    axis = hand - shoulder
    if axis.length < 0.0001:
        axis = Vector((0, -1, 0))
    axis.normalize()
    bend = elbow - shoulder
    plane = bend - axis * bend.dot(axis)
    if plane.length < 0.0001:
        plane = Vector((-1 if side == "L" else 1, -0.2, 0))
    plane.normalize()
    outside = Vector((-0.22 if side == "L" else 0.22, -0.18, 0.0))
    return elbow + plane * 0.35 + outside


def ensure_controls(dayz, ctrl):
    mode("OBJECT")
    bpy.context.view_layer.objects.active = ctrl
    ctrl.select_set(True)
    mode("EDIT")
    inv = ctrl.matrix_world.inverted()
    changed = []
    for side, sd in SIDES.items():
        hand_head = world_head(dayz, sd["hand"])
        hand_tail = world_tail(dayz, sd["hand"])
        eb = ctrl.data.edit_bones.get(sd["hand_ctrl"]) or ctrl.data.edit_bones.new(sd["hand_ctrl"])
        # Match target orientation to the DayZ hand bone so use_rotation does not twist the hand.
        eb.head = inv @ hand_head
        eb.tail = inv @ hand_tail
        eb.roll = 0.0
        eb.use_connect = False
        eb.parent = None
        changed.append(sd["hand_ctrl"])

        pole = elbow_pole(dayz, side, sd)
        eb = ctrl.data.edit_bones.get(sd["elbow_ctrl"]) or ctrl.data.edit_bones.new(sd["elbow_ctrl"])
        eb.head = inv @ pole
        eb.tail = inv @ (pole + Vector((0, 0, 0.16)))
        eb.roll = 0.0
        eb.use_connect = False
        eb.parent = None
        changed.append(sd["elbow_ctrl"])
    mode("POSE")
    for pb in ctrl.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return changed


def fix_ik(dayz, ctrl):
    mode("OBJECT")
    bpy.context.view_layer.objects.active = dayz
    dayz.select_set(True)
    mode("POSE")
    fixed = []
    for side, sd in SIDES.items():
        pb = dayz.pose.bones.get(sd["hand"])
        if not pb:
            continue
        for c in list(pb.constraints):
            if c.name.startswith("DAT Preview Arm IK"):
                pb.constraints.remove(c)
        c = pb.constraints.new(type="IK")
        c.name = "DAT Preview Arm IK"
        c.target = ctrl
        c.subtarget = sd["hand_ctrl"]
        c.pole_target = ctrl
        c.pole_subtarget = sd["elbow_ctrl"]
        # Include Hand, ForeArmRoll, ForeArm, ArmRoll, Arm. With count 2 only the wrist/roll moves.
        c.chain_count = 5
        c.use_rotation = True
        c.use_stretch = False
        c.influence = 1.0
        # Keep both sides consistent first; pole position can be tuned visually after this.
        c.pole_angle = -1.57079632679
        fixed.append({
            "bone": sd["hand"],
            "target": sd["hand_ctrl"],
            "pole": sd["elbow_ctrl"],
            "chain_count": c.chain_count,
            "pole_angle": c.pole_angle,
        })
    return fixed


def show_only_useful(dayz, ctrl):
    dayz_keep = {
        "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
        "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    for b in dayz.data.bones:
        b.hide = b.name not in dayz_keep
    for b in ctrl.data.bones:
        b.hide = False


def main():
    dayz = bpy.data.objects.get(DAYZ)
    ctrl = bpy.data.objects.get(CTRL)
    if not dayz or dayz.type != "ARMATURE":
        raise RuntimeError(f"{DAYZ} not found")
    if not ctrl or ctrl.type != "ARMATURE":
        raise RuntimeError(f"{CTRL} not found")

    changed_controls = ensure_controls(dayz, ctrl)
    fixed_ik = fix_ik(dayz, ctrl)
    show_only_useful(dayz, ctrl)
    bpy.context.view_layer.update()
    mode("OBJECT")
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)
    data = {
        "saved_as": SAVE_PATH,
        "changed_controls": sorted(changed_controls),
        "fixed_ik": fixed_ik,
        "note": "Fixed control orientation to match hand bones and chain_count to include roll bones/whole arm.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
