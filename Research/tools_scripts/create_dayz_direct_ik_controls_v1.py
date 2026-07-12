import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BASE_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_controlrig_v1.blend"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_direct_ik_controls_v1.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-direct-ik-controls-v1-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
CONTROL_RIG = "DAT_DayZ_IKControls"
PREFIX = "DAT_DAYZ_DIRECT_IK_"

SIDES = {
    "L": {
        "upper": "LeftArm",
        "roll_upper": "LeftArmRoll",
        "fore": "LeftForeArm",
        "roll_fore": "LeftForeArmRoll",
        "hand": "LeftHand",
    },
    "R": {
        "upper": "RightArm",
        "roll_upper": "RightArmRoll",
        "fore": "RightForeArm",
        "roll_fore": "RightForeArmRoll",
        "hand": "RightHand",
    },
}


def remove_old():
    obj = bpy.data.objects.get(CONTROL_RIG)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
    export = bpy.data.objects.get(EXPORT_ARMATURE)
    if export:
        for pb in export.pose.bones:
            for con in list(pb.constraints):
                if con.name.startswith(PREFIX):
                    pb.constraints.remove(con)


def world_point(obj, bone_name, point):
    pb = obj.pose.bones[bone_name]
    return obj.matrix_world @ (pb.head if point == "head" else pb.tail)


def make_control_rig(export):
    data = bpy.data.armatures.new(CONTROL_RIG + "_Data")
    rig = bpy.data.objects.new(CONTROL_RIG, data)
    bpy.context.collection.objects.link(rig)
    rig.matrix_world = Matrix.Identity(4)
    data.display_type = "STICK"
    data.show_names = True

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for side, names in SIDES.items():
        hand_head = world_point(export, names["hand"], "head")
        hand_tail = world_point(export, names["hand"], "tail")
        elbow = world_point(export, names["fore"], "head")
        shoulder = world_point(export, names["upper"], "head")
        pole_dir = elbow - ((shoulder + hand_head) * 0.5)
        if pole_dir.length < 0.05:
            pole_dir = Vector((-1, 0, 0)) if side == "L" else Vector((1, 0, 0))
        pole = elbow + pole_dir.normalized() * 0.35

        hand_dir = hand_tail - hand_head
        if hand_dir.length < 0.05:
            hand_dir = Vector((0, 0, 0.15))
        eb = data.edit_bones.new(f"CTRL_Hand.{side}")
        eb.head = hand_tail
        eb.tail = hand_tail + hand_dir.normalized() * 0.18
        eb.roll = 0

        eb = data.edit_bones.new(f"CTRL_Elbow.{side}")
        eb.head = pole
        eb.tail = pole + Vector((0, 0, 0.14))
        eb.roll = 0

    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig.pose.bones:
        pb.color.palette = "THEME09"
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def save_basis(export):
    return {pb.name: pb.matrix_basis.copy() for pb in export.pose.bones}


def restore_basis(export, basis):
    for name, matrix in basis.items():
        pb = export.pose.bones.get(name)
        if pb:
            pb.matrix_basis = matrix.copy()
    bpy.context.view_layer.update()


def world_mats(export, names):
    return {name: (export.matrix_world @ export.pose.bones[name].matrix).copy() for name in names}


def delta_score(export, before, names):
    score = 0.0
    details = []
    for name in names:
        now = export.matrix_world @ export.pose.bones[name].matrix
        loc = (now.translation - before[name].translation).length
        rot = before[name].to_quaternion().rotation_difference(now.to_quaternion()).angle
        score += loc * 10.0 + rot
        details.append({"bone": name, "loc_delta": loc, "rot_delta_deg": rot * 180.0 / math.pi})
    return score, details


def add_ik_constraint(export, rig, side, chain_count, pole_angle):
    hand = SIDES[side]["hand"]
    pb = export.pose.bones[hand]
    con = pb.constraints.new(type="IK")
    con.name = PREFIX + side
    con.target = rig
    con.subtarget = f"CTRL_Hand.{side}"
    con.pole_target = rig
    con.pole_subtarget = f"CTRL_Elbow.{side}"
    con.chain_count = chain_count
    con.pole_angle = pole_angle
    con.use_rotation = True
    con.use_stretch = False
    con.influence = 1.0
    return con


def tune_side(export, rig, side):
    names = [SIDES[side][k] for k in ("upper", "roll_upper", "fore", "roll_fore", "hand")]
    basis = save_basis(export)
    before = world_mats(export, names)
    best = None
    tests = []
    for chain_count in (3, 4, 5):
        for pole_angle in [i * math.pi / 8.0 for i in range(-8, 9)]:
            restore_basis(export, basis)
            pb = export.pose.bones[SIDES[side]["hand"]]
            for con in list(pb.constraints):
                if con.name.startswith(PREFIX):
                    pb.constraints.remove(con)
            add_ik_constraint(export, rig, side, chain_count, pole_angle)
            bpy.context.view_layer.update()
            score, details = delta_score(export, before, names)
            item = {
                "chain_count": chain_count,
                "pole_angle": pole_angle,
                "score": score,
                "details": details,
            }
            tests.append(item)
            if best is None or score < best["score"]:
                best = item

    restore_basis(export, basis)
    pb = export.pose.bones[SIDES[side]["hand"]]
    for con in list(pb.constraints):
        if con.name.startswith(PREFIX):
            pb.constraints.remove(con)
    add_ik_constraint(export, rig, side, best["chain_count"], best["pole_angle"])
    bpy.context.view_layer.update()
    _, neutral_details = delta_score(export, before, names)
    return best, neutral_details, sorted(tests, key=lambda x: x["score"])[:5]


def movement_test(export, rig, side):
    names = [SIDES[side][k] for k in ("upper", "roll_upper", "fore", "roll_fore", "hand")]
    ctrl = rig.pose.bones[f"CTRL_Hand.{side}"]
    orig = ctrl.matrix_basis.copy()
    before = world_mats(export, names)
    ctrl.location.x += 0.08
    bpy.context.view_layer.update()
    _, details = delta_score(export, before, names)
    ctrl.matrix_basis = orig
    bpy.context.view_layer.update()
    return details


def show_authoring_scene(export, rig):
    export.hide_set(False)
    export.hide_select = False
    export.show_in_front = False
    export.data.show_names = False
    rig.hide_set(False)
    rig.hide_select = False
    rig.show_in_front = True
    rig.data.show_names = True
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.name in {"Female_body", "1", "1.001"}:
                obj.hide_set(False)
            elif obj.name in {"zMale_body", "zEntityPosition", "EntityPosition"}:
                obj.hide_set(True)
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")


def add_bake_text():
    for name in ["DAT_DIRECT_IK_BAKE", "DAT_REFBAKE_HELPERS", "DAT_Bake_TrueJoint_ControlRig.py"]:
        text = bpy.data.texts.get(name)
        if text:
            bpy.data.texts.remove(text)
    text = bpy.data.texts.new("DAT_DIRECT_IK_BAKE")
    text.write(
        """# DAT_DIRECT_IK_BAKE
import bpy

EXPORT_ARMATURE = "_DayZ_Character"
DRIVEN_BONES = [
    "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
    "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
]


def bake_current_frame():
    obj = bpy.data.objects[EXPORT_ARMATURE]
    bpy.context.view_layer.update()
    for name in DRIVEN_BONES:
        pb = obj.pose.bones[name]
        pb.keyframe_insert("location")
        if pb.rotation_mode == "QUATERNION":
            pb.keyframe_insert("rotation_quaternion")
        elif pb.rotation_mode == "AXIS_ANGLE":
            pb.keyframe_insert("rotation_axis_angle")
        else:
            pb.keyframe_insert("rotation_euler")


def bake_frame_range(start=None, end=None):
    scene = bpy.context.scene
    if start is None:
        start = scene.frame_start
    if end is None:
        end = scene.frame_end
    current = scene.frame_current
    for frame in range(int(start), int(end) + 1):
        scene.frame_set(frame)
        bake_current_frame()
    scene.frame_set(current)
"""
    )


def main():
    if bpy.data.filepath != BASE_BLEND:
        bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)

    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    export = bpy.data.objects.get(EXPORT_ARMATURE)
    if not export:
        raise RuntimeError(f"Missing {EXPORT_ARMATURE}")
    remove_old()
    rig = make_control_rig(export)
    report = {"base_blend": BASE_BLEND, "out_blend": OUT_BLEND, "sides": {}}
    for side in ("L", "R"):
        best, neutral_details, top = tune_side(export, rig, side)
        move = movement_test(export, rig, side)
        report["sides"][side] = {
            "best": best,
            "neutral_details": neutral_details,
            "move_test": move,
            "top_candidates": top,
        }
    add_bake_text()
    show_authoring_scene(export, rig)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    report["saved"] = OUT_BLEND
    return report


RESULT = main()
