# TXA -> ANM Prototype Status

Date: 2026-05-17

Prototype:

- `tools/TxaAnmPrototype/TxaAnmPrototype.csproj`
- `tools/TxaAnmPrototype/Program.cs`

CLI status:

- Running without arguments now prints usage/help and exits successfully.
- Conversion command is `txa2anm <input.txa> <output.anm>`.
- Supported modes are `--mode optimized` and `--mode exact`; `--zero-tolerance`
  remains an alias for exact mode.
- The converter writes `<output.anm>.meta` by default. The meta `Name` field
  uses the Workbench/Enfusion deterministic `ResourceGUID` algorithm from
  `FUN_1404541e0`, and `TXAResourceClass PC` stores the input TXA basename as
  `SourceFile`.

Golden pair:

- TXA: `anm/txa_anm/p_2hd_cro_interact_out.txa`
- Workbench ANM: `anm/txa_anm/p_2hd_cro_interact_out.anm`
- Prototype ANM: `anm/txa_anm/prototype_out.anm`

## Current Result

confirmed: the standalone prototype emits byte-identical ANM files for all
currently available Workbench TXA/ANM golden pairs. The first pair matches with
normal Workbench TXA thresholds. The newer `newtest/stand_turn_rs_90` and
`newtest/11/stand_walk_fwd` pairs match when using the zero-tolerance mode that
corresponds to the Workbench direct FBX/export path evidence.

Command:

```text
dotnet run --project tools/TxaAnmPrototype/TxaAnmPrototype.csproj -- anm/txa_anm/p_2hd_cro_interact_out.txa anm/txa_anm/p_2hd_cro_interact_out.anm anm/txa_anm/prototype_out.anm
```

Observed output:

```text
TXA nodes: 83
TXA frames: 30
TXA fps: 30
TXA events: 0
TXA custom properties: 0
Wrote: anm\txa_anm\prototype_out.anm (19898 bytes)
Expected: anm\txa_anm\p_2hd_cro_interact_out.anm (19898 bytes)
Size match: True
Byte match: true
```

Explicit converter CLI command:

```text
dotnet run --project tools/TxaAnmPrototype/TxaAnmPrototype.csproj -- txa2anm anm/txa_anm/p_2hd_cro_interact_out.txa anm/txa_anm/prototype_cli_out.anm --compare anm/txa_anm/p_2hd_cro_interact_out.anm
```

This also returns `Size match: True` and `Byte match: true`.

Second validation pair:

- TXA: `anm/txa_anm/newtest/stand_turn_rs_90.txa`
- Workbench ANM: `anm/txa_anm/newtest/stand_turn_rs_90.anm`
- Prototype ANM: `anm/txa_anm/newtest/stand_turn_rs_90.codex.anm`

Current observed output with `--mode exact`:

```text
TXA nodes: 67
TXA frames: 30
TXA fps: 25
TXA events: 4
TXA custom properties: 0
Wrote: anm\txa_anm\newtest\stand_turn_rs_90.codex.anm (24075 bytes)
Expected: anm\txa_anm\newtest\stand_turn_rs_90.anm (24075 bytes)
Size match: True
Byte match: true
```

Current analysis files:

- `anm/txa_anm/newtest/stand_turn_rs_90.workbench-analysis.md`
- `anm/txa_anm/newtest/stand_turn_rs_90.codex-analysis.md`

Third validation pair:

- TXA: `anm/txa_anm/newtest/11/stand_walk_fwd.txa`
- Workbench ANM: `anm/txa_anm/newtest/11/stand_walk_fwd.anm`
- Prototype ANM: `anm/txa_anm/newtest/11/stand_walk_fwd.codex.exact.anm`

Current observed output with `--mode exact`:

```text
TXA nodes: 67
TXA frames: 50
TXA fps: 25
TXA events: 4
TXA custom properties: 0
Wrote: anm\txa_anm\newtest\11\stand_walk_fwd.codex.exact.anm (34739 bytes)
Expected: anm\txa_anm\newtest\11\stand_walk_fwd.anm (34739 bytes)
Size match: True
Byte match: true
```

The same pair does not match in optimized mode: generated size is `26381`
bytes versus Workbench `34739` bytes. This confirms this ANM belongs to the
exact/zero-threshold output style.

Current analysis files:

- `anm/txa_anm/newtest/11/stand_walk_fwd.workbench-analysis.md`
- `anm/txa_anm/newtest/11/stand_walk_fwd.codex-analysis.md`

## What Is Covered

- Parses the Workbench TXA sample with `$animation`, `$node`, `$keys`,
  `$frame`, `#fps`, `#numFrames`, `#t`, `#q`, and `#s` syntax.
- Parses both `$`/`#`-prefixed Workbench tokens and unprefixed labels used in
  the implementation spec.
- Tracks `nodeDiff` and `keys` channel flags in the internal model.
- Parses `events { event ... }` and `custProps { custProp ... }` blocks and
  writes optional `EVNT`/`CPRP` chunks. `EVNT` is byte-validated by both
  `newtest` exact-mode pairs. `CPRP`, `nodeDiff`, and isolated odd
  `keys t/q/s` combinations are now covered by direct Ghidra parser/writer
  evidence in `txa-rare-paths.md`, but still need targeted Workbench golden
  files for byte-level rare-case testing.
- Emits the physical ANM wrapper:

```text
FORM <be32 size> ANIM
  SET6 <be32 size>
    FPS\0
    HEAD
    DATA
```

- Emits big-endian chunk sizes.
- Emits little-endian observed payload fields for `FPS`, `HEAD`, and `DATA`.
- Emits all 83 `HEAD` records, matching the 83 TXA node blocks in the golden
  pair.
- Matches Workbench retained-key counts and retained index streams for
  translation, rotation, and scale on this pair.
- Matches Workbench quantized `DATA` stream bytes for this pair.

## Reduction Fix That Closed The Gap

The earlier prototype was structurally correct but had retained rotation-key
mismatches. The final missing detail was the slerp helper fallback threshold:

- confirmed: `FUN_1402bbe70` uses `DAT_141a6d970` as the linear interpolation
  cutoff for near-equal quaternions.
- confirmed: HTTP `read_memory` on `workbenchApp.exe:0x141a6d970` returned
  bytes `77 be 7f 3f`, which are little-endian float `0.999`.
- confirmed: changing the prototype slerp cutoff from `0.999999` to `0.999`
  made the full ANM byte-identical.

Evidence:

- `ghidra-raw/ghidra-raw-anm-constants-transform.txt` lines 347-420:
  `FUN_1402bbe70` decompile.
- `ghidra-raw/ghidra-raw-slerp-threshold-http.txt`:
  raw HTTP memory read for `DAT_141a6d970`.

## Remaining Validation Scope

This proves the TXA -> ANM algorithm for the current Workbench-generated pair.
To claim broad converter compatibility, still validate:

- synthetic TXA files with events and custom properties, to exercise `EVNT` and
  `CPRP`.
- TXA files using sparse/range frames, `nodeDiff`, and `keys t`/`keys q`/`keys s`
  flags.
- malformed or overflow cases if matching Workbench diagnostics matters.

## Rare TXA Path Evidence

confirmed: `FUN_141058410` handles `keys` inside a TXA node. With no arguments
it sets both internal channel bytes `track +0x29` and `track +0x2a` to `1`.
With arguments, `t` sets `+0x29`, while `q` or `s` set `+0x2a`.

confirmed: `FUN_141067c00` maps those bytes into final writer flags by
inversion: `+0x29 == 0` sets ANM flag `0x02`, `+0x2a == 0` sets flag `0x04`,
and `+0x2b == 0` sets flag `0x08`.

confirmed: all TXA parser calls to `FUN_141055e40` found in this pass pass
`1,1,1` for the three channel bytes at creation time. The TXA `keys` callback
only modifies `+0x29` and `+0x2a`; no observed TXA token clears `+0x2b`.

confirmed: `FUN_141057b30` parses `custProp` and stores name/value through
`FUN_141055a40`; `FUN_141068360` writes optional `CPRP` when writer context
custom-property count `+0x34` is nonzero.

Raw evidence:

- `anm/ghidra-raw/ghidra-raw-rare-txa-cprp-nodediff-keys-http.txt`
- `anm/txa-rare-paths.md`

## Newtest Findings

confirmed: `workbenchApp.exe` TXA frame parser `FUN_1410580e0` initializes each
parsed frame key with quaternion `0,0,0,1`, translation `0,0,0`, and scale
`1,1,1`, parses the `frame` start/end values, then expands frame ranges by
copying the parsed key into following frame records.

confirmed: raw HTTP decompile for this function is saved in
`anm/ghidra-raw/ghidra-raw-newtest-frame-inheritance-http.txt`.

confirmed: `FUN_141068360` performs retained-key reduction over all writer
keys, using per-key frame index at writer-key offset `+0x28`; it does not reduce
only over explicit `#t/#q/#s` source fields.

confirmed: direct zero-tolerance/exact mode makes `stand_turn_rs_90.txa` produce a
byte-identical ANM to the supplied Workbench ANM:

```text
dotnet run --project tools/TxaAnmPrototype/TxaAnmPrototype.csproj -- txa2anm anm/txa_anm/newtest/stand_turn_rs_90.txa anm/txa_anm/newtest/stand_turn_rs_90.codex.anm --compare anm/txa_anm/newtest/stand_turn_rs_90.anm --mode exact
```

likely: `stand_turn_rs_90.anm` was produced by a Workbench path that zeroed the
translation/scale/rotation reduction thresholds before the common ANM writer.
This matches prior Ghidra evidence from the direct FBX/export call path and the
new byte-identical result.

confirmed: direct zero-tolerance/exact mode also makes
`newtest/11/stand_walk_fwd.txa` produce a byte-identical ANM to the supplied
Workbench ANM. This pair has 67 nodes, 50 frames, four events, and no
custom properties. Its `HEAD` flags are all `0x00`, and all nodes use
`$keys t q s`, so it validates larger exact-mode retained-key/data output and
another `EVNT` case.

## Usage

```text
dotnet run --project tools/TxaAnmPrototype/TxaAnmPrototype.csproj -- txa2anm <input.txa> <output.anm> [--compare <workbench.anm>] [--mode optimized|exact] [--no-meta]
```

Use `--mode optimized` for normal Workbench TXA thresholds. Use `--mode exact`
for Workbench exports that came through the direct FBX/export path or otherwise
match the zeroed-threshold writer behavior. `--zero-tolerance` remains accepted
as an alias for `--mode exact`.

Meta output is enabled by default. Use `--no-meta` to suppress it. For example,
an output named `StalkerSnork_runright.anm` gets `Name
"{FE542D5525E19BD8}StalkerSnork_runright.anm"` because Workbench's
ResourceGUID hash is calculated from the resource name, while `SourceFile`
points to the input `.txa` basename.

Backward-compatible research command:

```text
dotnet run --project tools/TxaAnmPrototype/TxaAnmPrototype.csproj -- <input.txa> <expected.anm> <output.anm>
```
