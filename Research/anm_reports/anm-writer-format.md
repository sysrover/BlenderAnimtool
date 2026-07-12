# ANM Writer and Format Findings

## Reader-Confirmed Animation Binary Signatures

confirmed: `FUN_140b896c0` reads an 8-byte signature and compares it against
`RTM_0100` and `RTM_0101`.

confirmed: `DayZDiag_x64.exe` also has an `ANIM/SET6` IFF reader at
`FUN_1400d4520`. This is the runtime reader for the Workbench-style `FORM ANIM`
files. It checks packed `ANIM`, `SET4`, `SET5`, `SET6`, `FPS`, and `HEAD`
constants and reads `DATA` through `FUN_1400d5160`.

confirmed: DayZDiag's `FUN_1400d5160` reads retained index arrays and 16-bit
component streams from the file. It reconstructs inline/all-key component
values as `uint16Sample * perChannelScale + base`; it does not apply the
Workbench writer reduction tolerances or the `0.999` slerp cutoff while loading.

Evidence:

- `dayzdiag-anm-reader.md`.
- `ghidra-raw/ghidra-raw-dayzdiag-anm-reader.txt`.

For `RTM_0100`, the function reads one 4-byte field, writes it to
`param_1 + 0xc0`, zeroes `param_1 + 0xb8`, then raises
`Old format used in animation %s`.

For `RTM_0101`, the function reads three 4-byte integers into local variables
and stores them to offsets:

- first 4-byte integer -> `param_1 + 0xb8`
- second 4-byte integer -> `param_1 + 0xbc`
- third 4-byte integer -> `param_1 + 0xc0`

Then it reads additional fields through `FUN_140199550`, initializes a mapping
array sized from `param_3 + 0x28`, and loops over named animation/channel data.

Evidence:

- `ghidra-raw/ghidra-raw-target-functions.txt`: target `140b896c0`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 498-535.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 668-671 for the bad-format error path.

confirmed: `dataExporter_v141_x64_RetailDX11.dll` contains parallel RTM reader
evidence in `FUN_1806d3aa0`, including `RTM_0100`, `RTM_0101`, old-format, and
bad-format error paths.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 774-808.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 717-733 and 884.

## Reader Loop Shape

confirmed: `FUN_140b896c0` reads repeated 0x20-byte name/identifier blocks from
the input stream, converts them through `FUN_1402c4af0`, resolves them against
`param_3` via `FUN_140b8b7a0`, and maps valid entries into an index array.

Evidence:

- `ghidra-raw/ghidra-raw-target-functions.txt`: decompile for `FUN_140b896c0`.

## Serializer-Confirmed `.anm`-Adjacent Fields

confirmed: `FUN_140efc710` writes animation fields and validates `.anm` output
paths. Its scalar write sequence includes byte writes from offsets `0xc0`,
`0xc1`, `0xc6`, `0xc2`, `0xc3`, `0xc5`, `0xc4`, and a 4-byte write from
`0x84`.

likely: these offsets correspond to fields in the same internal animation
object that `FUN_140b896c0` populates while reading RTM animation data, but the
exact semantic names are not fully proven.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1412-1422.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1464-1470.

## Workbench Binary ANM Writer

confirmed: `FUN_141068360` is the Workbench final binary animation writer used
by the in-process FBX animation conversion and the TXA build/write path. It
creates an `enf::IFFOutput`, opens a top-level tag `0x4d494e41`, and then
writes nested chunks. Interpreting the constants as little-endian ASCII gives:

- `0x4d494e41` -> `ANIM`
- `0x36544553` -> `SET6`
- `0x00535046` -> `FPS`
- `0x44414548` -> `HEAD`
- `0x41544144` -> `DATA`
- `0x544e5645` -> `EVNT`
- `0x50525043` -> `CPRP`

confirmed by Workbench golden output: the physical file starts with an
IFF-style `FORM` container. That `FORM` has form type `ANIM`, then nested
`SET6`. The observed layout is:

```text
FORM <be32 size> ANIM
  SET6 <be32 size>
    FPS\0 <be32 size> <le32 fps>
    HEAD <be32 size> ...
    DATA <be32 size> ...
```

The Ghidra constants still identify the logical `ANIM` and `SET6` writer
levels, but a standalone implementation should emit the outer `FORM` wrapper.

confirmed writer order:

1. write/open `FORM` with form type `ANIM`
2. open `SET6`
3. write `FPS\0`
4. write `HEAD`
5. write `DATA`
6. optionally write `EVNT` if event count at writer context `+0x24` is nonzero
7. optionally write `CPRP` if custom-property count at writer context `+0x34`
   is nonzero
8. close chunks/finalize IFF output

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1697-1818:
  writer setup and `ANIM`/`SET6` opening.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2245-2256:
  `FPS` and `HEAD` chunk opening.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2314-2316:
  `DATA` chunk opening.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2521-2589:
  optional `EVNT` chunk.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2591-2648:
  optional `CPRP` chunk.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 1013-1047:
  `FUN_1402ba0a0` writes a 4-byte chunk tag, reserves 4 bytes for chunk size,
  and records the chunk start.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 1073-1118:
  `FUN_1402ba320` closes a chunk and patches the reserved size.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 667-719:
  `FUN_1402ba790` and `FUN_1402ba7d0` are the 16-bit and 32-bit byte-swapping
  size patch helpers called by `FUN_1402ba320`.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 761-842:
  `FUN_1402ba8a0` and `FUN_1402ba8d0` write raw 2-byte and 4-byte payload
  values through the stream write vtable.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 859-887:
  `FUN_1402ba900` writes strings as a raw 4-byte length followed by string
  bytes, or length `-1` for null.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 936-965:
  `FUN_1402ba1f0` starts an IFF `FORM` record and writes the supplied form type.
- `ghidra-raw/ghidra-raw-anim-set6-trace.txt` lines 515-519:
  the defined string scan finds `RTM_0100`/`RTM_0101`, but no plain defined
  `SET6`, `EVNT`, or `CPRP` strings; those writer chunk IDs are packed constants
  in code, not normal string data.
- `ghidra-raw/ghidra-raw-writer-callsite-deep.txt` lines 364196-364197:
  instruction-address proof that `FUN_141068360` writes `ANIM` and `SET6`
  constants.
- `ghidra-raw/ghidra-raw-writer-callsite-deep.txt` lines 364265, 364267, 364282,
  364314, and 364319:
  instruction-address proof for `FPS`, `HEAD`, `DATA`, `EVNT`, and `CPRP`
  constants in the same writer.
- `ghidra-raw/ghidra-raw-writer-callsite-deep.txt` lines 625157-625170 and
  625874-625944:
  decompiler proof of chunk-open order and optional `EVNT`/`CPRP` conditions.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 453-462:
  instruction proof that `FPS` opens, writes 4 raw bytes from the writer context
  pointer, and closes.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 792-804:
  instruction proof that `EVNT` opens only when event count is nonzero and starts
  with a raw 16-bit count through `FUN_1402ba8a0`.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 902-912:
  instruction proof that `CPRP` opens only when custom-property count is nonzero
  and starts with a raw 16-bit count through `FUN_1402ba8a0`.

## IFF Primitive Behavior

confirmed: the output stream is chunked through `enf::IFFOutput`-style helpers.
`FUN_1402ba0a0` opens a chunk by writing the 4-byte tag, writing four zero
bytes as a placeholder size, recording the current stream position, and pushing
the tag onto the open-chunk stack. `FUN_1402ba320` closes the current chunk by
reading the current position, seeking back to the reserved size slot, writing
the computed chunk size, and seeking back to the end.

confirmed by Workbench golden output: chunk sizes are big-endian, while the
observed `FPS` and `HEAD` payload integer fields are little-endian.

confirmed: chunk-size patching uses byte-swapped helper writes:

- `FUN_1402ba7d0` writes a swapped 32-bit value.
- `FUN_1402ba790` writes a swapped 16-bit value.

confirmed: raw payload helper writes are separate from the swapped size-patch
helpers:

- `FUN_1402ba8d0` writes a raw 4-byte value.
- `FUN_1402ba8a0` writes a raw 2-byte value.
- `FUN_1402ba900` writes a 4-byte raw length followed by string bytes, or raw
  length `-1` for null strings.

Implementation rule: reproduce the chunk wrapper as tag + reserved size +
payload + size patch. Do not assume every payload scalar is globally
big-endian; the decompile shows separate raw payload helpers and explicit
optional byte-swapping in the ANM writer for selected record fields.

Evidence:

- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 1013-1047:
  `FUN_1402ba0a0` open-chunk behavior.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 1073-1118:
  `FUN_1402ba320` close-and-patch behavior.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 667-719:
  swapped 16-bit and 32-bit patch helpers.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 761-887:
  raw 2-byte, raw 4-byte, and string payload helpers.

## Writer Context From TXA

confirmed: before `FUN_141068360`, `FUN_141067c00` converts
`TXA::Animation` into a writer context:

- FPS copied from `TXA::Animation + 0x80`.
- track table read from `TXA::Animation + 0x50`, count from `+0x5c`.
- writer skeleton node entries are stride `0x28`.
- writer key records are stride `0x2c`.
- writer key records copy the TXA key data and add a 32-bit frame/key index at
  offset `+0x28`.
- TXA track flag byte `+0x28` maps directly into writer node flag bit `0x1`.
- TXA track bytes `+0x29`, `+0x2a`, and `+0x2b` are inverted for writer bits
  `0x2`, `0x4`, and `0x8`: the writer bit is set when the TXA byte is zero.
- TXA key records are copied from track data pointer `track + 0x18`.
- events are copied from `TXA::Animation + 0x60` with count `+0x6c`.
- custom properties are copied from `TXA::Animation + 0x70` with count `+0x7c`.

confirmed: writer skeleton nodes are created by `FUN_141067850`; it stores the
node name, allocates `frameCount * 0x2c` bytes for output key records, and
initializes missing key records with identity-like defaults.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1422-1680.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1503-1584:
  TXA `0x28` key records are copied into writer `0x2c` records and the
  frame/key index is stored at writer key offset `+0x28`.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 401-488.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` lines 1943-1965:
  direct flag mapping/inversion in `FUN_141067c00`.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` lines 1966-2047:
  TXA key records copied to writer stride `0x2c` with frame/key indices.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` lines 2053-2137:
  event and custom-property arrays copied into the writer context.
- `ghidra-raw/ghidra-raw-txa-tag-usage-exhaustive.txt` lines 211-220:
  final writer context and binary writer callers are only `FUN_140e75c10` and
  `FUN_140fc9d50` in this trace.

## HEAD Node Record Layout

confirmed: `FUN_141068360` builds one temporary `0x42` byte record per writer
node before writing the `HEAD` chunk. The writer emits records when translation
key count is nonzero, rotation key count is nonzero, or forced output through
the caller flag is enabled. The observed emission branch does not treat a
retained scale-key count by itself as sufficient. The actual bytes written for
each record are `0x22 + nameLength`.

confirmed raw record fields before optional endian swap:

- `+0x00` float: translation minimum/base.
- `+0x04` float: translation range.
- `+0x08` float: rotation minimum/base.
- `+0x0c` float: rotation range.
- `+0x10` float: scale minimum/base.
- `+0x14` float: scale range.
- `+0x18` uint16: total source frame/key count.
- `+0x1a` uint16: retained translation key count.
- `+0x1c` uint16: retained rotation key count.
- `+0x1e` uint16: retained scale key count.
- `+0x20` uint8: flags.
- `+0x21` uint8: name length, excluding terminator.
- `+0x22` bytes: node name bytes.

confirmed: when the endian-swap flag is set, the six float fields are
byte-swapped as 32-bit words, and the four 16-bit count fields are byte-swapped
before writing.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1821-1848:
  temporary header record size `nodeCount * 0x42`.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2201-2237:
  base/range/count/flag/name values are stored into the temp record.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2254-2307:
  `HEAD` writes `0x22 + nameLength` bytes, with optional byte swapping.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 572-578:
  emission condition checks retained translation count, retained rotation count,
  and caller force flag before skipping a node.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 647-668:
  optional endian-swap path writes swapped count fields and the flag byte into
  the temporary output record before stream write.

## Key Reduction And Packing

confirmed: `FUN_141068360` performs per-channel key reduction before writing
`DATA`. Translation, scale, and rotation are handled separately. If all frames
are retained for a component, the writer sets a flag bit instead of emitting an
index stream:

- translation all-frames flag: `0x10`
- rotation all-frames flag: `0x20`
- scale all-frames flag: `0x40`

confirmed: when not all frames are retained, `FUN_141069a50` writes the retained
key indices. For each selected key index, it reads a 16-bit value from
`base + keyIndex * 0x2c + 0x28`, optionally byte-swaps it, and writes
`count * 2` bytes to the IFF stream.

confirmed: `FUN_141069860` writes quantized float component streams. For each
float component it computes:

```text
q = clamp((value - base) * scale, 0, 65535)
write uint16(q)
```

If the endian flag is set, the 16-bit value is byte-swapped before output.

confirmed: Workbench computes min/range/scale values separately for
translation, scale, and rotation before calling `FUN_141069860`. Translation
uses three component streams per retained key, scale uses three, and rotation
uses four.

confirmed constants used by the writer:

- quantized stream clamp maximum: `65535.0`.
- initial min/max sentinels: `3.4028235e+38` and `-3.4028235e+38`.
- identity/default scalar: `1.0`.
- translation reduction threshold: `0.0005`.
- scale reduction threshold: `0.0005`.
- rotation reduction threshold: `0.000001`.
- quaternion slerp linear-fallback cutoff: `0.999`.
- translation component multipliers X/Y/Z: `1.0`, `1.0`, `1.0`.
- tiny range guard before computing quantization scale:
  `double 0.000001`; if range is below this, scale stays `1.0`.

confirmed reduction behavior:

- translation keeps frame 0, then drops intermediate frames if linear
  interpolation from previous kept key to next source key is within squared
  vector error threshold `0.0005^2`; the final frame is kept if it differs
  from the previous kept translation.
- scale keeps frame 0, then drops intermediate frames if each component's
  absolute interpolation error is `<= 0.0005`; scale may be omitted as an all
  identity/default stream when close to `1.0`.
- rotation keeps frame 0, uses quaternion slerp (`FUN_1402bbe70`) for
  interpolation, and drops intermediate frames if
  `abs(1.0 - dot(interpolated, source)) <= 0.000001`; the final frame is kept
  if its quaternion dot check differs from the previous kept key.
- `FUN_1402bbe70` negates the target quaternion when the source/target dot is
  negative. When the adjusted dot is at least `0.999`, it uses linear
  interpolation; otherwise it uses `acosf`/`sinf` slerp.

confirmed by golden pair: the standalone TXA -> ANM prototype became
byte-identical to Workbench output for
`anm/txa_anm/p_2hd_cro_interact_out.txa` only after using the Ghidra-confirmed
`0.999` slerp cutoff.

confirmed call-site behavior:

- `FUN_140fc9d50`, the TXA load/build/write helper, calls
  `FUN_141068360(writerContext, outputPath, 0, 0)`. This disables endian swapping
  and does not force extra `HEAD` records.
- `FUN_140e75c10`, the direct FBX animation conversion helper, also calls
  `FUN_141068360(writerContext, outputPath, 0, 0)`.
- before the direct FBX call, `FUN_140e75c10` sets `DAT_142373be8`,
  `DAT_142373bec`, and `DAT_142373bf0` to zero. Those globals are the
  translation, scale, and rotation reduction thresholds used inside
  `FUN_141068360`, so the direct FBX-to-ANM path uses zero tolerance for key
  reduction. The TXA helper does not show this zeroing at its call site.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1818-2135:
  translation and scale key reduction.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2135-2243:
  rotation key reduction.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2377-2504:
  index/float stream write calls for translation, scale, and rotation.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 198-255:
  `FUN_141069a50` retained-key index stream writer.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 268-390:
  `FUN_141069860` quantized float stream writer.
- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` lines 190-201:
  numeric constants used for clamp, sentinels, thresholds, multipliers, and
  range guard.
- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` lines 347-420:
  `FUN_1402bbe70` quaternion interpolation helper used by rotation reduction.
- `ghidra-raw/ghidra-raw-slerp-threshold-http.txt`:
  HTTP `read_memory` of `workbenchApp.exe:0x141a6d970`, showing bytes
  `77 be 7f 3f` for float `0.999`.
- `txa-anm-prototype-status.md`:
  byte-identical prototype run against the Workbench golden pair.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` lines 568-586:
  `FUN_140fc9d50` builds writer context and calls `FUN_141068360(..., 0, 0)`.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` lines 3562-3566:
  `FUN_140e75c10` builds writer context and zeroes the three threshold globals.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` lines 3607-3608:
  direct FBX path calls `FUN_141068360(..., 0, 0)`.
- `ghidra-raw/ghidra-raw-writer-callsite-deep.txt` lines 626014-626121:
  targeted decompile includes `FUN_141069a50` and `FUN_141069860` as retained
  index and quantized stream writers.

## Event And Custom Property Chunks

confirmed: `EVNT` starts with a 16-bit event count. Each event record writes:

- 4 raw bytes from the event record base, the frame field.
- 4 raw bytes for length of string at event `+0x08` plus terminator, then the
  string bytes.
- 4 raw bytes for length of string at event `+0x10` plus terminator, then the
  string bytes.
- 4 raw bytes from event `+0x18`, the user value field.

confirmed: for null event strings, the writer uses the empty-string data pointer
and writes length `1`, so the payload still includes a terminator byte.

confirmed: `CPRP` starts with a 16-bit custom-property count. Each record
writes:

- 4 raw bytes for length of string at record `+0x00` plus terminator, then the
  string bytes.
- 4 raw bytes for length of string at record `+0x08` plus terminator, then the
  string bytes.

confirmed: for null custom-property strings, the writer uses the empty-string
data pointer and writes length `1`, matching the event string behavior.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2521-2589.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2591-2648.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 792-864:
  `EVNT` count, frame write, string length/data writes, and user-value write.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 902-965:
  `CPRP` count and two string length/data writes per record.

## Writer Limits And Truncation Risks

confirmed: `FUN_141067c00`, the `TXA::Animation` to writer-context builder,
has one explicit overflow-style failure observed in this pass: if
`FUN_141067850` returns `0xffffffff`, it reports `Skeleton has too much nodes`
through the caller error object and returns failure.

confirmed: several writer fields are narrowed later:

- source frame/key count in `HEAD` is stored from the writer node key count into
  a 16-bit field.
- retained translation, rotation, and scale key counts are maintained/stored in
  16-bit fields.
- `EVNT` and `CPRP` counts are written through the raw 16-bit helper.
- node name length is scanned as a C string and stored in one byte before
  emitting `0x22 + nameLength` bytes.

unknown: no decompiled branch found in this pass reports a clear error for key
counts, event counts, custom-property counts, or node name lengths exceeding
those narrowed fields. A converter aiming for Workbench-compatible behavior
should treat these as practical limits and reject overflow before writing.

Evidence:

- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 1620-1654:
  writer-context build loop and `Skeleton has too much nodes` failure.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 2394-2402:
  `HEAD` source frame/key count narrowed and node name pointer selected.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 2425-2473:
  `HEAD` emission condition, one-byte node-name length, and record write size
  `0x22 + nameLength`.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 2493-2512:
  retained key counts read from 16-bit fields to size temporary streams.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 792-804:
  `EVNT` starts with a raw 16-bit count.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` lines 902-912:
  `CPRP` starts with a raw 16-bit count.

## Autodesk Cache XML Path

confirmed: `FUN_1414cec40` parses an `Autodesk_Cache_File` or
`Alias_Cache_File` XML-like structure. It extracts:

- `cacheType`
- `Version`
- `Channels`
- `Range`
- `TimePerFrame`
- repeated `extra` entries

confirmed: `FUN_1414cf050` writes an `Autodesk_Cache_File` XML-like structure.
It emits:

- `cacheType`
- `Format`
- optional `Range`
- `cacheTimePerFrame` with `TimePerFrame`
- `cacheVersion` with `Version`
- repeated `extra`
- `Channels`
- repeated `channel%d`
- `ChannelName`
- `ChannelType`
- `ChannelInterpretation`
- `SamplingType` as `Regular` or `Irregular`
- `SamplingRate`
- `StartTime`
- `EndTime`

confirmed: `FUN_1414cfd70` maps numeric channel type ids to strings:

- `1` -> `Double`
- `2` -> `DoubleArray`
- `3` -> `DoubleVectorArray`
- `4` -> `Int32Array`
- `6` -> `FloatVectorArray`
- other -> `UnknownData`

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 6059-6403.
- `ghidra-raw/ghidra-raw-target-functions.txt`: targets `1414cec40`, `1414cf050`,
  `1414cfd70`.

## DataExporter Cross-Check

- confirmed: the Workbench writer path documented above writes IFF-style
  `ANIM`/`SET6` output through `FUN_141068360`.
- likely: the separate reader path accepting `RTM_0100`/`RTM_0101` is a
  different animation binary family or runtime/import reader path. The current
  evidence does not connect it to the `FUN_141068360` `ANIM`/`SET6` writer.
- confirmed: `dataExporter_v141_x64_RetailDX11.dll` reaches the final `.anm`
  save boundary through `FUN_1800b1820`, which calls `FUN_1807f68b0` and
  `FUN_1807f7010` after writing the text TXA path through `FUN_1807e4a50`.
- confirmed: `FUN_1807e4a50` is a separate text/XML-like TXA writer path. It
  writes labels including `animation`, `version`, `fps`, `numFrames`, `events`,
  and `custProp`.
- confirmed: `FUN_1807f68b0` is the DLL-side writer-context builder matching
  Workbench `FUN_141067c00`: it reads FPS from `TXA::Animation +0x80`, tracks
  from `+0x50/+0x5c`, TXA key stride `0x28`, writer key stride `0x2c`, and
  copies events/custom properties from `+0x60/+0x6c` and `+0x70/+0x7c`.
- confirmed: `FUN_1807f7010` is a binary IFF-style writer path matching
  Workbench `FUN_141068360`. It creates an `enf::IFFOutput`, opens `ANIM`
  (`0x4d494e41`) and `SET6` (`0x36544553`), then writes `FPS`, `HEAD`, `DATA`,
  optional `EVNT` (`0x544e5645`), and optional `CPRP` (`0x50525043`).
- confirmed: DLL helper `FUN_1807f8510` writes quantized float streams as
  16-bit values after clamping `(value - min) * scale` to `[0, 65535]`.
- confirmed: DLL helper `FUN_1807f8700` writes retained key indices by reading
  the 16-bit frame/index field from each selected writer key at
  `keyIndex * 0x2c + 0x28`.
- confirmed: quantization behavior for the `FUN_141068360` writer uses
  16-bit clamped streams as described above.
- confirmed: FBX-to-internal `TXA::Animation` conversion is documented in
  `fbx-import.md`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 1091-1195:
  `FUN_1800b1820` creates file wrappers and calls `FUN_1807e4a50`,
  `FUN_1807f68b0`, and `FUN_1807f7010`.
- `ghidra-raw/ghidra-raw-dataexporter-save-helpers.txt` lines 192-572:
  `FUN_1807e4a50` text writer.
- `ghidra-raw/ghidra-raw-dataexporter-save-helpers.txt` lines 910-1033 and 1737-1805:
  `FUN_1807f7010` IFF creation and chunk constants.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: HTTP decompile of
  `FUN_1800b1820`, `FUN_1807e4a50`, `FUN_1807f68b0`, `FUN_1807f7010`,
  `FUN_1800ae930`, `FUN_1800af0c0`, and TXA track/key helpers.
- `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt`: HTTP decompile of
  `FUN_1807f8510`, `FUN_1807f8700`, and low-level IFF open/close/raw-write
  helpers.
- `dataexporter-export-boundary.md`: current export-loop and save-boundary
  summary.

## Not Yet Proven

- unknown: no byte-level Workbench output fixture has been compared against a
  standalone implementation in this pass. A Workbench-generated golden pair now
  validates the physical `FORM/ANIM/SET6` container, `FPS`, `HEAD`, and `DATA`
  size accounting, but implementation certification still requires producing a
  matching file from our own writer.
- unknown: no Ghidra evidence currently proves TXA tags are copied into or used
  by the final `ANIM`/`SET6` writer.
