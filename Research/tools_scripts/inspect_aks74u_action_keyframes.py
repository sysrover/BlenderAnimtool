import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "aks74u-action-keyframes.json")


def dump_action(name):
    action = bpy.data.actions.get(name)
    if action is None:
        return {"missing": True}
    interesting = [
        "RightHandOrigin",
        "RightHand_Dummy",
        "LeftHandIKTarget",
        "LeftHandOrigin",
        "LeftForeArmDirection",
    ]
    result = {"frame_range": [float(action.frame_range[0]), float(action.frame_range[1])], "fcurves": {}}
    for bone in interesting:
        for prop in ("location", "rotation_quaternion"):
            path = f'pose.bones["{bone}"].{prop}'
            for index in range(4 if prop == "rotation_quaternion" else 3):
                fc = action.fcurves.find(path, index=index)
                if fc is None:
                    continue
                key = f"{bone}.{prop}[{index}]"
                result["fcurves"][key] = [
                    {
                        "co": [float(kp.co.x), float(kp.co.y)],
                        "interp": kp.interpolation,
                    }
                    for kp in fc.keyframe_points
                ]
    return result


def main():
    data = {
        "aks74u": dump_action("aks74u"),
        "aks74u_helpers_only": dump_action("aks74u_helpers_only"),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
