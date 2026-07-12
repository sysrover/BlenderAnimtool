# FBX Import and Version Evidence

## Workbench FBX Surface

- confirmed: Workbench exposes `Fbx (*.fbx)` and `Export Fbx` strings in
  `FUN_140ebdce0`.
- confirmed: despite the UI label `Export Fbx`, the same function builds and
  executes an external converter command:
  `FBXConverter.exe -anm -bin -simplename "%s" "%s/%s"`.
- likely: this is Workbench's obsolete/manual FBX-to-ANM conversion path. It
  asks the user for one or more `.fbx` files and a destination folder, then
  runs the converter once per selected file.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 986-988.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1193-1194.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1033-1041: the function opens a file
  dialog titled `Export Fbx` with filter `Fbx (*.fbx)`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1043-1051: it opens a second dialog
  titled `Destination Folder`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1053-1077: it iterates selected files
  and formats the command string
  `FBXConverter.exe -anm -bin -simplename "%s" "%s/%s"`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1085-1098: it calls `system()` and shows
  `Cannot convert '%s'` on nonzero result.

## FBX As Animation Resource

confirmed: Workbench has a resource-registration flow where `.fbx` can be
ambiguous between model and animation. If the user chooses animation, the code
requests `FBXAnimResourceClass`; if model, it requests `FBXResourceClass`.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1949-1954: extension check for `fbx`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1980-1999: message
  `File %1 is ambiguous. Do you want to register it as a model or as an animation?`
  and button labels `as Model` / `as Animation`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 2006-2009: model path requests
  `FBXResourceClass`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 2024-2029: animation path requests
  `FBXAnimResourceClass`.

likely: an `.fbx` intended for animation must be registered as
`FBXAnimResourceClass` in Workbench, or passed through the external
`FBXConverter.exe -anm` path. The deeper Ghidra trace now proves
`FBXAnimResourceClassWB` has an in-process `.anm` write path; see
`Is FBX To ANM Possible?` below.

## Embedded FBX SDK

confirmed: `workbenchApp.exe` contains embedded FBX SDK/plugin code and strings.
Notable static strings include:

- `FbxSdkDefaultEvaluator` at `0x141caaf90`.
- `FbxSDKBindPose` at `0x141cad278`.
- `FbxSdkSceneEvaluator` at `0x141cb72e8` and `0x141cb7330`.
- `FBX file version` at `0x141cc4140`.
- `Autodesk FBX Binary` at `0x141cc43f8`.
- `Copyright (C) 1997-2010 Autodesk Inc. and/or its licensors.` at
  `0x141cc4978`.
- `FBX SDK/FBX Plugins` at `0x141cc4cb0`.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 4434-5666.

## Supported/Exposed FBX Versions

confirmed: Workbench/embedded FBX option setup function `FUN_1412950c0` builds
an export advanced-options group `Export|AdvOptGrp|Fbx`, then adds
`ExportFileVersion` and version/label/compatibility arrays.

confirmed version labels present in Ghidra strings:

- `FBX 6.0 binary (*.fbx)`
- `FBX 6.0 ascii (*.fbx)`
- `FBX 6.0 encrypted (*.fbx)`
- `FBX binary (*.fbx)`
- `FBX ascii (*.fbx)`
- `FBX encrypted (*.fbx)`
- `Compatible with Autodesk 2016 applications/FBX plug-ins`
- `Compatible with Autodesk 2014/2015 applications/FBX plug-ins`
- `Compatible with Autodesk 2013 applications/FBX plug-ins`
- `Compatible with Autodesk 2012 applications/FBX plug-ins`
- `Compatible with Autodesk 2011 applications/FBX plug-ins`
- `Compatible with Autodesk 2010 applications/FBX plug-ins and MotionBuilder 2009`
- `Compatible with Autodesk 2009 applications/FBX plug-ins`
- `Compatible with Autodesk 2006 FBX plug-ins and MotionBuilder 7.5, 7.0 and 6.0`

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 5694-6057.
- `ghidra-raw/ghidra-raw-target-functions.txt`: target `1412950c0`, decompile registers
  `Export|AdvOptGrp|Fbx`, `FBX File Format`, `AsciiFbx`,
  `ExportFileVersion`, `VersionsUIAlias`, and `VersionsCompDescriptions`.

confirmed: the embedded FBX SDK/plugin version string reported by
`FUN_14115a380` is `2016.1.1`, build `20150824`.

confirmed: importer/parser code rejects unsupported major FBX versions above
7. `FUN_1410bc2f0` and `FUN_1410bc590` both report
`FBX File version %d is not supported in this product` if the parsed major
version field at context offset `+0x1a0` is greater than `7`. Another parser
path `FUN_14114d0a0` computes `major = version / 1000` and accepts only
`major < 8`, with an extra condition for major `7` tied to a context flag at
`+0x90`.

likely practical import target: FBX files compatible with Autodesk FBX SDK
2016.1.1, using FBX major version 6 or 7. Evidence does not prove support for
newer FBX 2018/2019/2020+ files; the decompile explicitly rejects major
versions above 7.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 5664-5680:
  `FBX SDK/FBX Plugins version 2016.1.1 build=20150824`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 4924-5005:
  `FUN_1410bc2f0` rejects `*(int *)(context + 0x1a0) > 7`.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 5048-5120:
  `FUN_1410bc590` has the same unsupported-version branch.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 5389-5437:
  `FUN_14114d0a0` computes `major = version / 1000`, accepts `major < 8`
  subject to the major-7 flag condition, otherwise reports the unsupported
  version string.

## FBX Time Mode And Tick Conversion

confirmed: Workbench uses FBX SDK-style time helpers before sampling animation
frames.

- `FUN_1410d7760` resolves a scene/context time mode. It reads the mode from
  context data, falls back through `FUN_1410879b0()` when the mode is zero, and
  returns mode `6` if the fallback is still zero.
- `FUN_1410894e0(timeMode)` maps time-mode ids to integer tick counts per
  frame.
- `FUN_1410884c0(timeSpan, timeMode)` divides the stored tick span by
  `FUN_1410894e0(timeMode)` and returns zero if the denominator is zero.
- `FUN_141087b40(outTicks, seconds)` converts seconds into ticks using
  `DAT_141ca4fa8`, rounding by adding or subtracting `DAT_141b1fd68`.
- `FUN_141087b80(ticks)` converts ticks back to seconds by dividing by
  `DAT_141ca4fa8`.

confirmed tick-per-frame mapping from `FUN_1410894e0`:

```text
mode  1 -> 0x16f0dfaa
mode  2 -> 0x1b8772cc
mode  3 -> 0x2de1bf54
mode  4 -> 0x370ee598
mode  5 -> 0x395a2f29
mode  6 -> 0x5bc37ea8
mode  8 -> 0x5bdafc7a
mode  9 -> 0x5bdafc7a
mode 10 -> 0x6e1dcb30
mode 11 -> 0x72b45e52
mode 12 -> 0x02c0beae
mode 13 -> 0x72d1bb99
mode 14 -> DAT_141ca4fa8 / _DAT_1458559e0
mode 15 -> 0x1cad1794
mode 16 -> 0x263c1f70
mode 17 -> 0x2ded7e3d
```

confirmed: `DAT_141ca4fa8` is referenced by the tick conversion helpers and
time-mode mapping. The raw data at that address is `0x422581d1af600000`.

Evidence:

- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` lines 1189-1275:
  earlier decompile for time-mode resolution and tick/frame helpers.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 189-200:
  data reference scan for `DAT_141ca4fa8` and its refs from
  `FUN_141087b40`, `FUN_141087b80`, and `FUN_1410894e0`.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 226-250:
  `FUN_1410879b0` default/fallback time mode helper.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 266-321:
  `FUN_1410894e0` tick-per-frame mapping.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 434-448:
  `FUN_141087b40` seconds-to-ticks conversion.
- `ghidra-raw/ghidra-raw-time-iff-primitives.txt` lines 635-639:
  `FUN_1410884c0` divides tick span by ticks per frame.
- `ghidra-raw/ghidra-raw-fbx-main-build-decompile-http.txt`: `FUN_140e75c10` stores the
  selected take span at context `+0x40/+0x48`, subtracts start from end through
  `FUN_141089460`, resolves scene time mode through `FUN_1410d7760`, and stores
  `FUN_1410884c0(durationTicks, timeMode) + 1` as `TXA::Animation + 0x84`.
- `ghidra-raw/ghidra-raw-fbx-time-take-helpers-http.txt`: fresh HTTP decompile of
  `FUN_1410884c0`, `FUN_141087b80`, `FUN_141087b40`, `FUN_141089460`,
  `FUN_1410d7760`, `FUN_1410bea70`, and `FUN_1410d7940`.

## Import Requirements

confirmed: Workbench exposes FBX import settings for animation data through FBX
SDK IO settings:

- `Import|IncludeGrp|Animation`
- `Convert Animation Curves At: (fps)`
- `Import|IncludeGrp|Animation|ExtraGrp`
- `Animation Take`
- `Bake Animation Layers`
- `Import|IncludeGrp|Animation|Deformation`

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 2664-2710.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 2749-2749.

confirmed: the embedded FBX SDK registers animation-related classes including
`FbxAnimStack`, `FbxAnimLayer`, `FbxAnimCurveNode`, `FbxAnimCurveBase`,
`FbxAnimCurve`, and `FbxAnimEvaluator`.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 3141-3198.

confirmed: the embedded FBX SDK registers skeleton/skin-related classes
including `FbxPose`, `FbxSkin`, `FbxCluster`, and `FbxSkeleton`.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 2985-2993.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 3290-3312.
- `ghidra-raw/ghidra-raw-exact-strings.txt` line 3442.

likely accepted input shape, based only on Workbench/FBX SDK evidence:

- an FBX file with animation stacks/takes and curves.
- skeleton/bone nodes if the target `.anm` is skeletal.
- optionally skin/cluster/bind-pose data when Workbench needs to associate
  curves with a skeleton hierarchy.

confirmed: for the animation conversion path, node names are taken from FBX
scene nodes and sanitized by replacing spaces and dashes with underscores.
`EntityPosition` has special handling. Take selection and FPS behavior are
documented below. `FUN_140e7e780` also proves Workbench reorders FBX transform
components before extracting key values.

confirmed: node attribute type value `4` in `FUN_140e75770` is `FbxMesh`.
Workbench skips those nodes in the recursive FBX-to-TXA conversion. This is not
`FbxNull`: the `FbxNull` vtable slot `+0xb8` returns `1`, while `FbxMesh`
returns `4`.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-nodeattribute-registration-http.txt` lines 484-526:
  Workbench registers `FbxNull`, `FbxMarker`, `FbxCamera`, `FbxLight`, and
  `FbxSkeleton` as `NodeAttribute` classes with separate factory functions.
- `ghidra-raw/ghidra-raw-fbx-nodeattribute-registration-http.txt` lines 562-600:
  Workbench registers `FbxMesh`, `FbxPatch`, `FbxNurbs`, `FbxNurbsSurface`,
  `FbxNurbsCurve`, and `FbxLine` as `Geometry` classes.
- `ghidra-raw/ghidra-raw-fbx-attribute-constructors-http.txt`: constructors assign
  class-specific vtables, including `FbxNull -> PTR_FUN_141cd9530` and
  `FbxSkeleton -> PTR_FUN_141cd9f00`.
- `ghidra-raw/ghidra-raw-fbx-geometry-constructors-http.txt`: the `FbxMesh` constructor
  assigns `PTR_FUN_141cb9158`.
- `ghidra-raw/ghidra-raw-fbx-attribute-type-slot-summary-http.json` and
  `ghidra-raw/ghidra-raw-fbx-geometry-type-slot-summary-http.json`: vtable slot `+0xb8`
  return bytes map `FbxNull -> 1`, `FbxMarker -> 2`, `FbxSkeleton -> 3`,
  `FbxMesh -> 4`, `FbxNurbs -> 5`, `FbxPatch -> 6`, `FbxCamera -> 7`,
  `FbxLight -> 10`, `FbxNurbsCurve -> 13`, `FbxNurbsSurface -> 16`,
  `FbxLODGroup -> 18`, and `FbxLine -> 21`.

likely: the semantic reason for `EntityPosition` is root-motion/entity-motion
separation. Static evidence proves how it is sampled and applied, but the
authoring meaning/name is inferred from the node name and flow, not from a
decompiled label.

## Is FBX To ANM Possible?

confirmed: yes. There are two Workbench-side FBX-to-ANM clues:

1. an older/manual UI branch that attempts to run an external command:

```text
FBXConverter.exe -anm -bin -simplename "<input.fbx>" "<destination>/<fileName>"
```

2. an in-process `FBXAnimResourceClassWB` conversion path that opens the FBX
   scene, selects an animation take, builds a `TXA::Animation`, constructs a
   `.anm` output path, and writes it through the internal animation writer.

Evidence for external branch:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1073-1077.

Evidence for in-process branch:

- `ghidra-raw/ghidra-raw-fbx-anim-resource-trace.txt` lines 191-203:
  Workbench has `enf::FBXAnimResourceClass`, `FBXAnimResourceClassWB`, and their
  vtables/RTTI, separate from `FBXResourceClass`.
- `ghidra-raw/ghidra-raw-fbx-anim-resource-trace.txt` lines 352-365:
  `FUN_140fc9aa0` constructs `FBXAnimResourceClassWB` by calling the base
  constructor and installing `FBXAnimResourceClassWB::vftable`.
- `ghidra-raw/ghidra-raw-fbx-anim-vtable-trace.txt` lines 276-310:
  `FBXAnimResourceClassWB::vftable` overrides slot `+0xc0` with
  `FUN_140fc9fc0`.
- `ghidra-raw/ghidra-raw-fbx-anim-vtable-trace.txt` lines 392-431:
  base `FUN_1404555f0` registers `AnimationName` with default `Take 001` and
  `FPS` with default `30`.
- `ghidra-raw/ghidra-raw-fbx-anim-methods-trace.txt` lines 256-343:
  `FUN_140fc9fc0` reads the `AnimationName` and `FPS` property IDs
  `DAT_142321adc` / `DAT_142321ae0`, defaulting to `Take 001` and `0x1e`
  frames per second.
- `ghidra-raw/ghidra-raw-fbx-anim-methods-trace.txt` lines 365-416:
  `FUN_140fc9fc0` calls `FUN_140e75c10`, then builds a `.anm` path and writes
  via `FUN_141068360`.
- `ghidra-raw/ghidra-raw-fbx-anim-convert-helpers.txt` lines 239-299:
  `FUN_140e75c10` searches FBX animation stacks/takes by name and reports
  `Can't find anim take` if the requested take is absent.
- `ghidra-raw/ghidra-raw-fbx-anim-convert-helpers.txt` lines 320-344:
  `FUN_140e75c10` allocates a `0x88` byte `TXA::Animation`, sets
  `TXA::Animation::vftable`, stores FPS at offset `0x80`, and stores frame count
  at offset `0x84`.
- `ghidra-raw/ghidra-raw-fbx-anim-convert-helpers.txt` lines 401-416:
  `FUN_140e75c10` appends `.anm` to the target path and calls `FUN_141068360`.
- `ghidra-raw/ghidra-raw-fbx-anim-convert-helpers.txt` lines 497-624:
  `FUN_140fc9d50` is another ANM build/write helper; it logs
  `building ANM...`, creates a `TXA::Animation`, validates/loads it with
  `FUN_141057800`, then writes through `FUN_141068360`.

updated conclusion:

- the missing `FBXConverter.exe` does not block Workbench's current conversion
  path. Ghidra shows an in-process path under `FBXAnimResourceClassWB`.
- for a standalone converter, the easiest route is now to reproduce
  `FUN_140e75c10`/`FUN_140fc9fc0`: load FBX, select take `AnimationName`,
  sample at `FPS`, populate `TXA::Animation`, then serialize `.anm`.

## FBX To TXA::Animation Algorithm

confirmed: the current Workbench in-process algorithm is:

1. `FUN_140fc9fc0` opens/initializes an FBX scene context, then calls
   `FUN_140e7daa0` to import the FBX scene.
2. It reads resource properties `AnimationName` and `FPS`; defaults are
   `Take 001` and `30`.
3. It calls `FUN_140e75c10(context, takeName, targetPath, fps, flag, error)`.
4. `FUN_140e75c10` enumerates FBX animation stacks/takes, compares names, and
   reports `Can't find anim take` when the requested take cannot be resolved.
   If at least one take exists, the decompile shows a fallback to the first
   take before selection.
5. It clears/evaluates scene state with `FUN_1410db540(scene)` and activates the
   selected take with `FUN_1410db3a0(scene, take)`.
6. It reads the take/global time span, stores start/end at context
   `+0x40/+0x48`, computes `durationTicks = endTicks - startTicks`, allocates a
   `0x88` byte `TXA::Animation`, sets `TXA::Animation::vftable`, stores FPS at
   offset `+0x80`, and stores
   `frameCount = durationTicks / ticksPerFrame + 1` at offset `+0x84`.
7. It searches the FBX node tree for `EntityPosition` with `FUN_140e7bf50`.
   When present, `FUN_140e78260` creates a TXA track for it and samples it into
   a per-frame transform array.
8. It recursively walks the scene with `FUN_140e75770`. Node names are
   sanitized by replacing spaces and dashes with underscores. The scene root is
   named `Scene_Root`; the special `EntityPosition` node is not processed again
   as a normal node. FBX nodes whose attribute type is `4` (`FbxMesh`) are
   skipped by the recursive conversion branch.
9. Each node track is created with `FUN_141055e40(animation, name, parentIndex,
   frameCount, 1, 1, 1)`. Track key records are allocated at stride `0x28`.
10. For every frame, Workbench samples time as
   `frameIndex / (frameCount - 1) * duration`, evaluates the FBX transform, and
   writes rotation, translation, and scale into the TXA track record. The track
   record uses rotation data at the start, translation at offsets
   `+0x10/+0x14/+0x18`, and scale at `+0x1c/+0x20/+0x24`.
11. If `EntityPosition` was sampled, normal nodes whose parent is the scene root
    are converted relative to the per-frame `EntityPosition` transform array.
    The direct evidence is `FUN_140e75770` calling `FUN_14108d8b0` with
    `frameIndex * 0x80 + entityPositionArray`, then writing the resulting matrix
    through `FUN_140e7e9c0` and `FUN_1402badd0`.
12. It writes a TXA text file through `FUN_141056750(animation, targetPath)`.
    That writer emits `animation "<name>"`, `version 1.0`, optional `fps`,
    `numFrames`, tag/track output, optional `events`, and optional `custProps`.
13. In the FBX path traced here, `FUN_140e75c10` and recursive sampler
    `FUN_140e75770` create tracks/keys only. Event/custom-property store helpers
    are not called from this path in the current evidence pass.

confirmed transform conversion details:

- `FUN_140e7e780` reorders transform matrix/vector components. For the first
  three rows/vectors it reads source columns in order `0`, `2`, `1`, then writes
  them back through `FUN_14108e5e0`; for the translation row it writes
  `x, z, y`.
- `FUN_140e7e780(..., 1)` also sets a zero/identity-like component through
  `FUN_14108cae0`.
- `FUN_1402badd0` converts the final 3x3 matrix to a quaternion and stores TXA
  key quaternion fields in order `x, y, z, w`.
- For normal nodes, scale is read from the evaluated FBX transform and multiplied
  by the context scale at `context + 0x58`; for the scene root, scale defaults to
  the identity constant.
- For `EntityPosition`, Workbench writes translation from the transformed matrix
  and forces scale to `1, 1, 1`.
- For the scene root, Workbench writes identity transform keys and default scale
  without evaluating the FBX node.
- For scene-root children without an `EntityPosition` array, Workbench evaluates
  the child global transform, reorders it, and extracts key data directly.
- For non-root children, Workbench evaluates the parent global transform,
  reorders and inverts it with `FUN_14108dce0`, evaluates/reorders the child
  global transform, then composes parent-inverse with child-global through
  `FUN_14108d8b0` before key extraction.
- `FUN_14108dce0` is a 4x4 matrix inverse helper. It computes the 3x3
  determinant/cofactor inverse, writes inverse rotation values, computes inverse
  translation, then writes affine bottom-row defaults `0,0,0,1`.
- `FUN_14108d8b0` is a transform composition/multiply helper. It multiplies the
  rotation axes and composes translation with the left transform's translation.
- `FUN_14108cf60` is a 16-double matrix copy helper.
- `FUN_140e7e9c0` extracts three matrix rows/vectors and translation from a
  transform, converts doubles to floats, applies the context scale at
  `context + 0x58`, and fills the 3x4 float matrix consumed by `FUN_1402badd0`.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 2920-3076:
  `FUN_140fc9fc0` reads `AnimationName`/`FPS`, calls `FUN_140e75c10`, then
  reaches the ANM build/write helper.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 215-300:
  `FUN_140e75c10` resolves the requested FBX take and time span.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 300-344:
  `TXA::Animation` allocation, vtable install, FPS, and frame count.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 611-656:
  `FUN_140e78260` samples `EntityPosition`, stores a per-frame transform array,
  converts matrices, writes quaternion/translation, and forces scale to
  `1,1,1`.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 701-858:
  `FUN_140e75770` recursive node walk, node-name sanitizing, per-frame sampling,
  optional `EntityPosition` relative conversion, matrix-to-quaternion write, and
  recursive child traversal.
- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` lines 444-503:
  `FUN_140e7e780` component reorder helper.
- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` lines 286-326:
  `FUN_1402badd0` matrix-to-quaternion helper.
- `ghidra-raw/ghidra-raw-fbx-transform-helper-deep.txt` lines 405-459:
  `FUN_140e7e9c0` extracts the final float matrix/translation values used for
  TXA key writing.
- `ghidra-raw/ghidra-raw-fbx-transform-helper-deep.txt` lines 1403-1436:
  `FUN_14108d8b0` transform multiply/composition helper.
- `ghidra-raw/ghidra-raw-fbx-transform-helper-deep.txt` lines 1667-1736:
  `FUN_14108dce0` affine matrix inverse helper.
- `ghidra-raw/ghidra-raw-fbx-transform-helper-deep.txt` lines 1967-1986:
  `FUN_14108cf60` 16-double transform copy helper.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 345-416:
  `EntityPosition`, recursive conversion, and optional `.anm` writer branch.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 505-537:
  `FUN_140e7bf50` recursive FBX node-name search.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 553-660:
  `FUN_140e78260` creates/samples the `EntityPosition` track.
- `ghidra-raw/ghidra-raw-fbx-txa-anm-algorithm.txt` lines 701-864:
  `FUN_140e75770` recursive node-to-track conversion.
- `ghidra-raw/ghidra-raw-anm-writer-packing.txt` lines 549-660:
  `FUN_141055e40` creates TXA tracks, links parent/child/sibling indices, and
  allocates `0x28` byte key records.
- `ghidra-raw/ghidra-raw-fbx-main-build-decompile-http.txt`: fresh HTTP decompile of
  `FUN_140e75c10`, including take fallback, take activation, time span,
  `TXA::Animation` allocation, `EntityPosition`, recursive conversion, TXA text
  export, `.anm` path construction, and zero-tolerance writer call.
- `ghidra-raw/ghidra-raw-fbx-missing-parts-decompile-http.txt`: fresh HTTP decompile of
  `FUN_140e75770`, `FUN_140e78260`, `FUN_140e7e780`, `FUN_140e7e9c0`,
  `FUN_1410c3840`, node parent/child helpers, and scene conversion helpers.
- `ghidra-raw/ghidra-raw-fbx-node-helper-decompile-http.txt`: node parent/child/name and
  node-attribute helper decompile.
- `ghidra-raw/ghidra-raw-fbx-attribute-type-slot-summary-http.json` and
  `ghidra-raw/ghidra-raw-fbx-geometry-type-slot-summary-http.json`: FBX node attribute
  type slot mapping proving `type == 4` is `FbxMesh`.
- `ghidra-raw/ghidra-raw-fbx-resource-mode-pass-http.txt`: HTTP xrefs and function analysis
  for `DAT_142321adc`, `DAT_142321ae0`, `FUN_140fc9fc0`, `FUN_140e75c10`,
  `FUN_140e75770`, and `FUN_141056750`.
- `ghidra-raw/ghidra-raw-fbx-txa-text-writer-pass-http.txt`: HTTP function analysis for
  the TXA text writer helpers `FUN_1410574b0`, `FUN_1410570b0`,
  `FUN_141056230`, `FUN_1410562e0`, `FUN_141055c60`, and track creation helper
  `FUN_141055e40`.

## FBX To TXA Text Output Details

confirmed: Workbench's FBX-to-TXA path builds an in-memory `TXA::Animation`,
then writes the text TXA through `FUN_141056750`. The track writer is not a
plain one-line-per-frame dump.

confirmed track text behavior:

- `FUN_1410574b0` writes `node` or `nodeDiff` depending on the track diff byte
  at track offset `+0x28`.
- The FBX sampler creates tracks through `FUN_141055e40(..., frameCount, 1, 1,
  1)`, so normal FBX-created tracks have translation, quaternion, and scale
  channel bytes enabled at `+0x29/+0x2a/+0x2b`.
- `FUN_1410574b0` writes a `keys` block and emits `t`, `q`, `s` tokens based on
  those channel bytes.
- Child tracks are written recursively through first-child offset `+0x10` and
  next-sibling offset `+0x0c`.
- Because `FUN_140e75770` places child recursion inside the same
  `attributeType != 4` branch as track creation, an `FbxMesh` node is skipped
  together with its subtree by this conversion helper.

confirmed frame range compression:

- `FUN_1410574b0` groups contiguous keys while active components remain equal
  to the starting key under Workbench's comparison helpers.
- Translation comparison uses `FUN_1410562e0(..., 7)`, three floats, threshold
  `powf(10.0, -7)`.
- Quaternion comparison uses `FUN_141056230(..., 6)`, four floats, threshold
  `powf(10.0, -6)`.
- Scale comparison uses `FUN_1410562e0(..., 5)`, three floats, threshold
  `powf(10.0, -5)`.
- `FUN_1410570b0` writes `frame <start> [end]`, and emits the end frame only
  when `end != start`.

confirmed frame block default elision:

- `FUN_1410570b0` compares each frame key against default key values:
  quaternion `0,0,0,1`, translation `0,0,0`, scale `1,1,1`.
- It omits `t` when translation is default under `10^-7`.
- It omits `q` when quaternion is default under `10^-6`.
- It omits `s` when scale is default under `10^-5`.
- Non-default `t` writes three floats from key offsets `+0x10/+0x14/+0x18`.
- Non-default `q` writes four floats from key offsets `+0x00/+0x04/+0x08/+0x0c`.
- Non-default `s` writes three floats from key offsets `+0x1c/+0x20/+0x24`.

confirmed numeric formatting:

- `FUN_141055c60` writes float tokens with format string `"%.*f"` at
  `DAT_141a757a8`.
- The float writer zeroes values whose absolute value is less than
  `powf(10.0, -precision)`.
- For `t`, `q`, and `s` emitted by `FUN_1410570b0`, the output precision argument
  is `7`.
- After formatting, `FUN_141055c60` trims trailing zeroes and the unnecessary
  decimal tail.
- Raw memory at `0x141f859e0` begins with float `10.0`, confirming the pow base
  used by the comparison/format helpers.

likely implementation impact: a Blender-oriented converter should either emit
TXA with the same Workbench text compaction rules, or generate the in-memory
model and then use the already implemented TXA-to-ANM writer directly. If we
need byte-identical TXA text to Workbench, these writer rules are required.

likely Blender export impact: keep animated armature/bone/null hierarchy outside
FBX mesh nodes. Since Workbench's sampler skips `FbxMesh` nodes together with
their child traversal, putting a skeleton under a mesh node can make the whole
animated subtree disappear from the generated TXA.

## FBX Resource Properties And Conversion Modes

confirmed: the Workbench `FBXAnimResourceClass` properties that directly feed
the in-process FBX-to-TXA conversion are `AnimationName` and `FPS`.

- `FUN_1404555f0` registers `AnimationName` with default `Take 001` and tooltip
  `Name of the animation take to import`.
- `FUN_1404555f0` registers `FPS` with default `30` and tooltip `Play speed`.
- xrefs to `DAT_142321adc` are only the property registration write in
  `FUN_1404555f0` and the read in `FUN_140fc9fc0`.
- xrefs to `DAT_142321ae0` are only the property registration write in
  `FUN_1404555f0` and the read in `FUN_140fc9fc0`.
- `FUN_140fc9fc0` reads those two property IDs, defaults to `Take 001` and
  `0x1e`, then calls `FUN_140e75c10(context, takeName, targetPath, fps, flag,
  error)`.

confirmed: additive/partial/IK/full-body strings exist in Workbench, but the
current Ghidra evidence does not place them in the FBX-to-TXA conversion path.

- `BaseAnimation` anchors point to `FUN_140e8fe40`, which creates AnimEditor UI
  actions such as `Show IK targets`, `Show bone hierarchy`, `Set base animation`,
  and LOD actions. Its tooltip says `Set base animation for partial or additive
  animations`.
- `AnimationType` anchors point to plugin command lookup in `FUN_1405d5610`, not
  to `FUN_140fc9fc0` or `FUN_140e75c10`.
- `FullBody` string hits are runtime/command/class names such as
  `TagFullBodyActions`, `CMD_FullBodyAction`, and
  `HumanCommandFullBodyDamage`; this scan found no anchor in the FBX conversion
  helpers.
- `FUN_140e75c10` callers are limited to `FUN_140fc9fc0` in the HTTP function
  analysis, and its decompile shows no branch on additive, IK, full-body,
  partial, or base-animation properties.

likely: for a Blender integration, additive/IK/full-body authoring should be
baked into ordinary node/bone transforms before FBX export. Workbench's
FBX-to-TXA conversion appears to sample the selected take as a transform-track
animation, not as a semantic animation-graph mode export.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-resource-mode-pass-http.txt`: resource-property xrefs,
  `BaseAnimation`/`AnimationType` anchor reports, `FullBody` string scan, and
  `FUN_140e8fe40` UI-action decompile summary.
- `ghidra-raw/ghidra-raw-fbx-mode-signs-related-decompile-http.txt`: `FUN_1404555f0`
  registration of `AnimationName` and `FPS`.
- `ghidra-raw/ghidra-raw-fbx-mode-signs-fbxanim-convert-http.txt`: `FUN_140fc9fc0`
  reads `AnimationName`/`FPS` and calls `FUN_140e75c10`.

## Deeper FBX Evaluator Boundary

confirmed: the scene import helper `FUN_140e7daa0` creates/imports an FBX scene
through embedded FBX SDK wrapper helpers, then applies scene/global conversion
helpers before animation sampling.

- `FUN_1410da670(*context, &DAT_141f68c1a)` creates/stores the scene object.
- `FUN_1410bb3d0(*context, &DAT_141f68c1a)` creates/stores the importer object.
- the importer vtable call at `+0xb8` receives the input path.
- `FUN_1410bb980(importer, scene, 0)` imports/finalizes into the scene.
- after import, `FUN_141090230(&DAT_142373c80, scene, flags)` may update scene
  conversion state, and `FUN_1410d74a0(root, out)` plus `FUN_1410904e0(out)`
  stores a context scale value at `context + 0x58`.

confirmed: `DAT_142373c80` is Workbench's `Meters` system-unit entry. The system
unit table stores `(scale, multiplier)` double pairs and the string helpers map
the entries as:

```text
DAT_142373c50 -> Millimeters    (0.1, 1.0)
DAT_142373c60 -> Decimeters     (10.0, 1.0)
DAT_142373c70 -> Centimeters    (1.0, 1.0)
DAT_142373c80 -> Meters         (100.0, 1.0)
DAT_142373c90 -> Kilometers     (100000.0, 1.0)
DAT_142373ca0 -> Inches         (2.54, 1.0)
DAT_142373cb0 -> Feet           (30.48, 1.0)
DAT_142373cc0 -> Miles          (160934.4, 1.0)
DAT_142373cd0 -> Yards          (91.44, 1.0)
```

confirmed: Workbench imports FBX, then calls
`FUN_141090230(&DAT_142373c80, scene, flags)` with local bytes
`00 01 01 01 01 01`. That converts/updates the scene to meters and enables five
property conversion groups in `FUN_141092c60`.

confirmed conversion behavior from `FUN_141090230` and callees:

- `FUN_1410d74a0(globalSettings, outUnit)` reads the current unit pair from
  global settings.
- If the current unit differs from the target meters pair by more than
  `DAT_141a6d578`, Workbench converts the root scene.
- `FUN_141090ed0(targetUnit, root, 1)` scales node translation vectors at
  node offset `+0x98` by `targetUnit[1]`; for meters this multiplier is `1.0`.
- `FUN_141092c60(targetUnit, root, currentUnit, 0, flags)` computes a conversion
  ratio from current unit to target unit and applies it to transform/property
  data. The enabled property groups include transform vectors/animation curves,
  deformation/bind-related matrices, camera/geometry attributes, light radius/
  shape fields, and another attribute group at offsets `+0x298/+0x2a8`.
- `FUN_141092000(targetUnit, scene, currentUnitScale / targetUnitScale)` updates
  scene pose/bind matrices after the unit conversion.
- `FUN_1410d7500(globalSettings, convertedUnit)` and
  `FUN_1410d7450(globalSettings, targetUnit)` write the resulting global unit
  state back.

confirmed: after conversion, `FUN_140e7daa0` rereads the global unit and stores
the first unit component at FBX import context offset `+0x58`. For the target
meters unit this is `100.0`. Later, `FUN_140e7e9c0` scales TXA translation by
`contextScale * DAT_141b79340`; `DAT_141b79340` is the double value
`0.00999999977648258`, so the meters path multiplies translations by
approximately `1.0`.

confirmed: animation transform sampling delegates to the embedded FBX evaluator
boundary instead of manually reconstructing pivots/inherit modes in Workbench
code. `FUN_1410c3840(node, time, flags...)` obtains an evaluator/cache object
from either the current global context or the node's scene, then calls
`FUN_1411235b0(evaluator, node, &time, ...)`. `FUN_1411235b0` itself resolves
an internal table pointer at `FUN_141123ba0() + 0xe8`, so the heavy evaluator
logic is behind SDK-style object dispatch.

confirmed: parent/child helpers used by `FUN_140e75770` are now bounded:

- `FUN_1410bfba0(node)` reads collection token `DAT_145856518` from
  `node + 0x10` and returns the first linked object, matching its use as a
  parent lookup in the sampler.
- `FUN_1410bfd40(node, recursiveFlag)` counts child objects from the same
  collection token.
- `FUN_1410bfe00(node, index)` returns the child at the requested index.
- `FUN_1410c05d0(node)` resolves an object from node property/collection data;
  `FUN_140e75770` skips normal track creation/sampling when a vtable call on
  that resolved object returns type value `4`. The latest HTTP vtable pass
  confirms value `4` is `FbxMesh`.

confirmed: take/time helpers are concrete:

- `FUN_1410bea70(scene, takeName)` iterates entries at `scene + 0xa0` with
  count `scene + 0x98`, comparing the requested take name against each entry at
  `+8`, and returns the matching time-span object or `0`.
- `FUN_141089440(out, a, b)` stores `*out = *a + *b`.
- `FUN_141089460(out, a, b)` stores `*out = *a - *b`.

Evidence:

- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt` lines 1347-1437:
  `FUN_140e7daa0` scene/importer creation, vtable import call, scene conversion
  helper calls, context scale extraction, and source filename storage.
- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt` lines 1511-1591:
  take enumeration, fallback to first take, current take selection, time-span
  selection, duration subtraction, time-mode lookup, and frame-count compute.
- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt` lines 1722-1892:
  recursive node sampling, parent/global transform handling, root handling,
  `EntityPosition` relative branch, and child recursion.
- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt` lines 1894-2011:
  detailed `EntityPosition` sampling and per-frame inverse transform array.
- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt` lines 2301-2385:
  `FUN_141089440` tick addition.
- `ghidra-raw/ghidra-raw-fbx-evaluator-deep.txt` lines 2390-2499:
  `FUN_141089460` tick subtraction.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt` lines 1131-1145:
  `FUN_1411235b0` resolves internal evaluator dispatch pointer
  `FUN_141123ba0() + 0xe8`.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt` lines 1196-1234:
  `FUN_14108c0a0` extracts three scale/vector components from the evaluated
  transform.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt` lines 1399-1408:
  `FUN_1410bfba0` parent/object lookup through token `DAT_145856518`.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt` lines 1429-1448:
  `FUN_1410bea70` take time-span lookup by name.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt` lines 1549-1581:
  `FUN_141090230` scene conversion/update helper body.
- `ghidra-raw/ghidra-raw-fbx-evaluator-core.txt` lines 1921-1940:
  `FUN_1410c3840` evaluator wrapper.
- `ghidra-raw/ghidra-raw-fbx-attribute-type-slot-summary-http.json` and
  `ghidra-raw/ghidra-raw-fbx-geometry-type-slot-summary-http.json`: vtable slot `+0xb8`
  return values for `FbxNull`, `FbxSkeleton`, `FbxMesh`, and other attribute/
  geometry classes.
- `ghidra-raw/ghidra-raw-fbx-scene-conversion-deep-http.txt`: fresh HTTP decompile of
  `FUN_141090230`, `FUN_1410904e0`, global unit getters/setters, node
  translation scaling, property conversion, and pose/update helpers.
- `ghidra-raw/ghidra-raw-fbx-system-unit-table-http.txt`: raw memory for the system-unit
  table at `0x142373c50`.
- `ghidra-raw/ghidra-raw-fbx-system-unit-strings-memory-http.txt`: raw memory containing
  unit labels and aliases such as `mm`, `centimeter`, `Meters`, `Inches`,
  `Feet`, `Yards`, and `Miles`.
- `ghidra-raw/ghidra-raw-fbx-scene-conversion-property-helpers-http.txt`: decompile of the
  property conversion helpers gated by the six conversion flag bytes.
- `ghidra-raw/ghidra-raw-fbx-unit-ratio-helper-http.txt`: `FUN_141090e30` ratio helper used
  by system-unit conversion.

## dataExporter DLL Cross-Check

confirmed: the loaded `dataExporter_v141_x64_RetailDX11.dll` scan found no
`.fbx` or `FBX` byte-string hits, and no `Autodesk_Cache_File` /
`Alias_Cache_File` hits. The strong FBX evidence remains in `workbenchApp.exe`,
not in this DLL pass.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 902 and 932-934.

## HTTP Evaluator Cross-Check

confirmed: direct HTTP call-graph analysis finds a path from the recursive FBX
node sampler to the evaluator dispatch:

```text
FUN_140e75770 -> FUN_1410c3840 -> FUN_1411235b0
```

confirmed: focused HTTP decompile of `FUN_1410c3840` shows it obtains an
evaluator/cache object through `FUN_1410a5790`; if absent, it resolves one from
the scene with `FUN_1410a5660` and `FUN_1410b2c60`, otherwise it uses
`FUN_1410db540`, then calls `FUN_1411235b0`.

confirmed: HTTP string search finds FBX SDK/plugin version evidence:
`2016.1.1 Release (237687)`, `2016.1.1`, and build string `20150824`. It also
finds FBX 6 exporter labels and unsupported-version strings.

Evidence:

- `ghidra-raw/ghidra-raw-missing-parts-http.txt` line 32: call-graph path
  `FUN_140e75770 -> FUN_1410c3840 -> FUN_1411235b0`.
- `ghidra-raw/ghidra-raw-missing-parts-focused-http.txt`: `fbx_eval_wrapper_complete`
  section.
- `ghidra-raw/ghidra-raw-fbx-strings-http.txt`: searches for `2016.1.1`, `20150824`,
  `Unsupported file version`, and `FBX 6`.
