import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
SOURCE_SCRIPT = os.path.join(ROOT, "tools", "create_dayz_truejoint_controlrig_v6.py")
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_controlrig_v7_truejoint_rollfollow.blend"
OUT_JSON = os.path.join(ROOT, "anm", "dayz-controlrig-v7-rollfollow-result.json")


def main():
    namespace = {"__name__": "not_main"}
    with open(SOURCE_SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()
    # Reuse v6 construction, then add roll-bone rotation follow and save v7.
    exec(code, namespace, namespace)

    dayz = bpy.data.objects["_DayZ_Character"]
    rig = bpy.data.objects["DAT_ControlRigV6"]
    rig.name = "DAT_ControlRigV7"
    rig.data.name = "DAT_ControlRigV7"

    pairs = [
        ("LeftArmRoll", "IK_Arm.L"),
        ("LeftForeArmRoll", "IK_ForeArm.L"),
        ("RightArmRoll", "IK_Arm.R"),
        ("RightForeArmRoll", "IK_ForeArm.R"),
    ]
    made = []
    for dayz_bone, proxy_bone in pairs:
        pb = dayz.pose.bones.get(dayz_bone)
        if not pb:
            continue
        for c in list(pb.constraints):
            if c.name.startswith("DAT TrueJoint Roll Follow"):
                pb.constraints.remove(c)
        c = pb.constraints.new(type="COPY_ROTATION")
        c.name = "DAT TrueJoint Roll Follow Rotation"
        c.target = rig
        c.subtarget = proxy_bone
        c.target_space = "WORLD"
        c.owner_space = "WORLD"
        made.append({"bone": dayz_bone, "proxy": proxy_bone})

    # Update existing constraints to point at renamed rig object.
    for pb in dayz.pose.bones:
        for c in pb.constraints:
            if c.name.startswith("DAT TrueJoint"):
                c.target = rig

    for b in rig.data.bones:
        b.hide = not b.name.startswith("CTRL_")

    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)
    result = {
        "saved_as": SAVE_PATH,
        "control_rig": rig.name,
        "added_roll_follow": made,
        "note": "v7 is v6 true-joint proxy IK plus rotation follow on DayZ ArmRoll/ForeArmRoll bones, so the DayZ hierarchy between arm and forearm follows the solved segment.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


RESULT = main()
