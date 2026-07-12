#!/usr/bin/env python3
"""
TXA to ANM converter with optional original ANM metadata preservation.
If original ANM path provided, uses its HEAD (bias/mult) for quantization.
"""

import pathlib
import struct
import sys
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from anm_to_txa import FQuaternion, FVector
from txa_to_anm import parse_txa
from DayzAnimationToolsBinary.Types.Anm import Anm, SCALE_FACTOR

def convert_with_metadata(txa_path: pathlib.Path, orig_anm_path: Optional[pathlib.Path], out_path: pathlib.Path):
    """Convert TXA to ANM, optionally using original ANM's HEAD metadata."""
    anim = parse_txa(txa_path)
    
    # Load original ANM if provided to get HEAD metadata
    orig_anm = None
    if orig_anm_path and orig_anm_path.exists():
        orig_anm = Anm.CreateFromFile(str(orig_anm_path))
        print(f"Using original ANM metadata from {orig_anm_path.name}")
    
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
        anim.num_frames = 1
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_anm_with_metadata(anim, orig_anm, out_path)
    print(f"Wrote {out_path} ({anim.num_frames} frames, {len(anim.nodes)} bones)")


def _write_anm_with_metadata(anim, orig_anm: Optional[Anm], out_path: pathlib.Path):
    """Write ANM using original metadata if available."""
    head_bytes = bytearray()
    data_bytes = bytearray()

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

    # Build bone list parallel to original ANM if provided
    orig_bones_by_name = {}
    if orig_anm:
        orig_bones_by_name = {b.name: b for b in orig_anm.bones}

    for node_name, node in ordered_nodes:
        orig_bone = orig_bones_by_name.get(node_name) if orig_anm else None
        
        # Use original HEAD metadata if available
        if orig_bone:
            pos_bias = orig_bone.posBias
            pos_mult = orig_bone.posMulti
            rot_bias = orig_bone.rotBias
            rot_mult = orig_bone.rotMulti
            scale_bias = orig_bone.scaleBias
            scale_mult = orig_bone.scaleMulti
            print(f"{node_name}: using original metadata")
        else:
            # Fallback: ensure defaults exist
            if not node.t:
                node.t = {0: (0.0, 0.0, 0.0)}
            if not node.q:
                node.q = {0: (0.0, 0.0, 0.0, 1.0)}
            if not node.s:
                if node_name == "Scene_Root":
                    node.s = {0: (1.0, 1.0, 1.0)}
                else:
                    node.s = {0: (100.0, 100.0, 100.0)}
            
            # Compute quantization (fallback)
            pos_frames = sorted(node.t.items())
            pos_vals = [v for _, vec in pos_frames for v in vec]
            pos_bias, pos_mult = _quantize_bias_mult(pos_vals)
            
            rot_frames = sorted(node.q.items())
            rot_vals = [v for _, quat in rot_frames for v in quat]
            rot_bias, rot_mult = _quantize_bias_mult(rot_vals)
            
            scale_frames = sorted(node.s.items())
            scale_vals = [v for _, vec in scale_frames for v in vec]
            scale_bias, scale_mult = _quantize_bias_mult(scale_vals)

        # Always use TXA's frame data
        pos_frames = sorted(node.t.items())
        rot_frames = sorted(node.q.items())
        scale_frames = sorted(node.s.items())

        # Write HEAD entry with original metadata
        head_bytes.extend(struct.pack('<f', pos_bias))
        head_bytes.extend(struct.pack('<f', pos_mult))
        head_bytes.extend(struct.pack('<f', rot_bias))
        head_bytes.extend(struct.pack('<f', rot_mult))
        head_bytes.extend(struct.pack('<f', scale_bias))
        head_bytes.extend(struct.pack('<f', scale_mult))
        head_bytes.extend(struct.pack('<h', anim.num_frames))
        head_bytes.extend(struct.pack('<h', len(pos_frames)))
        head_bytes.extend(struct.pack('<h', len(rot_frames)))
        head_bytes.extend(struct.pack('<h', len(scale_frames)))
        head_bytes.extend(struct.pack('<B', 0))  # flags
        name_b = node_name.encode('ascii', errors='ignore')
        head_bytes.extend(struct.pack('<B', len(name_b)))
        head_bytes.extend(name_b)

        # Encode DATA using original mult/bias
        _encode_data(data_bytes, pos_frames, node.t, pos_bias, pos_mult, 3)
        _encode_data(data_bytes, scale_frames, node.s, scale_bias, scale_mult, 3)
        _encode_data(data_bytes, rot_frames, node.q, rot_bias, rot_mult, 4)

    # Build FORM
    head_chunk = b'HEAD' + struct.pack('>i', len(head_bytes)) + head_bytes
    data_chunk = b'DATA' + struct.pack('>i', len(data_bytes)) + data_bytes

    evnt_chunk = b''
    if anim.events:
        payload = bytearray()
        payload.extend(struct.pack('<H', len(anim.events)))
        for frame, name, user_str, user_int in sorted(anim.events, key=lambda e: e[0]):
            nb = name.encode('utf-8') + b'\x00'
            ub = user_str.encode('utf-8') + b'\x00'
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

    content = bytearray()
    content.extend(b'FORM')
    content.extend(struct.pack('>i', 0))
    content.extend(b'ANIMSET')
    content.extend(bytes([ord('6')]))
    anim_data_len_offset = len(content)
    content.extend(struct.pack('>I', 0))
    content.extend(b'FPS\x00')
    content.extend(struct.pack('>I', 4))
    content.extend(struct.pack('<i', anim.fps))
    
    content.extend(head_chunk)
    content.extend(data_chunk)
    if evnt_chunk:
        content.extend(evnt_chunk)
    if cprp_chunk:
        content.extend(cprp_chunk)

    form_size = len(content) - 8
    struct.pack_into('>i', content, 4, form_size)
    anim_data_len = 4 + 4 + 4 + len(head_chunk) + len(data_chunk)
    struct.pack_into('>I', content, anim_data_len_offset, anim_data_len)

    out_path.write_bytes(content)


def _quantize_bias_mult(values: List[float]) -> Tuple[float, float]:
    """Compute bias and mult for quantization."""
    if not values:
        return 0.0, 0.0
    vmin = min(values)
    vmax = max(values)
    spread = vmax - vmin
    if spread <= 0:
        return vmin, 0.0
    return vmin, spread / 65535.0


def _encode_data(data_bytes, frames: List[Tuple[int, tuple]], values_dict: Dict, bias: float, mult: float, components: int):
    """Encode keyframe data using original bias/mult."""
    # Write frame numbers
    for frame, _ in frames:
        data_bytes.extend(struct.pack('<H', frame))
    
    # Encode and write values
    for frame, _ in frames:
        val = values_dict[frame]
        for i in range(components):
            if mult > 0:
                encoded = int(round((val[i] - bias) / mult))
            else:
                encoded = 0
            encoded = max(0, min(65535, encoded))
            data_bytes.extend(struct.pack('<H', encoded))


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_with_metadata.py <input.txa> [orig.anm] [output.anm]")
        sys.exit(1)
    
    inp = pathlib.Path(sys.argv[1]).resolve()
    orig = None
    outp = inp.with_suffix('.anm')
    
    if len(sys.argv) >= 3:
        orig_arg = sys.argv[2]
        if orig_arg.endswith('.anm'):
            orig = pathlib.Path(orig_arg).resolve()
            if len(sys.argv) >= 4:
                outp = pathlib.Path(sys.argv[3]).resolve()
        else:
            outp = pathlib.Path(orig_arg).resolve()
    
    convert_with_metadata(inp, orig, outp)


if __name__ == '__main__':
    main()
