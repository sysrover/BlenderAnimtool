# dataExporter Export Boundary

## What The Runtime Dialog Proved

confirmed: ordinal `#4` opens the native `TXA Export Dialog` after Qt plugin
discovery is configured. That proves the DLL can be loaded and its UI can run
outside Workbench.

Evidence:

- `dataexporter-runtime-test.md`: C# probe resolves ordinal `#4` and opens the
  dialog after setting `QT_QPA_PLATFORM_PLUGIN_PATH`, current directory, and
  `qt.conf`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1515-1584:
  `ShowExportDialog(HWND*)` constructs `QApplication`, creates the dialog,
  shows it, and enters `QApplication::exec`.

## Main Export Function

confirmed: `FUN_1800ae930` is the export boundary called by
`ShowAnimExportDialogThread2`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 190-195:
  function `FUN_1800ae930` at `0x1800ae930`; callers include
  `ShowAnimExportDialogThread2`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` line 248:
  decompiler signature
  `undefined8 FUN_1800ae930(longlong *param_1,longlong *param_2,QString *param_3)`.

confirmed: the second parameter is a host/export-access object with a vtable.
The DLL repeatedly calls callbacks through offsets on `*param_2`; this means the
DLL is not a path-only TXA/ANM converter.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 310-314:
  callback at vtable offset `0x08` gets the take count, and callback at `0x18`
  gets take metadata.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 381-383:
  callback at `0x40` prepares or exports take raw data.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` line 413:
  callback at `0x48` performs cleanup/end-export work.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 553-555:
  callback at `0x60` gets differential-pose data.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 873-875:
  helper `FUN_1800af0c0` calls vtable offset `0x50` to get per-bone/channel
  key data.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` line 1048:
  callback at `0x58` releases key data.

## Export Algorithm Shape

confirmed: `FUN_1800ae930` loops over takes from the host object, matches each
take to a profile, prepares channel contexts, exports key data into a
`TXA::Animation` object, then finalizes/saves the output.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 310-327:
  take count and take metadata are fetched, then profile names are compared.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 331-369:
  channel context records are allocated with stride `0x28`; the code installs
  `AnimExportDialogCtxTransMod::vftable` and
  `AnimExportDialogCtxTransGen::vftable`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 375-386:
  after validation, the host prepare callback runs and `FUN_1800afc00` creates
  the animation object.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 389-400:
  profile channels are exported through `FUN_1800af0c0`, with a special branch
  for flag `0x10`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 414-416:
  successful per-channel export calls `FUN_1800b1820` to finalize/save.

confirmed: profile errors and export failures are reported as take-level
messages.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 443-446:
  `Take %s not exported: error preparing export`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 529-532:
  `Take %s not exported: no diff target specified`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 591-595:
  differential-pose export failure with missing bone/profile message.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 620-623:
  `Take %s not exported: profile %s missing`.

## TXA Animation Construction

confirmed: `FUN_1800afc00` creates a `TXA::Animation` object and opens/loads a
first output path before key export begins.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 660-662:
  function signature
  `undefined8 * FUN_1800afc00(undefined8 param_1,longlong *param_2,ulonglong param_3,int param_4)`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` line 678:
  calls `FUN_1800af8c0(..., 0, ...)` to build a first output path.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 680-699:
  allocates `0x88` bytes and initializes `TXA::Animation::vftable`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 705-710:
  opens the first path and initializes/loads the animation object through
  `FUN_1807e5c70`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 715-716:
  writes duration/count style fields at offsets `0x10` and `0x84`.

## Key Export

confirmed: `FUN_1800af0c0` exports one profile channel/bone. It requests key
data from the host callback, creates or finds a track in `TXA::Animation`, then
iterates keyframes and writes transform values into a track buffer.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 764-766:
  `FUN_1800af0c0` signature.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 833-849:
  channel profile entries use stride `0x20`; flags are read from entry offset
  `0x18`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 857-872:
  channel flags map to output flag values `0x10`, `0x20`, `0x30`, and `0x40`;
  lower bits select key components.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 873-883:
  host callback at vtable offset `0x50` supplies key data or raises
  `error exporting keys`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 890-895:
  track creation/lookup happens through `FUN_1807e4650` and `FUN_1807e4060`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 912-1046:
  keyframes are converted through transform math and written with stride
  `0x28`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 982-1007:
  non-orthonormal matrices are detected/repaired before output.

## Final Save Boundary

confirmed: `FUN_1800b1820` is the final save step after a `TXA::Animation`
object has been populated.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 1091-1095:
  `FUN_1800b1820` decompile signature.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 1129-1152:
  creates the first file wrapper and writes the animation through
  `FUN_1807e4a50`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 1166-1170:
  creates an error reporter and calls `FUN_1807f68b0`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 1175-1195:
  builds a second output path and calls `FUN_1807f7010`.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: HTTP decompile confirms the
  same save boundary and shows `FUN_1800b1820` zeroing the three reduction
  threshold globals before calling `FUN_1807f7010(local_80, local_48, 0, 1)`.

confirmed: `FUN_1807f68b0` is the DLL writer-context builder for the final
binary ANM path.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: reads FPS from animation
  offset `+0x80`, track table/count from `+0x50/+0x5c`, TXA key stride `0x28`,
  and emits writer key records with stride `0x2c`.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: maps TXA track byte `+0x28`
  directly and inverts TXA bytes `+0x29/+0x2a/+0x2b` into writer flag bits,
  matching the Workbench `FUN_141067c00` mapping.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: copies events and custom
  properties from animation offsets `+0x60/+0x6c` and `+0x70/+0x7c`.

confirmed: `FUN_1807f7010` is the DLL final binary ANM writer and is parallel
to Workbench `FUN_141068360`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: opens `ANIM` (`0x4d494e41`) and
  `SET6` (`0x36544553`), then writes `FPS`, `HEAD`, `DATA`, optional `EVNT`,
  and optional `CPRP`.
- `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt`: `FUN_1807f8510`
  quantizes floats as 16-bit clamped samples and is called by `FUN_1807f7010`.
- `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt`: `FUN_1807f8700` emits
  retained frame/index values from writer key offset `+0x28` and is called by
  `FUN_1807f7010`.

likely: `FUN_1800af8c0` mode `0` builds the `.txa` path and mode `1` builds the
`.anm` path. This is supported by the two mode calls in `FUN_1800b1820` and the
earlier byte/string mapping for `DAT_180900a98` and `DAT_180900aa0`, but the
mode-to-extension labels are not shown inline in the `FUN_1800b1820` decompile.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` line 678:
  `FUN_1800af8c0(..., 0, ...)`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` line 1175:
  `FUN_1800af8c0(..., 1, ...)`.
- `ghidra-raw/ghidra-raw-dataexporter-callable-surface.txt` lines 483 and 489:
  `FUN_1800af8c0` selects string data at `DAT_180900a98` or `DAT_180900aa0`.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 896-901:
  byte search identifies `.anm` and `.txa` hits referenced by `FUN_1800af8c0`.

## Practical Use Conclusion

confirmed: the DLL is usable as a dialog/runtime component, but actual export
requires an object implementing the host callback vtable consumed through
`param_2`.

likely minimum host surface:

- take count callback at vtable offset `0x08`.
- take metadata callback at `0x18`.
- prepare/export-take callback at `0x40`.
- cleanup/end callback at `0x48`.
- key-data callback at `0x50`.
- key-data release callback at `0x58`.
- differential-pose callback at `0x60` if differential export is used.

unknown: exact C++ class name, full ABI, and structure layouts for the host
object. The Ghidra evidence proves the callback offsets and usage pattern, but
not all parameter types.

confirmed: a managed empty-host probe is not enough. `DataExporterProbe`
implements a minimal callback vtable and tests three ordinal `#6` ABI variants;
each resolves the export and then crashes with `0xC0000005` before any callback
slot logs.

Evidence:

- `tools\DataExporterProbe\Program.cs`: `anim-empty`, `anim-empty-both`, and
  `anim-empty-4arg` modes.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-disasm.txt` lines 198-244:
  ordinal `#6` stores `RDX` into the dialog/export context as the host object
  and stores `R8B`, `R9`, and a stack byte into the same context.

likely: ordinal `#6` needs additional Workbench-side state beyond the visible
`IAnimExporterAcc` callback object, or it must be called from a native C++
context matching the original caller more closely.

## Dialog Population Before Export

confirmed: the animation export dialog has a pre-export population path. The
dialog constructor eventually calls `FUN_1800afd70`, and the table setup helper
`FUN_1800b2260` asks the host object for take data before any final save/export
work.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` lines 307-308:
  `ShowAnimExportDialogThread2` passes `*(undefined8 *)lpParameter` into
  `FUN_1800abcb0`; this is the host object originally stored from ordinal `#6`
  `param_2`.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` line 1193:
  `FUN_1800abcb0` stores that object at dialog offset `+0x148`.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` lines 1344-1384:
  the constructor finishes path setup and calls `FUN_1800afd70`.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1479-1484:
  `FUN_1800b2260` calls `(**(dialog+0x148)->vtable + 0x08)()` for take count
  and `(**(dialog+0x148)->vtable + 0x18)()` for take metadata.

confirmed: the take metadata returned by vtable offset `0x18` has at least this
layout as consumed by the dialog table:

| Offset | Use in dialog |
| --- | --- |
| `0x00` | `Valid` checkbox/state byte |
| `0x01` | `Exp` checkbox/state byte |
| `0x08` | `Take` C string |
| `0x10` | `File` C string |
| `0x18` | `Profile` C string |
| `0x20` | `DiffTarget` C string |
| `0x30` | optional `SFrame` integer |
| `0x34` | optional `EFrame` integer |

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1421-1428:
  base table headers.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1445-1455:
  optional `SFrame`/`EFrame` columns when dialog byte `+0x1b8` is nonzero.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1494-1600:
  metadata bytes and strings read from offsets `0x00`, `0x01`, `0x08`, `0x10`,
  `0x18`, and `0x20`.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1661-1687:
  optional frame values read from offsets `0x30` and `0x34`.

likely: this explains the current external-use boundary more precisely. A
working caller must either provide a real Workbench `IAnimExporterAcc` object or
implement a native-compatible substitute with the table-population callbacks,
the later export callbacks, and any construction-time object assumptions.

## Next Ghidra-Only Work

- Build golden-file tests against Workbench output to validate a standalone
  implementation byte-for-byte. The static DLL and Workbench algorithms are now
  bounded, but output validation is still outside Ghidra-only evidence.
- Trace the unresolved crash path before `FUN_1800b2260` callback logging:
  ordinal `#6` call frame, the fifth `QWidget`/flag argument, and constructor
  state consumed before the host callback at `0x08`.
- Rename the `param_2` callback slots in Ghidra once the caller-side class is
  found, then build a native shim only after the ABI is verified.
