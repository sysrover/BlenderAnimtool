# Workbench ANM Research

This folder records a Ghidra-only reverse pass on `workbenchApp.exe` and the
loaded `dataExporter_v141_x64_RetailDX11.dll` for DayZ Workbench animation
import/export behavior.

Codex Diff editor-decoration test line.

Primary binary:

`C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench\workbenchApp.exe`

## Files

- `ghidra-raw/` - raw Ghidra HTTP, script, xref, memory, and decompile dumps.
  Put new raw pulls here.
- `workbench-anm-pipeline.md` - Workbench UI and serializer/reader paths found so far.
- `fbx-import.md` - FBX SDK and Workbench FBX option evidence.
- `fbx-sdk-test.md` - downloaded Autodesk FBX SDK 2016.1 VS2015 validation,
  install layout, load test, and converter build notes.
- `fbx-sdk-reference.md` - official Autodesk FBX 2016 SDK reference notes for
  supported FBX versions, scene elements, and practical converter API direction.
- `txa-import.md` - TXA search result and current gap.
- `dataexporter-findings.md` - DLL-side animation export dialog and RTM/config
  animation evidence.
- `dataexporter-usage.md` - what the DLL exports and how it can currently be
  called safely from an external host.
- `dataexporter-export-boundary.md` - decompiled export loop showing the host
  callback interface required for real TXA/ANM export.
- `dataexporter-runtime-test.md` - local C# runtime probe results for loading
  and calling the DLL exports.
- `anm-writer-format.md` - Current `.anm`/animation binary format facts from decompile.
- `converter-implementation-spec.md` - Implementation-facing summary for
  building standalone FBX->ANM and TXA->ANM converters.
- `converter-open-gaps.md` - remaining uncovered or validation-only gaps before
  claiming a fully compatible converter.
- `workbench-golden-pair-analysis.md` - parsed Workbench-generated TXA/ANM pair
  from `anm/txa_anm`, used to validate the Ghidra-derived writer shape.
- `txa-anm-prototype-status.md` - current standalone TXA->ANM converter CLI
  result, supported TXA surface, and golden-pair byte-identity status.
- `dayzdiag-anm-reader.md` - DayZDiag runtime `ANIM/SET6` reader check,
  showing the game reads retained/quantized streams and does not apply writer
  reduction tolerances while loading.
- `ghidra-evidence-log.md` - Raw evidence index and confidence labels.
- `ghidra-raw/ghidra-raw-exact-strings.txt` - Raw Ghidra exact string/xref/decompile output.
- `ghidra-raw/ghidra-raw-target-functions.txt` - Raw Ghidra target function decompile output.
- `ghidra-raw/ghidra-raw-byte-needle-search.txt` - Raw Ghidra memory byte search output.
- `ghidra-raw/ghidra-raw-txa-targets.txt` - Raw Ghidra TXA-referenced function output.
- `ghidra-raw/ghidra-raw-project-programs.txt` - Ghidra project program listing.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` - Raw Ghidra DLL string/byte scan.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` - Raw Ghidra DLL decompiler dump.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` - Raw Ghidra DLL export/decompile dump.
- `ghidra-raw/ghidra-raw-dataexporter-callable-surface.txt` - Raw Ghidra callable surface
  and TXA dialog detail dump.
- `ghidra-raw/ghidra-raw-dataexporter-caller-search.txt` - Raw Ghidra project-wide caller
  and RTTI/string search for dataExporter/ShowAnim/IAnimExporter names.
- `ghidra-raw/ghidra-raw-dataexporter-save-helpers.txt` - Raw Ghidra decompile for TXA
  text writer and final save helpers.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-disasm.txt` - Raw ordinal `#6` instruction
  dump.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` - Raw deeper ordinal `#6`,
  Qt application, worker, and animation dialog constructor dump.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` - Raw dialog population trace
  showing pre-export host callbacks and take metadata layout.
- `ghidra-raw/ghidra-raw-fbx-anim-resource-trace.txt` - Raw Ghidra trace for
  `FBXAnimResourceClass`/`FBXAnimResourceClassWB` symbols and constructors.
- `ghidra-raw/ghidra-raw-fbx-anim-vtable-trace.txt` - Raw Ghidra vtable dump for FBX
  resource classes.
- `ghidra-raw/ghidra-raw-fbx-anim-methods-trace.txt` - Raw Ghidra method trace for
  `FBXAnimResourceClassWB` conversion methods.
- `ghidra-raw/ghidra-raw-fbx-anim-convert-helpers.txt` - Raw Ghidra trace for FBX
  animation conversion helpers.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` - Raw decompile for the core
  FBX-to-TXA and TXA-to-ANM Workbench functions.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` - Raw decompile for ANM writer packing,
  IFF chunk helpers, TXA track allocation, and parser validation helpers.
- `ghidra-raw/ghidra-raw-txa-parser-callbacks.txt` - Raw decompile for TXA text parser
  callback vtables: animation, node, keys, frame, events, and custom
  properties.
- `ghidra-raw/ghidra-raw-txa-parser-strings.txt` - Raw string probe for TXA parser DAT
  labels such as `fps`, `tag`, `node`, `keys`, `t`, `q`, and `s`.
- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` - Raw constants and transform/
  quaternion helper decompile for writer thresholds and FBX transform mapping.
- `ghidra-raw/ghidra-raw-txa-storage-helpers.txt` - Raw TXA storage helpers for events,
  custom properties, tags, track lookup, and key-buffer resize.
- `ghidra-raw/ghidra-raw-deep-gap-trace.txt` - Raw follow-up trace for writer call sites,
  threshold globals, `FUN_141067c00` flags, and event/custom copies.
- `ghidra-raw/ghidra-raw-txa-tag-deep.txt` - Raw follow-up trace for tag-specific parser
  callbacks and text tag writing.
- `ghidra-raw/ghidra-raw-anim-set6-trace.txt` - Raw defined-string/decompile trace
  separating RTM string reader evidence from packed `ANIM`/`SET6` writer
  constants.
- `ghidra-raw/ghidra-raw-writer-callsite-deep.txt` - Raw instruction/decompile trace for
  writer chunk constants, `FUN_1402ba0a0`/`FUN_1402ba320` callsites, and packing
  helpers.
- `ghidra-raw/ghidra-raw-txa-tag-usage-exhaustive.txt` - Raw exhaustive caller trace for
  TXA tag store/write helpers and final writer boundaries.
- `ghidra-raw/ghidra-raw-fbx-transform-helper-deep.txt` - Raw decompile for remaining FBX
  transform/matrix helper routines.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` - Raw decompile for FBX time-base helpers
  and low-level IFF/integer/string write primitives.
- `ghidra-raw/ghidra-raw-writer-byte-level.txt` - Raw instruction/decompile pass for
  `FUN_141068360` byte-level `FPS`, `HEAD`, `DATA`, `EVNT`, and `CPRP` writes.
- `ghidra-raw/ghidra-raw-http-accelerated-pass.txt` - Raw direct HTTP MCP string-anchor,
  xref, and batch-decompile pass over Workbench and dataExporter candidates.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt` - Raw direct HTTP MCP decompile
  of the DLL export/save boundary, TXA writer, writer-context builder, final
  binary writer, and track/key construction helpers.
- `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt` - Raw direct HTTP MCP
  decompile of DLL quantized-float, retained-index, and IFF primitive helpers.
- `ghidra-raw/ghidra-raw-missing-parts-http.txt` - Raw direct HTTP MCP pass for remaining
  gaps: tag-store callers, writer context, final writer, dataflow attempts,
  string anchors, and FBX evaluator call graph.
- `ghidra-raw/ghidra-raw-missing-parts-focused-http.txt` - Cleaner HTTP decompile pass for
  tag callers, frame/event/custom parser callbacks, writer limit helpers, and
  FBX evaluator wrapper.
- `ghidra-raw/ghidra-raw-fbx-strings-http.txt` - HTTP string searches for FBX SDK version,
  unsupported-version messages, FBX 6 exporter labels, and count-limit strings.
- `ghidra-raw/ghidra-raw-fbx-main-build-decompile-http.txt` - fresh HTTP decompile of the
  main `FUN_140e75c10` FBX take-to-TXA/ANM build helper.
- `ghidra-raw/ghidra-raw-fbx-missing-parts-decompile-http.txt` - fresh HTTP decompile of
  recursive FBX node conversion, `EntityPosition`, transform reorder/extraction,
  evaluator boundary, and node helpers.
- `ghidra-raw/ghidra-raw-fbx-node-helper-decompile-http.txt` - node parent/child/name and
  node-attribute helper decompile.
- `ghidra-raw/ghidra-raw-fbx-nodeattribute-registration-http.txt` - FBX SDK class
  registration decompile around `FbxNodeAttribute`, `FbxNull`, `FbxSkeleton`,
  and geometry classes.
- `ghidra-raw/ghidra-raw-fbx-attribute-type-slot-summary-http.json` and
  `ghidra-raw/ghidra-raw-fbx-geometry-type-slot-summary-http.json` - vtable slot `+0xb8`
  return-value mapping proving skipped type `4` is `FbxMesh`.
- `ghidra-raw/ghidra-raw-fbx-time-take-helpers-http.txt` - time/take helper decompile for
  tick conversion, time mode fallback, take span lookup, and duration math.
- `ghidra-raw/ghidra-raw-fbx-scene-conversion-deep-http.txt` - Workbench FBX post-import
  system-unit conversion helper decompile.
- `ghidra-raw/ghidra-raw-fbx-system-unit-table-http.txt` - raw memory for the system-unit
  double-pair table at `0x142373c50`.
- `ghidra-raw/ghidra-raw-fbx-system-unit-strings-memory-http.txt` - unit aliases/labels
  proving the table maps to millimeters, centimeters, meters, inches, feet,
  yards, miles, and decimeters.
- `ghidra-raw/ghidra-raw-fbx-scene-conversion-property-helpers-http.txt` - decompile of
  property conversion helpers gated by Workbench's six conversion flag bytes.
- `ghidra-raw/ghidra-raw-fbx-unit-ratio-helper-http.txt` - unit conversion ratio helper
  used by the system-unit path.
- `ghidra-raw/ghidra-raw-fbx-resource-mode-pass-http.txt` - HTTP xrefs and function
  analysis proving `FBXAnimResourceClassWB` conversion reads `AnimationName` and
  `FPS`, and separating AnimEditor additive/IK/full-body strings from the
  FBX-to-TXA conversion path.
- `ghidra-raw/ghidra-raw-fbx-txa-text-writer-pass-http.txt` - HTTP function analysis of
  Workbench TXA text output after FBX conversion: `node`/`nodeDiff`, `keys`,
  frame range compression, default component elision, and float formatting.
- `ghidra-raw/ghidra-raw-metafile-guid-pass-http.txt` - HTTP evidence for Workbench
  `.meta` `Name&GUID` handling, `ResourceGUID` formatting, resource database
  duplicate-GUID diagnostics, and `StalkerSnork_runright` Workbench ANM
  byte-validation.
- `ghidra-raw/ghidra-raw-slerp-threshold-http.txt` - HTTP memory read proving
  `FUN_1402bbe70` uses float `0.999` as the quaternion slerp linear-fallback
  cutoff.
- `ghidra-raw/ghidra-raw-dayzdiag-anm-reader.txt` - HTTP/decompiler dump for
  `DayZDiag_x64.exe` `ANIM/SET6` reader functions.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-nodediff.txt` - focused DayZDiag HTTP/decompiler
  dump for `CPRP`, `EVNT`, and `HEAD` flag-byte handling.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-scan.txt` - broad DayZDiag instruction scan for
  runtime track flag offset `+0x64`.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-lowbit-scan.txt` - early noisy low-bit scan for
  `+0x64`; kept as raw evidence but superseded by the exact scan below.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-candidates-decompile.txt` - decompile of the
  strongest `+0x64` track-reader candidates.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-bit1-exact.txt` - exact scan for `+0x64`
  instructions with immediate `0x01`.
- `ghidra-raw/ghidra-raw-dayzdiag-bit1-candidate-decompile.txt` - decompile proving the
  exact `0x01` candidates are outside the ANM reader/sampler path.
- `ghidra-raw/ghidra-raw-dayzdiag-sampler-xrefs.txt` - xrefs to the runtime animation
  sampler functions.
- `ghidra-raw/ghidra-raw-dayzdiag-sampler-d3e40-decompile.txt` and
  `ghidra-raw/ghidra-raw-dayzdiag-sampler-d4250-decompile.txt` - focused decompile of the
  interpolation and non-interpolation sampler paths.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-offset-use-scan.txt` - broad DayZDiag offset scan
  for CPRP table/count fields `+0x178/+0x182`.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-usage-candidates.txt` - CPRP apply/init/copy/free
  candidate decompile, including `FUN_1400d53b0`.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-value-parser.txt` - comma-separated three-float
  parser used by `entitypos` and `entityrot`.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-apply-xrefs.txt` and
  `ghidra-raw/ghidra-raw-dayzdiag-cprp-apply-caller.txt` - proof that CPRP apply runs
  after ANM load.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-entityposrot-use-scan.txt` and
  `ghidra-raw/ghidra-raw-dayzdiag-cprp-runtime-entityposrot.txt` - runtime use of applied
  `entitypos`/`entityrot` fields.

## Current Status

- 10-pass Ghidra digging status for this continuation:
  1. tag storage callers and semantics traced.
  2. writer call parameters and threshold globals traced.
  3. `ANIM`/`SET6` packed writer constants rechecked against defined strings.
  4. RTM reader path separated from the `ANIM`/`SET6` writer path.
  5. `EntityPosition` sampling array traced.
  6. FBX transform component reorder and quaternion extraction traced.
  7. FBX take/time/FPS sampling behavior rechecked against `FUN_140e75c10`.
  8. direct FBX writer reduction-zeroing behavior documented.
  9. event/custom-property copy and chunk output path rechecked.
  10. implementation spec and open questions consolidated.
- extra Ghidra digging status after that:
  11. packed chunk constants confirmed at instruction addresses in
      `FUN_141068360`.
  12. `FUN_1402ba0a0`/`FUN_1402ba320` writer call windows captured.
  13. tag store helper callers enumerated exhaustively.
  14. tag text writer helper callers enumerated exhaustively.
  15. `FUN_141067c00` confirmed outside the tag-copy path.
  16. `FUN_14108dce0` identified as a 4x4 matrix inverse helper.
  17. `FUN_14108d8b0` identified as a 4x4 transform multiply/composition helper.
  18. `FUN_140e7e9c0` identified as the helper extracting a 3x4 float matrix for
      TXA quaternion/translation writing.
- further deep-pass status:
  19. IFF open/close helpers resolved: chunk open writes tag plus zero size,
      chunk close seeks back and patches size.
  20. IFF size patch helpers identified as byte-swapping 16-bit/32-bit sizes.
  21. raw 16-bit/32-bit payload write helpers identified separately.
  22. TXA track creation default key values documented.
  23. TXA `frame` parser default/copy/range behavior documented from decompile.
  24. FBX time-mode fallback and ticks-per-second conversion helpers documented.
  25. `FPS` chunk payload instruction-traced as exactly four raw bytes from
      writer context offset `+0`.
  26. `EVNT` and `CPRP` payloads instruction-traced as 16-bit count followed by
      raw 4-byte string lengths and bytes.
  27. `HEAD` node emission condition narrowed: retained translation or retained
      rotation count, or caller force flag; retained scale alone does not pass
      the observed emission branch.

- confirmed: Ghidra MCP executed against loaded `workbenchApp.exe`, image base
  `0x140000000`.
- confirmed: Workbench has a `.anm` path validator in `FUN_140efc710`.
- confirmed: Workbench has animation binary readers accepting `RTM_0100` and
  `RTM_0101` in `FUN_140b896c0`.
- confirmed: Workbench embeds FBX SDK code/options, including 2016, 2014/2015,
  2013, 2012, 2011, 2010, 2009, and 2006 compatibility labels.
- confirmed: Workbench contains an FBX-to-ANM command path in
  `FUN_140ebdce0`: it formats and executes
  `FBXConverter.exe -anm -bin -simplename "<input.fbx>" "<destination>/<file>"`.
- confirmed: Workbench can register `.fbx` files as `FBXAnimResourceClass`
  after an ambiguity prompt asking model versus animation.
- confirmed: Workbench also has an in-process `FBXAnimResourceClassWB`
  conversion path. It uses `AnimationName` default `Take 001`, `FPS` default
  `30`, builds a `TXA::Animation`, appends `.anm`, and writes through
  `FUN_141068360`.
- confirmed: the FBX conversion algorithm samples selected take transforms into
  `TXA::Animation` tracks. Track names are sanitized, root is named
  `Scene_Root`, `EntityPosition` is special-cased, key records are stride
  `0x28`, and sample time is
  `frameIndex / (frameCount - 1) * duration`.
- confirmed: latest HTTP mode scan shows the FBX animation resource conversion
  property surface is `AnimationName` plus `FPS`; additive, partial, IK, and
  full-body signs found in Workbench are AnimEditor/runtime/plugin strings, not
  branches in `FUN_140fc9fc0` or `FUN_140e75c10`.
- confirmed: latest TXA text writer pass shows FBX-generated TXA is compacted by
  Workbench text writer rules: `keys t q s`, frame ranges for adjacent equal
  keys, default t/q/s elision, float `"%.*f"` precision `7`, and trailing-zero
  trimming.
- confirmed: `anm/fbx/StalkerSnork_runright.fbx` and
  `anm/fbx/StalkerSnork_runright.txa` provide a real Workbench FBX->TXA
  validation pair. The FBX is binary 7.4; the meta registers
  `FBXAnimResourceClass` without explicit `AnimationName`/`FPS`; the TXA uses
  default `#fps 30`, `#numFrames 25`, 78 nodes, and Workbench-style compacted
  `$keys t q s` output.
- confirmed: `anm/fbx/StalkerSnork_runright.anm` is now available as the
  Workbench-generated ANM for that pair. It matches the local optimized
  TXA->ANM output byte-for-byte: `MATCH 13749 bytes`. The exact/zero-threshold
  local mode is larger at `20947` bytes, so this Workbench artifact follows the
  optimized TXA-style writer behavior.
- confirmed: `StalkerSnork_runright.anm.meta` uses
  `Name "{FE542D5525E19BD8}StalkerSnork_runright.anm"`. Ghidra evidence shows
  this is a 64-bit Enfusion `ResourceGUID` in the `MetaFileClass.Name`
  `Name&GUID` property, not a field inside the ANM payload.
- confirmed: Workbench uses `ResourceGUID` for resource database identity and
  duplicate detection; `FUN_140f96970` shows a duplicate-GUID dialog when two
  files share one GUID.
- confirmed: ResourceGUID generation is deterministic when no explicit
  `{GUID}` is supplied. `FUN_1404541e0` hashes the normalized resource name with
  the 256-entry table at `DAT_141a81160`; reproducing it gives
  `StalkerSnork_runright.anm => FE542D5525E19BD8`.
- confirmed: `FE542D5525E19BD8` is not derived from the full local path, FBX,
  TXA, or ANM bytes.
- confirmed: TXA-to-ANM uses `FUN_141057800` to parse TXA into
  `TXA::Animation`, `FUN_141067c00` to build a binary writer context, and
  `FUN_141068360` to emit IFF-style `ANIM`/`SET6` output.
- confirmed: the TXA parser grammar now covers `animation`, `version`, `fps`,
  `numFrames`, `tag`, `node`, `nodeDiff`, `keys`, `frame`, `q`, `t`, `s`,
  `events`, `event`, `custProps`, and `custProp`.
- confirmed: TXA storage layouts for events (`0x20` stride), custom properties
  (`0x10` stride), tracks, tags, and key-buffer resize are now documented.
- confirmed: `FUN_141068360` writes `FPS`, `HEAD`, `DATA`, optional `EVNT`,
  and optional `CPRP` chunks, with 16-bit retained-key indices and 16-bit
  quantized float streams.
- confirmed: writer constants are now extracted: translation/scale reduction
  threshold `0.0005`, rotation threshold `0.000001`, quantization clamp
  `65535.0`, range guard `0.000001`, and slerp near-equal cutoff `0.999`.
- confirmed: the standalone `tools/TxaAnmPrototype` TXA -> ANM writer now
  produces byte-identical copies of all currently available Workbench golden
  ANMs: `p_2hd_cro_interact_out` in optimized mode, plus
  `newtest/stand_turn_rs_90` and `newtest/11/stand_walk_fwd` in
  exact/zero-tolerance mode.
- confirmed: direct FBX-to-ANM zeroes the three reduction threshold globals
  immediately before `FUN_141068360`; the TXA helper call site does not show
  that zeroing.
- confirmed: `FUN_141067c00` maps TXA track flag `+0x28` directly to writer bit
  `0x1`, and inverts TXA bytes `+0x29..+0x2b` into writer bits `0x2/0x4/0x8`.
- confirmed: `EntityPosition` is sampled into a `0x80` stride per-frame
  transform array and can be used to make root-level FBX nodes relative to
  entity motion during `FUN_140e75770`.
- confirmed: TXA tag storage is traced, and related parser callbacks interpret
  `Scale`, `Coords XZY`, and `SourceName *.p3d`.
- confirmed: the only direct callers of `FUN_141058640` found in this pass are
  `FUN_1410578e0`, `FUN_1410643c0`, and `FUN_141064680`; the binary writer
  context builder `FUN_141067c00` is not a tag-store caller.
- confirmed: TXA newly allocated key records default to quaternion
  `0,0,0,1`, translation `0,0,0`, and scale `1,1,1`.
- confirmed: `FUN_141087b40` converts seconds to FBX ticks with rounding, and
  `FUN_141087b80` converts ticks back to seconds using constant
  `0x422581d1af600000`.
- confirmed: the newest FBX evaluator pass shows Workbench delegates transform
  evaluation through `FUN_1410c3840` into embedded evaluator dispatch
  `FUN_1411235b0`; the converter should use SDK evaluator-compatible global
  transforms, then apply Workbench's post-processing.
- confirmed: the latest FBX node-attribute vtable pass maps the recursive
  sampler's skipped type value `4` to `FbxMesh`; `FbxNull` returns `1` and
  `FbxSkeleton` returns `3` from the same vtable slot.
- confirmed: the latest FBX build pass translates `FUN_140e75c10` frame-count
  logic as `durationTicks / ticksPerFrame + 1`, with take activation before
  sampling and fallback to global scene time span when take span lookup fails.
- confirmed: the latest scene-conversion pass maps `DAT_142373c80` to the
  `Meters` system-unit pair `(100.0, 1.0)`. Workbench calls
  `FUN_141090230(&DAT_142373c80, scene, flags)` after FBX import with flags
  bytes `00 01 01 01 01 01`, stores context scale `100.0`, and
  `FUN_140e7e9c0` applies translation multiplier `contextScale * 0.01`.
- confirmed: the newest TXA limit pass shows integer parser helper
  `FUN_140202210` uses `strtol` base 10 and float helper `FUN_140080e60` uses
  `strtod`; both return caller defaults on parse failure.
- confirmed: the observed TXA callbacks check enough parameters but do not show
  semantic range checks for `fps`, `numFrames`, frame ranges, or float vector
  magnitudes.
- confirmed: `FUN_141067c00` reports `Skeleton has too much nodes` if writer
  node creation fails, while frame/key/event/custom counts are later stored or
  written through 16-bit fields.
- confirmed: FBX SDK/plugin version is `2016.1.1` build `20150824`; importer
  paths reject parsed FBX major versions above `7`.
- confirmed: raw memory search finds `.txa`, `txa`, and `TXA` byte strings,
  including a `.txa` hit referenced by `FUN_140d5cf10`.
- confirmed: `FUN_140eb8840` configures the animation file browser filter list
  with `anm`, `txa`, and `age`.
- confirmed: Workbench has `TXAResourceClass` and `TXAResourceClassWB` class
  name paths.
- confirmed: the loaded `dataExporter_v141_x64_RetailDX11.dll` contains
  `AnimExportDialog`, `TXAExportDialog`, exported dialog entry names, and a save
  filter `Anm files (*.anm *.txa);;All files (*.*)`.
- confirmed: the DLL exports `ShowExportDialog`, `ShowExportDialogThread`, and
  `ShowAnimExportDialogThread2`; only `ShowExportDialog(HWND*)` is currently
  safe enough to call as an external experiment.
- confirmed: runtime probe loads the DLL and resolves ordinals `#4`, `#5`, and
  `#6`.
- confirmed: after configuring Qt plugin discovery to
  `Bin\Workbench\platforms`, ordinal `#4` opens the `TXA Export Dialog`.
- confirmed: the DLL's actual export loop is `FUN_1800ae930`; it requires a
  host callback object for takes, key data, cleanup, and differential poses.
- confirmed: `FUN_1800b1820` is the DLL-side final save boundary and calls
  `FUN_1807e4a50`, `FUN_1807f68b0`, and `FUN_1807f7010`.
- confirmed: HTTP decompile now proves `FUN_1807f68b0` and `FUN_1807f7010`
  are DLL-side equivalents of Workbench `FUN_141067c00` and `FUN_141068360`:
  they copy the same `TXA::Animation` offsets/strides, emit `ANIM`/`SET6`,
  and write `FPS`, `HEAD`, `DATA`, `EVNT`, and `CPRP`.
- confirmed: DLL helper `FUN_1807f8510` quantizes float streams as
  `clamp((value - min) * scale, 0, 65535)` into 16-bit samples, and
  `FUN_1807f8700` writes retained frame indices from writer-key offset
  `+0x28`; both are called only by `FUN_1807f7010` in the analyzed xrefs.
- confirmed: the C# probe now implements experimental ordinal `#6` empty-host
  modes, but all tested variants crash with `0xC0000005` before callback
  logging.
- confirmed: the ordinal `#6` animation dialog constructor stores the host
  object at dialog offset `+0x148`; the population helper calls host vtable
  offset `0x08` for take count and `0x18` for take metadata before export.
- confirmed: take metadata consumed by the animation dialog includes state
  bytes at offsets `0x00`/`0x01`, C strings at `0x08`/`0x10`/`0x18`/`0x20`,
  and optional frame integers at `0x30`/`0x34`.
- confirmed: the DLL contains RTM animation reader evidence for `RTM_0100` and
  `RTM_0101`, plus skeleton/keyframe validation paths.
- confirmed: the DLL fast byte scan found no `.fbx`, `FBX`,
  `Autodesk_Cache_File`, or `Alias_Cache_File` hits.
- confirmed: HTTP call-graph path search proves the FBX sampler reaches the
  evaluator in exactly this path:
  `FUN_140e75770 -> FUN_1410c3840 -> FUN_1411235b0`.
- confirmed: focused HTTP decompile shows top-level TXA `tag` stores through
  `FUN_1410578e0 -> FUN_141058640(param_2 + 8, ...)`, while
  `FUN_141067c00` reads FPS, tracks, events, and custom properties but not that
  tag list.
- confirmed: HTTP string search found `Skeleton has too much nodes` as the only
  relevant ANM writer count-style error in the searched terms; `65535` matches
  unrelated static-array/reference strings, not the ANM writer.
- unknown: no Ghidra evidence currently proves TXA tags are copied into or used
  by the final `FUN_141068360` `ANIM`/`SET6` writer.
- unknown: without byte-level validation against Workbench output, the research
  is not honestly "100%" implementation-certified, even though the main static
  algorithms are now bounded.

## Latest Raw Evidence

- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt`: deep FBX import, take, node recursion,
  `EntityPosition`, and tick helper evidence.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt`: evaluator wrapper, scene conversion,
  parent/take helpers, and transform component extraction evidence.
- `ghidra-raw/ghidra-raw-txa-writer-limits.txt`: TXA numeric parse helpers, track/key
  allocation behavior, writer-context node overflow, and 16-bit writer field
  evidence.
- `ghidra-raw/ghidra-raw-http-accelerated-pass.txt`: HTTP MCP string anchors and batch
  decompile for `.anm`, `.txa`, `.fbx`, Workbench writer functions, and
  dataExporter save candidates.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: confirms DLL
  `FUN_1800b1820 -> FUN_1807e4a50/FUN_1807f68b0/FUN_1807f7010` save chain.
- `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt`: confirms DLL
  quantized-float, retained-index, and IFF primitive helper behavior.
- `ghidra-raw/ghidra-raw-missing-parts-focused-http.txt`: confirms top-level tag storage
  offset, tag-special-callback behavior, TXA frame/event/custom parsing, writer
  helper behavior, and evaluator wrapper xrefs/callees.
- `ghidra-raw/ghidra-raw-fbx-strings-http.txt`: confirms FBX SDK `2016.1.1`/`20150824`,
  FBX 6 export labels, unsupported-version strings, and absence of ANM writer
  `65535` limit strings in that string search.
