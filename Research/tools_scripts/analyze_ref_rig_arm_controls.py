import json
import os


ROOT = r"C:\Users\sysro\diag\CsharpModVScode"
DUMP = os.path.join(ROOT, "anm", "blender-ref-skeleton-dump.json")
OUT_JSON = os.path.join(ROOT, "anm", "ref-rig-arm-control-analysis.json")
OUT_MD = os.path.join(ROOT, "anm", "ref-rig-arm-control-analysis.md")


KEYWORDS = (
    "upper_arm", "forearm", "hand", "arm", "ik", "pole",
    "RightHand", "LeftHand", "RightForeArm", "LeftForeArm",
    "OriginPose", "DirectionOriginPose",
)


def is_interesting(name):
    low = name.lower()
    return any(k.lower() in low for k in KEYWORDS)


def main():
    with open(DUMP, encoding="utf-8") as f:
        data = json.load(f)
    result = {"file": data["file"], "armatures": {}}
    for arm in data["armatures"]:
        bones = {b["name"]: b for b in arm["bones"]}
        pose = {pb["name"]: pb for pb in arm["pose_bones"]}
        interesting_bones = sorted([n for n in bones if is_interesting(n)])
        constraints = []
        for name, pb in pose.items():
            if is_interesting(name) or any(is_interesting(str(c.get(x, ""))) for c in pb["constraints"] for x in ("subtarget", "pole_subtarget")):
                for c in pb["constraints"]:
                    if (
                        is_interesting(name)
                        or is_interesting(c.get("subtarget", ""))
                        or is_interesting(c.get("pole_subtarget", ""))
                        or c.get("type") in ("IK", "COPY_TRANSFORMS", "COPY_LOCATION", "COPY_ROTATION", "STRETCH_TO")
                    ):
                        constraints.append({
                            "bone": name,
                            "constraint": c["name"],
                            "type": c["type"],
                            "target": c.get("target"),
                            "subtarget": c.get("subtarget"),
                            "pole_subtarget": c.get("pole_subtarget"),
                            "chain_count": c.get("chain_count"),
                            "pole_angle": c.get("pole_angle"),
                            "influence": c.get("influence"),
                        })
        result["armatures"][arm["object"]] = {
            "bone_count": arm["bone_count"],
            "interesting_bones": interesting_bones,
            "constraints": constraints,
        }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    lines = []
    lines.append("# Reference Rig Arm Control Analysis\n")
    lines.append(f"Source: `{data['file']}`\n")
    for arm_name, arm_data in result["armatures"].items():
        lines.append(f"## {arm_name}\n")
        lines.append(f"- bone count: `{arm_data['bone_count']}`")
        lines.append(f"- interesting bones: `{len(arm_data['interesting_bones'])}`")
        lines.append(f"- interesting constraints: `{len(arm_data['constraints'])}`\n")
        lines.append("### High-value bones\n")
        for name in arm_data["interesting_bones"][:180]:
            lines.append(f"- `{name}`")
        lines.append("\n### Constraints\n")
        for c in arm_data["constraints"][:260]:
            bits = [
                f"`{c['bone']}`",
                c["type"],
                f"target=`{c.get('target')}`",
                f"sub=`{c.get('subtarget')}`",
            ]
            if c.get("pole_subtarget"):
                bits.append(f"pole=`{c.get('pole_subtarget')}`")
            if c.get("chain_count"):
                bits.append(f"chain={c.get('chain_count')}")
            if c.get("influence") is not None:
                bits.append(f"infl={c.get('influence')}")
            lines.append("- " + " | ".join(bits))
        lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return result


if __name__ == "__main__":
    main()
