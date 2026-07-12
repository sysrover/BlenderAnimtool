#!/usr/bin/env python3
"""Count actual keyframes in stand_roar.txa hip bone"""

with open('examples/stand_roar.txa') as f:
    lines = f.readlines()

in_hip = False
hip_t_frames = []
hip_q_frames = []
hip_s_frames = []

for i, line in enumerate(lines):
    if '$node "hip"' in line:
        in_hip = True
        continue
    
    if in_hip and line.strip() == '}' and i > 0:
        # Check if this closes hip (look for indentation)
        if lines[i].startswith(' $'):
            break
        if lines[i].startswith('  }') or lines[i].startswith(' }'):
            break
    
    if in_hip:
        if '$frame' in line:
            parts = line.split()
            frame_num = int(parts[1])
            
            # Look ahead to see which channels have data
            j = i + 1
            has_t = False
            has_q = False
            has_s = False
            while j < len(lines) and lines[j].strip() != '}':
                if '#t' in lines[j]:
                    has_t = True
                if '#q' in lines[j]:
                    has_q = True
                if '#s' in lines[j]:
                    has_s = True
                j += 1
            
            if has_t:
                hip_t_frames.append(frame_num)
            if has_q:
                hip_q_frames.append(frame_num)
            if has_s:
                hip_s_frames.append(frame_num)

print(f"Hip bone position keyframes: {len(hip_t_frames)} frames")
print(f"  First 10: {hip_t_frames[:10]}")
print(f"  Last 10: {hip_t_frames[-10:]}")

print(f"\nHip bone rotation keyframes: {len(hip_q_frames)} frames")
print(f"  First 10: {hip_q_frames[:10]}")

print(f"\nHip bone scale keyframes: {len(hip_s_frames)} frames")
print(f"  Frames: {hip_s_frames}")
