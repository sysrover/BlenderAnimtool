import importlib
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
CLEAN = r"P:\Animation_Weapon\Weapon_template_dayz_diag_restored.blend"
ANM = r"P:\DZ\anims\anm\player\ik\weapons\aks74u.anm"
USER_JSON = os.path.join(ROOT, "anm", "right-hand-loaded-pose-delta.json")
OUT = os.path.join(ROOT, "anm", "anm-reload-right-hand-offset-test.json")
SAVE_AS = r"P:\Animation_Weapon\Weapon_template_aks74u_anm_reload_right_hand_offset.blend"
ARMATURE_NAME = "_DayZ_Character"


class FakeFile:
    def __init__(self, name):
        self.name = name


class FakeImportSelf:
    def __init__(self, filepath):
        self.filepath = filepath
        self.files = [FakeFile(os.path.basename(filepath))]

    def report(self, kind, message):
        print("[FakeImportSelf]", kind, message)


def ensure_addon_path():
    addon_root = os.path.join(
        os.environ["APPDATA"],
        "Blender Foundation",
        "Blender",
        "4.2",
        "scripts",
        "addons",
    )
    if addon_root not in sys.path:
        sys.path.append(addon_root)


def rows(m):
    return [[float(v) for v in row] for row in m]


def vlist(v):
    return [float(v.x), float(v.y), float(v.z)]


def pose_row(arm, name):
    pb = arm.pose.bones[name]
    head = arm.matrix_world @ pb.head
    tail = arm.matrix_world @ pb.tail
    return {
        "head": vlist(head),
        "tail": vlist(tail),
        "direction": vlist((tail - head).normalized()),
        "basis_quat": [float(v) for v in pb.matrix_basis.to_quaternion()],
        "basis_euler_xyz_deg": [float(math.degrees(v)) for v in pb.matrix_basis.to_quaternion().to_euler("XYZ")],
    }


def sample_frames(scene):
    start = int(scene.frame_start)
    end = int(scene.frame_end)
    frames = [start, min(start + 1, end), (start + end) // 2, end]
    result = []
    for f in frames:
        if f not in result:
            result.append(f)
    return result


def capture(arm, frames):
    data = {}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        data[str(frame)] = {
            name: pose_row(arm, name)
            for name in [
                "RightHand",
                "RightHand_Dummy",
                "RightHandIK",
                "RightHandOrigin",
                "RightForeArmDirection",
                "RightForeArmDirectionOrigin",
                "LeftHand",
            ]
            if name in arm.pose.bones
        }
    return data


def apply_offset_to_action(arm, action, offset):
    path = 'pose.bones["RightHand"].rotation_quaternion'
    q_curves = {fc.array_index: fc for fc in action.fcurves if fc.data_path == path}
    frames = set()
    for fc in q_curves.values():
        for kp in fc.keyframe_points:
            frames.add(int(round(kp.co.x)))
    if not frames:
        frames = set(range(int(bpy.context.scene.frame_start), int(bpy.context.scene.frame_end) + 1))

    # First sample the imported animation without adding RightHand curves. IK
    # ANM files commonly do not include a RightHand track; adding keys while
    # sampling would contaminate later frames.
    samples = {}
    previous = None
    for frame in sorted(frames):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        q_orig = arm.pose.bones["RightHand"].matrix_basis.to_quaternion()
        q_new = (q_orig.to_matrix().to_4x4() @ offset).to_quaternion()
        if previous is not None:
            q_new.make_compatible(previous)
        previous = q_new.copy()
        samples[frame] = q_new

    # Replace/create the RightHand quaternion curves with corrected keys.
    for fc in list(action.fcurves):
        if fc.data_path == path:
            action.fcurves.remove(fc)

    new_curves = [action.fcurves.new(data_path=path, index=i) for i in range(4)]
    for axis, fc in enumerate(new_curves):
        fc.color_mode = "AUTO_YRGB"
        fc.keyframe_points.add(len(samples))
        for i, frame in enumerate(sorted(samples)):
            fc.keyframe_points[i].co = (frame, float(samples[frame][axis]))
            fc.keyframe_points[i].interpolation = "LINEAR"
        fc.update()

    bpy.context.view_layer.update()
    return sorted(frames)


def main():
    with open(USER_JSON, "r", encoding="utf-8") as f:
        user = json.load(f)

    # The measured local correction: clean RightHand basis -> user-correct basis.
    clean_basis = Matrix(user["bones"]["RightHand"]["matrix_basis"])
    # We need the delta, not the absolute target, for arbitrary imported ANM frames.
    bpy.ops.wm.open_mainfile(filepath=CLEAN)
    arm = bpy.data.objects[ARMATURE_NAME]
    current_clean_basis = arm.pose.bones["RightHand"].matrix_basis.copy()
    right_hand_offset = current_clean_basis.inverted_safe() @ clean_basis

    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    ensure_addon_path()
    # Call the real Blender operator rather than ImportAnm.load() directly.
    # The bridge timer context does not expose bpy.context.object, while the
    # operator receives a normal object override similar to the UI import path.
    with bpy.context.temp_override(object=arm, active_object=arm, selected_objects=[arm], selected_editable_objects=[arm]):
        op_result = bpy.ops.import_scene.anm(
            "EXEC_DEFAULT",
            filepath=ANM,
            files=[{"name": os.path.basename(ANM)}],
        )
    if "FINISHED" not in op_result:
        raise RuntimeError(f"ANM import operator failed: {op_result}")

    action = arm.animation_data.action
    if action is None:
        raise RuntimeError("ANM import did not create active action")

    frames = sample_frames(bpy.context.scene)
    before = capture(arm, frames)
    keyed_frames = apply_offset_to_action(arm, action, right_hand_offset)
    after = capture(arm, frames)

    payload = {
        "clean_source": CLEAN,
        "anm": ANM,
        "saved_as": SAVE_AS,
        "imported_action": action.name,
        "scene_frame_range": [int(bpy.context.scene.frame_start), int(bpy.context.scene.frame_end)],
        "sample_frames": frames,
        "right_hand_offset_matrix": rows(right_hand_offset),
        "right_hand_offset_quat": [float(v) for v in right_hand_offset.to_quaternion()],
        "right_hand_offset_euler_xyz_deg": [
            float(math.degrees(v)) for v in right_hand_offset.to_quaternion().to_euler("XYZ")
        ],
        "keyed_frames_count": len(keyed_frames),
        "keyed_frames_first_last": [keyed_frames[0], keyed_frames[-1]] if keyed_frames else [],
        "before": before,
        "after": after,
        "accepted": True,
        "meaning": "ANM was imported fresh, then the measured local RightHand offset was applied to RightHand rotation keys across the action.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    bpy.ops.wm.save_as_mainfile(filepath=SAVE_AS)
    return payload


RESULT = main()
