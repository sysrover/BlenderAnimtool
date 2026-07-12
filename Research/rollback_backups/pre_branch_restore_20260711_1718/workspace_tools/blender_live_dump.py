import bpy, json, os, traceback
out = r"C:\Users\sysro\diag\CsharpModVScode\anm\blender-live-skeleton-dump.json"
try:
    data = {
        "file": bpy.data.filepath,
        "active_object": bpy.context.object.name if bpy.context.object else None,
        "mode": bpy.context.mode,
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
            "matrix_world": [list(row) for row in obj.matrix_world],
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
        arm = obj.data
        bones = []
        for b in arm.bones:
            bones.append({
                "name": b.name,
                "parent": b.parent.name if b.parent else None,
                "head_local": list(b.head_local),
                "tail_local": list(b.tail_local),
                "matrix_local": [list(row) for row in b.matrix_local],
                "use_connect": bool(b.use_connect),
            })
        pose_bones = []
        for pb in obj.pose.bones:
            pose_bones.append({
                "name": pb.name,
                "rotation_mode": pb.rotation_mode,
                "matrix": [list(row) for row in pb.matrix],
                "matrix_basis": [list(row) for row in pb.matrix_basis],
                "matrix_channel": [list(row) for row in pb.matrix_channel],
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
            "data": arm.name,
            "bone_count": len(bones),
            "matrix_world": [list(row) for row in obj.matrix_world],
            "bones": bones,
            "pose_bones": pose_bones,
        })
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("CODEX_LIVE_DUMP_OK", out, "armatures", len(data["armatures"]))
except Exception:
    err = traceback.format_exc()
    with open(out + ".error.txt", "w", encoding="utf-8") as f:
        f.write(err)
    print("CODEX_LIVE_DUMP_ERROR", err)
