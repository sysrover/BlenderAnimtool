# DayZDiag AnimNodeWeaponIK Deep Pass

## Source

- Program: `DayZDiag_x64.exe`
- Main class string: `AnimNodeWeaponIK` at `0x140decd90`
- Vtable candidate: `0x140decb30`
- Raw Ghidra evidence:
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-slot2-callgraph-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-slot2-callees-decompile-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-constructor-parse-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-offset-use-script.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-string-anchors-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-cmd-type3-scan.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-cmd-dispatch-byte3-scan.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-cmd-consumer-candidates-decompile.txt`

## Vtable Shape

`confirmed`: `AnimNodeWeaponIK` vtable at `0x140decb30` has seven executable
entries before non-code/data entries:

- slot `+0x00`: `0x1401083a0` / thunk to `FUN_1401092a0`, returns
  `"AnimNodeWeaponIK"`.
- slot `+0x08`: `FUN_140108bb0`, editor accessor allocation.
- slot `+0x10`: `FUN_140108750`, runtime update/evaluator candidate.
- slot `+0x18`: `FUN_140108c10`, destructor/free wrapper.
- slot `+0x20`: `FUN_1401083b0`, config/load path.
- slot `+0x28`: `FUN_140108540`, load/remap path.
- slot `+0x30`: `FUN_140108620`, serialize/save path.

Evidence: Bohr agent raw summary and
`ghidra-raw-dayzdiag-weaponik-vtable-batch-decompile-fresh.txt`.

## Remap Fields

`confirmed`: `FUN_140108d00` allocates `0x230` bytes, installs the
`AnimNodeWeaponIK` vtable, and initializes remap ids/flags:

- `+0x1b8`, `+0x1bc`, `+0x1c0`: initial `0xff`.
- `+0x1f4`, `+0x1f8`, `+0x1fc`, `+0x200`, `+0x204`, `+0x208`,
  `+0x20c`, `+0x210`, `+0x214`: initial `0xff`.
- `+0x218`: byte flag, initial `0`.

`confirmed`: `FUN_1401093e0` parses the remap text and writes:

- `hand` -> `+0x1b8`
- `weapon` -> `+0x1bc`
- `weaponrotator` -> `+0x1c0`
- `weaponaxis` -> `+0x1c4`
- `chain` -> `+0x1c8`, count `+0x1f0`
- `secchain` -> `+0x1dc`, count `+0x1f1`
- `chainaxis` -> `+0x1f2`
- `secchainaxis` -> `+0x1f3`
- `ikpose_chainoffset` -> `+0x1f4`
- `ikpose_secchainoffset` -> `+0x1f8`
- `ikpose_weaponoffset` -> `+0x1fc`
- `ikpose_chainmiddledir` -> `+0x200`
- `ikpose_chainmiddlediro` -> `+0x204` and `+0x208`, exactly two names
- `ikpose_secchainmiddledir` -> `+0x20c`
- `ikpose_secchainmiddlediro` -> `+0x210` and `+0x214`, exactly two names
- `outputweaponoffsettobuffer` -> byte `+0x218 = 1`

`confirmed`: success gate in `FUN_1401093e0` requires `hand`, `weapon`,
`ikpose_weaponoffset`, and primary `chain` count greater than three.

## Runtime Update Method

`confirmed`: `FUN_140108750` is the runtime update/evaluator candidate. It:

- calls generic node start helper `FUN_1400e54c0`;
- reads three boolean/weight-like node inputs through `FUN_1400e5980` from
  object offsets `+0x50`, `+0x70`, `+0x90`;
- calls the child node through the virtual pointer stored at `param_1 + 0x40`;
- allocates a `0x20` byte output command via `FUN_1400da470`;
- writes command type/opcode byte `0x0c` at command offset `+0x3`;
- writes a config/bone id byte at command offset `+0x1c`;
- evaluates two direction/angle inputs at `+0xb8` and `+0xd8` through
  `FUN_1400e59a0` and `FUN_140dc01e0`;
- finishes with generic node end helper `FUN_1400e54b0`.

`confirmed`: direct decompile of `FUN_140108750` does not read
`+0x1f4..+0x218`. The `ikpose_*` ids are therefore not consumed inside this
method directly.

`likely`: `FUN_140108750` emits a deferred animation command; the actual arm IK
solve happens later when command opcode `0x0c` is interpreted by the animation
runtime.

## Command Consumer Status

`confirmed`: `FUN_140108750` emits `byte ptr [RAX + 0x3] = 0x0c` after
allocating `0x20` bytes. This is strong evidence that WeaponIK is represented
as a compact runtime command, not as immediate bone-matrix writes in the node
method.

`confirmed`: `FUN_1400dec30` is the command dispatcher/consumer for this stream.
It iterates records returned by `FUN_1400da540`, sets
`puVar16 = local_468 + 8 + local_460`, then switches on
`*(byte *)(puVar16 + 0x3)`. Its `case 0xc` is the WeaponIK command emitted by
`FUN_140108750`.

Evidence:

- `FUN_140108750` writes opcode `0x0c` at command offset `+0x3`.
- `FUN_140108750` stores config id at command offset `+0x1c`.
- `FUN_1400dec30` `case 0xc` uses `(char)puVar16[7]`, which is the byte at
  command offset `+0x1c`, to resolve a config/object through
  `(**(param_5 + 0x70)->vtable[0x20])`.
- The same branch reads command floats from `puVar16[1]..puVar16[6]`, matching
  command offsets `+0x4..+0x18`.

Raw excerpts:

- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-consumer-1400dec30-http.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-consumer-1400dec30-case0c-excerpt.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-consumer-1400dec30-case0c-excerpt2.txt`

## Solver Field Mapping

`confirmed`: `FUN_1400dec30 case 0xc` receives a config pointer `lVar8`. The
runtime uses `lVar8` as a shifted base for the `AnimNodeWeaponIK` remap fields.
The shift matches `object_offset - 0x100`.

| Runtime read | Original object offset | Remap meaning |
|---|---:|---|
| `lVar8 + 0xb8` | `+0x1b8` | `hand` |
| `lVar8 + 0xbc` | `+0x1bc` | `weapon` |
| `lVar8 + 0xc0` | `+0x1c0` | `weaponrotator` |
| `lVar8 + 0xc4` | `+0x1c4` | `weaponaxis` |
| `lVar8 + 0xc8` | `+0x1c8` | `chain` bone-id list |
| `lVar8 + 0xdc` | `+0x1dc` | `secchain` bone-id list |
| `lVar8 + 0xf0` | `+0x1f0` | `chain` count |
| `lVar8 + 0xf1` | `+0x1f1` | `secchain` count |
| `lVar8 + 0xf2` | `+0x1f2` | `chainaxis` |
| `lVar8 + 0xf3` | `+0x1f3` | `secchainaxis` |
| `lVar8 + 0xf4` | `+0x1f4` | `ikpose_chainoffset` |
| `lVar8 + 0xf8` | `+0x1f8` | `ikpose_secchainoffset` |
| `lVar8 + 0xfc` | `+0x1fc` | `ikpose_weaponoffset` |
| `lVar8 + 0x100` | `+0x200` | `ikpose_chainmiddledir` |
| `lVar8 + 0x104`, `+0x108` | `+0x204`, `+0x208` | `ikpose_chainmiddlediro` pair |
| `lVar8 + 0x10c` | `+0x20c` | `ikpose_secchainmiddledir` |
| `lVar8 + 0x110`, `+0x114` | `+0x210`, `+0x214` | `ikpose_secchainmiddlediro` pair |
| `lVar8 + 0x118` | `+0x218` | `outputweaponoffsettobuffer` |

## Solver Flow

`confirmed`: `case 0xc` does these high-level steps:

1. Takes the current pose object from the node stack:
   `plVar5 = *(param_1 + 0x78 + (stackIndex - 1) * 8)`.
2. Resolves WeaponIK config by command byte at offset `+0x1c`.
3. Validates the config/pose pair through `FUN_1400e17c0`.
4. Reads primary chain count from `lVar8 + 0xf0` and secondary count from
   `lVar8 + 0xf1`.
5. Reads primary chain transforms with
   `FUN_14005eba0(..., lVar8 + 0xc8, *(byte *)(lVar8 + 0xf0), local_398)`.
6. If secondary is active, reads secondary chain transforms with
   `FUN_14005eba0(..., lVar8 + 0xdc, *(byte *)(lVar8 + 0xf1), local_198)`.
7. Builds weapon/hand-space transforms from offsets around `lVar8 + 0x10..0x6f`.
8. For the primary/right chain, computes target vectors and calls
   `FUN_1400e1be0(..., *(byte *)(lVar8 + 0xf2), ..., chainWeight, ...)`.
9. Writes primary chain result back with
   `FUN_14005f5a0(..., local_398, chainCount + 1)`.
10. If secondary is active, computes left/secondary target vectors and calls
    `FUN_1400e1be0(..., *(byte *)(lVar8 + 0xf3), ..., secWeight, ...)`.
11. Writes secondary chain result back with
    `FUN_14005f5a0(..., local_198, secCount + 1)`.
12. If `outputweaponoffsettobuffer` is true (`lVar8 + 0x118`) and no live
    weapon transform was read, writes/updates a transform record for the
    `weapon` bone id (`lVar8 + 0xbc`) into the pose buffer.

`likely`: `FUN_1400e1be0` is the generic chain IK solver used for both primary
and secondary chains. It receives the axis byte (`chainaxis` or `secchainaxis`),
the current root transform, optional pole/direction points, and a blend weight.

`likely`: `FUN_14005eba0` reads a list of bone ids from the current pose into a
compact transform array; `FUN_14005f5a0` writes the solved transform array back.

`likely`: `FUN_14013fa00` applies a quaternion/rotation transform to a vector;
it is used repeatedly to convert helper offsets into the current hand/weapon
space.

`unknown`: exact variable names and exact world/local multiplication convention
inside `FUN_1400e1be0`. This is now the next function to decompile deeply.

## Blender Implication

`confirmed`: the `ikpose_*` names in AGR are resolved to integer ids by
DayZDiag. They are not hardcoded DayZDiag strings except for the remap key names
themselves.

`likely`: Blender should model these as authoring helper tracks/bones and
export them into the IK pose animation namespace. Do not assume they all exist
as vanilla XOB skeleton bones.

`likely`: Blender constraints should use:

- `ikpose_*offset` tracks as target transforms;
- `*middlediro` pairs as origin/direction references for pole vectors;
- `chainaxis`, `secchainaxis`, and `weaponaxis` as local chain-axis
  orientation controls, not as world-space offsets.

`unknown`: exact runtime multiplication order and the final correction written
when `outputweaponoffsettobuffer = true`. This depends on finding the opcode
`0x0c` command consumer.

`confirmed`: the opcode `0x0c` consumer is now identified as
`FUN_1400dec30 case 0xc`. The remaining unknown moved from "find consumer" to
"fully name/decompile the generic solver helpers", especially `FUN_1400e1be0`,
`FUN_14005eba0`, `FUN_14005f5a0`, `FUN_14005f980`, and `FUN_14005fc20`.

## Solver Helpers

`confirmed`: `FUN_1400e1be0` is the core IK chain solver used by
`FUN_1400dec30 case 0xc`. Evidence:

- `FUN_1400e1be0` is called only from `FUN_1400ddb80` and
  `FUN_1400dec30`.
- Its callee list includes `FUN_1400e33b0`, `FUN_1400e3240`,
  `FUN_14013fa00`, vector normalization helpers, `acosf`, and `sinf`.
- Its body computes segment distances, target direction vectors, quaternion
  rotations, and slerp-style blends, then mutates the transform array passed in
  `param_1`.

Raw evidence:

- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-solver-helpers-http.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e1be0-decompile.txt`

`confirmed`: `FUN_14005f980` reads one bone transform from the current pose by
bone/remap id. It searches the pose transform table by a combined remap/index
key, writes quaternion to `out[0..3]`, translation to `out[4..6]`, and stores
record metadata bytes at offsets `+0x1c..+0x1e`.

`confirmed`: `FUN_14005fc20` is the parent-aware variant of single-bone read.
It first reads the requested record like `FUN_14005f980`, then walks parent
indices through the skeleton parent table returned by the pose object and
accumulates parent transforms with quaternion-vector rotation
`FUN_14013fa00`.

`confirmed`: `FUN_14005eba0` reads a list/chain of bone ids into a compact
array of `0x20` byte transform records. It is the chain-array equivalent of the
single-bone readers above.

`confirmed`: `FUN_14005f5a0` writes solved transforms back to the pose table.
It iterates adjacent `0x20` byte transform records, composes each child record
against the previous record, then writes quaternion and translation into the
pose table slot addressed by the record metadata byte at offset `+0x1d`.

`confirmed`: `FUN_14013fa00` rotates a 3D vector by a quaternion. The function
uses quaternion components `q[0..3]`, vector `v[0..2]`, divides by quaternion
length squared, and returns rotated vector.

`confirmed`: `FUN_1400e3240` builds the quaternion that rotates one normalized
direction vector to another. When the vectors are near opposite it falls back
to a fixed 180-degree-like quaternion.

## Axis Semantics

`confirmed`: `FUN_1400e33b0(out, transformQuat, axisId)` converts an axis id
into a local direction vector from the transform quaternion. The six valid axis
ids are:

| axis id | helper | direction |
|---:|---|---|
| `0` | `FUN_1400dac60` | local `+X` |
| `1` | `FUN_1400dad40` | local `+Y` |
| `2` | `FUN_1400dae70` | local `+Z` |
| `3` | `FUN_1400dacd0` | local `-X` |
| `4` | `FUN_1400dadd0` | local `-Y` |
| `5` | `FUN_1400daf10` | local `-Z` |

`confirmed`: if `axisId` is outside `0..5`, `FUN_1400e33b0` returns a default
constant vector via `FUN_140c2d5c0`.

Raw evidence:

- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-functions-http.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-1400dac60-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-1400dacd0-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-1400dad40-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-1400dadd0-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-1400dae70-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-axis-1400daf10-decompile.txt`

## Current Blender Skeleton Model

`confirmed`: DayZDiag does not require the IK helper names to exist as normal
XOB skeleton bones. `FUN_1400e17c0` reads `ikpose_chainoffset`,
`ikpose_secchainoffset`, `ikpose_weaponoffset`, `ikpose_chainmiddledir`,
`ikpose_chainmiddlediro`, `ikpose_secchainmiddledir`, and
`ikpose_secchainmiddlediro` through pose lookup helpers and caches their
transforms into the WeaponIK config object.

`likely`: for Blender authoring, these should be represented as helper bones
or exported helper tracks in the IK pose/action namespace, then converted to
the same remap ids expected by the AGR `AnimNodeWeaponIK` configuration.

`confirmed`: `chain`, `secchain`, `hand`, `weapon`, `weaponrotator`, and the
`ikpose_*` ids are remap ids consumed by runtime. The runtime chain solver
reads the current skeleton pose, applies helper target transforms, and writes
only solved real chain transforms back into the pose buffer through
`FUN_14005f5a0`.

`likely`: Blender constraints should therefore preview the same model as:

- helper target bones drive weapon/hand offset transforms;
- `chainaxis` and `secchainaxis` select the local aim axis on the solved chain,
  not a separate bone;
- pole/middle-direction helpers come from `ikpose_*middledir` and
  `ikpose_*middlediro` pairs;
- solved output should affect the actual arm chains named in AGR `chain` and
  `secchain`.

## Next Ghidra Target

The next useful pass is to decompile and document the generic helpers called by
`FUN_1400dec30 case 0xc`:

1. `FUN_1400e1be0`: chain IK solve math and pole/axis semantics.
2. `FUN_14005eba0`: read current chain transforms by bone-id list.
3. `FUN_14005f5a0`: write solved chain transforms back into pose.
4. `FUN_14005f980` / `FUN_14005fc20`: read single-bone transforms used for
   `weapon` / `weaponrotator`.
5. `FUN_1400e33b0`: axis vector conversion from `weaponaxis`.
