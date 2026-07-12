# Ghidra Evidence Log

## Runs

- confirmed: `AnmWorkbenchExactStrings.java` executed through
  `/run_script_inline` against Ghidra program `workbenchApp.exe`; raw output is
  `ghidra-raw/ghidra-raw-exact-strings.txt`.
- confirmed: `AnmWorkbenchTargetFunctions.java` executed through
  `/run_script_inline` against Ghidra program `workbenchApp.exe`; raw output is
  `ghidra-raw/ghidra-raw-target-functions.txt`.
- confirmed: `AnmWorkbenchByteNeedleSearch.java` executed through
  `/run_script_inline` against Ghidra program `workbenchApp.exe`; raw output is
  `ghidra-raw/ghidra-raw-byte-needle-search.txt`.
- confirmed: `AnmWorkbenchTxaTargets.java` executed through
  `/run_script_inline` against Ghidra program `workbenchApp.exe`; raw output is
  `ghidra-raw/ghidra-raw-txa-targets.txt`.
- confirmed: `GhidraProjectProgramList.java` showed
  `/dataExporter_v141_x64_RetailDX11.dll` loaded as a Ghidra `Program`; raw
  output is `ghidra-raw/ghidra-raw-project-programs.txt`.
- confirmed: `DataExporterAnmResearch.java` opened
  `dataExporter_v141_x64_RetailDX11.dll` from the Ghidra project and scanned
  strings/byte needles; raw output is `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt`.
- confirmed: `DataExporterFunctionDump.java` opened the same DLL and decompiled
  target functions; raw output is `ghidra-raw/ghidra-raw-dataexporter-functions.txt`.
- confirmed: `DataExporterUsageResearch.java` dumped DLL external entry points
  and decompiled the public dialog exports; raw output is
  `ghidra-raw/ghidra-raw-dataexporter-usage.txt`.
- confirmed: `DataExporterCallableSurface.java` decompiled nearby callable/UI
  functions and export-name string references; raw output is
  `ghidra-raw/ghidra-raw-dataexporter-callable-surface.txt`.
- confirmed: `DataExporterAe930Trace.java` decompiled the DLL export loop,
  helper functions, host callback calls, and final save boundary; raw output is
  `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt`.
- confirmed: `DataExporterCallerSearch.java` scanned all loaded Ghidra programs
  for dataExporter/ShowAnim/IAnimExporter symbols and strings; raw output is
  `ghidra-raw/ghidra-raw-dataexporter-caller-search.txt`.
- confirmed: `DataExporterSaveHelpersTrace.java` decompiled the TXA text writer
  and deeper ANM/IFF save helpers; raw output is
  `ghidra-raw/ghidra-raw-dataexporter-save-helpers.txt`.
- confirmed: `DataExporterShowAnimDisasm.java` dumped the first ordinal `#6`
  instructions; raw output is `ghidra-raw/ghidra-raw-dataexporter-showanim-disasm.txt`.
- confirmed: `DataExporterShowAnimDeepTrace.java` decompiled ordinal `#6`,
  its Qt application helper, worker path, and animation dialog constructor; raw
  output is `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt`.
- confirmed: `DataExporterDialogPopulateTrace.java` decompiled the animation
  dialog population path and related helpers; raw output is
  `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt`.
- confirmed: `FbxAnimResourceTrace.java` traced Workbench
  `FBXAnimResourceClass`/`FBXAnimResourceClassWB` symbols, strings, and
  constructors; raw output is `ghidra-raw/ghidra-raw-fbx-anim-resource-trace.txt`.
- confirmed: `FbxAnimVtableTrace.java` dumped FBX resource class vtables and
  base constructors; raw output is `ghidra-raw/ghidra-raw-fbx-anim-vtable-trace.txt`.
- confirmed: `FbxAnimMethodsTrace.java` decompiled
  `FBXAnimResourceClassWB` conversion methods; raw output is
  `ghidra-raw/ghidra-raw-fbx-anim-methods-trace.txt`.
- confirmed: `FbxAnimConvertHelpersTrace.java` decompiled FBX animation
  conversion helpers; raw output is `ghidra-raw/ghidra-raw-fbx-anim-convert-helpers.txt`.
- confirmed: `FbxTxaAnmAlgorithmTrace.java` decompiled the core Workbench
  FBX-to-TXA and TXA-to-ANM functions; raw output is
  `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt`.
- confirmed: `AnmWriterPackingTrace.java` decompiled writer packing helpers,
  TXA track allocation, parser loop, and IFF chunk helpers; raw output is
  `ghidra-raw/ghidra-raw-anm-writer-packing.txt`.
- confirmed: `TxaParserCallbacksTrace.java` decompiled TXA parser callback
  vtables for animation, node, keys, frame, events, and custom properties; raw
  output is `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt`.
- confirmed: `TxaParserStringProbe.java` read parser DAT labels used by those
  callbacks; raw output is `ghidra-raw/ghidra-raw-txa-parser-strings.txt`.
- confirmed: `AnmConstantsAndTransformTrace.java` dumped writer constants and
  decompiled quaternion/transform helpers; raw output is
  `ghidra-raw/ghidra-raw-anm-constants-transform.txt`.
- confirmed: `TxaStorageHelpersTrace.java` decompiled TXA event/custom
  property/tag/track lookup/key resize helpers; raw output is
  `ghidra-raw/ghidra-raw-txa-storage-helpers.txt`.
- confirmed: `AnmDeepGapTrace.java` decompiled writer call sites, threshold
  globals, `FUN_141067c00` flag/key/event/custom copying, and FBX direct-write
  behavior; raw output is `ghidra-raw/ghidra-raw-deep-gap-trace.txt`.
- confirmed: `TxaTagDeepTrace.java` decompiled tag-specific parser callbacks
  and TXA text tag writing; raw output is `ghidra-raw/ghidra-raw-txa-tag-deep.txt`.
- confirmed: `AnmAnimSet6StringTrace.java` scanned defined strings and
  decompiled RTM reader functions; raw output is
  `ghidra-raw/ghidra-raw-anim-set6-trace.txt`.
- confirmed: `AnmWriterCallsiteDeepTrace.java` traced packed chunk constants,
  writer helper call windows, and targeted writer helper decompiles; raw output
  is `ghidra-raw/ghidra-raw-writer-callsite-deep.txt`.
- confirmed: `TxaTagUsageExhaustiveTrace.java` enumerated direct callers of tag
  store/text-write helpers and final writer boundaries; raw output is
  `ghidra-raw/ghidra-raw-txa-tag-usage-exhaustive.txt`.
- confirmed: `FbxTransformHelperDeepTrace.java` decompiled FBX transform helper
  routines for inverse, multiply, copy, and matrix extraction behavior; raw
  output is `ghidra-raw/ghidra-raw-fbx-transform-helper-deep.txt`.
- confirmed: `AnmTimeAndIffPrimitivesTrace.java` decompiled FBX time/tick
  helpers and low-level IFF primitive write helpers; raw output is
  `ghidra-raw/ghidra-raw-time-iff-primitives.txt`.
- confirmed: `AnmWriterByteLevelTrace.java` instruction-traced and decompiled
  the final writer around `FPS`, `HEAD`, `DATA`, `EVNT`, `CPRP`, retained-index
  packing, quantized streams, writer-context construction, and key defaults;
  raw output is `ghidra-raw/ghidra-raw-writer-byte-level.txt`.
- confirmed: direct HTTP MCP pass collected string anchors, xrefs, and batch
  decompiles for Workbench and dataExporter candidates; raw output is
  `ghidra-raw/ghidra-raw-http-accelerated-pass.txt`.
- confirmed: direct HTTP MCP pass decompiled DLL save/export boundary helpers;
  raw output is `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`.
- confirmed: direct HTTP MCP pass decompiled DLL writer primitive helpers; raw
  output is `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt`.
- confirmed: direct HTTP MCP pass targeted remaining converter gaps; raw output
  is `ghidra-raw/ghidra-raw-missing-parts-http.txt`.
- confirmed: focused direct HTTP MCP pass decompiled tag callers, TXA parser
  callbacks, writer limit helpers, and FBX evaluator wrapper; raw output is
  `ghidra-raw/ghidra-raw-missing-parts-focused-http.txt`.
- confirmed: direct HTTP string search pass checked FBX SDK/version and
  count-limit strings; raw output is `ghidra-raw/ghidra-raw-fbx-strings-http.txt`.
- confirmed: direct HTTP MetaFile/ResourceGUID pass decompiled
  `MetaFileClass` registration, ResourceName/GUID property editor helpers,
  duplicate-GUID handling, ResourceManager signal use, and ResourceGUID hex
  formatting; raw output is `ghidra-raw/ghidra-raw-metafile-guid-pass-http.txt`.
- caveat: the Ghidra user script directory reports stale compile errors from
  older broken scripts before successful output. The ANM scripts still completed
  successfully.

## Main Addresses

- `FUN_140b896c0` - animation binary reader; detects `RTM_0100`/`RTM_0101`.
- `FUN_140b89e40` - animation data reader path that raises
  `Broken animation file`.
- `FUN_140efc710` - `.anm` path validation and animation serializer candidate.
- `FUN_140ef5800` - child/object serializer helper called repeatedly by
  `FUN_140efc710`.
- `FUN_140ef43e0` - recursive/list serializer helper called by
  `FUN_140efc710`.
- `FUN_140ed6a50` - byte/block write helper used by `FUN_140efc710`.
- `FUN_1412950c0` - FBX export advanced option registration.
- `FUN_140ebdce0` - Workbench UI path that selects `.fbx` files and executes
  `FBXConverter.exe -anm -bin -simplename`.
- `FUN_140fc9aa0` - constructs `FBXAnimResourceClassWB`.
- `FUN_1404555f0` - base `FBXAnimResourceClass` constructor; registers
  `AnimationName` default `Take 001` and `FPS` default `30`.
- `FUN_140fc9fc0` - `FBXAnimResourceClassWB` vtable slot `+0xc0`; conversion
  method reading `AnimationName`/`FPS`, calling FBX animation conversion helper,
  and building `.anm` output.
- `FUN_140e75c10` - in-process FBX animation-take conversion helper; selects an
  FBX take, creates `TXA::Animation`, appends `.anm`, and writes via
  `FUN_141068360`.
- `FUN_140e7bf50` - recursive FBX node search by name.
- `FUN_140e78260` - special `EntityPosition` FBX node to TXA track conversion.
- `FUN_140e75770` - recursive FBX scene-node to TXA track conversion.
- `FUN_141055e40` - creates TXA tracks, links parent/child/sibling indices, and
  allocates `0x28` byte key records.
- `FUN_141057800` - TXA file load/parse boundary into `TXA::Animation`.
- `FUN_141058e60` - generic TXA parse dispatch loop.
- `FUN_1410578e0` - TXA top-level attribute parser for `version`, `fps`,
  `numFrames`, and `tag`.
- `FUN_141057e50` - TXA block dispatcher for `animation`, `node`, `nodeDiff`,
  `events`, and `custProps`.
- `FUN_141058410` - TXA node parser for nested nodes and `keys` blocks.
- `FUN_1410580e0` - TXA `frame` parser under `keys`.
- `FUN_141057c80` - TXA frame-field parser for `q`, `t`, and `s`.
- `FUN_141057bb0` - TXA `event` parser.
- `FUN_141057b30` - TXA `custProp` parser.
- `FUN_141055a40` - stores custom properties into `TXA::Animation`.
- `FUN_141055b40` - stores events into `TXA::Animation`.
- `FUN_141058640` - appends/stores TXA tag lists.
- `FUN_141064680` - tag-aware parser callback; handles `Scale`, `Coords XZY`,
  and `SourceName *.p3d` before storing tags.
- `FUN_1410643c0` - related parser callback for `texCoords`, `parent`, and
  `tag`.
- `FUN_141056380` - finds track index by name.
- `FUN_141057790` / `FUN_1410564c0` - resize/copy TXA key buffers.
- `FUN_1410572d0` - TXA post-parse hierarchy validator.
- `FUN_141067c00` - converts `TXA::Animation` to binary writer context.
- `FUN_141067850` - adds writer skeleton nodes and allocates `0x2c` output key
  records.
- `FUN_141068360` - final Workbench binary `.anm` writer; emits IFF-style
  `ANIM`/`SET6` chunks.
- `FUN_141069a50` - retained-key index stream writer.
- `FUN_141069860` - 16-bit quantized float stream writer.
- `FUN_1410879b0` - default/fallback FBX time-mode helper.
- `FUN_141087b40` - converts seconds to FBX-style ticks using
  `DAT_141ca4fa8`.
- `FUN_141087b80` - converts stored ticks back to seconds.
- `FUN_1410884c0` - divides a tick span by the time-mode tick-per-frame value.
- `FUN_1410894e0` - maps FBX time-mode ids to tick-per-frame constants.
- `DAT_141ca4fa8` - tick conversion constant referenced by time helpers; raw
  data observed as `0x422581d1af600000`.
- `FUN_1402ba0a0` - opens an IFF chunk by writing tag and placeholder size.
- `FUN_1402ba320` - closes an IFF chunk and patches the computed size.
- `FUN_1402ba790` - byte-swapped 16-bit IFF size/value patch helper.
- `FUN_1402ba7d0` - byte-swapped 32-bit IFF size/value patch helper.
- `FUN_1402ba8a0` - raw 2-byte payload write helper.
- `FUN_1402ba8d0` - raw 4-byte payload write helper.
- `FUN_1402ba900` - string payload helper; writes raw 4-byte length then bytes.
- `FUN_1402ba1f0` - starts an IFF `FORM` record and writes the form type.
- `FUN_1402badd0` - converts a 3x3 rotation matrix to quaternion in key order
  `x,y,z,w`.
- `FUN_1402bbe70` - quaternion interpolation helper used by ANM rotation key
  reduction.
- `FUN_140e7e780` - FBX/Workbench transform axis/order conversion helper.
- `FUN_140e7e9c0` - extracts scaled 3x4 float matrix data from a transform for
  TXA key writing.
- `FUN_14108dce0` - affine 4x4 matrix inverse helper.
- `FUN_14108d8b0` - affine transform multiply/composition helper.
- `FUN_14108cf60` - 16-double transform copy helper.
- `FUN_140fc9d50` - ANM build/write helper that logs `building ANM...`, creates
  `TXA::Animation`, validates/loads it with `FUN_141057800`, and writes through
  `FUN_141068360`.
- `FUN_1414cec40` - Autodesk/Alias cache XML parser.
- `FUN_1414cf050` - Autodesk cache XML writer.
- `FUN_1414cfd70` - cache channel type string mapper.
- `FUN_140eb8840` - `AnimFileBrowser` constructor/filter setup; includes
  `anm`, `txa`, `age`.
- `FUN_140d5cf10` - TXA-referenced resource/animation commit path.
- `FUN_140fce290` - returns `TXAResourceClassWB`.
- `FUN_140457bd0` - returns `TXAResourceClass`.
- `FUN_1800ab7a0` - DLL animation export save dialog; uses `.anm`/`.txa` filter.
- `FUN_1806d3aa0` - DLL RTM animation reader; checks `RTM_0100`/`RTM_0101`.
- `FUN_1806d4720` - DLL skeleton config parser; reads `skeletonInherit` and
  `skeletonBones`.
- `FUN_18070cda0` - DLL config animation parser; handles `#Animation#` and
  required `keyframe` property.
- `ShowExportDialog` / `0x1800ba700` - exported generic Qt export dialog entry.
- `ShowExportDialogThread` / `0x1800ba990` - exported threaded dialog wrapper.
- `ShowAnimExportDialogThread2` / `0x1800b7b90` - exported animation/TXA dialog
  wrapper; ABI unresolved.
- `FUN_1800ae930` - DLL export loop; consumes host callback object and selected
  export profiles.
- `FUN_1800abcb0` - animation export dialog constructor; stores host object at
  dialog `+0x148`, context at `+0x170`, and calls table/profile setup.
- `FUN_1800afd70` - dialog/profile population boundary called from
  `FUN_1800abcb0`.
- `FUN_1800b2260` - table setup helper; calls host vtable `0x08` for take count
  and `0x18` for take metadata.
- `FUN_1800afc00` - creates/initializes `TXA::Animation` for a take.
- `FUN_1800af0c0` - exports one profile channel/bone into the animation track
  buffer.
- `FUN_1800b1820` - final save boundary; calls `FUN_1807e4a50`,
  `FUN_1807f68b0`, and `FUN_1807f7010`.
- `FUN_1807e4a50` - text/XML-like TXA writer; emits labels such as
  `animation`, `version`, `fps`, `numFrames`, `events`, and `custProp`.
- `FUN_1807f68b0` - builds a skeleton/track export table from
  `TXA::Animation`.
- `FUN_1807f7010` - binary IFF-style final animation writer; starts with tag
  constant `0x4d494e41` and writes chunks including `0x544e5645` and
  `0x50525043`.
- `FUN_1807f8510` - DLL quantized-float stream writer; clamps
  `(value - min) * scale` to `[0, 65535]` and emits 16-bit samples.
- `FUN_1807f8700` - DLL retained-key index stream writer; emits the 16-bit
  frame/index field from writer key offset `+0x28`.
- `FUN_1404305b0` - registers `MetaFileClass` properties. The `Name` property
  is registered as `Name&GUID` with `resourceNamePicker`.
- `FUN_140430460` - constructs an `enf::MetaFile`, installs
  `enf::MetaFile::vftable`, and assigns the `Name` property through
  `DAT_142321660`.
- `FUN_140de0110` - property editor path that parses/formats ResourceName plus
  GUID and displays `"%s (GUID=%s)"`.
- `FUN_140454380` - parses/builds a resource-name object from text containing
  a resource GUID and name.
- `FUN_1404541e0` - deterministic ResourceGUID generator for resource names
  that do not already contain an explicit `{GUID}` prefix. It normalizes path
  separators, uppercases ASCII lowercase letters, runs a 64-bit table update
  through `DAT_141a81160`, and returns the inverted accumulator.
- `FUN_140454dd0` - parses an explicit `{GUID}` prefix into a 64-bit value and
  returns the remaining resource-name pointer.
- `DAT_141a81160` - 2048-byte / 256-entry 64-bit hash table used only by
  `FUN_1404541e0`.
- `FUN_140454640` and `FUN_1404547c0` - ResourceName creation helpers that call
  `FUN_1404541e0` when an explicit `{GUID}` is absent.
- `FUN_140454e90` - returns the stored ResourceGUID pointer/value from a
  resource-name object or a default zero GUID.
- `FUN_140454eb0` - formats a 64-bit ResourceGUID as exactly 16 uppercase hex
  characters.
- `FUN_140f96970` - duplicate data-file diagnostic for two files sharing the
  same GUID.
- `FUN_140fb2140` - ResourceManager constructor path connecting file
  add/delete signals that carry `const enf::ResourceGUID&`.

## Confidence Notes

- confirmed: `.anm` extension validation is in `FUN_140efc710`.
- confirmed: current reader accepts `RTM_0101`; `RTM_0100` is treated as old.
- confirmed: embedded FBX SDK option strings include Autodesk 2016 through old
  FBX 6.0/2006 compatibility labels.
- confirmed: Workbench has a Ghidra-proven external converter path for
  FBX-to-ANM using `FBXConverter.exe -anm -bin -simplename`; evidence is
  `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1033-1098.
- confirmed: Workbench can classify `.fbx` resources as `FBXAnimResourceClass`;
  evidence is `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1949-2029.
- confirmed: Workbench's current FBX animation resource path does not require
  the missing `FBXConverter.exe`; `FBXAnimResourceClassWB` performs in-process
  conversion through `FUN_140fc9fc0` -> `FUN_140e75c10`.
- confirmed: `FUN_140e75c10` reports `Can't find anim take` when the requested
  take name is absent, creates a `TXA::Animation`, stores FPS at offset `0x80`,
  stores frame count at offset `0x84`, appends `.anm`, and calls
  `FUN_141068360`.
- confirmed: `FUN_140e75770` and `FUN_140e78260` sample FBX transforms into
  TXA key records at stride `0x28`, using sample time
  `frameIndex / (frameCount - 1) * duration`.
- confirmed: `FUN_140e78260` stores `EntityPosition` samples into a per-frame
  `0x80` stride matrix array, and `FUN_140e75770` can make root-level node
  transforms relative to that array.
- confirmed: `FUN_141057800` parses TXA through `FUN_141058e60` and validates
  hierarchy through `FUN_1410572d0`.
- confirmed: TXA text grammar callbacks map `version`, `fps`, `numFrames`,
  `tag`, `node`, `nodeDiff`, `keys`, `frame`, `q`, `t`, `s`, `event`, and
  `custProp` into `TXA::Animation`/track/key fields.
- confirmed: TXA key defaults are quaternion `0,0,0,1`, translation `0,0,0`,
  and scale `1,1,1`; both track allocation and parsed frame creation initialize
  keys this way.
- confirmed: `FUN_141067c00` builds the writer context from `TXA::Animation`
  and `FUN_141068360` writes final IFF-style ANM output.
- confirmed: in `FUN_141067c00`, TXA track byte `+0x28` maps directly to writer
  bit `0x1`, while TXA bytes `+0x29..+0x2b` are inverted into writer bits
  `0x2/0x4/0x8`.
- confirmed: `FUN_141068360` writes chunks `ANIM`, `SET6`, `FPS`, `HEAD`,
  `DATA`, optional `EVNT`, and optional `CPRP`.
- confirmed: HTTP call graph proves
  `FUN_140e75770 -> FUN_1410c3840 -> FUN_1411235b0` for FBX transform
  evaluation in the sampler path.
- confirmed: packed chunk constants in `FUN_141068360` are now verified at
  instruction addresses `1410683fe`, `14106843f`, `141068e97`, `141068eca`,
  `141069140`, `1410695c0`, and `1410696e7`.
- confirmed: the `FPS` chunk writes exactly four raw bytes from writer-context
  offset `+0`.
- confirmed: `HEAD` node record emission checks retained translation count,
  retained rotation count, and caller force flag; retained scale count alone is
  not part of the observed emission condition.
- confirmed: `FUN_141069a50` writes retained key indices as 16-bit values, and
  `FUN_141069860` writes quantized floats as clamped 16-bit values.
- confirmed: `EVNT` and `CPRP` counts are written as raw 16-bit values.
- confirmed: event/custom-property strings in `EVNT`/`CPRP` are written as raw
  4-byte length including terminator, followed by that many string bytes; null
  pointers emit length `1` and the empty-string terminator.
- confirmed: writer constants include translation/scale threshold `0.0005`,
  rotation threshold `0.000001`, clamp max `65535.0`, and range guard
  `0.000001`.
- confirmed: `FUN_1402badd0` writes quaternion fields in key order `x,y,z,w`
  from a matrix, and `FUN_1402bbe70` uses shortest-path quaternion interpolation
  for rotation reduction.
- confirmed: Workbench reports embedded `FBX SDK/FBX Plugins version 2016.1.1`
  build `20150824`, and importer paths reject parsed FBX major versions above
  `7`.
- confirmed: HTTP string search finds `2016.1.1 Release (237687)`, `2016.1.1`,
  build `20150824`, unsupported-version strings, and FBX 6 exporter labels.
- confirmed: FBX time helpers map time-mode ids to tick-per-frame constants;
  seconds/ticks conversion references `DAT_141ca4fa8`, and unresolved zero time
  mode falls back to mode `6`.
- confirmed: IFF chunk helpers open chunks with tag + zero size placeholder and
  close chunks by seeking back and patching size; size patch helpers are
  byte-swapped, while generic 2-byte/4-byte payload helpers write raw values.
- confirmed: direct FBX-to-ANM zeroes the translation/scale/rotation reduction
  threshold globals before calling `FUN_141068360(..., 0, 0)`; the TXA helper
  call site calls the same writer with `0, 0` but does not show the zeroing.
- confirmed: TXA exists in Workbench; raw byte search found `.txa` and TXA class
  names, and decompile shows `AnimFileBrowser` filters include `txa`.
- confirmed: TXA tags are parsed/stored, and related callbacks give direct
  semantics for `Scale`, `Coords XZY`, and `SourceName *.p3d`.
- confirmed: direct callers of `FUN_141058640` are `FUN_1410578e0`,
  `FUN_1410643c0`, and `FUN_141064680`; `FUN_141067c00` is not a tag-store
  caller.
- confirmed: focused HTTP decompile shows top-level animation tags are stored
  by `FUN_1410578e0` through `FUN_141058640(param_2 + 8, ...)`, while
  `FUN_141067c00` reads `param_2 + 0x50/+0x5c`, `+0x60/+0x6c`, `+0x70/+0x7c`,
  and `+0x80`, but not `param_2 + 8`.
- confirmed: transform helpers used by FBX conversion include matrix inverse,
  matrix multiply/composition, copy, and scaled 3x4 extraction routines.
- confirmed: `FbxEvaluatorDeepTrace.java` completed on `workbenchApp.exe` and
  saved `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt`; despite stale script compile
  errors, the output contains `SCRIPT COMPLETED` at lines 3818 and 3821.
- confirmed: `FUN_141089440` is raw tick addition and `FUN_141089460` is raw
  tick subtraction.
- confirmed: `FbxEvaluatorCoreTrace.java` completed on `workbenchApp.exe` and
  saved `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt`; the output contains
  `SCRIPT COMPLETED` at lines 1945 and 1948.
- confirmed: `FUN_1410c3840` is the FBX transform evaluator wrapper used by the
  sampler; it obtains an evaluator/cache object and dispatches through
  `FUN_1411235b0`.
- confirmed: `FUN_141090230` is Workbench's FBX scene system-unit conversion
  state handling for this path. The later HTTP pass maps the target
  `DAT_142373c80` to the `Meters` system-unit pair and proves the global-setting
  update/writeback flow.
- confirmed: `TxaWriterLimitsTrace.java` completed on `workbenchApp.exe` and
  saved `ghidra-raw/ghidra-raw-txa-writer-limits.txt`; the output contains
  `SCRIPT COMPLETED` at lines 2981 and 2984.
- confirmed: `FUN_140202210` parses integers with C `strtol` base 10 and
  returns the caller-provided default on null/empty/failed/`errno` parse.
- confirmed: `FUN_140080e60` parses floats with C `strtod`, casts to 32-bit
  float on success, and returns the caller-provided default on null/empty/failed
  parse.
- confirmed: `FUN_141067c00` emits `Skeleton has too much nodes` when
  `FUN_141067850` returns `0xffffffff`; no equivalent explicit range error was
  found for key/event/custom counts before later 16-bit stores/writes.
- confirmed: `dataExporter_v141_x64_RetailDX11.dll` contains an animation export
  save-file filter for `.anm` and `.txa`.
- confirmed: `ShowExportDialog(HWND*)` is a `__cdecl` external export that
  constructs its own `QApplication` and enters a Qt event loop.
- confirmed: local runtime probe loads the DLL and resolves `ShowExportDialog`
  only by decorated name / ordinal `#4`, `ShowExportDialogThread` only by
  decorated name / ordinal `#5`, and `ShowAnimExportDialogThread2` by plain name
  / ordinal `#6`.
- confirmed: runtime probe opens `TXA Export Dialog` through ordinal `#4` after
  setting Qt plugin path/current directory/`qt.conf`.
- confirmed: `FUN_1800ae930` proves real export requires a host callback object
  for takes, key data, cleanup, and differential poses.
- confirmed: `FUN_1800b1820` writes through deeper save helpers after the
  `TXA::Animation` object is populated.
- confirmed: HTTP decompile now proves `FUN_1807f68b0` is the DLL-side
  writer-context builder equivalent to Workbench `FUN_141067c00`.
- confirmed: HTTP decompile now proves `FUN_1807f7010` is the DLL-side binary
  `ANIM`/`SET6` writer equivalent to Workbench `FUN_141068360`.
- confirmed: `FUN_1807f8510` and `FUN_1807f8700` match the Workbench
  quantized-float and retained-index helper behavior.
- confirmed: managed ordinal `#6` empty-host ABI probes crash with
  `0xC0000005` before callback logging, so a complete direct C# call is not
  solved yet.
- confirmed: the animation dialog's pre-export table population reads host
  callback object data before final export; take metadata fields consumed by the
  UI are proven at offsets `0x00`, `0x01`, `0x08`, `0x10`, `0x18`, `0x20`,
  `0x30`, and `0x34`.
- confirmed: the DLL scan found zero `.fbx`/`FBX` byte-string hits, so DLL-side
  FBX involvement is not proven in this pass.
- likely: `FUN_140efc710` is part of Workbench animation save/serialize flow.
- confirmed: DLL final writer `FUN_1807f7010` is parallel to Workbench
  `FUN_141068360`; Workbench remains the primary source for the in-process
  FBX/TXA converter path because it is directly tied to `FBXAnimResourceClassWB`.
- unknown: no Ghidra evidence currently proves TXA tags are copied into or used
  by the final `FUN_141068360` binary writer; current caller evidence makes this
  unlikely for the documented ANM path.
- confirmed: fresh HTTP decompile of `FUN_140e75c10` in
  `ghidra-raw/ghidra-raw-fbx-main-build-decompile-http.txt` proves the in-process
  FBX-to-TXA path activates the selected take, computes duration ticks from
  selected/global time span, stores `durationTicks / ticksPerFrame + 1` at
  `TXA::Animation + 0x84`, samples `EntityPosition`, recursively converts scene
  nodes, writes text TXA through `FUN_141056750`, and optionally writes `.anm`
  with zeroed reduction thresholds.
- confirmed: fresh HTTP vtable scan in
  `ghidra-raw/ghidra-raw-fbx-attribute-type-slot-summary-http.json` and
  `ghidra-raw/ghidra-raw-fbx-geometry-type-slot-summary-http.json` maps the node-attribute
  type slot used by `FUN_140e75770`: `FbxNull -> 1`, `FbxMarker -> 2`,
  `FbxSkeleton -> 3`, `FbxMesh -> 4`, `FbxNurbs -> 5`, `FbxPatch -> 6`,
  `FbxCamera -> 7`, `FbxLight -> 10`, `FbxNurbsCurve -> 13`,
  `FbxNurbsSurface -> 16`, `FbxLODGroup -> 18`, and `FbxLine -> 21`.
- confirmed: therefore the `iVar2 == 4` skip branch in `FUN_140e75770` skips
  `FbxMesh` nodes, not `FbxNull` or `FbxSkeleton`.
- confirmed: fresh HTTP scene-conversion pass in
  `ghidra-raw/ghidra-raw-fbx-scene-conversion-deep-http.txt`,
  `ghidra-raw/ghidra-raw-fbx-system-unit-table-http.txt`,
  `ghidra-raw/ghidra-raw-fbx-system-unit-strings-memory-http.txt`, and
  `ghidra-raw/ghidra-raw-fbx-unit-ratio-helper-http.txt` maps `DAT_142373c80` to the
  `Meters` system-unit pair `(100.0, 1.0)`.
- confirmed: `FUN_140e7daa0` calls
  `FUN_141090230(&DAT_142373c80, scene, &local_res8)` with bytes
  `00 01 01 01 01 01`, then rereads the converted global unit and stores
  `100.0` as the FBX import context scale at offset `+0x58`.
- confirmed: `FUN_140e7e9c0` multiplies output translation by
  `contextScale * DAT_141b79340`; raw memory and instruction xref show
  `DAT_141b79340` is the double value `0.00999999977648258`, so the converted
  meters path uses an effective translation multiplier of approximately `1.0`.
- confirmed: `ghidra-raw/ghidra-raw-fbx-resource-mode-pass-http.txt` records HTTP xrefs to
  `DAT_142321adc` and `DAT_142321ae0`. Each has only the registration write in
  `FUN_1404555f0` and the conversion read in `FUN_140fc9fc0` in this pass,
  proving the current FBX animation resource conversion surface is
  `AnimationName` plus `FPS`.
- confirmed: the same pass rechecked `FUN_140fc9fc0`, `FUN_140e75c10`,
  `FUN_140e75770`, and `FUN_141056750`. The path imports FBX, selects the take,
  builds TXA tracks/keys, writes TXA text through `FUN_141056750`, and does not
  call the TXA event/custom-property store helpers from the FBX sampler.
- likely: additive, partial, IK, and full-body strings found by Workbench string
  scans belong to AnimEditor UI/runtime/plugin-command paths. The scanned anchors
  point to `FUN_140e8fe40` or `FUN_1405d5610`, not to `FUN_140fc9fc0` or
  `FUN_140e75c10`.
- confirmed: `ghidra-raw/ghidra-raw-fbx-txa-text-writer-pass-http.txt` records fresh HTTP
  analysis of `FUN_1410574b0`, `FUN_1410570b0`, `FUN_141056230`,
  `FUN_1410562e0`, `FUN_141055c60`, and `FUN_141055e40`. It proves
  Workbench-style TXA text output uses hierarchical `node`/`nodeDiff`, channel
  tokens from track bytes, contiguous frame range compression, default component
  elision, and `"%.*f"` float formatting with precision `7`.
- confirmed: TXA text range/default comparisons use pow base `10.0` from memory
  `workbenchApp.exe:0x141f859e0`; observed thresholds are translation `10^-7`,
  quaternion `10^-6`, and scale `10^-5`.
- confirmed: `anm/fbx/StalkerSnork_runright.anm` matches
  `anm/fbx/StalkerSnork_runright.optimized.from_txa.anm` exactly:
  `MATCH 13749 bytes`. The local exact/zero-threshold output is `20947` bytes.
- confirmed: `.anm.meta` value `FE542D5525E19BD8` is a Workbench/Enfusion
  `ResourceGUID` stored in `MetaFileClass.Name` as `{GUID}filename`; it is not
  an ANM binary chunk or checksum.
- confirmed: `FUN_140454eb0` formats that GUID representation from a 64-bit
  value into 16 uppercase hex characters.
- confirmed: Workbench resource database code uses ResourceGUID for identity,
  add/delete events, and duplicate-GUID diagnostics.
- confirmed: `FUN_1404541e0` is the ResourceGUID generation algorithm for names
  without explicit `{GUID}`. Reproducing its table/hash logic gives
  `StalkerSnork_runright.anm => FE542D5525E19BD8`.
- confirmed: the algorithm is case-insensitive for ASCII letters and normalizes
  slash/backslash separators. It hashes the resource name, not file contents.

## Reproduction Commands

```powershell
$code = Get-Content -Raw 'ghidra_scripts\AnmWorkbenchExactStrings.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\DataExporterUsageResearch.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\DataExporterCallableSurface.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\DataExporterAnmResearch.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\DataExporterFunctionDump.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\AnmWorkbenchByteNeedleSearch.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\AnmWorkbenchTxaTargets.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```

```powershell
$code = Get-Content -Raw 'ghidra_scripts\AnmWorkbenchTargetFunctions.java'
$body = @{ code = $code } | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'http://127.0.0.1:8089/run_script_inline' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing
```
