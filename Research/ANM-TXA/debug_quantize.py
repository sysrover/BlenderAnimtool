#!/usr/bin/env python3
"""Debug why frames 39, 47, 48 aren't being deduped."""

import re

def _quantize_channel(values):
    """Quantize a list of float values to 16-bit unsigned integers."""
    if not values:
        return 0.0, 0.0, []
    vmin = min(values)
    vmax = max(values)
    spread = vmax - vmin
    if spread <= 0:
        return vmin, 0.0, [0 for _ in values]
    mult = spread / 65535.0
    encoded = [int((v - vmin) / mult) for v in values]
    encoded = [max(0, min(65535, e)) for e in encoded]
    return vmin, mult, encoded

# Parse TXA for hip rotation values
with open('examples/stand_walk_fwd.txa', 'r') as f:
    content = f.read()

hip_start = content.find('$node "hip"')
hip_end = content.find('$node ', hip_start + 10)
hip_section = content[hip_start:hip_end]

# Extract all #q lines with frame numbers
frames_and_quats = []
lines = hip_section.split('\n')
current_frame = None
for line in lines:
    if '$frame ' in line and '{' in line:
        match = re.search(r'\$frame (\d+)', line)
        if match:
            current_frame = int(match.group(1))
    elif '#q ' in line and current_frame is not None:
        match = re.search(r'#q ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)', line)
        if match:
            x, y, z, w = [float(v) for v in match.groups()]
            frames_and_quats.append((current_frame, (x, y, z, w)))

print(f"Found {len(frames_and_quats)} rotation keyframes in TXA")

# Flatten quaternions for quantization (TXA order: x, y, z, w)
rot_vals = []
for frame, quat in frames_and_quats:
    rot_vals.extend(list(quat))

# Quantize
rot_bias, rot_mult, rot_enc = _quantize_channel(rot_vals)
print(f"Rotation bias: {rot_bias}")
print(f"Rotation mult: {rot_mult}")

# Check for consecutive identical chunks
print("\nFrames with identical encoding to previous:")
for i in range(1, len(frames_and_quats)):
    frame_num = frames_and_quats[i][0]
    prev_frame_num = frames_and_quats[i-1][0]
    
    chunk_curr = tuple(rot_enc[i*4:(i+1)*4])
    chunk_prev = tuple(rot_enc[(i-1)*4:i*4])
    
    if chunk_curr == chunk_prev:
        print(f"  Frame {frame_num}: {chunk_curr} (same as frame {prev_frame_num})")

print("\nFrames that SHOULD be dropped (39, 47, 48):")
for target_frame in [39, 47, 48]:
    # Find index in frames_and_quats
    idx = None
    for j, (f, _) in enumerate(frames_and_quats):
        if f == target_frame:
            idx = j
            break
    
    if idx is not None and idx > 0:
        chunk_curr = tuple(rot_enc[idx*4:(idx+1)*4])
        chunk_prev = tuple(rot_enc[(idx-1)*4:idx*4])
        print(f"  Frame {target_frame}: curr={chunk_curr}, prev={chunk_prev}, match={chunk_curr == chunk_prev}")
    else:
        print(f"  Frame {target_frame}: NOT FOUND in rotation keyframes")
