import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_JSON = os.path.join(ROOT, "anm", "ref-blender-deep-dump.json")
OUT_MD = os.path.join(ROOT, "anm", "ref-blender-deep-analysis.md")


def matrix_rows(m):
    return [list(row) for row in m]


def idprops(obj):
    out = {}
    try:
        for k in obj.keys():
            try:
                v = obj[k]
                if isinstance(v, (str, int, float, bool)) or v is None:
                    out[k] = v
                else:
                    out[k] = repr(v)
            except Exception as e:
                out[k] = f"<error {e!r}>"
    except Exception:
        pass
    return out


def constraint_data(c):
    keys = [
        "name", "type", "influence", "mute", "target_space", "owner_space",
        "subtarget", "pole_subtarget", "chain_count", "pole_angle",
        "use_rotation", "use_stretch", "use_location", "use_offset",
        "mix_mode", "target_space", "owner_space",
    ]
    out = {}
    for key in keys:
        if hasattr(c, key):
            try:
                out[key] = getattr(c, key)
            except Exception:
                pass
    for key in ("target", "pole_target"):
        if hasattr(c, key):
            obj = getattr(c, key)
            out[key] = obj.name if obj else None
    return out


def animation_data(idblock):
    ad = getattr(idblock, "animation_data", None)
    if not ad:
        return None
    out = {
        "action": ad.action.name if ad.action else None,
        "drivers": [],
        "nla_tracks": [],
    }
    if ad.drivers:
        for fc in ad.drivers:
            drv = fc.driver
            out["drivers"].append({
                "data_path": fc.data_path,
                "array_index": fc.array_index,
                "type": drv.type,
                "expression": drv.expression,
                "variables": [
                    {
                        "name": v.name,
                        "type": v.type,
                        "targets": [
                            {
                                "id": t.id.name if t.id else None,
                                "data_path": t.data_path,
                                "bone_target": t.bone_target,
                                "transform_type": t.transform_type,
                                "transform_space": t.transform_space,
                            }
                            for t in v.targets
                        ],
                    }
                    for v in drv.variables
                ],
            })
    for tr in ad.nla_tracks:
        out["nla_tracks"].append({
            "name": tr.name,
            "mute": tr.mute,
            "strips": [
                {
                    "name": s.name,
                    "action": s.action.name if s.action else None,
                    "frame_start": s.frame_start,
                    "frame_end": s.frame_end,
                    "influence": s.influence,
                }
                for s in tr.strips
            ],
        })
    return out


def action_data(action):
    groups = {}
    for fc in action.fcurves:
        group = fc.group.name if fc.group else ""
        groups.setdefault(group, 0)
        groups[group] += 1
    return {
        "name": action.name,
        "frame_range": list(action.frame_range),
        "fcurves": len(action.fcurves),
        "groups": groups,
        "idprops": idprops(action),
    }


def main():
    data = {
        "file": bpy.data.filepath,
        "objects": [],
        "armatures": [],
        "actions": [action_data(a) for a in bpy.data.actions],
        "texts": [],
        "collections": [],
    }

    for coll in bpy.data.collections:
        data["collections"].append({
            "name": coll.name,
            "objects": [o.name for o in coll.objects],
            "children": [c.name for c in coll.children],
            "hide_viewport": coll.hide_viewport,
        })

    for text in bpy.data.texts:
        body = text.as_string()
        data["texts"].append({
            "name": text.name,
            "filepath": text.filepath,
            "lines": len(body.splitlines()),
            "chars": len(body),
            "preview": body[:500],
        })

    for obj in bpy.data.objects:
        objrow = {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "parent_bone": obj.parent_bone,
            "matrix_world": matrix_rows(obj.matrix_world),
            "idprops": idprops(obj),
            "constraints": [constraint_data(c) for c in obj.constraints],
            "animation_data": animation_data(obj),
        }
        data["objects"].append(objrow)
        if obj.type != "ARMATURE":
            continue

        arm = obj.data
        armrow = {
            "object": obj.name,
            "data": arm.name,
            "idprops_object": idprops(obj),
            "idprops_data": idprops(arm),
            "animation_data": animation_data(obj),
            "bone_collections": [],
            "bones": [],
            "pose_bones": [],
        }
        try:
            for bc in arm.collections:
                armrow["bone_collections"].append({
                    "name": bc.name,
                    "is_visible": bc.is_visible,
                    "is_solo": bc.is_solo,
                    "bones": [b.name for b in bc.bones],
                })
        except Exception:
            pass
        for b in arm.bones:
            armrow["bones"].append({
                "name": b.name,
                "parent": b.parent.name if b.parent else None,
                "head_local": list(b.head_local),
                "tail_local": list(b.tail_local),
                "matrix_local": matrix_rows(b.matrix_local),
                "hide": b.hide,
                "use_connect": b.use_connect,
                "collections": [c.name for c in getattr(b, "collections", [])],
                "idprops": idprops(b),
            })
        for pb in obj.pose.bones:
            armrow["pose_bones"].append({
                "name": pb.name,
                "parent": pb.parent.name if pb.parent else None,
                "rotation_mode": pb.rotation_mode,
                "matrix": matrix_rows(pb.matrix),
                "matrix_basis": matrix_rows(pb.matrix_basis),
                "matrix_channel": matrix_rows(pb.matrix_channel),
                "custom_shape": pb.custom_shape.name if pb.custom_shape else None,
                "bone_group": pb.color.palette if hasattr(pb, "color") else None,
                "idprops": idprops(pb),
                "constraints": [constraint_data(c) for c in pb.constraints],
            })
        data["armatures"].append(armrow)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    lines = [
        "# Reference Blender Deep Analysis",
        "",
        f"Source: `{data['file']}`",
        "",
        "## Summary",
        f"- objects: `{len(data['objects'])}`",
        f"- armatures: `{len(data['armatures'])}`",
        f"- actions: `{len(data['actions'])}`",
        f"- text datablocks: `{len(data['texts'])}`",
        "",
    ]
    for arm in data["armatures"]:
        lines += [
            f"## Armature `{arm['object']}`",
            f"- bones: `{len(arm['bones'])}`",
            f"- pose bones: `{len(arm['pose_bones'])}`",
            f"- bone collections: `{len(arm['bone_collections'])}`",
            f"- object custom props: `{list(arm['idprops_object'].keys())}`",
            f"- data custom props: `{list(arm['idprops_data'].keys())}`",
            "",
            "### Arm/IK Relevant Constraints",
        ]
        for pb in arm["pose_bones"]:
            name = pb["name"]
            if not any(s.lower() in name.lower() for s in ["arm", "hand", "forearm", "ik", "originpose", "direction"]):
                continue
            for c in pb["constraints"]:
                lines.append(
                    f"- `{name}` | {c.get('type')} | `{c.get('name')}` | "
                    f"target=`{c.get('target')}` sub=`{c.get('subtarget')}` "
                    f"pole=`{c.get('pole_subtarget')}` chain=`{c.get('chain_count')}` infl=`{c.get('influence')}`"
                )
        lines.append("")
    lines += [
        "## Text Scripts",
    ]
    for t in data["texts"]:
        lines.append(f"- `{t['name']}`: {t['lines']} lines, {t['chars']} chars")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return {"json": OUT_JSON, "markdown": OUT_MD, "armatures": len(data["armatures"]), "texts": len(data["texts"])}


RESULT = main()
