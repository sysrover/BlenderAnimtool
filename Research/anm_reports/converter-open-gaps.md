# Converter Open Gaps

Date: 2026-05-17

This file lists what is still not covered enough to claim a 100% finished
FBX -> TXA -> ANM converter. As of the latest pass, TXA -> ANM core output is
byte-identical for all currently available Workbench golden pairs; remaining
gaps are mostly FBX import/sampling and rare TXA edge-case validation.

Codex Diff accept-file workflow test.
Second Codex Diff in-editor accept test.
Third Codex Diff CodeLens visibility test.

## TXA -> ANM Status

- `confirmed for optimized mode`: Workbench-generated golden pair
  `anm/txa_anm/p_2hd_cro_interact_out.txa` and
  `anm/txa_anm/p_2hd_cro_interact_out.anm` converts byte-identically with
  `--mode optimized`.
- `confirmed for exact mode`: Workbench-generated golden pair
  `anm/txa_anm/newtest/stand_turn_rs_90.txa` and
  `anm/txa_anm/newtest/stand_turn_rs_90.anm` converts byte-identically with
  `--mode exact`.
- `confirmed for exact mode`: Workbench-generated golden pair
  `anm/txa_anm/newtest/11/stand_walk_fwd.txa` and
  `anm/txa_anm/newtest/11/stand_walk_fwd.anm` converts byte-identically with
  `--mode exact`; optimized mode does not match this pair.
- `confirmed`: `EVNT` event output is now byte-validated by the `newtest` pair,
  including same-frame reverse insertion ordering, and by the 50-frame
  `stand_walk_fwd` pair.
- `confirmed from Ghidra, still needs rare-case byte samples`: `CPRP`,
  `nodeDiff`, and unusual `keys t`/`keys q`/`keys s` combinations are covered by
  parser/writer decompile evidence and implemented, but do not yet have
  dedicated golden-pair byte tests.

## ANM Writer Gaps

- `unknown`: TXA tags are parsed and stored, but no Ghidra evidence proves they
  are copied into or used by the final `ANIM/SET6` writer.
- `unknown`: overflow behavior for frame/key counts, event counts,
  custom-property counts, and node-name lengths is not fully proven. Ghidra shows
  several fields narrow to `uint16` or `uint8`, but only the skeleton-node count
  has a clear error string: `Skeleton has too much nodes`.
- `confirmed for one golden pair`: retained-key reduction, quantization,
  `HEAD`, and `DATA` now byte-match Workbench for
  `p_2hd_cro_interact_out.txa`.
- `implemented, partly validated`: event chunks are byte-validated by two
  exact-mode `newtest` pairs; custom-property chunks and less common TXA flag
  combinations are Ghidra-confirmed but still need targeted golden-file byte
  comparison.
- `confirmed by golden pair`: Workbench output uses `FORM` with form type
  `ANIM`, then nested `SET6`, with big-endian chunk sizes and little-endian
  payload fields in the observed `FPS` and `HEAD` records.

## FBX Import/Sampling Gaps

- `unknown`: exact Autodesk FBX SDK `2016.1.1` runtime has not been recovered as
  a standalone SDK. Workbench embeds `2016.1.1 Release (237687)` build
  `20150824`; the installed public SDK is `2016.1.0`.
- `needs validation`: SDK `2016.1.0` evaluator output should be compared against
  Workbench on a small FBX with known animation. It is probably close, but not
  proven identical to Workbench's embedded `2016.1.1`.
- `confirmed`: the Workbench in-process `FBXAnimResourceClassWB` conversion path
  reads only `AnimationName` and `FPS` resource properties before calling
  `FUN_140e75c10`. The latest mode-string pass found additive/partial/IK/
  full-body signs in AnimEditor/runtime/plugin areas, not in the FBX-to-TXA
  conversion helper.
- `confirmed`: the FBX node-attribute type value `4` skipped by
  `FUN_140e75770` is `FbxMesh`. The HTTP vtable pass maps `FbxMesh` slot
  `+0xb8` to return `4`; `FbxNull` returns `1`, `FbxSkeleton` returns `3`.
- `implemented recipe, needs validation`: `EntityPosition` relative-root
  handling is now translated from decompile into an implementation recipe, but
  should still be tested with an FBX that has and does not have that node.
- `implemented recipe, needs validation`: axis/unit conversion via
  `FUN_141090230` is now translated into an implementation recipe. Workbench
  converts imported scenes to its `Meters` system-unit pair `(100.0, 1.0)`,
  passes conversion flags `00 01 01 01 01 01`, stores context scale `100.0`,
  then TXA translation extraction multiplies by `contextScale * 0.01`, giving
  approximately `1.0` for the converted meters path. This still needs a
  controlled FBX comparison against Workbench output.
- `confirmed`: Workbench TXA text output after FBX conversion is now bounded:
  hierarchical `node`/`nodeDiff`, `keys t q s`, contiguous frame-range
  compression, default t/q/s elision, float `"%.*f"` precision `7`, and trailing
  zero trimming are documented from `FUN_1410574b0`, `FUN_1410570b0`, and
  `FUN_141055c60`.
- `validation sample available`: `anm/fbx/StalkerSnork_runright.fbx` and
  `anm/fbx/StalkerSnork_runright.txa` are a real Workbench FBX->TXA pair. The
  FBX is binary 7.4, the meta uses `FBXAnimResourceClass` without explicit
  `AnimationName`/`FPS`, and the TXA confirms default `#fps 30` and
  `#numFrames 25`.
- `confirmed from sample, aligned with Ghidra`: the sample TXA uses hierarchical
  `$node`, `$keys t q s`, frame-range compression, and default component
  elision. The lowercase `entityposition` node appears to be a normal node, not
  the exact-case `EntityPosition` special branch seen in `FUN_140e75c10`.

## TXA Parser Gaps

- `mostly covered`: TXA grammar, key defaults, range-copy, events,
  custom properties, numeric parsing, and hierarchy validation are covered.
- `unknown`: semantic use of tags such as `Scale`, `Coords XZY`, and
  `SourceName *.p3d` outside the final ANM writer remains unclear.
- `needs validation`: parser behavior for malformed input, negative frames,
  out-of-range ranges, duplicate node names, and missing `fps`/`numFrames` should
  be tested if we want Workbench-compatible diagnostics.

## Build/Tooling Gaps

- `missing locally`: no C++ compiler was found on PATH (`cl`, `cmake`,
  `msbuild`, and `vswhere` were not available), so the installed FBX SDK has not
  been compile-tested here.
- `needed`: choose converter implementation language and FBX SDK binding path.
  Practical options are:
  - C++ executable linked to Autodesk FBX SDK.
  - C# application calling a native C++ bridge around FBX SDK.
  - C# for TXA/ANM only, with FBX conversion delegated to a native helper.

## What Is Covered Enough To Start Implementation

- TXA text parser shape and internal `TXA::Animation` model. The golden sample
  uses `$` block commands and `#` value directives, e.g. `$animation`, `$node`,
  `$keys`, `$frame`, `#fps`, `#numFrames`, `#q`, and `#t`.
- TXA track/key/event/custom-property storage layout.
- FBX take selection, default animation name, FPS default, frame-count basis,
  node-name sanitizing, root name, recursive node walk, and `EntityPosition`
  special handling.
- FBX resource-property surface for conversion: `AnimationName` and `FPS`.
- Workbench-style FBX->TXA text writer behavior: track hierarchy, key channel
  tokens, frame range compression, default component elision, and numeric
  formatting.
- Absence, in current Ghidra evidence, of a separate FBX conversion mode for
  additive, partial, IK, or full-body animation. Those should be treated as
  authoring/runtime graph concepts and baked to sampled transforms for our
  converter.
- Delegating transform evaluation to FBX SDK evaluator rather than hand-rolling
  FBX pivot/layer math.
- ANM top-level `ANIM/SET6` chunk order.
- `FPS`, `HEAD`, `DATA`, optional `EVNT`, and optional `CPRP` chunk shape.
- writer-context field mapping from TXA tracks/keys to ANM records.
- quantized 16-bit float stream and retained key-index stream behavior.

## Recommended Next Step

Build the converter in this order:

1. Keep the current TXA -> ANM prototype as the reference implementation.
2. Add targeted golden files for `CPRP`, `nodeDiff`, and channel-flag variants
   if byte-identical rare-case coverage is required. The static Workbench
   parser/writer evidence for those paths is summarized in `txa-rare-paths.md`.
3. Add FBX SDK import/evaluation.
4. Validate FBX -> ANM against Workbench for tiny controlled FBX files.
