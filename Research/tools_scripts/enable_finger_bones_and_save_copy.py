import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "blender-save-fingers-visible-copy.json")
SAVE_PATH = r"P:\Animation_Weapon\Weapon_template_aks74u_anm_full_import_fingers_visible.blend"
ARMATURE_NAME = "_DayZ_Character"
ACTION_NAME = "aks74u"

def is_finger_or_hand_bone(name):
    return name.startswith("LeftHand") or name.startswith("RightHand")


def set_collection_visible(collection):
    changed = []
    for attr in ("is_visible", "hide"):
        if hasattr(collection, attr):
            try:
                current = getattr(collection, attr)
                desired = True if attr == "is_visible" else False
                if current != desired:
                    setattr(collection, attr, desired)
                    changed.append(f"{collection.name}.{attr}={desired}")
            except Exception:
                pass
    return changed


def main():
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

    arm.show_in_front = True
    arm.data.show_names = True
    arm.data.display_type = "BBONE"

    visible_collections = []
    for collection in getattr(arm.data, "collections", []):
        visible_collections.extend(set_collection_visible(collection))

    unhidden_bones = []
    finger_bones = []
    for bone in arm.data.bones:
        if is_finger_or_hand_bone(bone.name):
            finger_bones.append(bone.name)
            if getattr(bone, "hide", False):
                bone.hide = False
                unhidden_bones.append(bone.name)
            if hasattr(bone, "hide_select"):
                bone.hide_select = False

    for pb in arm.pose.bones:
        if is_finger_or_hand_bone(pb.name):
            for constraint in pb.constraints:
                constraint.mute = False

    # Keep this as a raw imported ANM authoring/view file. Do not add or apply
    # runtime WeaponIK preview constraints here.
    arm["dayz_weaponik_mode"] = "Full imported aks74u ANM; finger bones visible"
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=SAVE_PATH)

    data = {
        "saved": SAVE_PATH,
        "active_action": arm.animation_data.action.name if arm.animation_data.action else None,
        "frame": bpy.context.scene.frame_current,
        "mode": arm["dayz_weaponik_mode"],
        "action_fcurves": len(action.fcurves),
        "finger_bones_count": len(finger_bones),
        "finger_bones": sorted(finger_bones),
        "unhidden_bones": sorted(unhidden_bones),
        "visible_collections_changes": visible_collections,
        "note": "Separate copy with full imported .anm action and visible/selectable hand/finger bones.",
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
