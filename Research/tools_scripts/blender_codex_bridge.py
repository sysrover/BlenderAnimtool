import json
import os
import time
import traceback

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
REQ = os.path.join(ROOT, "tools", "blender_bridge_request.json")
RESP = os.path.join(ROOT, "tools", "blender_bridge_response.json")
STATUS = os.path.join(ROOT, "tools", "blender_bridge_status.json")
DUMP = os.path.join(ROOT, "anm", "blender-live-skeleton-dump.json")

_last_request_id = None
_bridge_generation = None


def _matrix_rows(m):
    return [list(row) for row in m]


def dump_scene(path=DUMP):
    data = {
        "file": bpy.data.filepath,
        "mode": bpy.context.mode,
        "active_object": bpy.context.object.name if bpy.context.object else None,
        "selected_objects": [o.name for o in bpy.context.selected_objects],
        "armatures": [],
        "objects": [],
    }
    for obj in bpy.data.objects:
        data["objects"].append({
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "parent_bone": obj.parent_bone if obj.parent_bone else None,
            "matrix_world": _matrix_rows(obj.matrix_world),
            "constraints": [
                {
                    "name": c.name,
                    "type": c.type,
                    "target": c.target.name if getattr(c, "target", None) else None,
                    "subtarget": getattr(c, "subtarget", ""),
                    "influence": getattr(c, "influence", None),
                }
                for c in obj.constraints
            ],
        })
        if obj.type != "ARMATURE":
            continue

        bones = []
        for b in obj.data.bones:
            bones.append({
                "name": b.name,
                "parent": b.parent.name if b.parent else None,
                "head_local": list(b.head_local),
                "tail_local": list(b.tail_local),
                "matrix_local": _matrix_rows(b.matrix_local),
                "use_connect": bool(b.use_connect),
            })

        pose_bones = []
        for pb in obj.pose.bones:
            pose_bones.append({
                "name": pb.name,
                "rotation_mode": pb.rotation_mode,
                "matrix": _matrix_rows(pb.matrix),
                "matrix_basis": _matrix_rows(pb.matrix_basis),
                "matrix_channel": _matrix_rows(pb.matrix_channel),
                "constraints": [
                    {
                        "name": c.name,
                        "type": c.type,
                        "target": c.target.name if getattr(c, "target", None) else None,
                        "subtarget": getattr(c, "subtarget", ""),
                        "pole_target": c.pole_target.name if getattr(c, "pole_target", None) else None,
                        "pole_subtarget": getattr(c, "pole_subtarget", ""),
                        "chain_count": getattr(c, "chain_count", None),
                        "use_rotation": getattr(c, "use_rotation", None),
                        "use_stretch": getattr(c, "use_stretch", None),
                        "influence": getattr(c, "influence", None),
                    }
                    for c in pb.constraints
                ],
            })

        data["armatures"].append({
            "object": obj.name,
            "data": obj.data.name,
            "bone_count": len(bones),
            "matrix_world": _matrix_rows(obj.matrix_world),
            "bones": bones,
            "pose_bones": pose_bones,
        })

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"dump": path, "armatures": len(data["armatures"])}


def _write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _make_tick(generation):
    def _tick():
        global _last_request_id
        try:
            if os.path.exists(REQ):
                with open(REQ, "r", encoding="utf-8") as f:
                    req = json.load(f)
                req_id = req.get("id")
                if req_id != _last_request_id:
                    _last_request_id = req_id
                    cmd = req.get("cmd", "dump")
                    if cmd == "dump":
                        result = dump_scene(req.get("path", DUMP))
                    elif cmd == "exec":
                        namespace = {"bpy": bpy, "json": json, "os": os, "dump_scene": dump_scene}
                        exec(req.get("code", ""), namespace, namespace)
                        result = namespace.get("RESULT", {"message": "exec completed"})
                    else:
                        result = {"error": "unknown command", "cmd": cmd}
                    _write_json(RESP, {"id": req_id, "ok": True, "generation": generation, "result": result})
        except Exception:
            _write_json(RESP, {"id": _last_request_id, "ok": False, "generation": generation, "error": traceback.format_exc()})
        return 0.25
    return _tick


def _tick():
    global _last_request_id
    try:
        if os.path.exists(REQ):
            with open(REQ, "r", encoding="utf-8") as f:
                req = json.load(f)
            req_id = req.get("id")
            if req_id != _last_request_id:
                _last_request_id = req_id
                cmd = req.get("cmd", "dump")
                if cmd == "dump":
                    result = dump_scene(req.get("path", DUMP))
                elif cmd == "exec":
                    namespace = {"bpy": bpy, "json": json, "os": os, "dump_scene": dump_scene}
                    exec(req.get("code", ""), namespace, namespace)
                    result = namespace.get("RESULT", {"message": "exec completed"})
                else:
                    result = {"error": "unknown command", "cmd": cmd}
                _write_json(RESP, {"id": req_id, "ok": True, "result": result})
    except Exception:
        _write_json(RESP, {"id": _last_request_id, "ok": False, "error": traceback.format_exc()})
    return 0.25


dump_result = dump_scene()
_bridge_generation = time.time()
_write_json(STATUS, {"ok": True, "file": bpy.data.filepath, "generation": _bridge_generation, "initial_dump": dump_result})

bpy.app.timers.register(_make_tick(_bridge_generation), persistent=True)

print("CODEX_BLENDER_BRIDGE_READY", STATUS)
