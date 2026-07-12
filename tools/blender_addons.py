"""Install, verify, and safely hot-reload local Blender add-ons."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BLENDER_VERSION = "4.5"
ADDONS = {
    "DayzAnimationTools": ROOT / "DayzAnimationTools",
    "bld_remote_mcp": (
        ROOT
        / "blender-remote-1.3.3"
        / "src"
        / "blender_remote"
        / "addon"
        / "bld_remote_mcp"
    ),
}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".git"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def addon_root() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not defined")
    return (
        Path(appdata)
        / "Blender Foundation"
        / "Blender"
        / BLENDER_VERSION
        / "scripts"
        / "addons"
    )


def source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        yield path, relative


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path, relative in source_files(root):
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_hash(path)))
    return digest.hexdigest()


def install_tree(source: Path, destination: Path) -> dict[str, Any]:
    changed = []
    copied = 0
    for source_path, relative in source_files(source):
        destination_path = destination / relative
        if not destination_path.exists() or file_hash(source_path) != file_hash(
            destination_path
        ):
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
            changed.append(relative.as_posix())
            copied += 1

    source_digest = tree_hash(source)
    installed_digest = tree_hash(destination)
    if source_digest != installed_digest:
        raise RuntimeError(f"Hash verification failed for {source.name}")
    return {
        "changed": changed,
        "copied": copied,
        "source_hash": source_digest,
        "installed_hash": installed_digest,
        "verified": True,
    }


def status() -> dict[str, Any]:
    destination_root = addon_root()
    addons = {}
    for name, source in ADDONS.items():
        destination = destination_root / name
        source_digest = tree_hash(source)
        installed_digest = tree_hash(destination) if destination.exists() else None
        addons[name] = {
            "installed": destination.exists(),
            "matches": source_digest == installed_digest,
            "source_hash": source_digest,
            "installed_hash": installed_digest,
        }
    return {"ok": True, "addon_root": str(destination_root), "addons": addons}


def hot_reload(port: int) -> dict[str, Any]:
    from blender_remote.client import BlenderMCPClient

    client = BlenderMCPClient(host="127.0.0.1", port=port, timeout=20)
    code = r"""
import hashlib
import importlib
import json
import bld_remote_mcp
from bld_remote_mcp import compact_query
from DayzAnimationTools.Tools import AddSurvivorIK

importlib.reload(compact_query)
bld_remote_mcp.CompactQueryService = compact_query.CompactQueryService
if bld_remote_mcp._tcp_server is None:
    raise RuntimeError("BLD Remote TCP server instance not found")
bld_remote_mcp._tcp_server.compact_queries = compact_query.CompactQueryService(bpy)

importlib.reload(AddSurvivorIK)
AddSurvivorIK.register_dayz_proxy_ik_sync_handlers()

def digest(path):
    with open(path, "rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()

print(json.dumps({
    "file": bpy.data.filepath,
    "compact_query_hash": digest(compact_query.__file__),
    "dayz_ik_hash": digest(AddSurvivorIK.__file__),
    "sync_handlers": sum(
        getattr(handler, "__name__", "") == "_dayz_proxy_ik_sync_handler"
        for handler in bpy.app.handlers.depsgraph_update_post
    ),
}, separators=(",", ":")))
"""
    output = client.execute_python(code, return_as_base64=False).strip()
    return json.loads(output)


def install(port: int, reload_live: bool) -> dict[str, Any]:
    destination_root = addon_root()
    results = {}
    for name, source in ADDONS.items():
        results[name] = install_tree(source, destination_root / name)

    live = None
    live_error = None
    if reload_live:
        try:
            live = hot_reload(port)
            expected_compact = file_hash(
                destination_root / "bld_remote_mcp" / "compact_query.py"
            )
            expected_dayz = file_hash(
                destination_root / "DayzAnimationTools" / "Tools" / "AddSurvivorIK.py"
            )
            live["verified"] = (
                live.get("compact_query_hash") == expected_compact
                and live.get("dayz_ik_hash") == expected_dayz
                and live.get("sync_handlers") == 1
            )
            if not live["verified"]:
                raise RuntimeError("Live Blender hashes or sync handler do not match")
        except Exception as error:
            live_error = f"{type(error).__name__}: {error}"

    return {
        "ok": live_error is None,
        "installed": results,
        "live": live,
        "live_error": live_error,
        "restart_required": live_error is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("install", "status"))
    parser.add_argument("--port", type=int, default=6688)
    parser.add_argument("--no-hot-reload", action="store_true")
    args = parser.parse_args()

    result = (
        status()
        if args.command == "status"
        else install(args.port, reload_live=not args.no_hot_reload)
    )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
