import json
import os

import bpy


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
OUT_DIR = os.path.join(ROOT, "anm", "ref-blender-texts")
OUT_JSON = os.path.join(ROOT, "anm", "ref-blender-texts-index.json")


def safe_name(name):
    keep = []
    for ch in name:
        if ch.isalnum() or ch in ("_", "-", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep).strip("._") or "text"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for text in bpy.data.texts:
        body = text.as_string()
        filename = safe_name(text.name)
        if not filename.lower().endswith(".py"):
            filename += ".txt"
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        rows.append({
            "name": text.name,
            "filepath": text.filepath,
            "is_modified": bool(text.is_modified),
            "is_in_memory": bool(text.is_in_memory),
            "lines": len(body.splitlines()),
            "chars": len(body),
            "dumped_to": path,
            "preview": body[:300],
        })
    data = {
        "file": bpy.data.filepath,
        "texts_count": len(rows),
        "texts": rows,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


RESULT = main()
