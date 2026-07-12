import importlib
import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-binary-anm-addon-reload.json")


def has_operator_property(prop_name):
    try:
        props = bpy.ops.export_scene.anm.get_rna_type().properties
        return prop_name in props
    except Exception:
        return False


def main():
    before = has_operator_property("bPreserveImportedRawAnm")
    errors = []
    try:
        import DayzAnimationToolsBinary
        try:
            DayzAnimationToolsBinary.unregister()
        except Exception as e:
            errors.append(f"unregister: {repr(e)}")

        module_names = [
            "DayzAnimationToolsBinary.Export.ExportAnm",
            "DayzAnimationToolsBinary.Export",
            "DayzAnimationToolsBinary.Import.ImportAnm",
            "DayzAnimationToolsBinary.Import",
            "DayzAnimationToolsBinary",
        ]
        for name in module_names:
            try:
                mod = importlib.import_module(name)
                importlib.reload(mod)
            except Exception as e:
                errors.append(f"reload {name}: {repr(e)}")

        import DayzAnimationToolsBinary as ReloadedAddon
        ReloadedAddon.register()
    except Exception as e:
        errors.append(f"reload root: {repr(e)}")

    after = has_operator_property("bPreserveImportedRawAnm")
    data = {
        "property_before_reload": before,
        "property_after_reload": after,
        "errors": errors,
        "note": "If property_after_reload is false, restart Blender or disable/enable the addon to load the patched operator class.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
