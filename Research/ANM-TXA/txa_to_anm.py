#!/usr/bin/env python3
"""
TXA to ANM (AnimSet6) converter - matches DayZ binary reader exactly.
"""

import pathlib
import struct
import sys
from typing import Dict, List, Optional, Tuple

# Reuse quaternion helpers from anm_to_txa for slerp comparison
from anm_to_txa import FQuaternion, FVector

SCALE_FACTOR = 1.525902e-05

class TxaNode:
    def __init__(self, name: str):
        self.name = name
        self.t: Dict[int, Tuple[float, float, float]] = {}
        self.q: Dict[int, Tuple[float, float, float, float]] = {}
        self.s: Dict[int, Tuple[float, float, float]] = {}

class TxaAnim:
    def __init__(self, name: str):
        self.name = name
        self.fps = 30
        self.num_frames = 0
        self.nodes: Dict[str, TxaNode] = {}
        self.events: List[Tuple[int, str, str, int]] = []
        self.cust_props: List[Tuple[str, str]] = []

# -------- TXA parsing --------

def _parse_vector(parts: List[str], count: int) -> Tuple[float, ...]:
    return tuple(float(x) for x in parts[:count])

def _unquote(text: str) -> str:
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    return text

def parse_txa(path: pathlib.Path) -> TxaAnim:
    lines = path.read_text(encoding="utf-8").splitlines()
    anim: Optional[TxaAnim] = None
    current_node: Optional[TxaNode] = None
    in_events = False
    in_cust = False
    depth = 0
    node_depth: Optional[int] = None
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1
        if not line:
            continue

        opens = raw.count("{")
        closes = raw.count("}") if not line.startswith("#") else 0
        depth += opens

        if line.startswith("$animation"):
            name = line.split('"')[1]
            anim = TxaAnim(name)
            continue
        if anim is None:
            depth -= closes
            continue

        if line.startswith("#fps"):
            anim.fps = int(line.split()[1])
            depth -= closes
            continue
        if line.startswith("#numFrames"):
            anim.num_frames = int(line.split()[1])
            depth -= closes
            continue

        if line.startswith("$node"):
            node_name = line.split('"')[1]
            current_node = TxaNode(node_name)
            anim.nodes[node_name] = current_node
            node_depth = depth
            depth -= closes
            continue
        if line.startswith("$events"):
            in_events = True
            depth -= closes
            continue
        if line.startswith("$custProps"):
            in_cust = True
            depth -= closes
            continue

        if in_events:
            if line.startswith("#event"):
                parts = line.split()
                frame = int(parts[1])
                name = _unquote(parts[2]) if len(parts) > 2 else ""
                user = _unquote(parts[3]) if len(parts) > 3 else ""
                user_int = int(parts[4]) if len(parts) > 4 else -1
                anim.events.append((frame, name, user, user_int))
            depth -= closes
            continue

        if in_cust:
            if line.startswith("#custProp"):
                parts = line.split('"')
                if len(parts) >= 4:
                    key = parts[1]
                    val = parts[3]
                    anim.cust_props.append((key, val))
            depth -= closes
            continue

        if current_node is None:
            depth -= closes
            continue

        if line.startswith("$frame"):
            parts = line.split()
            start = int(parts[1])
            end = int(parts[2]) if len(parts) >= 4 and parts[2].isdigit() else start
            frame_t: Optional[Tuple[float, float, float]] = None
            frame_q: Optional[Tuple[float, float, float, float]] = None
            frame_s: Optional[Tuple[float, float, float]] = None
            while i < len(lines):
                block = lines[i].strip()
                i += 1
                if block == "}":
                    break
                if block.startswith("#t"):
                    frame_t = _parse_vector(block.split()[1:], 3)
                elif block.startswith("#q"):
                    frame_q = _parse_vector(block.split()[1:], 4)
                elif block.startswith("#s"):
                    frame_s = _parse_vector(block.split()[1:], 3)
            
            # Handle ranges per channel: rotations expand fully (dynamic), translations keep start/end,
            # scales stay sparse (first, and optionally last once per node) to match original key counts.
            if end < start:
                end = start

            if frame_t is not None:
                current_node.t[start] = frame_t
                if end != start:
                    current_node.t[end] = frame_t

            if frame_q is not None:
                for fidx in range(start, end + 1):
                    current_node.q[fidx] = frame_q

            if frame_s is not None:
                # Add the first scale key; add the end only once per node to avoid over-duplication
                if start not in current_node.s:
                    current_node.s[start] = frame_s
                if end != start and not any(f == end for f in current_node.s):
                    current_node.s[end] = frame_s
            depth -= closes
            continue

        depth -= closes
        if node_depth is not None and depth < node_depth:
            current_node = None
            node_depth = None

    if anim is None:
        raise ValueError("No animation found in TXA")
    return anim

# -------- Quantization --------

def _quantize_channel(values: List[float]) -> Tuple[float, float, List[int]]:
    if not values:
        return 0.0, 0.0, []
    vmin = min(values)
    vmax = max(values)
    spread = vmax - vmin
    if spread <= 0:
        return vmin, 0.0, [0 for _ in values]
    mult = spread / 65535.0
    encoded = [int(round((v - vmin) / mult)) for v in values]
    encoded = [max(0, min(65535, e)) for e in encoded]
    return vmin, mult, encoded

# -------- ANM writing (AnimSet6 format) --------

def _write_anm(anim: TxaAnim, out_path: pathlib.Path):
    head_bytes = bytearray()
    data_bytes = bytearray()

    # Preserve TXA bone order, but pin Scene_Root first and entityposition last to
    # match observed ANM ordering.
    remaining = list(anim.nodes.items())

    def pop_name(name: str):
        for idx, (n, node) in enumerate(remaining):
            if n == name:
                return remaining.pop(idx)
        return None

    ordered_nodes = []
    root_entry = pop_name("Scene_Root")
    if root_entry:
        ordered_nodes.append(root_entry)

    entity_entry = pop_name("entityposition")
    ordered_nodes.extend(remaining)
    if entity_entry:
        ordered_nodes.append(entity_entry)

    # Per-bone: write head, then data
    for node_name, node in ordered_nodes:
        # Track which channels had keys in the TXA before adding defaults
        t_has_keys = bool(node.t)
        q_has_keys = bool(node.q)
        s_has_keys = bool(node.s)
        
        # Ensure channels exist with defaults, but do NOT collapse runs.
        # The TXA already has the desired keyframe layout from the original ANM;
        # collapsing would lose information that was intentionally preserved.
        if not node.t:
            node.t = {0: (0.0, 0.0, 0.0)}
        if not node.q:
            node.q = {0: (0.0, 0.0, 0.0, 1.0)}
        if not node.s:
            if node_name == "Scene_Root":
                node.s = {0: (1.0, 1.0, 1.0)}
            else:
                node.s = {0: (100.0, 100.0, 100.0)}
        
        # If a channel has a single key at frame 0 AND had keys in the TXA, 
        # only duplicate SCALE keys at the last frame. This matches DayZ ANM behavior where 
        # constant scale channels span the full animation. Position and rotation single keys 
        # are not duplicated.
        last_frame = anim.num_frames - 1 if anim.num_frames > 0 else 0
        if last_frame > 0:
            # Only duplicate scale keys for non-Scene_Root bones
            if s_has_keys and len(node.s) == 1 and 0 in node.s and node_name != "Scene_Root":
                node.s[last_frame] = node.s[0]
        
        # Quantize channels
        pos_frames = sorted(node.t.items())
        pos_vals = [v for _, vec in pos_frames for v in vec]
        pos_bias, pos_mult, pos_enc = _quantize_channel(pos_vals)

        rot_frames = sorted(node.q.items())
        rot_vals = [v for _, quat in rot_frames for v in quat]
        rot_bias, rot_mult, rot_enc = _quantize_channel(rot_vals)

        scale_frames = sorted(node.s.items())
        scale_vals = [v for _, vec in scale_frames for v in vec]
        scale_bias, scale_mult, scale_enc = _quantize_channel(scale_vals)

        # HEAD entry (AnimSet6): no name here, comes at end
        # Note: mult values are divided by SCALE_FACTOR because the ANM reader will multiply by it
        head_bytes.extend(struct.pack('<f', pos_bias))
        head_bytes.extend(struct.pack('<f', pos_mult / SCALE_FACTOR if pos_mult else 0.0))
        head_bytes.extend(struct.pack('<f', rot_bias))
        head_bytes.extend(struct.pack('<f', rot_mult / SCALE_FACTOR if rot_mult else 0.0))
        head_bytes.extend(struct.pack('<f', scale_bias))
        head_bytes.extend(struct.pack('<f', scale_mult / SCALE_FACTOR if scale_mult else 0.0))
        head_bytes.extend(struct.pack('<h', anim.num_frames))
        head_bytes.extend(struct.pack('<h', len(pos_frames)))
        head_bytes.extend(struct.pack('<h', len(rot_frames)))
        head_bytes.extend(struct.pack('<h', len(scale_frames)))
        head_bytes.extend(struct.pack('<B', 0))  # flags
        name_b = node_name.encode('ascii', errors='ignore')
        head_bytes.extend(struct.pack('<B', len(name_b)))
        head_bytes.extend(name_b)

        # DATA: pos frames, pos values, scale frames, scale values, rot frames, rot values
        for frame, _ in pos_frames:
            data_bytes.extend(struct.pack('<H', frame))
        idx = 0
        for frame, _ in pos_frames:
            data_bytes.extend(struct.pack('<HHH', pos_enc[idx], pos_enc[idx + 2], pos_enc[idx + 1]))
            idx += 3

        for frame, _ in scale_frames:
            data_bytes.extend(struct.pack('<H', frame))
        idx = 0
        for frame, _ in scale_frames:
            data_bytes.extend(struct.pack('<HHH', scale_enc[idx], scale_enc[idx + 2], scale_enc[idx + 1]))
            idx += 3

        for frame, _ in rot_frames:
            data_bytes.extend(struct.pack('<H', frame))
        idx = 0
        for frame, _ in rot_frames:
            data_bytes.extend(struct.pack('<HHHH', rot_enc[idx], rot_enc[idx + 2], rot_enc[idx + 1], rot_enc[idx + 3]))
            idx += 4

    # Build chunks
    head_chunk = b'HEAD' + struct.pack('>i', len(head_bytes)) + head_bytes
    data_chunk = b'DATA' + struct.pack('>i', len(data_bytes)) + data_bytes

    evnt_chunk = b''
    if anim.events:
        payload = bytearray()
        payload.extend(struct.pack('<H', len(anim.events)))
        for frame, name, user_str, user_int in sorted(anim.events, key=lambda e: e[0]):
            nb = name.encode('utf-8')
            ub = user_str.encode('utf-8')
            payload.extend(struct.pack('<i', frame))
            payload.extend(struct.pack('<i', len(nb)))
            payload.extend(nb)
            payload.extend(struct.pack('<i', len(ub)))
            payload.extend(ub)
            payload.extend(struct.pack('<i', user_int))
        evnt_chunk = b'EVNT' + struct.pack('>i', len(payload)) + payload

    cprp_chunk = b''
    if anim.cust_props:
        payload = bytearray()
        payload.extend(struct.pack('<H', len(anim.cust_props)))
        for key, val in anim.cust_props:
            kb = key.encode('utf-8')
            vb = val.encode('utf-8')
            payload.extend(struct.pack('<i', len(kb)))
            payload.extend(kb)
            payload.extend(struct.pack('<i', len(vb)))
            payload.extend(vb)
        cprp_chunk = b'CPRP' + struct.pack('>i', len(payload)) + payload

    # FORM header + chunks
    content = bytearray()
    content.extend(b'FORM')
    content.extend(struct.pack('>i', 0))  # placeholder for FORM size
    content.extend(b'ANIMSET')
    content.extend(bytes([ord('6')]))
    
    # The anim_data_len value - represents size from here to end of DATA chunk
    # This will be calculated after we know the size of all chunks
    anim_data_len_offset = len(content)
    content.extend(struct.pack('>I', 0))  # placeholder
    
    content.extend(b'FPS\x00')
    content.extend(struct.pack('>I', 4))  # Unknown constant (seems to always be 4?)
    content.extend(struct.pack('<i', anim.fps))
    
    content.extend(head_chunk)
    content.extend(data_chunk)
    if evnt_chunk:
        content.extend(evnt_chunk)
    if cprp_chunk:
        content.extend(cprp_chunk)

    # Patch FORM size (total content size - 8 bytes for "FORM" marker and size field)
    form_size = len(content) - 8
    struct.pack_into('>i', content, 4, form_size)
    
    # Patch anim_data_len (size from after the anim_data_len field to end of DATA chunk)
    # This is: "FPS\x00" (4) + unknown (4) + FPS (4) + HEAD chunk + DATA chunk
    anim_data_len = 4 + 4 + 4 + len(head_chunk) + len(data_chunk)
    struct.pack_into('>I', content, anim_data_len_offset, anim_data_len)

    out_path.write_bytes(content)

# -------- CLI --------

def convert_txa_to_anm(inp: pathlib.Path, outp: pathlib.Path):
    anim = parse_txa(inp)
    if anim.num_frames <= 0:
        max_frame = 0
        for node in anim.nodes.values():
            for d in (node.t, node.q, node.s):
                if d:
                    max_frame = max(max_frame, max(d.keys()))
        for ev in anim.events:
            max_frame = max(max_frame, ev[0])
        anim.num_frames = max_frame + 1
    
    if anim.num_frames == 0:
        anim.num_frames = 1  # Ensure at least 1 frame
    
    outp.parent.mkdir(parents=True, exist_ok=True)
    _write_anm(anim, outp)
    print(f"Wrote {outp} ({anim.num_frames} frames, {len(anim.nodes)} bones)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python txa_to_anm.py <input.txa> [output.anm]")
        sys.exit(1)
    inp = pathlib.Path(sys.argv[1])
    if not inp.exists():
        print(f"Input not found: {inp}")
        sys.exit(1)
    if inp.suffix.lower() != '.txa':
        print("Please provide a .txa file")
        sys.exit(1)
    outp = pathlib.Path(sys.argv[2]) if len(sys.argv) >= 3 else inp.with_suffix('.anm')
    convert_txa_to_anm(inp, outp)


if __name__ == '__main__':
    main()
