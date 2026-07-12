import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "blender-restore-clean-fullbody.json")
ARMATURE_NAME = "_DayZ_Character"
FULL_BODY_ACTION = "p_rfl_erc_idle_ras"


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    removed_constraints = []
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DayZ WIK Control") or c.name == "DayZ WeaponIK Preview":
                removed_constraints.append(f"{pb.name}:{c.name}")
                pb.constraints.remove(c)

    removed_controls = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith("WIK_") or obj.get("dayz_weaponik_control") or obj.get("dayz_weaponik_computed_pole"):
            removed_controls.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()

    if arm.animation_data is None:
        arm.animation_data_create()

    # Full body only. Disable the active IK helper/finger action so no bad
    # helper/finger import can twist the visible hands while we debug.
    arm.animation_data.action = None
    full = bpy.data.actions.get(FULL_BODY_ACTION)
    if full is not None:
        found = False
        for tr in arm.animation_data.nla_tracks:
            for st in tr.strips:
                if st.action == full:
                    found = True
                    tr.mute = False
                    st.mute = False
                    st.influence = 1.0
                    st.blend_type = "REPLACE"
        if not found:
            tr = arm.animation_data.nla_tracks.new()
            st = tr.strips.new(full.name, int(full.frame_range[0]), full)
            st.influence = 1.0
            st.blend_type = "REPLACE"

    scene = bpy.context.scene
    scene.frame_set(scene.frame_current)
    bpy.context.view_layer.update()

    names = [
        "LeftArm", "LeftForeArm", "LeftHand",
        "RightArm", "RightForeArm", "RightHand",
        "LeftHandThumb1", "LeftHandIndex1", "LeftHandMiddle1",
        "RightHandThumb1", "RightHandIndex1", "RightHandMiddle1",
    ]
    heads = {
        n: list(arm.pose.bones[n].head)
        for n in names
        if arm.pose.bones.get(n)
    }
    arm["dayz_weaponik_mode"] = "Clean FullBody Only"
    data = {
        "mode": arm["dayz_weaponik_mode"],
        "frame": scene.frame_current,
        "removed_constraints": removed_constraints,
        "removed_controls": removed_controls,
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
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
        "heads": heads,
        "note": "Weapon IK preview and IK helper/finger active action disabled. This should be visually stable full-body pose only.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
