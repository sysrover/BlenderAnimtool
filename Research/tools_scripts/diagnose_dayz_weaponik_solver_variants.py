import json
import os
import sys

import bpy
from mathutils import Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ADDON_ROOT = r"P:\BlenderAnimtool"
OUT = os.path.join(ROOT, "anm", "dayz-weaponik-solver-variant-diagnostic.json")
ARMATURE_NAME = "_DayZ_Character"

if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)

from DayzAnimationTools.Utils.WeaponIKSolver import IkXform, solve_weapon_ik_chain


CHAINS = {
    "primary": {
        "bones": ["RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand"],
        "target": "RightHandOrigin",
        "dir": "RightForeArmDirection",
        "a": "RightHandOrigin",
        "b": "RightForeArmDirectionOrigin",
        "axis_candidates": [0, 1, 2, 3, 4, 5],
    },
    "secondary": {
        "bones": ["LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand"],
        "target": "LeftHandIKTarget",
        "dir": "LeftForeArmDirection",
        "a": "LeftHandOrigin",
        "b": "LeftForeArmDirectionOrigin",
        "axis_candidates": [0, 1, 2, 3, 4, 5],
    },
}


def ensure_state(arm):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name.startswith("DayZ WIK Control") or c.name == "DayZ WeaponIK Preview":
                pb.constraints.remove(c)
        pb.matrix_basis.identity()
    # Use whatever clean action/NLA state is currently active; do not apply.
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()


def xf(arm, name, location_mode):
    pb = arm.pose.bones.get(name)
    if pb is None:
        raise RuntimeError(f"Missing pose bone {name}")
    if location_mode == "head":
        loc = Vector(pb.head)
    elif location_mode == "matrix_translation":
        loc = Vector(pb.matrix.translation)
    elif location_mode == "tail":
        loc = Vector(pb.tail)
    else:
        raise ValueError(location_mode)
    return IkXform(pb.matrix.to_quaternion().normalized(), loc)


def dist(a, b):
    return (Vector(a) - Vector(b)).length


def run_variant(arm, cfg, axis_id, location_mode, helper_mode):
    records = [xf(arm, name, location_mode) for name in cfg["bones"]]
    target = xf(arm, cfg["target"], location_mode)
    kwargs = {"blend": 1.0}
    if helper_mode == "none":
        kwargs.update({"helper_dir": None, "helper_a": None, "helper_b": None})
    else:
        kwargs.update({
            "helper_dir": xf(arm, cfg["dir"], location_mode).location,
            "helper_a": xf(arm, cfg["a"], location_mode).location,
            "helper_b": xf(arm, cfg["b"], location_mode).location,
        })
    ok = solve_weapon_ik_chain(records, axis_id, target, **kwargs)
    end = records[-1].location
    root = records[0].location
    mid = records[2].location
    return {
        "ok": ok,
        "axis": axis_id,
        "location_mode": location_mode,
        "helper_mode": helper_mode,
        "target": list(target.location),
        "root": list(root),
        "mid": list(mid),
        "end": list(end),
        "end_to_target": (end - target.location).length,
        "root_to_end": (end - root).length,
        "mid_height_delta": float(mid.z - root.z),
        "record_locations": [list(r.location) for r in records],
    }


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    ensure_state(arm)

    variants = {}
    for chain_name, cfg in CHAINS.items():
        rows = []
        for location_mode in ["head", "matrix_translation", "tail"]:
            for helper_mode in ["dayz_helpers", "none"]:
                for axis in cfg["axis_candidates"]:
                    rows.append(run_variant(arm, cfg, axis, location_mode, helper_mode))
        rows.sort(key=lambda r: (r["end_to_target"], abs(r["mid_height_delta"])))
        variants[chain_name] = rows

    data = {
        "frame": bpy.context.scene.frame_current,
        "mode": "offline diagnostics only; no pose applied",
        "variants": variants,
        "top_primary": variants["primary"][:8],
        "top_secondary": variants["secondary"][:8],
        "note": "If all variants reach the target but bad elbows remain, issue is helper-plane/twist interpretation, not Blender matrix application.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
