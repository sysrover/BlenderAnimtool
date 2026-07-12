import json
import os
import sys

from DayzAnimationToolsBinary.Types.Anm import Anm


SOURCE = r"P:\UARP_Items_3\ANM\cable2.anm"
REPORT = r"P:\BlenderAnimtool\Research\anm_reports\cable2-raw-tracks-20260711.json"
if "--" in sys.argv:
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    if arguments:
        SOURCE = arguments[0]
    if len(arguments) > 1:
        REPORT = arguments[1]
TRACKS = {
    "RightHand",
    "RightHandOrigin",
    "RightForeArmDirectionOrigin",
    "RightForeArmDirection",
    "RightHand_Dummy",
    "LeftHandOrigin",
    "LeftHandIKTarget",
}


def decoded(keys, bias, multiplier):
    return [
        {"frame": key.frame, "value": [x * multiplier + bias for x in key.data]}
        for key in keys
    ]


anm = Anm.CreateFromFile(SOURCE)
report = {
    "source": SOURCE,
    "fps": anm.fps,
    "frames": anm.numFrames,
    "tracks": {},
}
for bone in anm.bones:
    if bone.name not in TRACKS:
        continue
    report["tracks"][bone.name] = {
        "flags": bone.flags,
        "position": decoded(bone.posKeys, bone.posBias, bone.posMulti),
        "rotation_xyzw": decoded(bone.rotKeys, bone.rotBias, bone.rotMulti),
    }

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report))
