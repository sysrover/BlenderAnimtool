# TXA Import Evidence

## Search Result Correction

confirmed: the first defined-string pass did not emit `.txa` because Ghidra had
not materialized that region as ordinary defined string data. A later raw memory
byte-search pass found TXA evidence in `workbenchApp.exe`.

Evidence:

- `ghidra-raw/ghidra-raw-byte-needle-search.txt` lines 167-170: ASCII `.txa` found at
  `0x141c14618`, referenced from `FUN_140d5cf10 @ 0x140d5cf10`.
- `ghidra-raw/ghidra-raw-byte-needle-search.txt` lines 175-186: ASCII `txa` found at
  `0x141a756d4`, `0x141c14619`, and `0x141c51e64`.
- `ghidra-raw/ghidra-raw-byte-needle-search.txt` lines 191-232: ASCII `TXA` found in 18
  locations, including `0x141aaeed8` referenced by `FUN_140f64690` and
  `FUN_140d5cf10`, and `0x141c8c820` referenced by `FUN_140fce290`.

## Workbench File Browser

confirmed: `FUN_140eb8840` constructs an `AnimFileBrowser` and configures file
filters for `anm`, `txa`, and `age`.

Evidence:

- `ghidra-raw/ghidra-raw-txa-targets.txt` lines 1725-1728: target function identity.
- `ghidra-raw/ghidra-raw-txa-targets.txt` lines 1841-1843: `QString` construction for
  `anm`, `txa`, and `age`.
- `ghidra-raw/ghidra-raw-txa-targets.txt` line 1858: the list is applied through
  `FUN_140f9ac50(this, &local_res10)`.

## TXA Resource Classes

confirmed: Workbench contains TXA resource class names:

- `TXAResourceClass`
- `TXAResourceClassWB`

Evidence:

- `ghidra-raw/ghidra-raw-txa-targets.txt` lines 1913-1922:
  `FUN_140fce290` returns `TXAResourceClassWB`.
- `ghidra-raw/ghidra-raw-txa-targets.txt` lines 1948-1957:
  `FUN_140457bd0` returns `TXAResourceClass`.
- `ghidra-raw/ghidra-raw-txa-targets.txt` lines 442 and 994 show `TXAResourceClass`
  consumed by other decompiled Workbench/resource paths.

## Current Interpretation

confirmed: TXA is a Workbench animation-adjacent resource type, not absent from
the binary. The current evidence proves browser/resource-class integration and
the TXA-to-ANM conversion boundary. Individual TXA text keyword handlers remain
partially unresolved.

## TXA To ANM Algorithm

confirmed: the TXA-to-ANM path is now bounded by three functions:

1. `FUN_141057800` loads/parses a TXA file into a `TXA::Animation`.
2. `FUN_141067c00` converts `TXA::Animation` into the binary writer context.
3. `FUN_141068360` serializes that writer context to the final binary `.anm`
   IFF stream.

confirmed: `FUN_141057800` opens the input, creates a
`TXA::ParseAnimation::vftable` parser object, calls
`FUN_141058e60(animation, stream, parser)`, reports `Broken data` on parse
failure, and calls `FUN_1410572d0(animation, errorHandler)` after parsing.

confirmed: `FUN_141058e60` is the generic TXA text parser loop. It repeatedly
calls `FUN_1410674f0` to read tokens/attributes, dispatches to parser vtable
methods for attribute/open/close or data entries, and logs `ERROR: Unknown
attribute %s` / `ERROR: Unparsed data %s` if the parser rejects content.

confirmed: `FUN_1410572d0` validates node hierarchy references after parse. It
checks each node's child index at track offset `+0x10` and sibling index at
`+0x0c`; bad references report `Bad node->children index. Node %s` or
`Bad node->sibling index. Node %s`.

confirmed: `FUN_141067c00` builds the writer context from the parsed
`TXA::Animation`. It copies FPS from animation offset `+0x80`, iterates tracks
from the table at `animation + 0x50` with count `animation + 0x5c`, creates
writer skeleton nodes, copies track flags from track bytes `+0x28..+0x2b`,
copies per-frame key data from the TXA `0x28` stride into writer `0x2c` stride
records, and copies event/custom-property arrays from animation offsets
`+0x60/+0x6c` and `+0x70/+0x7c`.

## TXA Text Grammar And Field Mapping

confirmed: `TXA::ParseAnimation::vftable` is at `0x141ca35c8`. The parser
recognizes the top-level block `animation <name>`, storing the name at
`TXA::Animation + 0x40`, then recursively parses animation attributes.

confirmed top-level animation attributes:

- `version <float>` -> `TXA::Animation + 0x3c`.
- `fps <int>` -> `TXA::Animation + 0x80`.
- `numFrames <int>` -> `TXA::Animation + 0x84`.
- `tag <strings...>` -> copied into the tag/list field starting at
  `TXA::Animation + 0x08` through `FUN_141058640`.
- `node <name> { ... }` -> creates a TXA track with `FUN_141055e40`.
- `nodeDiff <name> { ... }` -> creates a TXA track and sets track byte
  `+0x28 = 1`.
- `events { ... }` -> parsed through `TXA::ParseEvents::vftable`.
- `custProps { ... }` -> parsed through
  `TXA::ParseCustomProperties::vftable`.

confirmed node grammar:

- nested `node <name>` / `nodeDiff <name>` creates a child track. The parser
  resolves the parent by current track name through `FUN_141056380`, then calls
  `FUN_141055e40` with that parent index.
- `keys` without arguments sets track bytes `+0x29 = 1` and `+0x2a = 1`.
- `keys t ...` sets track byte `+0x29 = 1`.
- `keys q ...` or `keys s ...` sets track byte `+0x2a = 1`.
- The `keys` block is parsed through `TXA::ParseKeys::vftable`.

confirmed key/frame grammar:

- `frame <startFrame> { ... }` appends one `0x28` byte key record.
- `frame <startFrame> <endFrame> { ... }` appends the parsed key, then copies
  it for each frame through the end-frame range.
- If `startFrame` is not zero, the parser initializes the new key from an
  existing key record at that frame index before applying nested fields.
- inside `frame`:
  - `q <x> <y> <z> <w>` writes four floats to key offsets
    `+0x00/+0x04/+0x08/+0x0c`.
  - `t <x> <y> <z>` writes three floats to key offsets
    `+0x10/+0x14/+0x18`.
  - `s <x> <y> <z>` writes three floats to key offsets
    `+0x1c/+0x20/+0x24`.

confirmed default key initialization:

- newly allocated TXA key records are initialized with quaternion
  `0, 0, 0, 1`, translation `0, 0, 0`, and scale `1, 1, 1`.
- the `frame` parser creates the same default key before applying nested
  `q`, `t`, or `s` fields.
- if `startFrame` is nonzero, the parser can copy an existing key record before
  applying the nested frame fields, then range-copy the final parsed key through
  the requested inclusive end frame.

confirmed event/custom-property grammar:

- `event <frame> <name> [value] [userValue]` calls
  `FUN_141055b40(animation, frame, name, valueOrNull, userValueOrFFFFFFFF)`.
- `custProp <name> <value>` calls `FUN_141055a40(animation, name, value)`.

confirmed storage:

- custom properties are stored at `TXA::Animation + 0x70`, capacity `+0x78`,
  count `+0x7c`, with record stride `0x10`: name pointer/string at `+0x00`,
  value pointer/string at `+0x08`.
- events are stored at `TXA::Animation + 0x60`, capacity `+0x68`, count
  `+0x6c`, with record stride `0x20`: frame at `+0x00`, name at `+0x08`,
  value at `+0x10`, user value/int at `+0x18`.
- tag lists are appended through `FUN_141058640` into the animation tag/list
  area beginning at `TXA::Animation + 0x08`; the helper also maintains a name
  lookup map for nonempty first tag strings.
- a separate tag-aware parser callback `FUN_141064680` gives named semantics for
  some tag values in a related TXA-like object:
  - `tag Scale <float>` parses the second value with `strtod` and stores a float
    at object offset `+0x50`.
  - `tag Coords XZY` clears byte `+0x54`.
  - `tag SourceName <...p3d>` lowercases/normalizes the name, checks for a
    `.p3d` suffix, and writes `0.125` to float offsets `+0x60` and `+0x64`.
  - after these semantic checks it still appends the tag list through
    `FUN_141058640(param_2 + 8, tagList)`.
- `FUN_141056380` finds a track index by string name and returns `0xffffffff`
  if absent.
- key-buffer resize uses `FUN_141057790`, allocates `capacity * 0x28`, and
  copies existing key records with `FUN_1410564c0`.

Evidence:

- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 189-190:
  `TXA::ParseAnimation::vftable` address and first callback.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 211-299:
  `version`, `fps`, `numFrames`, and `tag` handling.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 334-411:
  `animation`, `node`, `nodeDiff`, `events`, and `custProps` block dispatch.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 461-548:
  nested node handling and `keys` flag parsing.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 591-740:
  `frame` parsing, range copy, and key-record append behavior.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 765-841:
  `q`, `t`, and `s` frame-field mapping.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 641-653:
  `FUN_141055e40` initializes allocated TXA keys to identity/default
  quaternion, translation, and scale.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 645-654:
  `FUN_1410580e0` initializes a parsed `frame` key with the same defaults.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 887-1001:
  `event` and `custProp` parsing.
- `ghidra-raw/ghidra-raw-txa-parser-strings.txt`: confirms string labels `fps`, `tag`,
  `node`, `keys`, `t`, `q`, and `s` at the DAT addresses used by the parser.
- `ghidra-raw/ghidra-raw-txa-storage-helpers.txt` lines 188-261:
  `FUN_141055a40` custom-property storage.
- `ghidra-raw/ghidra-raw-txa-storage-helpers.txt` lines 262-338:
  `FUN_141055b40` event storage.
- `ghidra-raw/ghidra-raw-txa-storage-helpers.txt` lines 339-387:
  `FUN_141058640` tag/list storage.
- `ghidra-raw/ghidra-raw-txa-storage-helpers.txt` lines 388-425:
  `FUN_141056380` track-name lookup.
- `ghidra-raw/ghidra-raw-txa-storage-helpers.txt` lines 426-553:
  key-buffer resize/copy helpers.
- `ghidra-raw/ghidra-raw-txa-tag-deep.txt` lines 320-528:
  `FUN_141064680` tag-specific handling for `Scale`, `Coords XZY`, and
  `SourceName *.p3d`, followed by `FUN_141058640`.
- `ghidra-raw/ghidra-raw-txa-tag-deep.txt` lines 196-295:
  `FUN_1410643c0` is another parser callback that accepts `texCoords`,
  `parent`, and `tag`, then stores tags via `FUN_141058640`.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1356-1404:
  `FUN_141057800` parse/load boundary.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 761-879:
  `FUN_141058e60` generic parser dispatch loop.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 882-1003:
  `FUN_1410572d0` post-parse hierarchy validation.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 1422-1680:
  `FUN_141067c00` writer-context construction from `TXA::Animation`.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 401-488:
  `FUN_141067850` adds writer skeleton nodes, stores node name, and allocates
  `0x2c` byte output key records.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 504-532:
  `FUN_141067a20` recursively computes hierarchy depth/extent from child and
  sibling links.

confirmed: the loaded `dataExporter_v141_x64_RetailDX11.dll` also exposes TXA in
animation export UI. Its save-file filter is
`Anm files (*.anm *.txa);;All files (*.*)`, and it also contains a
`TXAExportDialog` string.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 209-213.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 255-256.

confirmed: the DLL constructs a `TXA::Animation` object during export before
the final save stage.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 680-699:
  `FUN_1800afc00` allocates `0x88` bytes and initializes
  `TXA::Animation::vftable`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 890-895:
  `FUN_1800af0c0` creates/finds tracks in `TXA::Animation`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 912-1046:
  keyframes are written into track buffers with stride `0x28`.

confirmed: the DLL save chain independently matches the Workbench TXA-to-ANM
flow.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: `FUN_1800b1820` saves text TXA
  through `FUN_1807e4a50`, builds a binary writer context through
  `FUN_1807f68b0`, then writes binary ANM through `FUN_1807f7010`.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: `FUN_1807f68b0` copies track
  data from `TXA::Animation +0x50/+0x5c`, TXA key stride `0x28`, and writes
  output key records at stride `0x2c`, matching Workbench `FUN_141067c00`.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: `FUN_1807f68b0` copies events
  and custom properties from animation offsets `+0x60/+0x6c` and `+0x70/+0x7c`.

## TXA Numeric Parsing And Limits

confirmed: integer fields parsed through `FUN_140202210` use C `strtol` base
10. If the source token is null, empty, fails to parse, or sets `errno`, the
helper returns the caller-provided default value instead of reporting an error.
The TXA parser passes default `0` for `fps`, `numFrames`, and `frame`
start/end values seen in this pass.

confirmed: float vector fields parsed through `FUN_140080e60` use C `strtod`.
If the source token is null, empty, fails to parse, or sets `errno`, the helper
returns the caller-provided default. On success it converts the parsed double to
float and returns the raw 32-bit float bits.

confirmed: the observed TXA parser callbacks check parameter count before
parsing fields, but they do not add semantic range checks for negative frame
numbers, `fps <= 0`, frame ranges beyond `numFrames`, or invalid float
magnitudes in the decompiled callbacks. Bad numeric text therefore silently
falls back to `0` for the observed integer call sites and to the passed default
for float call sites.

confirmed: track/key dynamic arrays grow by the same capacity rule in the
observed TXA helpers: when `capacity < count + 1`, new capacity starts at
`oldCapacity + 4`; once more than three entries are needed, it uses
`oldCapacity * 2 + 1` unless the exact requested count is larger.

confirmed: `FUN_141055e40` coerces a new top-level track's parent index from
`0xffffffff` to `0` if the animation already has tracks. It links child/sibling
indices and allocates `param_4 * 0x28` bytes for key records.

Evidence:

- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 1085-1107:
  `FUN_140202210` C `strtol` base-10 helper and default-on-failure behavior.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 1205-1227:
  `FUN_140080e60` C `strtod` helper, float cast, and default-on-failure
  behavior.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 211-299:
  top-level `version`, `fps`, `numFrames`, and `tag` parsing and parameter
  count checks.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 621-740:
  `frame` parsing, default key initialization, start/end parsing, and inclusive
  range copy with no visible semantic range check.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` lines 776-835:
  `q`, `t`, and `s` parse callbacks requiring enough parameters and writing
  float fields through `FUN_140080e60`.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 2839-2948:
  `FUN_141055e40` track creation, parent coercion/linking, allocation, and key
  default initialization.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt` lines 2961-2976:
  `FUN_141057790` key-buffer resize to `capacity * 0x28`.

## Remaining TXA Parser Gaps

confirmed: `tag` storage itself is fully traced for the animation parser, and
related callbacks show direct handling of `Scale`, `Coords XZY`, and
`SourceName *.p3d`.

confirmed: the exhaustive tag-usage pass found only three direct callers of
`FUN_141058640`, the tag-store helper:

- `FUN_1410578e0` - top-level animation parser.
- `FUN_1410643c0` - parser callback for `texCoords`, `parent`, and `tag`.
- `FUN_141064680` - parser callback with `Scale`, `Coords`, and `SourceName`
  semantics.

confirmed: `FUN_141067c00`, the `TXA::Animation -> ANM` writer-context builder,
is not a direct caller of the tag-store helper and its decompile only copies
tracks, events, and custom properties into the writer context.

confirmed: focused HTTP decompile narrows the top-level animation tag storage
site. `FUN_1410578e0` handles top-level `tag` attributes and calls
`FUN_141058640(param_2 + 8, tagList)`, while the same decompile stores `fps` at
`param_2 + 0x80` and `numFrames` at `param_2 + 0x84`. This places the top-level
tag list outside the fields read by `FUN_141067c00`.

unknown: tags may affect other TXA/model-resource workflows, but no Ghidra
evidence currently proves they affect `FUN_141068360` binary `.anm` output.

Evidence:

- `ghidra-raw/ghidra-raw-txa-tag-usage-exhaustive.txt` lines 188-195:
  direct callers of `FUN_141058640`.
- `ghidra-raw/ghidra-raw-txa-tag-usage-exhaustive.txt` lines 211-220:
  direct callers of `FUN_141067c00` and `FUN_141068360`.
- `ghidra-raw/ghidra-raw-txa-tag-usage-exhaustive.txt` lines 4910-5170:
  `FUN_141067c00` decompile, showing no tag-list copy into writer context.
- `ghidra-raw/ghidra-raw-missing-parts-focused-http.txt`: `tag_callers_decompile` section;
  `FUN_1410578e0` calls `FUN_141058640(param_2 + 8, ...)`, `FUN_1410643c0`
  calls `FUN_141058640(*(param_1 + 0x20), ...)`, and `FUN_141064680` handles
  `Scale`, `Coords XZY`, and `SourceName *.p3d` before storing the tag list.
