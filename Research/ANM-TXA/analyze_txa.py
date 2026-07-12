#!/usr/bin/env python3
"""Analyze TXA structure to understand keyframes."""

import sys
import pathlib

def parse_txa_simple(path):
    """Simple TXA parser to count frames per node."""
    with open(path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_node = None
    frames_by_node = {}
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('$node '):
            # Extract node name
            parts = stripped.split('"')
            if len(parts) >= 2:
                current_node = parts[1]
                frames_by_node[current_node] = {'frames': set(), 'ranges': []}
        elif stripped.startswith('$frame '):
            if current_node:
                # Parse frame number(s)
                frame_str = stripped[7:].rstrip('{').strip()
                parts = frame_str.split()
                if len(parts) == 1:
                    # Single frame
                    frames_by_node[current_node]['frames'].add(int(parts[0]))
                elif len(parts) == 2:
                    # Range frame start end
                    start = int(parts[0])
                    end = int(parts[1])
                    frames_by_node[current_node]['ranges'].append((start, end))
                    for f in range(start, end+1):
                        frames_by_node[current_node]['frames'].add(f)
    
    return frames_by_node

if __name__ == "__main__":
    path = pathlib.Path("examples/stand_roar.txa")
    frames = parse_txa_simple(path)
    
    for node_name in sorted(frames.keys()):
        frame_set = frames[node_name]['frames']
        ranges = frames[node_name]['ranges']
        print(f"\n{node_name}:")
        print(f"  Total frames: {len(frame_set)}")
        if ranges:
            print(f"  Ranges: {ranges}")
        if len(frame_set) <= 20:
            print(f"  Frames: {sorted(frame_set)}")
        else:
            sorted_frames = sorted(frame_set)
            print(f"  Frames: {sorted_frames[:10]} ... {sorted_frames[-5:]}")
