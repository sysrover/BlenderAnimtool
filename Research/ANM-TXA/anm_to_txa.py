import sys
import pathlib
import types
import importlib.util
from io import StringIO
from typing import Dict, List, Tuple

# Usage: python anm_to_txa.py input.anm output.txa
# Converts a DayZ binary .anm into a text .txa (flat hierarchy, no IK extras).

BIN_BASE = pathlib.Path(__file__).resolve().parent


# Float formatting helpers: emit exact values without tolerance snapping so the
# engine importer cannot collapse near-zero keys.
def _fmt_precise(number: float, precision: int = 9) -> str:
    ret = f"{number:.{precision}f}".rstrip("0")
    if not ret or ret == "-":
        return "0"
    if ret.endswith("."):
        ret += "0"
    if ret in {"-0", "-0.0"}:
        return "0"
    return ret


class FVector:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def swap_yz(self):
        self.y, self.z = self.z, self.y

    def get_swap_yz(self):
        return FVector(self.x, self.z, self.y)

    def __str__(self):
        x = _fmt_precise(self.x)
        y = _fmt_precise(self.y)
        z = _fmt_precise(self.z)
        return f"{x} {y} {z}"

    def __eq__(self, other):
        if not isinstance(other, FVector):
            return False
        return (self.x == other.x and self.y == other.y and self.z == other.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def lerp(self, other: "FVector", t: float) -> "FVector":
        """Linear interpolation between two vectors."""
        return FVector(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t,
        )


class FQuaternion:
    __slots__ = ("w", "x", "y", "z")

    def __init__(self, w: float = 1.0, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"{_fmt_precise(self.x)} {_fmt_precise(self.y)} {_fmt_precise(self.z)} {_fmt_precise(self.w)}"

    def __eq__(self, other):
        if not isinstance(other, FQuaternion):
            return False
        return (self.w == other.w and self.x == other.x and self.y == other.y and self.z == other.z)

    def __hash__(self):
        return hash((self.w, self.x, self.y, self.z))

    def dot(self, other: "FQuaternion") -> float:
        """Compute dot product of two quaternions."""
        return self.w * other.w + self.x * other.x + self.y * other.y + self.z * other.z

    def magnitude(self) -> float:
        """Compute magnitude of quaternion."""
        return (self.w**2 + self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalized(self) -> "FQuaternion":
        """Return a normalized copy of this quaternion."""
        mag = self.magnitude()
        if mag < 1e-10:
            return FQuaternion(1, 0, 0, 0)
        return FQuaternion(self.w / mag, self.x / mag, self.y / mag, self.z / mag)

    def slerp(self, other: "FQuaternion", t: float) -> "FQuaternion":
        """Spherical linear interpolation between two quaternions."""
        q1 = self.normalized()
        q2 = other.normalized()
        
        dot_product = q1.dot(q2)
        
        # If dot product is negative, negate one quaternion to take the shorter path
        if dot_product < 0.0:
            q2 = FQuaternion(-q2.w, -q2.x, -q2.y, -q2.z)
            dot_product = -dot_product
        
        # Clamp dot product to avoid numerical issues with acos
        dot_product = max(-1.0, min(1.0, dot_product))
        
        # If quaternions are very close, use linear interpolation
        if dot_product > 0.9995:
            result = FQuaternion(
                q1.w + (q2.w - q1.w) * t,
                q1.x + (q2.x - q1.x) * t,
                q1.y + (q2.y - q1.y) * t,
                q1.z + (q2.z - q1.z) * t,
            )
            return result.normalized()
        
        # Calculate angle between quaternions
        import math
        theta = math.acos(dot_product)
        sin_theta = math.sin(theta)
        
        # Avoid division by zero
        if sin_theta < 1e-10:
            return q1
        
        # Interpolate
        w1 = math.sin((1.0 - t) * theta) / sin_theta
        w2 = math.sin(t * theta) / sin_theta
        
        return FQuaternion(
            w1 * q1.w + w2 * q2.w,
            w1 * q1.x + w2 * q2.x,
            w1 * q1.y + w2 * q2.y,
            w1 * q1.z + w2 * q2.z,
        )


# Load ANM reader from the shipped binary tools (kept external to avoid reimplementation mistakes)
def load_anm(path: pathlib.Path):
    sys.modules.setdefault("DayzAnimationToolsBinary", types.ModuleType("DayzAnimationToolsBinary"))
    sys.modules.setdefault("DayzAnimationToolsBinary.Utils", types.ModuleType("DayzAnimationToolsBinary.Utils"))
    sys.modules.setdefault("DayzAnimationToolsBinary.Types", types.ModuleType("DayzAnimationToolsBinary.Types"))

    _load_module("DayzAnimationToolsBinary.Utils.BinaryReader", BIN_BASE / "DayzAnimationToolsBinary" / "Utils" / "BinaryReader.py")
    _load_module("DayzAnimationToolsBinary.Utils.Lz4Decoder", BIN_BASE / "DayzAnimationToolsBinary" / "Utils" / "Lz4Decoder.py")
    anm_mod = _load_module("DayzAnimationToolsBinary.Types.Anm", BIN_BASE / "DayzAnimationToolsBinary" / "Types" / "Anm.py")
    return anm_mod.Anm.CreateFromFile(str(path))


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _format_vector(v: FVector) -> str:
    return str(v)


def _format_quat_for_txa(q: FQuaternion) -> str:
    # Spec: #q <x y z w>
    return str(q)


def _frame_bounds(anm) -> Tuple[int, int]:
    """Return (start_frame, end_frame) inferred from keys and events."""
    min_frame = None
    max_frame = 0

    for bone in anm.bones:
        for seq in (bone.posKeys, bone.rotKeys, bone.scaleKeys):
            for key in seq:
                frame = key.frame
                max_frame = max(max_frame, frame)
                min_frame = frame if min_frame is None else min(min_frame, frame)

    for ev in getattr(anm, "events", []):
        max_frame = max(max_frame, ev.frame)
        min_frame = ev.frame if min_frame is None else min(min_frame, ev.frame)

    if min_frame is None:
        min_frame = 0
    return min_frame, max_frame


def _channels_for_bone(bone) -> List[str]:
    channels: List[str] = []
    if bone.posKeys:
        channels.append("t")
    if bone.rotKeys:
        channels.append("q")
    if bone.scaleKeys:
        channels.append("s")
    return channels or ["t", "q", "s"]


def _write_txa(anm, anim_name: str, out_path: pathlib.Path):
    start_frame, end_frame = _frame_bounds(anm)
    total_frames = max(anm.numFrames, end_frame + 1)
    max_frame = total_frames - 1 if total_frames > 0 else 0

    with StringIO() as fs:
        # Headers
        fs.write(f"$animation \"{anim_name}\" {{\n")
        fs.write(" #version 1.0\n")
        fs.write(f" #fps {anm.fps}\n")
        fs.write(f" #numFrames {total_frames}\n")

        # Bones
        for b in anm.bones:
            fs.write(f" $node \"{b.name}\" {{\n")
            fs.write(f"  $keys t q s {{\n")

            # Build per-channel key maps (frame -> value)
            pos_map: Dict[int, FVector] = {}
            rot_map: Dict[int, FQuaternion] = {}
            scale_map: Dict[int, FVector] = {}

            for k in b.posKeys:
                # Fix: TXA expects Y/Z order matching source ANM; swap Y/Z to avoid misordered components
                pos_map[k.frame] = FVector(
                    k.data[0] * b.posMulti + b.posBias,  # x
                    k.data[2] * b.posMulti + b.posBias,  # z -> y swapped
                    k.data[1] * b.posMulti + b.posBias,  # y -> z swapped
                )

            for k in b.rotKeys:
                # Fix: TXA expects Y/Z order matching source ANM; swap Y/Z to avoid misordered components
                rot_map[k.frame] = FQuaternion(
                    k.data[3] * b.rotMulti + b.rotBias,  # w
                    k.data[0] * b.rotMulti + b.rotBias,  # x
                    k.data[2] * b.rotMulti + b.rotBias,  # z -> y swapped
                    k.data[1] * b.rotMulti + b.rotBias,  # y -> z swapped
                )

            for k in b.scaleKeys:
                scale_map[k.frame] = FVector(
                    k.data[0] * b.scaleMulti + b.scaleBias,
                    k.data[1] * b.scaleMulti + b.scaleBias,
                    k.data[2] * b.scaleMulti + b.scaleBias,
                )

            pos_frames_sorted = sorted(pos_map.keys())
            rot_frames_sorted = sorted(rot_map.keys())
            scale_frames_sorted = sorted(scale_map.keys())

            # Collect all frames that have explicit keys (not interpolated)
            all_key_frames = set(pos_map.keys()) | set(rot_map.keys()) | set(scale_map.keys())
            
            # Build frame data for key frames only (don't generate interpolated frames)
            frame_data = {}  # frame_num -> (pos, rot, scale) tuple
            for f in sorted(all_key_frames):
                # Get values for this frame - use explicit keys only
                frame_pos = pos_map.get(f)
                frame_rot = rot_map.get(f)
                frame_scale = scale_map.get(f)
                
                # Only add this frame if at least one channel has data
                if frame_pos is not None or frame_rot is not None or frame_scale is not None:
                    frame_data[f] = (frame_pos, frame_rot, frame_scale)

            # Emit frames - do NOT collapse ranges in TXA since we're preserving exact key structure
            # The TXA format is meant to be lossless; collapsing would lose keyframe info when read back
            sorted_frames = sorted(frame_data.keys())
            for f in sorted_frames:
                # Write frame header (always individual frames, no ranges)
                fs.write(f"   $frame {f} {{\n")

                # Write frame data
                frame_pos, frame_rot, frame_scale = frame_data[f]
                
                if frame_pos is not None:
                    fs.write(f"    #t {_format_vector(frame_pos)}\n")
                if frame_rot is not None:
                    fs.write(f"    #q {_format_quat_for_txa(frame_rot)}\n")
                if frame_scale is not None:
                    fs.write(f"    #s {_format_vector(frame_scale)}\n")

                fs.write("   }\n")

            fs.write("  }\n")
            fs.write(" }\n")

        # Events
        if anm.events:
            fs.write(" $events {\n")
            for ev in anm.events:
                name = ev.name if ev.name else ""
                user_str = ev.userString if ev.userString else ""
                fs.write(f"  #event {ev.frame} \"{name}\" \"{user_str}\" {ev.userInt}\n")
            fs.write("}\n")

        cust_props = getattr(anm, "custProps", None)
        if cust_props:
            fs.write(" $custProps {\n")
            for prop in cust_props:
                if isinstance(prop, tuple) and len(prop) == 2:
                    key, value = prop
                elif isinstance(prop, dict):
                    key, value = prop.get("key", ""), prop.get("value", "")
                else:
                    continue
                # Quote both key and value to match TxaCustomProperty.Read() expectations
                fs.write(f"  #custProp \"{key}\" \"{value}\"\n")
            fs.write(" }\n")

        fs.write("}\n")

        out_path.write_text(fs.getvalue(), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python anm_to_txa.py <input.anm> [output.txa]")
        print("If output.txa is not specified, it will be created next to input with .txa extension")
        sys.exit(1)

    inp = pathlib.Path(sys.argv[1]).resolve()
    
    if len(sys.argv) >= 3:
        outp = pathlib.Path(sys.argv[2]).resolve()
    else:
        outp = inp.with_suffix('.txa')

    if not inp.exists():
        print(f"Input not found: {inp}")
        sys.exit(1)

    anm = load_anm(inp)
    anim_name = inp.stem
    _write_txa(anm, anim_name, outp)
    print(f"Wrote {outp}")


if __name__ == "__main__":
    main()
