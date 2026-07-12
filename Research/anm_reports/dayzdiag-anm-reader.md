# DayZDiag ANM Reader Check

Date: 2026-05-17

Scope: check whether `DayZDiag_x64.exe` reads `.anm` with the same `0.999`
quaternion slerp cutoff / reduction accuracy used by the Workbench writer.

## Finding

confirmed: the `0.999` value is not a DayZDiag `.anm` coordinate-read accuracy.
It is part of Workbench's writer-side quaternion interpolation helper used while
deciding which rotation source keys can be dropped.

confirmed: DayZDiag has a separate `ANIM/SET6` reader at `FUN_1400d4520`. It
recognizes the `ANIM` form and `SET4`/`SET5`/`SET6` chunks, reads `HEAD`, then
reads `DATA`.

confirmed: `FUN_1400d4520` calls `FUN_1400d5160` for the `DATA` translation,
scale, and rotation streams. `FUN_1400d5160` reads retained index arrays and
16-bit component streams from the file. It does not run the writer's key
reduction tolerances.

confirmed: DayZDiag also recognizes optional `EVNT` and `CPRP` chunks in the
same `FUN_1400d4520` reader. The chunk table at `0x140de9490` contains packed
`ANIM`, `SET4`, `SET5`, `SET6`, `FPS`, `HEAD`, `DATA`, `EVNT`, and `CPRP`
entries. Plain string searches for `EVNT`/`CPRP` return no matches because these
are stored as packed table bytes, not normal strings.

confirmed: the `CPRP` branch compares the current chunk id against
`DAT_140de94f8`, reads a 16-bit count with `FUN_14013f3c0`, stores that count at
`param_1 + 0x182`, allocates `count * 0x10 + 8`, stores the property table at
`param_1[0x2f]`, then reads each property as a name plus a string value. The name
is interned through `FUN_1401484f0`; the value is read by `FUN_1400d31a0`.

confirmed: the `EVNT` branch compares against `DAT_140de94f0`, reads a 16-bit
count, stores it at `param_1 + 0x180`, allocates `count * 0x10`, and reads event
frame, name, value/name, and user value fields into `param_1[0x2e]`.

likely: Workbench `nodeDiff` reaches DayZDiag as bit `0x01` in the per-track
`HEAD` flag byte. In DayZDiag `FUN_1400d4520`, that byte is copied from the
`HEAD` record into the runtime track record at offset `+0x64`.

confirmed: inside `FUN_1400d4520`, the visible `DATA` stream-read decisions use
the high bits of that byte, not the low `nodeDiff` bit:

- `byte +0x64 >> 4` controls the translation stream/index read mode.
- `byte +0x64 >> 6` controls the scale stream/index read mode for `SET6`.
- `byte +0x64 >> 5` controls the rotation stream/index read mode.

unknown: no direct branch on `HEAD` flag bit `0x01` was found in this focused
`FUN_1400d4520` reader pass. The loader preserves the flag byte, but any runtime
semantic use of `nodeDiff` would need a broader xref/dataflow pass over the
loaded animation track structure.

## Deeper `nodeDiff` Runtime Pass

confirmed: the runtime track flag byte copied from `HEAD` is used by the
sampling routines, but the sampled branches found in DayZDiag use high stream
mode bits, not Workbench `nodeDiff` bit `0x01`.

confirmed: `FUN_1400d3e40` is an interpolating track sampler. Its decompile
checks `((uint)param_1[0x19] & 0x10) == 0` for translation stream/index mode
and `((uint)param_1[0x19] & 0x20) == 0` for rotation stream/index mode.
`param_1[0x19]` maps to byte/word offset `+0x64` in the runtime track record.

confirmed: `FUN_1400d4250` is a simpler/non-interpolating sampler. Its
decompile checks the same `param_1[0x19] & 0x10` and
`param_1[0x19] & 0x20` paths. No direct `0x01` check appears in this function.

confirmed: xrefs to those samplers are from animation evaluation code:
`FUN_1400d3e40` is called from `FUN_1400de220` and `FUN_1400e0330`;
`FUN_1400d4250` is called from `FUN_1400e0330`.

confirmed: an exact instruction scan for `TEST`/`CMP`/`AND`/`BT` operations
that reference `+0x64` with immediate `0x01` found five instructions, but their
decompiled functions are not the ANM track sampler/reader path:

- `FUN_1407fef30`: sound/UI diagnostic flags.
- `FUN_140be3b60`: class/update logic.
- `FUN_140c23dc0`: memory/stat counter using `param_1 + 100` under a critical
  section.

likely: for DayZDiag loading/sampling, Workbench `nodeDiff` bit `0x01` is
preserved in the runtime flag byte but is not used by the visible ANM
`SET6` decode or normal transform sampling branches found so far. The important
writer-compatible requirement is to preserve the bit exactly when re-emitting
tracks, because another subsystem may still read or serialize the full flag
byte.

## CPRP Runtime Use

confirmed: `CPRP` is not only stored; DayZDiag applies selected custom
properties immediately after ANM load. `FUN_1400d44f0` calls `FUN_1400d4520`
to read the ANM, and if that succeeds it calls `FUN_1400d53b0` on the loaded
animation object.

confirmed: `FUN_1400d53b0` iterates `*(ushort *)(animation + 0x182)` records
from the CPRP table at `*(animation + 0x178)`. Each record is 16 bytes:

- `+0x00`: interned property name pointer/id.
- `+0x08`: string value pointer.

confirmed: the recognized CPRP property names in `FUN_1400d53b0` are:

- `entitypos`
- `entityrot`
- `speedupfactor`

likely: CPRP keys other than these three are preserved in the loaded CPRP table
but ignored by this apply pass. The loop falls through with no error for names
that do not match the recognized strings.

confirmed: `entitypos` value is parsed by `FUN_1400d5f00` as three comma
separated floats using two comma searches and three `atof` calls. On success
the vector is stored at animation offsets `+0x190`, `+0x194`, `+0x198`.

confirmed: `entityrot` value is parsed by the same `FUN_1400d5f00` helper as
three comma separated floats. On success it is stored at animation offsets
`+0x19c`, `+0x1a0`, `+0x1a4`, then each component is multiplied by
`DAT_140de7b04`. Raw memory at `0x140de7b04` is `35 fa 8e 3c`, float
`0.017453292`, so `entityrot` values are degrees converted to radians.

confirmed: `speedupfactor` is parsed through `strtod`. The default value is
`DAT_140de2b44`, raw bytes `00 00 80 3f`, float `1.0`. The apply helper
`FUN_1400d34c0` updates animation speed at `animation + 0x168`; if event
records exist at `+0x170/+0x180`, it rescales each event record's time/value at
record offset `+0x04` by `oldSpeed / newSpeed`.

confirmed: `FUN_1400e0330` later consumes the applied `entitypos` and
`entityrot` fields. It compares `animation + 0x190` and `animation + 0x19c`
against sentinel `DAT_140de8cc0`; raw memory at `0x140de8cc0` begins
`ff ff 7f ff`, the same value initialized by `FUN_1400d3d80`. If not sentinel:

- `entitypos` contributes a translation output: it ORs output byte `+0x0d`
  with `2` and writes scaled vector components to `param_2[8..10]`.
- `entityrot` contributes a rotation output: it ORs output byte `+0x0d` with
  `1` and writes quaternion-like values to `param_2[4..7]`.

## Runtime Accuracy Model

For `SET6`, accuracy is determined by what the Workbench writer already stored:

- retained key indices: 16-bit frame/index values.
- component samples: 16-bit quantized values.
- per-channel base and scale/range fields from `HEAD`.

The reader reconstructs values from the stored 16-bit data. The important
operation visible in `FUN_1400d5160` is:

```text
value = uint16Sample * perChannelScale + base
```

So the runtime precision is quantization precision, not the writer's reduction
tolerances. The writer-side tolerances only decide which source frames are kept
before quantization.

## Evidence

- `ghidra-raw/ghidra-raw-dayzdiag-anm-reader.txt`: raw HTTP/decompiler dump.
- `DayZDiag_x64.exe`, `FUN_1400d4520`: opens IFF input, checks `ANIM`, accepts
  `SET4`/`SET5`/`SET6`, reads `HEAD` and `DATA`.
- `DayZDiag_x64.exe`, `FUN_1400d4520`: `DATA` branch calls `FUN_1400d5160` for
  translation, scale, and rotation streams.
- `DayZDiag_x64.exe`, `FUN_1400d5160`: reads optional retained index arrays and
  quantized component arrays; reconstructs direct values for inline/all-key
  streams as `uint16 * scale + base`.
- `DayZDiag_x64.exe`, `FUN_1400d3e00`: stores first/last retained index metadata
  from the loaded index stream.
- `DayZDiag_x64.exe`, memory at `0x140de9490`: contains packed string/table
  data for `ANIM`, `SET4`, `SET5`, `SET6`, `FPS`, and `HEAD`; `SET6` xref goes
  to `FUN_1400d4520`.
- `DayZDiag_x64.exe`, memory at `0x140de9490`: the same table also contains
  `DATA`, `EVNT`, and `CPRP`.
- `DayZDiag_x64.exe`, `FUN_1400d4520` at `0x1400d4fa4..0x1400d50cc`: `CPRP`
  branch reads count and name/value records.
- `DayZDiag_x64.exe`, `FUN_1400d4520` at `0x1400d4e3a..0x1400d4f9c`: `EVNT`
  branch reads count and event records.
- `DayZDiag_x64.exe`, `FUN_1400d4520` at `0x1400d498a`,
  `0x1400d4b47`, and `0x1400d4bfc`: copies the `HEAD` flag byte into runtime
  track offset `+0x64`.
- `DayZDiag_x64.exe`, `FUN_1400d4520` at `0x1400d4d79`,
  `0x1400d4d97`, and `0x1400d4de6`: uses bits `0x10`, `0x40`, and `0x20` of
  runtime track byte `+0x64` for stream-read control.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-nodediff.txt`: focused raw HTTP/decompiler dump for
  `CPRP`, `EVNT`, and `HEAD` flag-byte handling.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-scan.txt`: broad scan for instruction uses of
  runtime track offset `+0x64`.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-candidates-decompile.txt`: decompile of the
  highest-value `+0x64` reader/sampler candidates.
- `ghidra-raw/ghidra-raw-dayzdiag-track64-bit1-exact.txt`: exact `+0x64`/`0x01`
  instruction scan.
- `ghidra-raw/ghidra-raw-dayzdiag-bit1-candidate-decompile.txt`: decompile proving the
  exact `0x01` candidates are outside the ANM sampler/reader path.
- `ghidra-raw/ghidra-raw-dayzdiag-sampler-xrefs.txt`: xrefs into `FUN_1400d3e40` and
  `FUN_1400d4250`.
- `ghidra-raw/ghidra-raw-dayzdiag-sampler-d3e40-decompile.txt` and
  `ghidra-raw/ghidra-raw-dayzdiag-sampler-d4250-decompile.txt`: focused sampler decompile
  showing `+0x64` high-bit checks.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-offset-use-scan.txt`: broad offset scan for CPRP
  table/count fields `+0x178/+0x182`.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-usage-candidates.txt`: decompile of CPRP apply,
  copy/swap, init, and cleanup candidates.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-value-parser.txt`: decompile of comma-separated
  three-float parser `FUN_1400d5f00`.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-apply-xrefs.txt` and
  `ghidra-raw/ghidra-raw-dayzdiag-cprp-apply-caller.txt`: xref/caller proof that
  `FUN_1400d53b0` runs after `FUN_1400d4520`.
- `ghidra-raw/ghidra-raw-dayzdiag-cprp-entityposrot-use-scan.txt` and
  `ghidra-raw/ghidra-raw-dayzdiag-cprp-runtime-entityposrot.txt`: runtime use of applied
  `entitypos`/`entityrot` fields in `FUN_1400e0330`.

## Practical Consequence

For our converter:

- Keep using Workbench writer constants for export:
  - translation reduction `0.0005`
  - scale reduction `0.0005`
  - rotation reduction `0.000001`
  - quaternion slerp cutoff `0.999`
- For DayZ runtime loading, expect no recovery of dropped keys. The game reads
  exactly the retained/quantized streams in the `.anm`.
- If we write byte-identical ANM, DayZDiag should read the same data Workbench
  produced.
