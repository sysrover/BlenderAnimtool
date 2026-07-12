"""Token-efficient, read-only queries for live Blender inspection."""

import json
import time
import uuid
from collections import OrderedDict

DEFAULT_LIMIT = 50
MAX_LIMIT = 500
DEFAULT_MAX_BYTES = 32 * 1024
MIN_MAX_BYTES = 1024
MAX_MAX_BYTES = 256 * 1024
CACHE_TTL_SECONDS = 300.0
MAX_CACHED_RESULTS = 16
FLOAT_DIGITS = 6


def _rounded(value):
    return round(float(value), FLOAT_DIGITS)


def _vector(value):
    return [_rounded(item) for item in value]


def _matrix(value):
    return [[_rounded(item) for item in row] for row in value]


def _json_size(value):
    return len(
        json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


class CompactQueryService:
    """Execute bounded Blender queries and page large results from memory."""

    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self._results = OrderedDict()
        self._snapshots = OrderedDict()

    def query(
        self,
        op="scene_summary",
        offset=0,
        limit=DEFAULT_LIMIT,
        max_bytes=DEFAULT_MAX_BYTES,
        result_id=None,
        fields=None,
        item_fields=None,
        **params,
    ):
        self._prune_caches()
        offset = max(0, int(offset))
        limit = min(MAX_LIMIT, max(1, int(limit)))
        max_bytes = min(MAX_MAX_BYTES, max(MIN_MAX_BYTES, int(max_bytes)))

        if op == "batch":
            return self.batch(max_bytes=max_bytes, **params)

        if op == "result_page":
            if not result_id or result_id not in self._results:
                raise ValueError("Unknown or expired result_id")
            items = self._results[result_id][1]
            return self._page(op, items, offset, limit, max_bytes, result_id)

        handlers = {
            "scene_summary": self._scene_summary,
            "list_objects": self._list_objects,
            "list_armatures": self._list_armatures,
            "list_bones": self._list_bones,
            "inspect_bone": self._inspect_bone,
            "inspect_action": self._inspect_action,
            "list_fcurves": self._list_fcurves,
            "snapshot_pose": self._snapshot_pose,
            "diff_pose": self._diff_pose,
            "restore_pose": self._restore_pose,
            "capabilities": self._capabilities,
        }
        handler = handlers.get(op)
        if handler is None:
            raise ValueError(f"Unknown compact query operation: {op}")

        result = handler(**params)
        if isinstance(result, list):
            result = self._project_items(result, item_fields)
            needs_cache = len(result) > limit or _json_size(result) > max_bytes
            cached_id = self._cache_result(result) if needs_cache else None
            return self._page(op, result, offset, limit, max_bytes, cached_id)

        result = self._project(result, fields)

        envelope = {"ok": True, "op": op, "data": result, "truncated": False}
        if self._response_size(envelope) > max_bytes:
            return self._finish(
                {
                    "ok": True,
                    "op": op,
                    "truncated": True,
                    "reason": "max_response_bytes",
                    "summary": self._summarize(result),
                }
            )
        return self._finish(envelope)

    def safe_query(self, **params):
        try:
            return self.query(**params)
        except Exception as error:
            return self._finish(
                {
                    "ok": False,
                    "op": params.get("op", "scene_summary"),
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )

    def batch(self, queries=None, max_bytes=DEFAULT_MAX_BYTES):
        queries = list(queries or [])
        if not queries:
            raise ValueError("queries must contain at least one compact query")
        max_bytes = min(MAX_MAX_BYTES, max(MIN_MAX_BYTES, int(max_bytes)))
        envelope = {
            "ok": True,
            "results": [],
            "count": len(queries),
            "next_index": None,
            "truncated": False,
        }
        for index, query in enumerate(queries):
            if not isinstance(query, dict):
                raise ValueError(f"queries[{index}] must be an object")
            result = self.safe_query(**query)
            envelope["results"].append(result)
            if self._response_size(envelope) > max_bytes:
                envelope["results"].pop()
                envelope["next_index"] = index
                envelope["truncated"] = True
                envelope["reason"] = "max_response_bytes"
                break
        return self._finish(envelope)

    def _page(self, op, items, offset, limit, max_bytes, result_id):
        total = len(items)
        page = list(items[offset : offset + limit])
        envelope = {
            "ok": True,
            "op": op,
            "items": page,
            "offset": offset,
            "limit": limit,
            "total": total,
            "next_offset": offset + len(page) if offset + len(page) < total else None,
            "truncated": offset + len(page) < total,
        }
        if result_id:
            envelope["result_id"] = result_id

        while page and self._response_size(envelope) > max_bytes:
            page.pop()
            envelope["items"] = page
            envelope["next_offset"] = offset + len(page)
            envelope["truncated"] = True
            envelope["reason"] = "max_response_bytes"

        if not page and offset < total and self._response_size(envelope) > max_bytes:
            envelope["reason"] = "item_exceeds_max_response_bytes"
        return self._finish(envelope)

    @staticmethod
    def _finish(envelope):
        envelope["response_bytes"] = 0
        for _ in range(3):
            size = _json_size(envelope)
            if envelope["response_bytes"] == size:
                break
            envelope["response_bytes"] = size
        return envelope

    @classmethod
    def _response_size(cls, envelope):
        return cls._finish(dict(envelope))["response_bytes"]

    def _cache_result(self, items):
        result_id = "result_" + uuid.uuid4().hex[:12]
        self._results[result_id] = (time.monotonic(), list(items))
        while len(self._results) > MAX_CACHED_RESULTS:
            self._results.popitem(last=False)
        return result_id

    @staticmethod
    def _normalize_fields(fields):
        if fields is None:
            return None
        if isinstance(fields, str):
            fields = [item.strip() for item in fields.split(",")]
        return {str(item) for item in fields if str(item)}

    def _project(self, value, fields):
        selected = self._normalize_fields(fields)
        if selected is None or not isinstance(value, dict):
            return value
        result = {}
        nested = {}
        for field in sorted(selected):
            root, separator, remainder = field.partition(".")
            if not separator:
                if root in value:
                    result[root] = value[root]
                continue
            nested.setdefault(root, set()).add(remainder)
        for root, child_fields in nested.items():
            if root not in value:
                continue
            child = value[root]
            if isinstance(child, list):
                result[root] = [self._project(item, child_fields) for item in child]
            elif isinstance(child, dict):
                result[root] = self._project(child, child_fields)
        return result

    def _project_items(self, items, fields):
        selected = self._normalize_fields(fields)
        if selected is None:
            return items
        return [self._project(item, selected) for item in items]

    def _prune_caches(self):
        now = time.monotonic()
        for cache in (self._results, self._snapshots):
            expired = [
                key
                for key, value in cache.items()
                if now - value[0] > CACHE_TTL_SECONDS
            ]
            for key in expired:
                cache.pop(key, None)

    def _armature(self, name=None):
        if name:
            obj = self.bpy.data.objects.get(name)
            if obj is None or obj.type != "ARMATURE":
                raise ValueError(f"Armature not found: {name}")
            return obj
        active = self.bpy.context.object
        if active is not None and active.type == "ARMATURE":
            return active
        obj = next(
            (
                item
                for item in self.bpy.context.scene.objects
                if item.type == "ARMATURE"
            ),
            None,
        )
        if obj is None:
            raise ValueError("No armature in the current scene")
        return obj

    def _scene_summary(self):
        scene = self.bpy.context.scene
        counts = {}
        for obj in scene.objects:
            counts[obj.type] = counts.get(obj.type, 0) + 1
        active = self.bpy.context.object
        return {
            "file": self.bpy.data.filepath,
            "scene": scene.name,
            "frame": scene.frame_current,
            "frame_range": [scene.frame_start, scene.frame_end],
            "object_count": len(scene.objects),
            "object_types": counts,
            "active_object": active.name if active else None,
            "mode": self.bpy.context.mode,
            "selected_objects": [obj.name for obj in self.bpy.context.selected_objects],
        }

    def _list_objects(self, object_type=None, name_contains=None):
        needle = str(name_contains or "").casefold()
        items = []
        for obj in self.bpy.context.scene.objects:
            if object_type and obj.type != str(object_type).upper():
                continue
            if needle and needle not in obj.name.casefold():
                continue
            items.append(
                {
                    "name": obj.name,
                    "type": obj.type,
                    "visible": bool(obj.visible_get()),
                    "selected": bool(obj.select_get()),
                    "parent": obj.parent.name if obj.parent else None,
                }
            )
        return items

    def _list_armatures(self):
        return [
            {
                "name": obj.name,
                "bones": len(obj.data.bones),
                "visible": bool(obj.visible_get()),
                "selected": bool(obj.select_get()),
                "action": (
                    obj.animation_data.action.name
                    if obj.animation_data and obj.animation_data.action
                    else None
                ),
            }
            for obj in self.bpy.context.scene.objects
            if obj.type == "ARMATURE"
        ]

    def _list_bones(self, armature=None, name_contains=None, visible_only=False):
        obj = self._armature(armature)
        needle = str(name_contains or "").casefold()
        items = []
        for pose_bone in obj.pose.bones:
            if needle and needle not in pose_bone.name.casefold():
                continue
            if visible_only and pose_bone.bone.hide:
                continue
            items.append(
                {
                    "name": pose_bone.name,
                    "parent": pose_bone.parent.name if pose_bone.parent else None,
                    "hidden": bool(pose_bone.bone.hide),
                    "selected": bool(pose_bone.bone.select),
                    "constraints": len(pose_bone.constraints),
                    "custom_shape": (
                        pose_bone.custom_shape.name if pose_bone.custom_shape else None
                    ),
                }
            )
        return items

    def _constraint(self, item):
        data = {
            "name": item.name,
            "type": item.type,
            "mute": bool(item.mute),
            "influence": _rounded(item.influence),
            "target": item.target.name if getattr(item, "target", None) else None,
            "subtarget": getattr(item, "subtarget", ""),
            "owner_space": getattr(item, "owner_space", None),
            "target_space": getattr(item, "target_space", None),
            "chain_count": getattr(item, "chain_count", None),
            "pole_angle": _rounded(getattr(item, "pole_angle", 0.0)),
        }
        return {key: value for key, value in data.items() if value not in (None, "")}

    def _inspect_bone(self, bone, armature=None, matrices=False):
        obj = self._armature(armature)
        pose_bone = obj.pose.bones.get(bone)
        if pose_bone is None:
            raise ValueError(f"Bone not found: {bone}")
        data = {
            "armature": obj.name,
            "name": pose_bone.name,
            "parent": pose_bone.parent.name if pose_bone.parent else None,
            "location": _vector(pose_bone.location),
            "rotation_mode": pose_bone.rotation_mode,
            "rotation_quaternion": _vector(pose_bone.rotation_quaternion),
            "rotation_euler": _vector(pose_bone.rotation_euler),
            "scale": _vector(pose_bone.scale),
            "head": _vector(pose_bone.head),
            "tail": _vector(pose_bone.tail),
            "locks": {
                "location": list(pose_bone.lock_location),
                "rotation": list(pose_bone.lock_rotation),
                "scale": list(pose_bone.lock_scale),
            },
            "constraints": [self._constraint(item) for item in pose_bone.constraints],
            "custom_properties": {
                key: value
                for key, value in pose_bone.items()
                if isinstance(value, (str, int, float, bool))
            },
        }
        if matrices:
            data["matrix"] = _matrix(pose_bone.matrix)
            data["matrix_basis"] = _matrix(pose_bone.matrix_basis)
        return data

    def _action(self, action=None, armature=None):
        if action:
            result = self.bpy.data.actions.get(action)
        else:
            obj = self._armature(armature)
            result = obj.animation_data.action if obj.animation_data else None
        if result is None:
            raise ValueError("Action not found")
        return result

    def _inspect_action(self, action=None, armature=None):
        item = self._action(action, armature)
        fcurves = self._action_fcurves(item)
        return {
            "name": item.name,
            "frame_range": _vector(item.frame_range),
            "fcurves": len(fcurves),
            "groups": sorted(
                {curve.group.name for curve in fcurves if curve.group is not None}
            ),
            "custom_properties": {
                key: value
                for key, value in item.items()
                if isinstance(value, (str, int, float, bool))
            },
        }

    def _list_fcurves(self, action=None, armature=None, data_path_contains=None):
        item = self._action(action, armature)
        needle = str(data_path_contains or "").casefold()
        result = []
        for curve in self._action_fcurves(item):
            if needle and needle not in curve.data_path.casefold():
                continue
            result.append(
                {
                    "data_path": curve.data_path,
                    "array_index": curve.array_index,
                    "keyframes": len(curve.keyframe_points),
                    "range": _vector(curve.range()),
                    "group": curve.group.name if curve.group else None,
                }
            )
        return result

    @staticmethod
    def _action_fcurves(action):
        legacy = getattr(action, "fcurves", None)
        if legacy is not None:
            return list(legacy)
        curves = []
        for layer in getattr(action, "layers", []):
            for strip in getattr(layer, "strips", []):
                for slot in getattr(action, "slots", []):
                    try:
                        channelbag = strip.channelbag(slot)
                    except (AttributeError, RuntimeError, TypeError):
                        channelbag = None
                    if channelbag is not None:
                        curves.extend(channelbag.fcurves)
        return curves

    @staticmethod
    def _pose_state(obj):
        return {bone.name: bone.matrix.copy() for bone in obj.pose.bones}

    def _snapshot_pose(self, armature=None):
        obj = self._armature(armature)
        snapshot_id = "pose_" + uuid.uuid4().hex[:12]
        self._snapshots[snapshot_id] = (
            time.monotonic(),
            obj.name,
            self._pose_state(obj),
        )
        while len(self._snapshots) > MAX_CACHED_RESULTS:
            self._snapshots.popitem(last=False)
        return {
            "snapshot_id": snapshot_id,
            "armature": obj.name,
            "bones": len(obj.pose.bones),
        }

    def _diff_pose(self, snapshot_id, tolerance=1.0e-5):
        record = self._snapshots.get(snapshot_id)
        if record is None:
            raise ValueError("Unknown or expired snapshot_id")
        _, armature_name, before = record
        obj = self._armature(armature_name)
        tolerance = max(0.0, float(tolerance))
        changed = []
        for bone in obj.pose.bones:
            old = before.get(bone.name)
            current = bone.matrix
            if old is None:
                changed.append({"bone": bone.name, "change": "added"})
                continue
            max_delta = max(
                abs(float(current[row][column]) - float(old[row][column]))
                for row in range(4)
                for column in range(4)
            )
            if max_delta > tolerance:
                changed.append(
                    {"bone": bone.name, "max_matrix_delta": _rounded(max_delta)}
                )
        return changed

    def _restore_pose(self, snapshot_id):
        record = self._snapshots.get(snapshot_id)
        if record is None:
            raise ValueError("Unknown or expired snapshot_id")
        _, armature_name, saved = record
        obj = self._armature(armature_name)
        restored = 0
        missing = []
        for bone_name, matrix in saved.items():
            bone = obj.pose.bones.get(bone_name)
            if bone is None:
                missing.append(bone_name)
                continue
            bone.matrix = matrix.copy()
            restored += 1
        self.bpy.context.view_layer.update()
        return {
            "snapshot_id": snapshot_id,
            "armature": armature_name,
            "restored": restored,
            "missing": missing,
        }

    def _capabilities(self):
        return {
            "version": 1,
            "default_limit": DEFAULT_LIMIT,
            "max_limit": MAX_LIMIT,
            "default_max_bytes": DEFAULT_MAX_BYTES,
            "max_max_bytes": MAX_MAX_BYTES,
            "cache_ttl_seconds": CACHE_TTL_SECONDS,
            "selective_fields": {
                "single_result": "fields",
                "list_result": "item_fields",
                "nested": "parent.child",
            },
            "batch_operation": "batch",
            "operations": [
                "capabilities",
                "scene_summary",
                "list_objects",
                "list_armatures",
                "list_bones",
                "inspect_bone",
                "inspect_action",
                "list_fcurves",
                "snapshot_pose",
                "diff_pose",
                "restore_pose",
                "result_page",
            ],
        }

    @staticmethod
    def _summarize(value):
        if isinstance(value, dict):
            return {
                "type": "object",
                "keys": sorted(value.keys()),
                "fields": len(value),
            }
        if isinstance(value, list):
            return {"type": "array", "items": len(value)}
        return {"type": type(value).__name__}
