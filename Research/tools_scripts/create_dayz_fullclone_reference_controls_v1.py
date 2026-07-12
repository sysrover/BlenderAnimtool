import json
import math
import os

import bpy
from mathutils import Matrix, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BASE_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_refbake_controlrig_v1.blend"
OUT_BLEND = r"P:\Animation_Weapon\Weapon_template_aks74u_fullclone_reference_controls_v1.blend"
REPORT = os.path.join(ROOT, "anm", "dayz-fullclone-reference-controls-v1-report.json")

EXPORT_ARMATURE = "_DayZ_Character"
RIG = "DAT_DayZ_FullCloneControls"
PREFIX = "DAT_REF_FULLCLONE_"

SIDES = {
    "L": ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"],
    "R": ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand"],
}


def clear_old(export):
    obj = bpy.data.objects.get(RIG)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
    for pb in export.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith(PREFIX):
                pb.constraints.remove(c)


def w_head(export, name):
    return export.matrix_world @ export.pose.bones[name].head


def w_tail(export, name):
    return export.matrix_world @ export.pose.bones[name].tail


def w_mat(export, name):
    return export.matrix_world @ export.pose.bones[name].matrix


def create_rig(export):
    data = bpy.data.armatures.new(RIG + "_Data")
    rig = bpy.data.objects.new(RIG, data)
    bpy.context.collection.objects.link(rig)
    rig.matrix_world = Matrix.Identity(4)
    data.display_type = "STICK"
    data.show_names = True
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    created = []
    for side, bones in SIDES.items():
        for i, bone in enumerate(bones):
            eb = data.edit_bones.new("DRV_" + bone)
            eb.head = w_head(export, bone)
            eb.tail = w_tail(export, bone)
            if (eb.tail - eb.head).length < 0.02:
                eb.tail = eb.head + Vector((0, 0, 0.08))
            if i > 0:
                eb.parent = data.edit_bones["DRV_" + bones[i - 1]]
                eb.use_connect = False
            source_z = (w_mat(export, bone).to_3x3() @ Vector((0, 0, 1))).normalized()
            if source_z.length > 0:
                eb.align_roll(source_z)
            eb.hide = True
            created.append(eb.name)
        hand = bones[-1]
        hand_tail = w_tail(export, hand)
        hand_head = w_head(export, hand)
        hand_dir = hand_tail - hand_head
        if hand_dir.length < 0.04:
            hand_dir = Vector((0, 0, 0.12))
        eb = data.edit_bones.new(f"CTRL_Hand.{side}")
        eb.head = hand_tail
        eb.tail = hand_tail + hand_dir.normalized() * 0.18
        hand_z = (w_mat(export, hand).to_3x3() @ Vector((0, 0, 1))).normalized()
        if hand_z.length > 0:
            eb.align_roll(hand_z)
        created.append(eb.name)
        shoulder = w_head(export, bones[0])
        elbow = w_head(export, bones[2])
        wrist = w_head(export, bones[-1])
        pole_dir = elbow - ((shoulder + wrist) * 0.5)
        if pole_dir.length < 0.05:
            pole_dir = Vector((-1, 0, 0)) if side == "L" else Vector((1, 0, 0))
        pole = elbow + pole_dir.normalized() * 0.35
        eb = data.edit_bones.new(f"CTRL_Elbow.{side}")
        eb.head = pole
        eb.tail = pole + Vector((0, 0, 0.14))
        eb.roll = 0
        created.append(eb.name)
    bpy.ops.object.mode_set(mode="POSE")
    for pb in rig.pose.bones:
        if pb.name.startswith("CTRL_"):
            pb.color.palette = "THEME09"
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig, created


def save_export_basis(export):
    return {pb.name: pb.matrix_basis.copy() for pb in export.pose.bones}


def restore_export_basis(export, basis):
    for name, mat in basis.items():
        pb = export.pose.bones.get(name)
        if pb:
            pb.matrix_basis = mat.copy()
    bpy.context.view_layer.update()


def add_clone_ik(rig, side, chain_count, pole_angle):
    hand_name = "DRV_" + SIDES[side][-1]
    pb = rig.pose.bones[hand_name]
    for c in list(pb.constraints):
        if c.name.startswith(PREFIX):
            pb.constraints.remove(c)
    c = pb.constraints.new(type="IK")
    c.name = PREFIX + "IK_" + side
    c.target = rig
    c.subtarget = f"CTRL_Hand.{side}"
    c.pole_target = rig
    c.pole_subtarget = f"CTRL_Elbow.{side}"
    c.chain_count = chain_count
    c.pole_angle = pole_angle
    c.use_rotation = True
    c.use_stretch = False
    c.influence = 1.0
    return c


def add_export_copy_constraints(export, rig, influence=1.0):
    added = []
    for side, bones in SIDES.items():
        for bone in bones:
            pb = export.pose.bones[bone]
            for c in list(pb.constraints):
                if c.name.startswith(PREFIX + "COPY_"):
                    pb.constraints.remove(c)
            c = pb.constraints.new(type="COPY_TRANSFORMS")
            c.name = PREFIX + "COPY_DRV_" + bone
            c.target = rig
            c.subtarget = "DRV_" + bone
            c.target_space = "WORLD"
            c.owner_space = "WORLD"
            c.mix_mode = "REPLACE"
            c.influence = influence
            added.append(f"{bone}->{c.subtarget}")
    bpy.context.view_layer.update()
    return added


def world_before(export):
    return {bone: w_mat(export, bone).copy() for side in SIDES for bone in SIDES[side]}


def delta_details(export, before):
    details = []
    for side in SIDES:
        for bone in SIDES[side]:
            now = w_mat(export, bone)
            old = before[bone]
            loc = (now.translation - old.translation).length
            rot = old.to_quaternion().rotation_difference(now.to_quaternion()).angle
            details.append({"bone": bone, "loc_delta": loc, "rot_delta_deg": rot * 180 / math.pi})
    return details


def score_details(details):
    return sum(d["loc_delta"] * 10.0 + d["rot_delta_deg"] * math.pi / 180.0 for d in details)


def tune(export, rig):
    basis = save_export_basis(export)
    before = world_before(export)
    best = {}
    for side in ("L", "R"):
        best_side = None
        for chain in (3, 4, 5):
            for angle in [i * math.pi / 8.0 for i in range(-8, 9)]:
                restore_export_basis(export, basis)
                add_clone_ik(rig, side, chain, angle)
                add_export_copy_constraints(export, rig, 1.0)
                bpy.context.view_layer.update()
                details = [d for d in delta_details(export, before) if d["bone"] in SIDES[side]]
                score = score_details(details)
                if best_side is None or score < best_side["score"]:
                    best_side = {"chain_count": chain, "pole_angle": angle, "score": score, "details": details}
        restore_export_basis(export, basis)
        add_clone_ik(rig, side, best_side["chain_count"], best_side["pole_angle"])
        best[side] = best_side
    add_export_copy_constraints(export, rig, 1.0)
    bpy.context.view_layer.update()
    neutral = delta_details(export, before)
    return best, neutral


def move_test(export, rig):
    before = world_before(export)
    out = {}
    for side in ("L", "R"):
        ctrl = rig.pose.bones[f"CTRL_Hand.{side}"]
        orig = ctrl.matrix_basis.copy()
        ctrl.location.x += 0.08
        bpy.context.view_layer.update()
        out[side] = [d for d in delta_details(export, before) if d["bone"] in SIDES[side]]
        ctrl.matrix_basis = orig
        bpy.context.view_layer.update()
    return out


def show_scene(export, rig):
    export.hide_set(False)
    export.hide_select = False
    export.data.show_names = False
    rig.hide_set(False)
    rig.show_in_front = True
    rig.data.show_names = True
    for b in rig.data.bones:
        b.hide = b.name.startswith("DRV_")
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.hide_set(obj.name not in {"Female_body", "1", "1.001"})
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")


def add_bake_text():
    for name in ["DAT_FULLCLONE_BAKE"]:
        text = bpy.data.texts.get(name)
        if text:
            bpy.data.texts.remove(text)
    text = bpy.data.texts.new("DAT_FULLCLONE_BAKE")
    text.write("""# DAT_FULLCLONE_BAKE\n# With constraints active, keyframe the DayZ export arm bones.\nimport bpy\nBONES = [\"LeftArm\",\"LeftArmRoll\",\"LeftForeArm\",\"LeftForeArmRoll\",\"LeftHand\",\"RightArm\",\"RightArmRoll\",\"RightForeArm\",\"RightForeArmRoll\",\"RightHand\"]\ndef bake_current_frame():\n    obj=bpy.data.objects[\"_DayZ_Character\"]\n    bpy.context.view_layer.update()\n    for name in BONES:\n        pb=obj.pose.bones[name]\n        pb.keyframe_insert(\"location\")\n        if pb.rotation_mode == \"QUATERNION\": pb.keyframe_insert(\"rotation_quaternion\")\n        elif pb.rotation_mode == \"AXIS_ANGLE\": pb.keyframe_insert(\"rotation_axis_angle\")\n        else: pb.keyframe_insert(\"rotation_euler\")\n""")


def main():
    if bpy.data.filepath != BASE_BLEND:
        bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    export = bpy.data.objects[EXPORT_ARMATURE]
    clear_old(export)
    rig, created = create_rig(export)
    best, neutral = tune(export, rig)
    movement = move_test(export, rig)
    add_bake_text()
    show_scene(export, rig)
    report = {
        "base": BASE_BLEND,
        "out": OUT_BLEND,
        "created": created,
        "best": best,
        "neutral": neutral,
        "movement": movement,
        "visible_controls": [b.name for b in rig.data.bones if not b.hide],
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    report["saved"] = OUT_BLEND
    return report


RESULT = main()
