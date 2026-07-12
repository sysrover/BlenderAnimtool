import importlib.util
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "blender_remote"
    / "addon"
    / "bld_remote_mcp"
    / "compact_query.py"
)
SPEC = importlib.util.spec_from_file_location("compact_query_under_test", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FakeObject:
    def __init__(self, name, object_type="MESH"):
        self.name = name
        self.type = object_type
        self.parent = None

    def visible_get(self):
        return True

    def select_get(self):
        return False


def fake_bpy(objects):
    scene = SimpleNamespace(
        name="Scene",
        frame_current=3,
        frame_start=0,
        frame_end=10,
        objects=objects,
    )
    context = SimpleNamespace(
        scene=scene,
        object=None,
        mode="OBJECT",
        selected_objects=[],
    )
    return SimpleNamespace(context=context, data=SimpleNamespace(filepath="test.blend"))


def test_list_objects_is_paginated_and_cached():
    service = MODULE.CompactQueryService(
        fake_bpy([FakeObject(f"Object_{index:03d}") for index in range(120)])
    )
    first = service.query(op="list_objects", limit=10)
    assert len(first["items"]) == 10
    assert first["total"] == 120
    assert first["next_offset"] == 10
    assert first["result_id"].startswith("result_")
    assert first["response_bytes"] == len(
        MODULE.json.dumps(first, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )

    second = service.query(
        op="result_page", result_id=first["result_id"], offset=10, limit=10
    )
    assert second["items"][0]["name"] == "Object_010"


def test_response_byte_limit_shrinks_page():
    service = MODULE.CompactQueryService(
        fake_bpy([FakeObject("X" * 200 + str(index)) for index in range(20)])
    )
    response = service.query(op="list_objects", limit=20, max_bytes=1024)
    assert response["truncated"] is True
    assert response["reason"] == "max_response_bytes"
    assert len(response["items"]) < 20
    assert response["result_id"].startswith("result_")
    assert response["response_bytes"] <= 1024


def test_scene_summary_stays_compact():
    service = MODULE.CompactQueryService(fake_bpy([FakeObject("Cube")]))
    response = service.query(op="scene_summary")
    assert response["ok"] is True
    assert response["data"]["object_count"] == 1
    assert response["data"]["file"] == "test.blend"


def test_fields_project_single_result():
    service = MODULE.CompactQueryService(fake_bpy([FakeObject("Cube")]))
    response = service.query(op="scene_summary", fields=["file", "frame"])
    assert response["data"] == {"file": "test.blend", "frame": 3}


def test_item_fields_project_list_results_before_caching():
    service = MODULE.CompactQueryService(
        fake_bpy([FakeObject(f"Object_{index:03d}") for index in range(60)])
    )
    response = service.query(op="list_objects", limit=10, item_fields="name,type")
    assert response["items"][0] == {"name": "Object_000", "type": "MESH"}
    second = service.query(
        op="result_page", result_id=response["result_id"], offset=10, limit=10
    )
    assert second["items"][0] == {"name": "Object_010", "type": "MESH"}


def test_nested_fields_do_not_return_full_child_objects():
    service = MODULE.CompactQueryService(fake_bpy([]))
    value = {
        "name": "Bone",
        "constraints": [
            {"name": "IK", "type": "IK", "target": "Rig", "influence": 1.0}
        ],
    }
    assert service._project(value, ["name", "constraints.name"]) == {
        "name": "Bone",
        "constraints": [{"name": "IK"}],
    }


def test_batch_uses_one_bounded_response():
    service = MODULE.CompactQueryService(fake_bpy([FakeObject("Cube")]))
    response = service.batch(
        [
            {"op": "scene_summary", "fields": ["file", "frame"]},
            {"op": "list_objects", "item_fields": ["name", "type"]},
        ]
    )
    assert response["count"] == 2
    assert len(response["results"]) == 2
    assert response["truncated"] is False
    assert response["response_bytes"] == len(
        MODULE.json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def test_compact_errors_are_short_and_do_not_abort_batch():
    service = MODULE.CompactQueryService(fake_bpy([]))
    single = service.safe_query(op="missing_operation")
    assert single["ok"] is False
    assert single["error_type"] == "ValueError"
    assert "traceback" not in single
    assert single["response_bytes"] < 256

    batch = service.batch(
        [
            {"op": "missing_operation"},
            {"op": "scene_summary", "fields": ["file"]},
        ]
    )
    assert batch["results"][0]["ok"] is False
    assert batch["results"][1]["ok"] is True
