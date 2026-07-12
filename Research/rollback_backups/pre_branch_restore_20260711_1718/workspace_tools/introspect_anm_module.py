import importlib
import json
import os
import sys

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT = os.path.join(ROOT, "anm", "anm-module-introspection.json")
ADDON_ROOT = r"P:\BlenderAnimtool"


def main():
    if ADDON_ROOT not in sys.path:
        sys.path.insert(0, ADDON_ROOT)
    import DayzAnimationToolsBinary.Types.Anm as AnmModule

    AnmModule = importlib.reload(AnmModule)
    data = {
        "module_file": getattr(AnmModule, "__file__", None),
        "module_dir": [x for x in dir(AnmModule) if not x.startswith("__")],
        "classes": {},
    }
    for name in data["module_dir"]:
        obj = getattr(AnmModule, name)
        if isinstance(obj, type):
            inst_dir = None
            try:
                inst = obj()
                inst_dir = [x for x in dir(inst) if not x.startswith("__")]
            except Exception as exc:
                inst_dir = [f"cannot instantiate: {exc!r}"]
            data["classes"][name] = {
                "class_dir": [x for x in dir(obj) if not x.startswith("__")],
                "instance_dir": inst_dir,
            }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
