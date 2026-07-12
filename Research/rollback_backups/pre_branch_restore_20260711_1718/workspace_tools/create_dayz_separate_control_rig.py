import json
import math
import os

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "dayz-separate-control-rig-result.json")
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_separate_controlrig.blend"
DAYZ_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_ControlRig"


SIDES = {
    "L": {
        "upper": "LeftArm",
        "fore": "LeftForeArm",
        "hand": "LeftHand",
        "hand_ctrl": "CTRL_Hand.L",
        "elbow_ctrl": "CTRL_Elbow.L",
        "helper_hand": ["LeftHandIKTarget", "LeftHandOrigin", "LeftHandIK"],
        "helper_elbow": ["LeftForeArmDirection", "LeftForeArmDirectionOrigin"],
    },
    "R": {
        "upper": "RightArm",
        "fore": "RightForeArm",
        "hand": "RightHand",
        "hand_ctrl": "CTRL_Hand.R",
        "elbow_ctrl": "CTRL_Elbow.R",
        "helper_hand": ["RightHandOrigin", "RightHandIK"],
        "helper_elbow": ["RightForeArmDirection", "RightForeArmDirectionOrigin"],
    },
}


def mode(mode_name):
    if bpy.context.mode != mode_name:
        bpy.ops.object.mode_set(mode=mode_name)


def world_head(arm, bone_name):
    return arm.matrix_world @ arm.pose.bones[bone_name].head


def world_tail(arm, bone_name):
    return arm.matrix_world @ arm.pose.bones[bone_name].tail


def pole_pos(arm, side_data, side):
    shoulder = world_head(arm, side_data["upper"])
    elbow = world_head(arm, side_data["fore"])
    hand = world_head(arm, side_data["hand"])
    axis = hand - shoulder
    if axis.length < 0.0001:
        axis = Vector((0, -1, 0))
    axis.normalize()
    bend = elbow - shoulder
    plane = bend - axis * bend.dot(axis)
    if plane.length < 0.0001:
        plane = Vector((-1 if side == "L" else 1, -0.25, 0))
    plane.normalize()
    # Put poles in front/outside so moving them behaves like elbow controls.
    outside = Vector((-0.18 if side == "L" else 0.18, -0.12, 0.0))
    return elbow + plane * 0.35 + outside


def ensure_control_rig(dayz):
    existing = bpy.data.objects.get(CONTROL_RIG)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    arm_data = bpy.data.armatures.new(CONTROL_RIG)
    obj = bpy.data.objects.new(CONTROL_RIG, arm_data)
    bpy.context.collection.objects.link(obj)
    obj.show_in_front = True
    obj.matrix_world = dayz.matrix_world.copy()

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mode("EDIT")

    inv = obj.matrix_world.inverted()
    for side, sd in SIDES.items():
        hand = world_head(dayz, sd["hand"])
        elbow = pole_pos(dayz, sd, side)

        eb = obj.data.edit_bones.new(sd["hand_ctrl"])
        eb.head = inv @ hand
        eb.tail = inv @ (hand + Vector((0, 0, 0.18)))
        eb.use_connect = False

        eb = obj.data.edit_bones.new(sd["elbow_ctrl"])
        eb.head = inv @ elbow
        eb.tail = inv @ (elbow + Vector((0, 0, 0.16)))
        eb.use_connect = False

    mode("POSE")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb["dat_role"] = "animator_control"

    return obj


def remove_preview_constraints(dayz):
    removed = []
    mode("POSE")
    for pb in dayz.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DAT Preview"):
                removed.append({"bone": pb.name, "constraint": c.name, "type": c.type})
                pb.constraints.remove(c)
    return removed


def add_ik(dayz, ctrl, side, sd):
    hand_pb = dayz.pose.bones.get(sd["hand"])
    if not hand_pb:
        return None
    con = hand_pb.constraints.new(type="IK")
    con.name = "DAT Preview Arm IK"
    con.target = ctrl
    con.subtarget = sd["hand_ctrl"]
    con.pole_target = ctrl
    con.pole_subtarget = sd["elbow_ctrl"]
    con.pole_angle = math.radians(-90.0)
    con.chain_count = 2
    con.use_rotation = True
    con.use_stretch = False
    con.influence = 1.0
    return {"bone": sd["hand"], "target": sd["hand_ctrl"], "pole": sd["elbow_ctrl"]}


def add_helper_follow(dayz, ctrl, sd):
    made = []
    for helper in sd["helper_hand"]:
        pb = dayz.pose.bones.get(helper)
        if not pb:
            continue
        loc = pb.constraints.new(type="COPY_LOCATION")
        loc.name = "DAT Preview Helper Follow Location"
        loc.target = ctrl
        loc.subtarget = sd["hand_ctrl"]
        loc.target_space = "WORLD"
        loc.owner_space = "WORLD"
        loc.influence = 1.0
        rot = pb.constraints.new(type="COPY_ROTATION")
        rot.name = "DAT Preview Helper Follow Rotation"
        rot.target = ctrl
        rot.subtarget = sd["hand_ctrl"]
        rot.target_space = "WORLD"
        rot.owner_space = "WORLD"
        rot.influence = 1.0
        made.append({"bone": helper, "target": sd["hand_ctrl"]})

    for helper in sd["helper_elbow"]:
        pb = dayz.pose.bones.get(helper)
        if not pb:
            continue
        loc = pb.constraints.new(type="COPY_LOCATION")
        loc.name = "DAT Preview Helper Follow Location"
        loc.target = ctrl
        loc.subtarget = sd["elbow_ctrl"]
        loc.target_space = "WORLD"
        loc.owner_space = "WORLD"
        loc.influence = 1.0
        made.append({"bone": helper, "target": sd["elbow_ctrl"]})
    return made


def visibility(dayz, ctrl):
    # Keep export skeleton mostly clean; animator handles are in DAT_ControlRig.
    dayz_keep = {
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightShoulder", "RightArm", "RightForeArm", "RightHand",
        "Weapon_Root", "Weapon_Magazine", "Weapon_Trigger", "Weapon_Bolt",
    }
    for b in dayz.data.bones:
        b.hide = b.name not in dayz_keep
    for b in ctrl.data.bones:
        b.hide = False

    coll = bpy.data.collections.get("BoneShapes")
    if coll:
        coll.hide_viewport = True
    for obj in bpy.data.objects:
        if obj.name.startswith("zJD_"):
            obj.hide_set(True)
            obj.hide_viewport = True


def add_bake_script_text():
    body = r'''import bpy

DAYZ_ARMATURE = "_DayZ_Character"

def bake_preview_constraints_to_action(action_name="DAT_Baked_WeaponPose", frame_start=None, frame_end=None):
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
    bones = ["LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand"]
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for name in bones:
            pb = arm.pose.bones.get(name)
            if not pb:
                continue
            pb.keyframe_insert("location", frame=frame)
            pb.keyframe_insert("rotation_quaternion", frame=frame)
            pb.keyframe_insert("scale", frame=frame)
    return action

print("DAT bake helper loaded. Call bake_preview_constraints_to_action().")
'''
    if "DAT_Bake_Preview_To_Action.py" in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts["DAT_Bake_Preview_To_Action.py"])
    text = bpy.data.texts.new("DAT_Bake_Preview_To_Action.py")
    text.write(body)


def main():
    mode("OBJECT")
    dayz = bpy.data.objects.get(DAYZ_ARMATURE)
    if dayz is None or dayz.type != "ARMATURE":
        raise RuntimeError(f"{DAYZ_ARMATURE} armature not found")

    dayz.select_set(True)
    bpy.context.view_layer.objects.active = dayz
    mode("POSE")
    removed = remove_preview_constraints(dayz)

    mode("OBJECT")
    ctrl = ensure_control_rig(dayz)

    dayz.select_set(True)
    bpy.context.view_layer.objects.active = dayz
    mode("POSE")
    ik = []
    helper = []
    for side, sd in SIDES.items():
        row = add_ik(dayz, ctrl, side, sd)
        if row:
            ik.append(row)
        helper.extend(add_helper_follow(dayz, ctrl, sd))

    visibility(dayz, ctrl)
    add_bake_script_text()

    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    result = {
        "saved_as": SAVE_PATH,
        "dayz_armature": DAYZ_ARMATURE,
        "control_rig": CONTROL_RIG,
        "removed_old_preview_constraints": removed,
        "ik_constraints": ik,
        "helper_follow_constraints": helper,
        "visible_dayz_bones": sorted([b.name for b in dayz.data.bones if not b.hide]),
        "control_bones": sorted([b.name for b in ctrl.data.bones]),
        "note": "Separate non-export control rig. Animator moves DAT_ControlRig CTRL_Hand.* and CTRL_Elbow.*. DayZ skeleton contains preview constraints only; bake before final export.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


if __name__ == "__main__":
    RESULT = main()
    print(json.dumps(RESULT, indent=2))
