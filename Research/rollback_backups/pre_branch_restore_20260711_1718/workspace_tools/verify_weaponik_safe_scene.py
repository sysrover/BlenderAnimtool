import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "weaponik-safe-scene-verify.json")
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    unsafe = []
    for pb in arm.pose.bones:
        for c in pb.constraints:
            if (
                c.name.startswith("DayZ WeaponIK Preview")
                or c.name.startswith("DayZ WIK Control")
                or c.name in {"DayZ Left Hand IK", "DayZ Right Hand IK"}
            ):
                unsafe.append({"bone": pb.name, "constraint": c.name, "type": c.type, "enabled": c.enabled})
    action = bpy.data.actions.get(ACTION_NAME)
    hand_visible = []
    if arm.data:
        for b in arm.data.bones:
            if b.name.startswith(("LeftHand", "RightHand")) and not b.hide:
                hand_visible.append(b.name)
    data = {
        "file": bpy.data.filepath,
        "active_action": arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
        "aks74u_action_exists": action is not None,
        "aks74u_fcurves": len(action.fcurves) if action else 0,
        "raw_cache_text": action.get("dayz_binary_anm_raw_text", "") if action else "",
        "raw_preserve": bool(action.get("dayz_binary_anm_raw_preserve", False)) if action else False,
        "visible_hand_finger_bones": len(hand_visible),
        "unsafe_constraints": unsafe,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
