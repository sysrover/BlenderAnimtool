# Converter Implementation Spec

This page condenses the Ghidra-backed findings into the implementation shape
for standalone converters.

## Confidence

- confirmed: all function names, offsets, constants, and flow summaries below
  are from Ghidra decompile/raw output listed in `ghidra-evidence-log.md`.
- confirmed: the dataExporter DLL independently contains the same
  `TXA::Animation -> writer context -> ANIM/SET6` save chain as Workbench, so
  the core TXA-to-ANM algorithm is cross-checked from two loaded Ghidra
  programs.
- confirmed: TXA tags are parsed/stored; related parser callbacks interpret
  `Scale`, `Coords XZY`, and `SourceName *.p3d`.
- confirmed: a deeper HTTP pass found the top-level TXA `tag` store at
  `FUN_1410578e0 -> FUN_141058640(param_2 + 8, ...)`; the ANM writer-context
  builder still does not read that field.
- unknown: no Ghidra evidence currently proves TXA tags are copied into or used
  by the final `ANIM`/`SET6` binary writer.

## FBX Input Target

confirmed:

- Workbench uses embedded FBX SDK/Plugins `2016.1.1`, build `20150824`.
- FBX major versions above `7` are rejected by importer code.
- practical target should be FBX major 6 or 7, compatible with Autodesk 2016
  FBX plug-ins.
- animation resource defaults are `AnimationName = Take 001` and `FPS = 30`.
- the in-process `FBXAnimResourceClassWB` path reads only those two resource
  properties before calling the take-to-TXA builder.

Implementation rule:

1. load FBX with an SDK/library that can read FBX 6/7.
2. select animation stack/take by requested name; fall back to first take only
   if matching Workbench behavior is desired.
3. use requested FPS, default `30`.
4. use Workbench's time-mode fallback behavior when deriving frame counts:
   resolve zero time mode through the global fallback helper, then use mode `6`
   if no mode is resolved.
5. compute `durationTicks = endTicks - startTicks`, then
   `numFrames = durationTicks / ticksPerFrame + 1`.
6. bake IK/additive/partial/full-body semantics into ordinary bone/node
   transforms before export; no Ghidra-backed FBX conversion branch currently
   consumes those semantic modes.

Blender export guidance from the Workbench path:

- Export FBX compatible with SDK 2016 / FBX major 6 or 7.
- Put the desired animation in a take/anim stack named by `AnimationName`, or use
  `Take 001`.
- Export at the FPS you intend Workbench to sample, defaulting to `30`.
- Animate skeleton/bone/null transform nodes. Do not rely on mesh transform nodes
  as animation tracks: Workbench skips nodes whose FBX node-attribute type is
  `FbxMesh`.
- Do not parent the animated skeleton/null hierarchy under an FBX mesh node if
  exact Workbench traversal is required. In `FUN_140e75770`, child recursion is
  inside the same `attributeType != FbxMesh` branch as track creation.
- Use an `EntityPosition` node only when the animation needs Workbench's special
  root-motion/entity-motion separation.
- Prefer meter-scale scene export. Workbench imports, converts the scene to its
  `Meters` system-unit entry, then applies its post-evaluation scale extraction.

Evidence:

- `fbx-import.md`, `Supported/Exposed FBX Versions`.
- `fbx-import.md`, `FBX Time Mode And Tick Conversion`.
- `fbx-import.md`, `FBX To TXA::Animation Algorithm`.
- `fbx-import.md`, `FBX Resource Properties And Conversion Modes`.

## Internal Animation Model

Represent Workbench `TXA::Animation` as:

```text
Animation:
  version: float
  tags: string[]
  name: string
  tracks: Track[]
  events: Event[]
  customProperties: (name,value)[]
  fps: int
  numFrames: int

Track:
  name: string
  siblingIndex: int
  childIndex: int
  parentIndex: int
  keys: Key[]
  diffFlag: bool        // TXA track +0x28 / writer flag 0x1
  translateFlag: bool   // TXA track +0x29 / writer flag 0x2
  rotateScaleFlag: bool // TXA track +0x2a / writer flag 0x4
  extraFlag: bool       // TXA track +0x2b / writer flag 0x8

Key:
  qx,qy,qz,qw: float
  tx,ty,tz: float
  sx,sy,sz: float
```

confirmed key layout:

- key stride in TXA track: `0x28`.
- `+0x00..+0x0c`: quaternion `q`.
- `+0x10..+0x18`: translation `t`.
- `+0x1c..+0x24`: scale `s`.

confirmed writer flag mapping:

- `diffFlag` maps directly to writer bit `0x1`.
- `translateFlag`, `rotateScaleFlag`, and `extraFlag` are inverted when building
  writer bits `0x2`, `0x4`, and `0x8`: writer bit set means the corresponding
  TXA byte was zero.

## FBX To Internal Model

confirmed Workbench algorithm:

1. import FBX scene.
2. convert/update the scene system unit to Workbench's meters entry
   `(100.0, 1.0)` through the same scene conversion pass Workbench calls after
   import.
3. store the first component of the converted global unit at context scale
   `+0x58`; for meters this is `100.0`.
4. select animation take.
5. activate the take, then compute time span and duration.
6. `numFrames = durationTicks / ticksPerFrame + 1`; store FPS and numFrames.
7. find special node `EntityPosition`.
8. recursively walk scene nodes.
9. sanitize node names by replacing spaces and dashes with underscores.
10. root node name is `Scene_Root`.
11. skip nodes whose node-attribute type is `FbxMesh`.
12. create each converted track with translation, rotation, and scale channels
    enabled.
13. for each frame:

```text
t = frameIndex / (numFrames - 1) * duration
sample FBX transform at t
write q,t,s into the track key record
```

confirmed: `EntityPosition` is sampled separately and passed into recursive
conversion so other nodes can be expressed relative to it when present.

confirmed: skip FBX node attribute type `4`, which the Ghidra vtable pass maps
to `FbxMesh`. Do not skip `FbxNull` for this reason; its same vtable slot
returns `1`.

confirmed: FBX-to-TXA writes the text file through Workbench TXA writer
`FUN_141056750`. The FBX conversion path builds tracks/keys; it does not call the
event or custom-property store helpers found in the TXA parser path.

confirmed Workbench TXA text output rules for FBX-created tracks:

- tracks are emitted as hierarchical `node` / `nodeDiff` blocks.
- FBX-created tracks enable all three channel tokens, so the `keys` block is
  written with `t q s`.
- adjacent equal keys are compressed into `frame <start> <end>` ranges.
- equality thresholds for range compression are translation `10^-7`,
  quaternion `10^-6`, and scale `10^-5`.
- default component blocks are omitted inside a `frame` block:
  `t = 0,0,0`, `q = 0,0,0,1`, `s = 1,1,1`.
- emitted floats use `"%.*f"` with precision `7`, values smaller than
  `10^-7` are printed as `0`, and trailing zeroes are trimmed.

Implementation consequence: exact Workbench-style FBX->TXA text requires the
same range compression, default elision, and float formatting. For FBX->ANM
direct conversion, it is enough to build the same internal model and skip text
serialization.

confirmed transform handling:

- Workbench samples time as `frameIndex / (numFrames - 1) * duration`.
- scene root writes identity/default keys.
- scene-root children use global transform keys unless `EntityPosition` exists.
- scene-root children with `EntityPosition` are composed against the per-frame
  `EntityPosition` matrix array before key extraction.
- non-root children use parent-relative keys:
  `inverse(reorderedParentGlobal) * reorderedChildGlobal`.
- translation extraction multiplies the reordered matrix translation by
  `contextScale * 0.00999999977648258`; after Workbench's meters conversion this
  is approximately `100.0 * 0.01 = 1.0`.
- scale keys are read from the evaluated FBX transform before the XZY reorder
  and multiplied by `contextScale`; root and `EntityPosition` scale use
  identity defaults.
- `FUN_140e7e780` reorders FBX transform components from FBX order into
  Workbench order before matrix-to-quaternion extraction. The observed row/vector
  component order is `x, z, y`.
- `FUN_1402badd0` stores quaternion fields as `x, y, z, w`.
- `EntityPosition` is sampled into a separate `0x80` stride matrix array and can
  be used to make root-level nodes relative to entity motion.
- Use affine matrix operations equivalent to Workbench helpers:
  `FUN_14108dce0` inverts a 4x4 transform, `FUN_14108d8b0` composes/multiplies
  transforms, and `FUN_140e7e9c0` extracts a scaled 3x4 float matrix before
  quaternion conversion.

## TXA Text To Internal Model

confirmed grammar:

```text
animation <name> {
  version <float>
  fps <int>
  numFrames <int>
  tag <string>...

  node <name> { ... }
  nodeDiff <name> { ... }

  events {
    event <frame> <name> [value] [userValue]
  }

  custProps {
    custProp <name> <value>
  }
}

node <name> {
  node <childName> { ... }
  nodeDiff <childName> { ... }
  keys [t] [q|s] {
    frame <startFrame> [endFrame] {
      q <x> <y> <z> <w>
      t <x> <y> <z>
      s <x> <y> <z>
    }
  }
}
```

confirmed behavior:

- `nodeDiff` sets track diff flag.
- `keys` without args enables both translation and rotation/scale flags.
- `keys t` enables translation flag.
- `keys q` or `keys s` enables rotation/scale flag.
- `frame start end` copies the parsed key over the inclusive range.
- missing key values start from identity/defaults:
  quaternion `0,0,0,1`, translation `0,0,0`, scale `1,1,1`.
- events are stored with stride `0x20`: frame, name, value, user value.
- custom properties are stored with stride `0x10`: name, value.
- animation tags are stored as string lists; related callbacks give special
  meaning to `Scale`, `Coords XZY`, and `SourceName *.p3d`, but these tags are
  not copied by `FUN_141067c00` into the binary writer context.
- direct Ghidra caller enumeration found only three `FUN_141058640` tag-store
  callers and none is the final ANM writer-context builder.
- integer parsing uses `strtol(..., 10)` and returns the caller default on null,
  empty, parse failure, or `errno`; observed TXA call sites pass default `0`.
- float parsing uses `strtod`, casts to 32-bit float on success, and returns the
  caller default on null, empty, parse failure, or `errno`.
- the observed TXA callbacks enforce parameter count, but no semantic numeric
  validation is visible for `fps`, `numFrames`, frame ranges, or vector values.

## FBX Sampling Rule

confirmed: Workbench does not implement FBX pivot/inherit/animation-layer math
manually inside the `FBXAnimResourceClassWB` conversion loop. The loop calls
`FUN_1410c3840`, which obtains an embedded evaluator/cache object and dispatches
through `FUN_1411235b0`. A compatible converter should therefore use the FBX SDK
2016-compatible scene evaluator/global-transform path, then apply Workbench's
post-evaluation axis reorder, scale multiplier, `EntityPosition`, and
matrix-to-quaternion steps.

Implementation consequence: do not hand-roll FBX local transform reconstruction
unless it exactly matches the FBX SDK evaluator behavior. The Workbench-specific
algorithm starts after the evaluated transform is returned.

## ANM Writer

confirmed top-level writer:

```text
FORM type ANIM
  SET6
    FPS
    HEAD
    DATA
    EVNT?   // if event count > 0
    CPRP?   // if custom property count > 0
```

confirmed IFF chunks:

- Workbench golden output confirms the physical file starts with
  `FORM <be32 size> ANIM`, then nested `SET6`.
- each chunk writes 4-byte tag, reserves 4-byte size, writes payload, then
  patches size on close.
- chunk sizes are big-endian in the Workbench golden output.
- observed `FPS` and `HEAD` payload integer fields are little-endian.
- chunk-size patch helpers write byte-swapped 16-bit or 32-bit values.
- raw payload helpers write raw 2-byte/4-byte values; selected ANM record fields
  are only byte-swapped when the writer's endian flag requires it.
- strings written through the generic helper are encoded as raw 4-byte length
  followed by bytes, with length `-1` for null.
- the `FPS` chunk payload is exactly four raw bytes from writer context offset
  `+0`, which is copied from `TXA::Animation + 0x80`.
- `EVNT` and `CPRP` chunk counts are written as raw 16-bit values.
- top-level tag constants are documented in `anm-writer-format.md`.
- the packed constants are instruction-address confirmed in `FUN_141068360`,
  not inferred from strings.

confirmed `HEAD` record. Workbench writes a record when translation count is
nonzero, rotation count is nonzero, or forced output is enabled. Retained scale
count alone does not pass the observed emission condition:

```text
float transBase
float transRange
float rotBase
float rotRange
float scaleBase
float scaleRange
uint16 frameCount
uint16 transKeyCount
uint16 rotKeyCount
uint16 scaleKeyCount
uint8 flags
uint8 nameLength
byte[nameLength] name
```

The emitted record length is `0x22 + nameLength`.

confirmed event/custom string rule:

- write `uint32(lengthIncludingTerminator)`, then write exactly that many bytes.
- if the source string pointer is null, write length `1` and one empty-string
  terminator byte.

confirmed `DATA` stream order per node:

1. translation retained key indices if flag `0x10` is not set.
2. translation quantized float stream, 3 components per retained key.
3. scale retained key indices if flag `0x40` is not set.
4. scale quantized float stream, 3 components per retained key.
5. rotation retained key indices if flag `0x20` is not set.
6. rotation quantized float stream, 4 components per retained key.

confirmed quantization:

```text
q = clamp((value - base) * scale, 0, 65535)
write uint16(q)
```

confirmed by both Workbench and dataExporter:

- Workbench uses `FUN_141069860` for the quantized float stream and
  `FUN_141069a50` for retained key indices.
- dataExporter uses `FUN_1807f8510` for the same quantized float stream and
  `FUN_1807f8700` for the same retained index stream.
- `FUN_1807f8700` reads each selected writer key's 16-bit frame/index value
  from `keyIndex * 0x2c + 0x28`.
- `FUN_1807f8510` writes `componentCount * retainedKeyCount` 16-bit samples
  and optionally byte-swaps them when the writer flag asks for swapped output.

confirmed reduction thresholds:

- translation: `0.0005`
- scale: `0.0005`
- rotation: `0.000001`
- quaternion slerp near-equal cutoff: `0.999`
- quantization max: `65535.0`
- range guard: `0.000001`

confirmed call-site nuance:

- TXA helper path `FUN_140fc9d50` writes with `FUN_141068360(..., 0, 0)` and
  does not zero the reduction globals at the call site.
- direct FBX helper path `FUN_140e75c10` zeros the three reduction globals before
  calling `FUN_141068360(..., 0, 0)`, so direct FBX export uses zero tolerance
  reduction.
- dataExporter `FUN_1800b1820` also zeroes its three reduction threshold globals
  before `FUN_1807f7010(..., 0, 1)`, so the DLL export path uses zero-tolerance
  reduction too.

confirmed golden-pair validation:

- `tools/TxaAnmPrototype` now converts
  `anm/txa_anm/p_2hd_cro_interact_out.txa` into a byte-identical copy of the
  Workbench-generated `p_2hd_cro_interact_out.anm`.
- the last mismatch was the slerp cutoff. Ghidra decompile references
  `DAT_141a6d970` in `FUN_1402bbe70`; HTTP memory read from
  `workbenchApp.exe:0x141a6d970` gives bytes `77 be 7f 3f`, float `0.999`.

confirmed writer limit behavior:

- `FUN_141067c00` reports `Skeleton has too much nodes` if writer node creation
  returns `0xffffffff`.
- source frame/key counts and retained key counts are stored into 16-bit fields
  in the `HEAD` record; no separate decompiled range error has been found for
  counts above `65535`.
- `EVNT` and `CPRP` counts are written as raw 16-bit values.
- node name length is stored as one byte in the `HEAD` record, after scanning
  the C string length.
- focused HTTP string search found no ANM-specific `65535` error string; the
  only relevant count-style string found by `too much` search is
  `Skeleton has too much nodes`.

## Implementation Order

1. Implement TXA parser and internal model.
2. Implement ANM writer using fixed synthetic animations and compare against
   Workbench output generated from the same TXA.
3. Implement FBX sampling into the same internal model.
4. Add Workbench-compatible name sanitizing, `EntityPosition`, and take/FPS
   behavior.

This order avoids mixing FBX transform issues with the binary writer protocol.
