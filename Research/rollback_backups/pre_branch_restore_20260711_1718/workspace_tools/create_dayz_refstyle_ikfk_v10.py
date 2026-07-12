import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BASE_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refstyle_controls_wire_v8.blend"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refstyle_ikfk_v10.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-refstyle-ikfk-v10-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
RIG = "DAT_DayZ_RefStyleControlsWireV8"
PREFIX = "DAT_IKFK_"

SIDES = {
    "L": ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"],
    "R": ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand"],
}


def w_mat(obj, bone):
    return obj.matrix_world @ obj.pose.bones[bone].matrix


def w_head(obj, bone):
    return obj.matrix_world @ obj.pose.bones[bone].head


def w_tail(obj, bone):
    return obj.matrix_world @ obj.pose.bones[bone].tail


def rows(m):
    return [list(r) for r in m]


def clear_old(export, rig):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    for pb in export.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith(PREFIX):
                pb.constraints.remove(c)
    for pb in rig.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith(PREFIX):
                pb.constraints.remove(c)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="EDIT")
    for b in list(rig.data.edit_bones):
        if b.name.startswith("FK_"):
            rig.data.edit_bones.remove(b)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="OBJECT")


def set_roll_from_world_axis(eb, axis):
    if axis.length > 0.0001:
        eb.align_roll(axis.normalized())


def make_fk_bones(export, rig):
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="EDIT")
    created = []
    for side, bones in SIDES.items():
        prev = None
        for bone in bones:
            name = f"FK_{bone}.{side}"
            eb = rig.data.edit_bones.new(name)
            eb.head = w_head(export, bone)
            eb.tail = w_tail(export, bone)
            if (eb.tail - eb.head).length < 0.025:
                eb.tail = eb.head + Vector((0, 0, 0.08))
            axis = (w_mat(export, bone).to_3x3() @ Vector((0, 0, 1))).normalized()
            set_roll_from_world_axis(eb, axis)
            if prev:
                eb.parent = rig.data.edit_bones[prev]
                eb.use_connect = False
            eb.use_deform = False
            prev = name
            created.append(name)
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="POSE")
    joint_shape = bpy.data.objects.get("WGT_DAT_Joint_Wire_Large") or bpy.data.objects.get("WGT_DAT_Joint_Disc_Clickable")
    roll_shape = bpy.data.objects.get("WGT_DAT_Roll_Wire_Large") or bpy.data.objects.get("WGT_DAT_Roll_Rect_Clickable")
    hand_shape = bpy.data.objects.get("WGT_DAT_Hand_Wire_Large") or bpy.data.objects.get("WGT_DAT_Hand_Plate_Clickable")
    for pb in rig.pose.bones:
        if not pb.name.startswith("FK_"):
            continue
        pb.color.palette = "THEME10"
        if "Roll" in pb.name:
            pb.custom_shape = roll_shape
        elif "Hand" in pb.name:
            pb.custom_shape = hand_shape
        else:
            pb.custom_shape = joint_shape
        pb.custom_shape_scale_xyz = (1.5, 1.5, 1.5)
        if hasattr(pb, "use_custom_shape_bone_size"):
            pb.use_custom_shape_bone_size = False
        pb.lock_location[0] = True
        pb.lock_location[1] = True
        pb.lock_location[2] = True
        pb.lock_scale[0] = True
        pb.lock_scale[1] = True
        pb.lock_scale[2] = True
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode="OBJECT")
    return created


def add_driver(constraint, rig, side, expression):
    fcurve = constraint.driver_add("influence")
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    drv.expression = expression
    var = drv.variables.new()
    var.name = "v"
    var.type = "SINGLE_PROP"
    var.targets[0].id = rig
    var.targets[0].data_path = f'["IK_FK_{side}"]'


def add_fk_constraints(export, rig):
    added = []
    for side, bones in SIDES.items():
        rig[f"IK_FK_{side}"] = 1.0
        for bone in bones:
            pb = export.pose.bones[bone]
            for c in pb.constraints:
                if c.name.startswith("DAT_REFWIRE8_ROT_"):
                    add_driver(c, rig, side, "v")
            c = pb.constraints.new(type="COPY_ROTATION")
            c.name = PREFIX + "FK_ROT_" + bone
            c.target = rig
            c.subtarget = f"FK_{bone}.{side}"
            c.target_space = "WORLD"
            c.owner_space = "WORLD"
            c.mix_mode = "REPLACE"
            c.influence = 0.0
            add_driver(c, rig, side, "1-v")
            added.append(c.name)
    return added


def add_switch_text():
    old = bpy.data.texts.get("DAT_IKFK_SWITCH")
    if old:
        bpy.data.texts.remove(old)
    text = bpy.data.texts.new("DAT_IKFK_SWITCH")
    text.write(
        "import bpy\n"
        "rig = bpy.data.objects['DAT_DayZ_RefStyleControlsWireV8']\n"
        "def left_ik(): rig['IK_FK_L'] = 1.0; bpy.context.view_layer.update()\n"
        "def left_fk(): rig['IK_FK_L'] = 0.0; bpy.context.view_layer.update()\n"
        "def right_ik(): rig['IK_FK_R'] = 1.0; bpy.context.view_layer.update()\n"
        "def right_fk(): rig['IK_FK_R'] = 0.0; bpy.context.view_layer.update()\n"
    )


def snapshot(export):
    return {bone: w_mat(export, bone).copy() for side in SIDES.values() for bone in side}


def deltas(export, before):
    out = []
    for side in SIDES.values():
        for bone in side:
            now = w_mat(export, bone)
            old = before[bone]
            out.append({
                "bone": bone,
                "loc_delta": (now.translation - old.translation).length,
                "rot_delta_deg": old.to_quaternion().rotation_difference(now.to_quaternion()).angle * 180 / math.pi,
            })
    return out


def test_fk_inheritance(export, rig):
    before = snapshot(export)
    rig["IK_FK_L"] = 0.0
    bpy.context.view_layer.update()
    fore = rig.pose.bones["FK_LeftForeArm.L"]
    orig = fore.matrix_basis.copy()
    fore.matrix_basis = Matrix.Rotation(math.radians(35.0), 4, "Z") @ fore.matrix_basis
    bpy.context.view_layer.update()
    moved = snapshot(export)
    fore.matrix_basis = orig
    rig["IK_FK_L"] = 1.0
    bpy.context.view_layer.update()
    return deltas(export, before), deltas_from_snap(before, moved)


def deltas_from_snap(before, moved):
    out = []
    for side in SIDES.values():
        for bone in side:
            old = before[bone]
            now = moved[bone]
            out.append({
                "bone": bone,
                "loc_delta": (now.translation - old.translation).length,
                "rot_delta_deg": old.to_quaternion().rotation_difference(now.to_quaternion()).angle * 180 / math.pi,
            })
    return out


def main():
    if bpy.data.filepath != BASE_BLEND:
        bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    export = bpy.data.objects[EXPORT_ARMATURE]
    rig = bpy.data.objects[RIG]
    before = snapshot(export)
    clear_old(export, rig)
    created = make_fk_bones(export, rig)
    added = add_fk_constraints(export, rig)
    add_switch_text()
    bpy.context.view_layer.update()
    neutral = deltas(export, before)
    neutral_ok = max(d["rot_delta_deg"] for d in neutral) < 0.25 and max(d["loc_delta"] for d in neutral) < 0.001
    fk_reset_delta, fk_moved_delta = test_fk_inheritance(export, rig)
    hand_move = next(d for d in fk_moved_delta if d["bone"] == "LeftHand")
    fore_move = next(d for d in fk_moved_delta if d["bone"] == "LeftForeArm")
    fk_ok = hand_move["rot_delta_deg"] > 1.0 and fore_move["rot_delta_deg"] > 1.0
    report = {
        "base": BASE_BLEND,
        "out": OUT_BLEND,
        "created": created,
        "constraints": added,
        "neutral": neutral,
        "neutral_ok": neutral_ok,
        "fk_moved_delta": fk_moved_delta,
        "fk_ok": fk_ok,
        "note": "Default mode is IK. Set rig custom prop IK_FK_L/R to 0 for FK joint rotation controls.",
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    if neutral_ok and fk_ok:
        bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
        report["saved"] = OUT_BLEND
    else:
        report["saved"] = None
    return report


RESULT = main()
