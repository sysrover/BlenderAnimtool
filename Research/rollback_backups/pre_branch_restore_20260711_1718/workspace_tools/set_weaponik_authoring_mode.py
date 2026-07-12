import json
import os

import bpy


ARMATURE_NAME = "_DayZ_Character"
OUT = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-weaponik-mode.json"
CONTROL_CONSTRAINT_PREFIX = "DayZ WIK Control"


def set_weaponik_mode(mode="Imported Playback"):
    if mode not in {"Imported Playback", "Manual Authoring"}:
        raise ValueError("mode must be 'Imported Playback' or 'Manual Authoring'")

    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")

    enable_manual = mode == "Manual Authoring"
    changed = []
    for pb in arm.pose.bones:
        for constraint in pb.constraints:
            if constraint.name.startswith(CONTROL_CONSTRAINT_PREFIX):
                constraint.mute = not enable_manual
                changed.append({
                    "bone": pb.name,
                    "constraint": constraint.name,
                    "mute": constraint.mute,
                })

    arm["dayz_weaponik_mode"] = mode
    data = {
        "mode": mode,
        "changed": changed,
        "note": (
            "Imported Playback uses imported ANM/TXA helper tracks. "
            "Manual Authoring lets WIK_* controls drive helper bones."
        ),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = set_weaponik_mode(globals().get("WEAPONIK_MODE", "Imported Playback"))
