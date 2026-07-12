import bpy
import os

# Config
import sys

# Simple CLI arg parsing after '--'
def get_arg(flag: str, default=None):
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        rest = sys.argv[idx + 1:]
        try:
            i = rest.index(flag)
            if i + 1 < len(rest):
                return rest[i + 1]
        except ValueError:
            pass
    return default

blend_path = get_arg("--blend")
out_path = get_arg("--out")
anim_type = get_arg("--type", "IK2H")
arm_name = get_arg("--arm")
action_name = get_arg("--action")

print("[export_from_blend] args:", {
    "blend": blend_path,
    "out": out_path,
    "type": anim_type,
    "arm": arm_name,
    "action": action_name,
})

if blend_path:
    print("[export_from_blend] Opening blend:", blend_path)
    bpy.ops.wm.open_mainfile(filepath=blend_path)
else:
    print("[export_from_blend] No blend path provided; using current session")

# Find an armature to export
arm_obj = None
if arm_name:
    arm_obj = bpy.data.objects.get(arm_name)
else:
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            arm_obj = obj
            break
if arm_obj is None:
    raise RuntimeError("Armature object not found; pass --arm <name>")

if arm_obj.animation_data is None:
    arm_obj.animation_data_create()

if action_name:
    act = bpy.data.actions.get(action_name)
    if act is None:
        raise RuntimeError(f"Action '{action_name}' not found")
    arm_obj.animation_data.action = act
else:
    act = arm_obj.animation_data.action

if act is not None:
    start, end = int(act.frame_range[0]), int(act.frame_range[1])
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    print(f"[export_from_blend] Using action '{act.name}' frames {start}-{end}")
else:
    print("[export_from_blend] No action bound; export will still run")


 # Ensure armature is active
bpy.context.view_layer.objects.active = arm_obj
for obj in bpy.context.selected_objects:
    obj.select_set(False)
arm_obj.select_set(True)

 # Default output path if missing
if not out_path:
    addons_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Blender Foundation", "Blender", "4.2", "scripts", "addons")
    root = os.path.join(addons_dir, "DayzAnimationToolsBinary")
    example_dir = None
    for cand in ("example", "Examples"):
        p = os.path.join(root, cand)
        if os.path.isdir(p):
            example_dir = p
            break
    if example_dir is None:
        example_dir = root
    out_path = os.path.join(example_dir, "aks74u_exported.anm")
print("[export_from_blend] Output ANM:", out_path)

 # Invoke exporter
try:
    res = bpy.ops.export_scene.anm(
        filepath=out_path,
        bExportSelectedBonesOnly=False,
        bExportShowingBonesOnly=False,
        bExportTranslationKeys=True,
        bExportRotationKeys=True,
        bExportScaleKeys=False,
        fpsOverride=0,
        eAnimType=anim_type,
        bSaveAll=False,
        fUnitScale=1.0,
    )
    print("[export_from_blend] export_scene.anm result:", res)
except Exception as e:
    print("[export_from_blend] Export failed:", repr(e))
    raise

print("[export_from_blend] Done.")
