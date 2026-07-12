#!/usr/bin/env python3
"""Debug dedup logic."""

import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from txa_to_anm import parse_txa, FVector, FQuaternion, _quantize_channel

# Parse original TXA
orig = parse_txa(pathlib.Path("examples/stand_walk_fwd.txa"))
hip = orig.nodes['hip']

print("Hip node before processing:")
print(f"  t: {len(hip.t)} keys")
print(f"  q: {len(hip.q)} keys")

# Simulate what encoder does for interpolation
last_frame = orig.num_frames - 1

# Interpolate all frames for rotation (dynamic)
def _interpolate_rotation(frame_num: int):
    rot_frames_sorted = sorted(hip.q.items())
    if frame_num in dict(rot_frames_sorted):
        return dict(rot_frames_sorted)[frame_num]
    frames = [f for f, _ in rot_frames_sorted]
    if not frames:
        return (0.0, 0.0, 0.0, 1.0)
    if frame_num < frames[0]:
        return rot_frames_sorted[0][1]
    if frame_num > frames[-1]:
        return rot_frames_sorted[-1][1]
    prev_frame, prev_val = None, None
    next_frame, next_val = None, None
    for i, f in enumerate(frames):
        if f < frame_num:
            prev_frame, prev_val = f, rot_frames_sorted[i][1]
        elif f > frame_num:
            next_frame, next_val = f, rot_frames_sorted[i][1]
            break
    if prev_frame is not None and next_frame is not None:
        t = (frame_num - prev_frame) / (next_frame - prev_frame)
        prev_quat = FQuaternion(prev_val[3], prev_val[0], prev_val[1], prev_val[2])
        next_quat = FQuaternion(next_val[3], next_val[0], next_val[1], next_val[2])
        interp = prev_quat.slerp(next_quat, t)
        return (interp.x, interp.y, interp.z, interp.w)
    if prev_val:
        return prev_val
    return (0.0, 0.0, 0.0, 1.0)

# Build interpolated rotation frames
rot_frames = [(f, _interpolate_rotation(f)) for f in range(0, last_frame + 1)]

# Quantize with Y/Z swap
rot_vals = []
for _, quat in rot_frames:
    rot_vals.extend([quat[0], quat[2], quat[1], quat[3]])

rot_bias, rot_mult, rot_enc = _quantize_channel(rot_vals)

print(f"\nAfter quantization: {len(rot_frames)} frames, {len(rot_enc)} encoded values")

# Count consecutive identical chunks
def count_dedup(enc_list, stride):
    if not enc_list:
        return 0
    chunks = [tuple(enc_list[i:i+stride]) for i in range(0, len(enc_list), stride)]
    dedup_count = len(chunks)
    prev_chunk = None
    for chunk in chunks:
        if chunk == prev_chunk:
            dedup_count -= 1
        prev_chunk = chunk
    return dedup_count

dedup_rot = count_dedup(rot_enc, 4)
print(f"After dedup (est): {dedup_rot} frames (collapsed {len(rot_frames) - dedup_rot})")

# Show first few chunks to understand
print("\nFirst 10 quantized rotation chunks:")
for i in range(min(10, len(rot_enc) // 4)):
    chunk = rot_enc[i*4:(i+1)*4]
    print(f"  Frame {i}: {chunk}")
