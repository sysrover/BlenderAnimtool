import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BASE_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refstyle_controls_wire_v8.blend"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refstyle_local_tweak_v9.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-refstyle-local-tweak-v9-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
RIG = "DAT_DayZ_RefStyleLocalTweakV9"
PREFIX = "DAT_REFTWEAK9_"
COPY_MIX_MODE = "REPLACE"
FORCED_POLES = {
    "R": 2.748893571891069,
}

SIDES = {
    "L": {
        "arm": "LeftArm",
        "arm_roll": "LeftArmRoll",
        "fore": "LeftForeArm",
        "fore_roll": "LeftForeArmRoll",
        "hand": "LeftHand",
    },
    "R": {
        "arm": "RightArm",
        "arm_roll": "RightArmRoll",
        "fore": "RightForeArm",
        "fore_roll": "RightForeArmRoll",
        "hand": "RightHand",
    },
}

TRACKED = [
    "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
    "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
]


def clear_old(export):
    for obj in list(bpy.data.objects):
        if obj.name.startswith("DAT_DayZ_") or obj.name == RIG:
            bpy.data.objects.remove(obj, do_unlink=True)
    for pb in export.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DAT_") or c.name.startswith(PREFIX):
                pb.constraints.remove(c)


def w_mat(export, bone):
    return export.matrix_world @ export.pose.bones[bone].matrix


def w_head(export, bone):
    return export.matrix_world @ export.pose.bones[bone].head


def w_tail(export, bone):
    return export.matrix_world @ export.pose.bones[bone].tail


def set_roll_from_world_axis(eb, axis):
    if axis.length > 0.0001:
        eb.align_roll(axis.normalized())


def make_edit_bone(data, name, head, tail, roll_axis=None, parent=None, hide=False):
    eb = data.edit_bones.new(name)
    eb.head = head
    eb.tail = tail
    if (eb.tail - eb.head).length < 0.025:
        eb.tail = eb.head + Vector((0, 0, 0.08))
    if parent:
        eb.parent = data.edit_bones[parent]
        eb.use_connect = False
    if roll_axis is not None:
        set_roll_from_world_axis(eb, roll_axis)
    eb.hide = hide
    return eb


def make_wire_shape(name, verts, edges):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.hide_set(True)
    obj.hide_viewport = True
    obj.hide_render = True
    return obj


def circle_points(radius, count=32, z=0.0):
    return [
        (
            math.cos((math.tau * i) / count) * radius,
            math.sin((math.tau * i) / count) * radius,
            z,
        )
        for i in range(count)
    ]


def loop_edges(count):
    return [(i, (i + 1) % count) for i in range(count)]


def create_control_shapes():
    hand_verts = [
        (-0.16, -0.07, 0.0),
        (-0.12, -0.11, 0.0),
        (0.12, -0.11, 0.0),
        (0.16, -0.07, 0.0),
        (0.16, 0.07, 0.0),
        (0.12, 0.11, 0.0),
        (-0.12, 0.11, 0.0),
        (-0.16, 0.07, 0.0),
    ]
    hand = make_wire_shape(
        "WGT_DAT_Hand_Wire_Large",
        hand_verts,
        loop_edges(8),
    )
    elbow_verts = circle_points(0.105, 40)
    elbow = make_wire_shape(
        "WGT_DAT_Elbow_Wire_Large",
        elbow_verts,
        loop_edges(40),
    )
    joint_verts = circle_points(0.085, 40)
    joint = make_wire_shape(
        "WGT_DAT_Joint_Wire_Large",
        joint_verts,
        loop_edges(40),
    )
    roll = make_wire_shape(
        "WGT_DAT_Roll_Wire_Large",
        [
            (-0.13, -0.035, 0.0),
            (0.13, -0.035, 0.0),
            (0.13, 0.035, 0.0),
            (-0.13, 0.035, 0.0),
        ],
        loop_edges(4),
    )
    return hand, elbow, joint, roll


def create_rig(export):
    if bpy.context.mode != "OBJECT" and bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    data = bpy.data.armatures.new(RIG + "_Data")
    rig = bpy.data.objects.new(RIG, data)
    bpy.context.collection.objects.link(rig)
    rig.matrix_world = Matrix.Identity(4)
    data.display_type = "STICK"
    data.show_names = True

    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.context.view_layer.update()
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="EDIT")

    created = []
    for side, spec in SIDES.items():
        shoulder = w_head(export, spec["arm"])
        elbow = w_head(export, spec["fore"])
        wrist = w_head(export, spec["hand"])
        hand_tail = w_tail(export, spec["hand"])

        arm_axis = (w_mat(export, spec["arm"]).to_3x3() @ Vector((0, 0, 1))).normalized()
        fore_axis = (w_mat(export, spec["fore"]).to_3x3() @ Vector((0, 0, 1))).normalized()
        hand_axis = (w_mat(export, spec["hand"]).to_3x3() @ Vector((0, 0, 1))).normalized()

        make_edit_bone(data, f"DRV_Arm.{side}", shoulder, elbow, arm_axis, hide=True)
        make_edit_bone(data, f"DRV_ForeArm.{side}", elbow, wrist, fore_axis, parent=f"DRV_Arm.{side}", hide=True)
        make_edit_bone(data, f"DRV_Hand.{side}", wrist, hand_tail, hand_axis, parent=f"DRV_ForeArm.{side}", hide=True)
        make_edit_bone(data, f"OUT_Arm.{side}", shoulder, elbow, arm_axis, parent=f"DRV_Arm.{side}", hide=True)
        make_edit_bone(
            data,
            f"OUT_ArmRoll.{side}",
            w_head(export, spec["arm_roll"]),
            w_tail(export, spec["arm_roll"]),
            (w_mat(export, spec["arm_roll"]).to_3x3() @ Vector((0, 0, 1))).normalized(),
            parent=f"DRV_Arm.{side}",
            hide=True,
        )
        make_edit_bone(data, f"OUT_ForeArm.{side}", elbow, wrist, fore_axis, parent=f"DRV_ForeArm.{side}", hide=True)
        make_edit_bone(
            data,
            f"OUT_ForeArmRoll.{side}",
            w_head(export, spec["fore_roll"]),
            w_tail(export, spec["fore_roll"]),
            (w_mat(export, spec["fore_roll"]).to_3x3() @ Vector((0, 0, 1))).normalized(),
            parent=f"DRV_ForeArm.{side}",
            hide=True,
        )
        make_edit_bone(data, f"OUT_Hand.{side}", wrist, hand_tail, hand_axis, parent=f"DRV_Hand.{side}", hide=True)

        hand_len = (hand_tail - wrist).length
        if hand_len < 0.05:
            hand_len = 0.11
        ctrl = make_edit_bone(
            data,
            f"CTRL_Hand.{side}",
            wrist,
            wrist + (hand_tail - wrist).normalized() * min(max(hand_len, 0.10), 0.14),
            hand_axis,
        )
        ctrl.use_deform = False

        pole_dir = elbow - ((shoulder + wrist) * 0.5)
        if pole_dir.length < 0.05:
            pole_dir = Vector((-0.35, 0, 0)) if side == "L" else Vector((0.35, 0, 0))
        pole_head = elbow + pole_dir.normalized() * 0.32
        pole = make_edit_bone(data, f"CTRL_Elbow.{side}", pole_head, pole_head + Vector((0, 0, 0.09)))
        pole.use_deform = False

        created.extend([
            f"DRV_Arm.{side}",
            f"DRV_ForeArm.{side}",
            f"DRV_Hand.{side}",
            f"OUT_Arm.{side}",
            f"OUT_ArmRoll.{side}",
            f"OUT_ForeArm.{side}",
            f"OUT_ForeArmRoll.{side}",
            f"OUT_Hand.{side}",
            f"CTRL_Hand.{side}",
            f"CTRL_Elbow.{side}",
        ])

    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="OBJECT")
    hand_shape, elbow_shape, joint_shape, roll_shape = create_control_shapes()
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="POSE")
    for pb in rig.pose.bones:
        if pb.name.startswith("CTRL_Hand."):
            pb.color.palette = "THEME09"
            pb.custom_shape = hand_shape
            pb.custom_shape_scale_xyz = (1.5, 1.5, 1.5)
        elif pb.name.startswith("CTRL_Elbow."):
            pb.color.palette = "THEME09"
            pb.custom_shape = elbow_shape
            pb.custom_shape_scale_xyz = (1.5, 1.5, 1.5)
        elif pb.name.startswith("OUT_ArmRoll.") or pb.name.startswith("OUT_ForeArmRoll."):
            pb.color.palette = "THEME04"
            pb.custom_shape = roll_shape
            pb.custom_shape_scale_xyz = (1.5, 1.5, 1.5)
            pb.lock_location[0] = True
            pb.lock_location[1] = True
            pb.lock_location[2] = True
            pb.lock_scale[0] = True
            pb.lock_scale[1] = True
            pb.lock_scale[2] = True
        elif pb.name.startswith("OUT_"):
            pb.color.palette = "THEME03"
            pb.custom_shape = joint_shape
            pb.custom_shape_scale_xyz = (1.5, 1.5, 1.5)
            pb.lock_location[0] = True
            pb.lock_location[1] = True
            pb.lock_location[2] = True
            pb.lock_scale[0] = True
            pb.lock_scale[1] = True
            pb.lock_scale[2] = True
        if pb.name.startswith(("CTRL_", "OUT_")) and hasattr(pb, "use_custom_shape_bone_size"):
            pb.use_custom_shape_bone_size = False
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="OBJECT")
    return rig, created


def add_copy(pb, rig, subtarget, name):
    for c in list(pb.constraints):
        if c.name.startswith(PREFIX + name) or c.name.startswith(PREFIX + "COPY_"):
            pb.constraints.remove(c)
    c = pb.constraints.new(type="COPY_TRANSFORMS")
    c.name = PREFIX + name
    c.target = rig
    c.subtarget = subtarget
    c.target_space = "WORLD"
    c.owner_space = "WORLD"
    c.mix_mode = COPY_MIX_MODE
    c.influence = 1.0
    return c


def add_export_rotation_follow(pb, rig, subtarget, name):
    for c in list(pb.constraints):
        if c.name.startswith(PREFIX + name) or c.name.startswith(PREFIX + "ROT_"):
            pb.constraints.remove(c)
    c = pb.constraints.new(type="COPY_ROTATION")
    c.name = PREFIX + name
    c.target = rig
    c.subtarget = subtarget
    c.target_space = "LOCAL"
    c.owner_space = "LOCAL"
    c.mix_mode = "REPLACE"
    c.influence = 1.0
    return c


def add_copy_rotation(pb, rig, subtarget, name):
    for c in list(pb.constraints):
        if c.name.startswith(PREFIX + name):
            pb.constraints.remove(c)
    c = pb.constraints.new(type="COPY_ROTATION")
    c.name = PREFIX + name
    c.target = rig
    c.subtarget = subtarget
    c.target_space = "WORLD"
    c.owner_space = "WORLD"
    c.mix_mode = "REPLACE"
    c.influence = 1.0
    return c


def setup_constraints(export, rig, pole_angles):
    for side, spec in SIDES.items():
        fore = rig.pose.bones[f"DRV_ForeArm.{side}"]
        for c in list(fore.constraints):
            if c.name.startswith(PREFIX):
                fore.constraints.remove(c)
        ik = fore.constraints.new(type="IK")
        ik.name = PREFIX + "IK_" + side
        ik.target = rig
        ik.subtarget = f"CTRL_Hand.{side}"
        ik.pole_target = rig
        ik.pole_subtarget = f"CTRL_Elbow.{side}"
        ik.chain_count = 2
        ik.pole_angle = pole_angles[side]
        ik.use_rotation = True
        ik.use_stretch = False
        ik.influence = 1.0

        hand = rig.pose.bones[f"DRV_Hand.{side}"]
        for c in list(hand.constraints):
            if c.name.startswith(PREFIX):
                hand.constraints.remove(c)
        add_copy_rotation(hand, rig, f"CTRL_Hand.{side}", "HAND_ROT_TO_CTRL_" + side)

        add_export_rotation_follow(export.pose.bones[spec["arm"]], rig, f"OUT_Arm.{side}", "ROT_" + spec["arm"])
        add_export_rotation_follow(export.pose.bones[spec["arm_roll"]], rig, f"OUT_ArmRoll.{side}", "ROT_" + spec["arm_roll"])
        add_export_rotation_follow(export.pose.bones[spec["fore"]], rig, f"OUT_ForeArm.{side}", "ROT_" + spec["fore"])
        add_export_rotation_follow(export.pose.bones[spec["fore_roll"]], rig, f"OUT_ForeArmRoll.{side}", "ROT_" + spec["fore_roll"])
        add_export_rotation_follow(export.pose.bones[spec["hand"]], rig, f"OUT_Hand.{side}", "ROT_" + spec["hand"])


def world_snapshot(export):
    return {bone: w_mat(export, bone).copy() for bone in TRACKED}


def delta(export, before):
    out = []
    for bone in TRACKED:
        now = w_mat(export, bone)
        old = before[bone]
        loc = (now.translation - old.translation).length
        rot = old.to_quaternion().rotation_difference(now.to_quaternion()).angle
        out.append({"bone": bone, "loc_delta": loc, "rot_delta_deg": rot * 180 / math.pi})
    return out


def side_score(items, side):
    names = set(SIDES[side].values())
    return sum((d["loc_delta"] * 10.0) + (d["rot_delta_deg"] * math.pi / 180.0) for d in items if d["bone"] in names)


def tune_poles(export, rig, before):
    best = {}
    angles = [i * math.pi / 8.0 for i in range(-8, 9)]
    for side in ("L", "R"):
        best_side = None
        for angle in angles:
            setup_constraints(export, rig, {side: angle, ("R" if side == "L" else "L"): 0.0})
            bpy.context.view_layer.update()
            items = delta(export, before)
            score = side_score(items, side)
            if best_side is None or score < best_side["score"]:
                best_side = {"pole_angle": angle, "score": score}
        best[side] = best_side
    for side, angle in FORCED_POLES.items():
        if side in best:
            best[side] = {"pole_angle": angle, "score": best[side]["score"], "forced": True}
    setup_constraints(export, rig, {"L": best["L"]["pole_angle"], "R": best["R"]["pole_angle"]})
    bpy.context.view_layer.update()
    return best


def set_out_offsets_to_export_neutral(rig, original_world):
    mapping = {
        "L": {
            "OUT_Arm.L": "LeftArm",
            "OUT_ArmRoll.L": "LeftArmRoll",
            "OUT_ForeArm.L": "LeftForeArm",
            "OUT_ForeArmRoll.L": "LeftForeArmRoll",
            "OUT_Hand.L": "LeftHand",
        },
        "R": {
            "OUT_Arm.R": "RightArm",
            "OUT_ArmRoll.R": "RightArmRoll",
            "OUT_ForeArm.R": "RightForeArm",
            "OUT_ForeArmRoll.R": "RightForeArmRoll",
            "OUT_Hand.R": "RightHand",
        },
    }
    inv = rig.matrix_world.inverted()
    bpy.context.view_layer.update()
    for side_map in mapping.values():
        for out_name, export_name in side_map.items():
            rig.pose.bones[out_name].matrix = inv @ original_world[export_name]
    bpy.context.view_layer.update()


def move_test(export, rig):
    before = world_snapshot(export)
    result = {}
    for side in ("L", "R"):
        ctrl = rig.pose.bones[f"CTRL_Hand.{side}"]
        orig = ctrl.matrix_basis.copy()
        ctrl.location.x += 0.08
        bpy.context.view_layer.update()
        result[side] = [d for d in delta(export, before) if d["bone"] in set(SIDES[side].values())]
        ctrl.matrix_basis = orig
        bpy.context.view_layer.update()
    return result


def chain_gaps(export, rig, amount=0.35):
    def dist(a, b):
        return ((export.matrix_world @ export.pose.bones[a].tail) - (export.matrix_world @ export.pose.bones[b].head)).length

    def side_gaps(side):
        spec = SIDES[side]
        return {
            "arm_to_roll": dist(spec["arm"], spec["arm_roll"]),
            "roll_to_fore": dist(spec["arm_roll"], spec["fore"]),
            "fore_to_roll": dist(spec["fore"], spec["fore_roll"]),
            "roll_to_hand": dist(spec["fore_roll"], spec["hand"]),
        }

    base = {"L": side_gaps("L"), "R": side_gaps("R")}
    moved = {}
    for side in ("L", "R"):
        ctrl = rig.pose.bones[f"CTRL_Hand.{side}"]
        orig = ctrl.matrix_basis.copy()
        ctrl.location.x += amount
        bpy.context.view_layer.update()
        moved[side] = side_gaps(side)
        ctrl.matrix_basis = orig
        bpy.context.view_layer.update()

    drift = {}
    max_drift = 0.0
    for side in ("L", "R"):
        drift[side] = {}
        for key, value in moved[side].items():
            d = abs(value - base[side][key])
            drift[side][key] = d
            max_drift = max(max_drift, d)
    return {"base": base, "moved": moved, "drift": drift, "max_drift": max_drift, "amount": amount}


def validation(neutral, movement):
    max_neutral_rot = max(d["rot_delta_deg"] for d in neutral)
    max_neutral_loc = max(d["loc_delta"] for d in neutral)
    moves = {}
    for side in ("L", "R"):
        names = SIDES[side]
        hand = next(d for d in movement[side] if d["bone"] == names["hand"])
        fore = next(d for d in movement[side] if d["bone"] == names["fore"])
        arm = next(d for d in movement[side] if d["bone"] == names["arm"])
        moves[side] = {
            "hand_loc": hand["loc_delta"],
            "fore_rot": fore["rot_delta_deg"],
            "arm_rot": arm["rot_delta_deg"],
        }
    ok = (
        max_neutral_rot < 0.25
        and max_neutral_loc < 0.001
        and moves["L"]["hand_loc"] > 0.03
        and moves["R"]["hand_loc"] > 0.03
        and abs(moves["L"]["arm_rot"]) < 90.0
        and abs(moves["R"]["arm_rot"]) < 90.0
        and (moves["L"]["fore_rot"] + moves["L"]["arm_rot"]) > 1.0
        and (moves["R"]["fore_rot"] + moves["R"]["arm_rot"]) > 1.0
    )
    return {
        "ok": ok,
        "max_neutral_rot_deg": max_neutral_rot,
        "max_neutral_loc": max_neutral_loc,
        "movement_summary": moves,
    }


def add_bake_text():
    old = bpy.data.texts.get("DAT_REFROT_BAKE")
    if old:
        bpy.data.texts.remove(old)
    text = bpy.data.texts.new("DAT_REFROT_BAKE")
    text.write(
        "# DAT_REFROT_BAKE\n"
        "import bpy\n"
        f"BONES = {TRACKED!r}\n"
        "def bake_current_frame():\n"
        f"    obj = bpy.data.objects[{EXPORT_ARMATURE!r}]\n"
        "    bpy.context.view_layer.update()\n"
        "    for name in BONES:\n"
        "        pb = obj.pose.bones[name]\n"
        "        pb.keyframe_insert('location')\n"
        "        if pb.rotation_mode == 'QUATERNION': pb.keyframe_insert('rotation_quaternion')\n"
        "        elif pb.rotation_mode == 'AXIS_ANGLE': pb.keyframe_insert('rotation_axis_angle')\n"
        "        else: pb.keyframe_insert('rotation_euler')\n"
    )


def show_scene(export, rig):
    export.hide_set(False)
    export.data.show_names = False
    rig.hide_set(False)
    rig.show_in_front = True
    rig.data.show_names = True
    for b in rig.data.bones:
        b.hide = b.name.startswith("DRV_")
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="POSE")


def main():
    if bpy.data.filepath != BASE_BLEND:
        bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    export = bpy.data.objects[EXPORT_ARMATURE]
    clear_old(export)
    rig, created = create_rig(export)
    before = world_snapshot(export)
    best = tune_poles(export, rig, before)
    set_out_offsets_to_export_neutral(rig, before)
    neutral = delta(export, before)
    movement = move_test(export, rig)
    check = validation(neutral, movement)
    continuity = chain_gaps(export, rig)
    check["max_chain_gap_drift"] = continuity["max_drift"]
    check["ok"] = check["ok"] and continuity["max_drift"] < 0.001
    add_bake_text()
    show_scene(export, rig)

    report = {
        "base": BASE_BLEND,
        "out": OUT_BLEND,
        "created": created,
        "best": best,
        "neutral": neutral,
        "movement": movement,
        "continuity": continuity,
        "validation": check,
        "visible_controls": [b.name for b in rig.data.bones if not b.hide],
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    if check["ok"]:
        bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
        report["saved"] = OUT_BLEND
    else:
        report["saved"] = None
    return report


RESULT = main()
