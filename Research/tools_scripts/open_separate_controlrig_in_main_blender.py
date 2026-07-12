import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
BLEND = r"P:\Animation_Weapon\Weapon_template_separate_controlrig.blend"
OUT_JSON = os.path.join(ROOT, "anm", "open-separate-controlrig-main-result.json")


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    data = {
        "opened": bpy.data.filepath,
        "armatures": [obj.name for obj in bpy.data.objects if obj.type == "ARMATURE"],
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
