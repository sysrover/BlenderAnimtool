import json

import bpy

from DayzAnimationToolsBinary.Types.Anm import Anm


SOURCE = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
EXPORTED = r"C:\temp\aks74u_v3_fresh_process_export.anm"
ARMATURE = "_DayZ_Character"


def decode(path):
    animation = Anm.CreateFromFile(path)
    tracks = {}
    for bone in animation.bones:
        tracks[bone.name] = {
            "position": {
                key.frame: [value * bone.posMulti + bone.posBias for value in key.data]
                for key in bone.posKeys
            },
            "rotation": {
                key.frame: [value * bone.rotMulti + bone.rotBias for value in key.data]
                for key in bone.rotKeys
            },
        }
    return animation, tracks


def held(keys, frame, identity):
    frames = [value for value in keys if value <= frame]
    return keys[max(frames)] if frames else identity


armature = bpy.data.objects[ARMATURE]
if bpy.context.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
for obj in bpy.context.selected_objects:
    obj.select_set(False)
armature.hide_set(False)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature

result = bpy.ops.export_scene.anm(
    filepath=EXPORTED,
    bExportSelectedBonesOnly=False,
    bExportShowingBonesOnly=False,
    bExportTranslationKeys=True,
    bExportRotationKeys=True,
    bExportScaleKeys=False,
    fpsOverride=30,
    eAnimType="IK2H",
    bSaveAll=False,
    bPreserveImportedRawAnm=True,
    fUnitScale=1.0,
)

source_animation, source = decode(SOURCE)
export_animation, exported = decode(EXPORTED)
maximum = 0.0
worst = None
missing = []
for name, source_track in source.items():
    if name not in exported:
        missing.append(name)
        continue
    for channel, identity in (
        ("position", [0.0, 0.0, 0.0]),
        ("rotation", [0.0, 0.0, 0.0, 1.0]),
    ):
        for frame in (0, 1):
            left = held(source_track[channel], frame, identity)
            right = held(exported[name][channel], frame, identity)
            if channel == "rotation":
                direct = max(abs(left[index] - right[index]) for index in range(4))
                negated = max(abs(left[index] + right[index]) for index in range(4))
                error = min(direct, negated)
            else:
                error = max(abs(left[index] - right[index]) for index in range(3))
            if error > maximum:
                maximum = error
                worst = {"track": name, "channel": channel, "frame": frame, "error": error}

print("CURRENT_EXPORT_RESULT " + json.dumps({
    "operator": sorted(result),
    "source_format": source_animation.format.name,
    "export_format": export_animation.format.name,
    "source_fps": int(source_animation.fps),
    "export_fps": int(export_animation.fps),
    "source_frames": int(source_animation.numFrames),
    "export_frames": int(export_animation.numFrames),
    "source_tracks": len(source_animation.bones),
    "export_tracks": len(export_animation.bones),
    "max_error": maximum,
    "worst": worst,
    "missing": missing,
    "raw_property": bool(armature.animation_data.action.get("dayz_binary_anm_raw_preserve", False)),
}))
