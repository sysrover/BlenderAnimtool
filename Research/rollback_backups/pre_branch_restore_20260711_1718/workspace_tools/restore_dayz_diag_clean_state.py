import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
SOURCE = r"P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend"
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_dayz_diag_restored.blend"
OUT = os.path.join(ROOT, "anm", "dayz-diag-restored-state-report.json")
ARMATURE_NAME = "_DayZ_Character"


CONTROL_PREFIXES = (
    "DAT_ControlRig",
    "CTRL_",
    "DRV_",
    "MCH_",
    "WIK_",
)


def rows(m):
    return [list(r) for r in m]


def bone_info(arm, name):
    pb = arm.pose.bones.get(name)
    b = arm.data.bones.get(name)
    if not pb or not b:
        return None
    return {
        "name": name,
        "parent": b.parent.name if b.parent else None,
        "head_local": list(b.head_local),
        "tail_local": list(b.tail_local),
        "matrix_local": rows(b.matrix_local),
        "pose_matrix": rows(pb.matrix),
        "constraints": [
            {
                "name": c.name,
                "type": c.type,
                "target": c.target.name if getattr(c, "target", None) else None,
                "subtarget": getattr(c, "subtarget", ""),
                "influence": getattr(c, "influence", None),
            }
            for c in pb.constraints
        ],
    }


def main():
    if not os.path.exists(SOURCE):
        raise RuntimeError(f"Clean source not found: {SOURCE}")

    bpy.ops.wm.open_mainfile(filepath=SOURCE)
    removed_objects = []
    removed_constraints = []

    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(prefix) for prefix in CONTROL_PREFIXES):
            removed_objects.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Missing armature {ARMATURE_NAME}")

    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if (
                c.name.startswith("DAT ")
                or c.name.startswith("Codex ")
                or c.type in {"IK", "COPY_TRANSFORMS", "COPY_LOCATION", "COPY_ROTATION", "STRETCH_TO"}
            ):
                removed_constraints.append({"bone": pb.name, "constraint": c.name, "type": c.type})
                pb.constraints.remove(c)

    bpy.context.view_layer.update()

    important = [
        "LeftShoulder",
        "LeftArm",
        "LeftArmRoll",
        "LeftForeArm",
        "LeftForeArmRoll",
        "LeftHand",
        "LeftHand_Dummy",
        "LeftHandIK",
        "RightShoulder",
        "RightArm",
        "RightArmRoll",
        "RightForeArm",
        "RightForeArmRoll",
        "RightHand",
        "RightHand_Dummy",
        "RightHandIK",
        "LeftHandOrigin",
        "LeftHandIKTarget",
        "RightHandOrigin",
        "LeftForeArmDirection",
        "LeftForeArmDirectionOrigin",
        "RightForeArmDirection",
        "RightForeArmDirectionOrigin",
    ]
    bones = [bone_info(arm, name) for name in important]
    bones = [b for b in bones if b is not None]

    report = {
        "source": SOURCE,
        "saved_as": SAVE_AS,
        "armature": ARMATURE_NAME,
        "removed_objects": removed_objects,
        "removed_constraints": removed_constraints,
        "remaining_pose_constraints_on_important_bones": sum(len(b["constraints"]) for b in bones),
        "bones": bones,
        "status": "restored_clean_dayz_diag_state",
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return report


RESULT = main()
