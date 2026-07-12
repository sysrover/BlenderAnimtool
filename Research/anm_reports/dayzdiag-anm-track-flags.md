# DayZDiag ANM Track Flags

Date: 2026-05-17

Scope: DayZDiag runtime handling of per-bone ANM HEAD `flags` and the player IK
corpus under `P:\DZ\anims\anm\player\ik\`.

## Findings

`confirmed`: DayZDiag reader `FUN_1400d4520` stores the per-track `flags` byte
at runtime track offset `+0x64`.

Evidence:

- `anm/ghidra-raw/ghidra-raw-dayzdiag-anm-reader-1400d4520.txt`
- In the HEAD copy block, the decompiler writes:
  `*(undefined1 *)(track + 100) = local_7b18`.
- In the DATA read block, the decompiler reads the same byte as:
  `bVar36 = *(byte *)(pfVar31 + 0x19)`. Since `pfVar31` is a `float *`, this is
  byte offset `0x64`.

`confirmed`: the relevant bits are channel-specific frame-index flags:

| Bit | Channel | DayZDiag call |
|---:|---|---|
| `0x10` | position | `FUN_1400d5160(reader, track + 0x00, 3, ~(flags >> 4) & 1)` |
| `0x20` | rotation | `FUN_1400d5160(reader, track + 0x20, 4, ~(flags >> 5) & 1)` |
| `0x40` | scale, SET6 only | `FUN_1400d5160(reader, track + 0x40, 3, ~(flags >> 6) & 1)` |

`confirmed`: `FUN_1400d5160` uses the fourth argument to decide whether to read
the per-key frame index array:

- If the channel has more than one key and the argument is non-zero, it
  allocates `count * 2` bytes at channel offset `+0x10` and reads frame indices.
- If the argument is zero, it sets channel offsets `+0x10` and `+0x14` to zero
  and does not read a frame-index array.
- It always reads the packed key values after that.

`confirmed`: `FUN_1400d3e00` finalizes the channel frame range:

- If a frame-index pointer exists, start/end are taken from first/last frame
  indices.
- If no frame-index pointer exists, start is `0` and end is `count - 1`.

Interpretation:

- If bit `0x10`, `0x20`, or `0x40` is clear, that channel stores explicit
  `uint16` frame indices before packed values.
- If the bit is set, frame indices are implicit dense frames `0..count-1` and
  are omitted from DATA.

## IK Corpus Impact

`confirmed`: the scanned player IK corpus contains only `flags = 0` and
`flags = 1`.

`confirmed`: because DayZDiag only uses bits `0x10`, `0x20`, and `0x40` for
frame-index omission, corpus `flags = 1` does not affect position, rotation, or
scale key reading.

`confirmed`: the eight `two_handed/*.anm` files with `flags = 1` on
`RightForeArmDirection` / `LeftForeArmDirection` should be parsed the same way
as `flags = 0` for key timing. The low bit may be reserved or used elsewhere,
but no DayZDiag evidence found in this pass shows it affecting ANM DATA decode.

## Converter Decision

For our Blender/TXA/ANM tooling:

- Writing `flags = 0` is valid and safest for now because it always writes
  explicit frame indices.
- We do not need to reproduce `flags = 1` for the current IK corpus to preserve
  key timing.
- A future compact writer may set:
  - `0x10` when position keys are dense frames `0..count-1`,
  - `0x20` when rotation keys are dense frames `0..count-1`,
  - `0x40` when SET6 scale keys are dense frames `0..count-1`,
  and then omit those frame arrays from DATA.

## Open Questions

- `unknown`: exact meaning of bit `0x01`. It appears in the corpus, but this
  pass found no DATA-decode effect from it.
- `unknown`: whether any non-player or non-IK ANM files use bits `0x10`,
  `0x20`, or `0x40`; the current scan was limited to player IK corpus.
