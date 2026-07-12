import importlib
import json
import os
from types import SimpleNamespace

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-reimport-weaponik-clean-base.json")
ARMATURE_NAME = "_DayZ_Character"
FULL_BODY_ACTION = "p_rfl_erc_idle_ras"
IK_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"


def ensure_armature():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    return arm


def remove_preview_constraints_and_controls(arm):
    removed = []
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DayZ WIK Control") or c.name == "DayZ WeaponIK Preview":
                removed.append(f"{pb.name}:{c.name}")
                pb.constraints.remove(c)
    for obj in list(bpy.data.objects):
        if obj.name.startswith("WIK_") or obj.get("dayz_weaponik_control") or obj.get("dayz_weaponik_computed_pole"):
            removed.append(f"object:{obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def reset_pose_basis(arm):
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()


def make_full_body_active_without_losing_nla(arm):
    action = bpy.data.actions.get(FULL_BODY_ACTION)
    if action is None:
        raise RuntimeError(f"Full-body action {FULL_BODY_ACTION!r} not found")
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    arm.animation_data.action_blend_type = "REPLACE"
    for track in arm.animation_data.nla_tracks:
        track.mute = True
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()


def import_ik_without_pushdown(arm):
    # ImportAnm pushes the active action to NLA. To force a clean base pose and
    # avoid duplicating full-body strips, temporarily leave the base action in
    # NLA-muted state only after generating a base-pose snapshot.
    # The importer needs evaluated full-body pose during context.scene.frame_set,
    # so we monkey-patch the pushdown by keeping full-body action active and
    # removing the duplicate strip afterward.
    for act in list(bpy.data.actions):
        if act.name == "aks74u":
            bpy.data.actions.remove(act)

    import DayzAnimationToolsBinary.Import.ImportAnm as ImportAnm
    ImportAnm = importlib.reload(ImportAnm)
    before_tracks = set(id(track) for track in arm.animation_data.nla_tracks)
    dummy_self = SimpleNamespace(filepath=IK_ANM, files=[SimpleNamespace(name=os.path.basename(IK_ANM))])
    result = ImportAnm.load(dummy_self, bpy.context, ImportAnm.AnmImportSettings())
    if result:
        raise RuntimeError(result)

    # Keep one full-body NLA strip enabled. Remove duplicate full-body tracks
    # created by repeated import attempts.
    seen_full_body = False
    for track in list(arm.animation_data.nla_tracks):
        full_body_strip = None
        for strip in track.strips:
            if strip.action and strip.action.name == FULL_BODY_ACTION:
                full_body_strip = strip
                break
        if full_body_strip:
            if seen_full_body:
                arm.animation_data.nla_tracks.remove(track)
                continue
            seen_full_body = True
            track.mute = False
            full_body_strip.mute = False
            full_body_strip.influence = 1.0
            full_body_strip.blend_type = "REPLACE"
        else:
            track.mute = True


def summarize(arm):
    names = [
        "LeftArm",
        "LeftForeArm",
        "LeftHand",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
        "LeftForeArmDirectionOrigin",
        "RightHand",
        "RightHand_Dummy",
        "RightHandOrigin",
        "RightForeArmDirection",
        "RightForeArmDirectionOrigin",
    ]
    out = {}
    for frame in [0, 1, 30]:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        out[str(frame)] = {
            name: list(arm.pose.bones[name].head)
            for name in names
            if arm.pose.bones.get(name)
        }
    return out


def main():
    arm = ensure_armature()
    removed = remove_preview_constraints_and_controls(arm)
    reset_pose_basis(arm)
    make_full_body_active_without_losing_nla(arm)
    import_ik_without_pushdown(arm)
    reset_pose_basis(arm)
    arm["dayz_weaponik_mode"] = "Clean FullBody + IK Helper Tracks"
    data = {
        "mode": arm["dayz_weaponik_mode"],
        "removed": removed,
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "nla": [
            {
                "track": tr.name,
                "mute": tr.mute,
                "strip": st.name,
                "action": st.action.name if st.action else None,
                "influence": st.influence,
                "strip_mute": st.mute,
            }
            for tr in arm.animation_data.nla_tracks
            for st in tr.strips
        ],
        "heads": summarize(arm),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
