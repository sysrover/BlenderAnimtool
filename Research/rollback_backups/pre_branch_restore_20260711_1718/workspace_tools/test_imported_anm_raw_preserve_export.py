import base64
import importlib
import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
ORIG_ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
OUT_DIR = os.path.join(ROOT, "anm", "blender_roundtrip")
OUT_ANM = os.path.join(OUT_DIR, "aks74u_raw_preserve_export.anm")
OUT_JSON = os.path.join(ROOT, "anm", "aks74u-anm-raw-preserve-export.json")
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"


def ensure_raw_cache(action, source_path):
    with open(source_path, "rb") as f:
        raw = f.read()
    text_name = f"DayZ_ANM_RAW_{action.name}"
    if text_name in bpy.data.texts:
        bpy.data.texts.remove(bpy.data.texts[text_name])
    text = bpy.data.texts.new(text_name)
    text.write(base64.b64encode(raw).decode("ascii"))
    action["dayz_binary_anm_source"] = source_path
    action["dayz_binary_anm_raw_text"] = text_name
    action["dayz_binary_anm_raw_preserve"] = True
    action["dayz_binary_anm_raw_note"] = "Disable raw preserve on export after editing this imported ANM action."
    return len(raw), text_name


def main():
    import DayzAnimationToolsBinary.Export.ExportAnm as ExportAnm
    ExportAnm = importlib.reload(ExportAnm)

    arm = bpy.data.objects.get(ARMATURE_NAME)
    if arm is None or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature {ARMATURE_NAME!r} not found")
    action = bpy.data.actions.get(ACTION_NAME)
    if action is None:
        raise RuntimeError(f"Action {ACTION_NAME!r} not found")

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action

    cached_len, text_name = ensure_raw_cache(action, ORIG_ANM)
    os.makedirs(OUT_DIR, exist_ok=True)
    class DummyProgress:
        def enter_substeps(self, *args, **kwargs):
            pass
        def leave_substeps(self, *args, **kwargs):
            pass
        def step(self, *args, **kwargs):
            pass

    class DummyExportSettings:
        bExportSelectedBonesOnly = False
        bExportShowingBonesOnly = False
        bExportTranslationKeys = True
        bExportRotationKeys = True
        bExportScaleKeys = False
        fpsOverride = 0
        eAnimType = "IK2H"
        bPreserveImportedRawAnm = True
        bSaveAll = False
        fUnitScale = 1.0

    ExportAnm.g_scale = 1.0
    ExportAnm.export_action(DummyExportSettings(), bpy.context, DummyProgress(), action, OUT_ANM)
    result = {"DIRECT_EXPORT_ACTION"}

    with open(ORIG_ANM, "rb") as f:
        orig = f.read()
    with open(OUT_ANM, "rb") as f:
        exp = f.read()
    first_diff = None
    for i, (a, b) in enumerate(zip(orig, exp)):
        if a != b:
            first_diff = i
            break
    if first_diff is None and len(orig) != len(exp):
        first_diff = min(len(orig), len(exp))

    save_path = r"P:\Animation_Weapon\Weapon_template_aks74u_anm_safe_authoring_rawcache.blend"
    bpy.ops.wm.save_as_mainfile(filepath=save_path)

    data = {
        "export_result": sorted(list(result)),
        "source_blend_saved_as": save_path,
        "action": action.name,
        "raw_cache_text": text_name,
        "raw_cache_bytes": cached_len,
        "original": ORIG_ANM,
        "exported": OUT_ANM,
        "original_bytes": len(orig),
        "exported_bytes": len(exp),
        "byte_identical": orig == exp,
        "first_diff_offset": first_diff,
        "note": "Raw-preserve export writes the imported ANM bytes exactly. Disable it when exporting edited keys.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
