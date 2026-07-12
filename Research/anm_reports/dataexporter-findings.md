# dataExporter DLL Findings

## Scope

confirmed: Ghidra project `test` contains a loaded program named
`dataExporter_v141_x64_RetailDX11.dll`. The MCP current program remained
`workbenchApp.exe`, so `DataExporterAnmResearch.java` opened the DLL by
`DomainFile` path `/dataExporter_v141_x64_RetailDX11.dll`.

Evidence:

- `ghidra-raw/ghidra-raw-project-programs.txt`: project listing includes
  `/dataExporter_v141_x64_RetailDX11.dll`.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 188-191:
  `TARGET_PROGRAM dataExporter_v141_x64_RetailDX11.dll`, path, image base
  `0x180000000`, language `x86:LE:64:default`.

## Export Dialog Surface

confirmed: the DLL contains the animation export dialog surface and an
exported entry-point name.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 197-213:
  `AnimExportDialog`, `OnButtonExport`, `AnimExportDialogProfile*`, and
  `TXAExportDialog` strings.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 874-878:
  exported-name strings `?ShowExportDialog@@YAHPEAUHWND__@@@Z` and
  `ShowAnimExportDialogThread2`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1515, 1597, and 1623:
  external entry points `ShowExportDialog`, `ShowExportDialogThread`, and
  `ShowAnimExportDialogThread2`.

confirmed: `ShowExportDialog(HWND*)` constructs a `QApplication`, creates an
`ExportDialog`, optionally parents the dialog window with `SetParent`, shows the
widget, and enters `QApplication::exec`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1546, 1576, and 1583-1584.

confirmed: `FUN_1800ab7a0` is a save-file dialog path for animation takes. It
uses the filter `Anm files (*.anm *.txa);;All files (*.*)` and title
`Select File for Take`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 209-211: string and xref to
  `FUN_1800ab7a0`.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 255-256: decompile constructs
  the filter/title strings and calls `QFileDialog::getSaveFileName`.

## Extension and FBX Search Result

confirmed: raw byte scan in the DLL found `.anm` and `.txa` but did not find
`.fbx`, `FBX`, `Autodesk_Cache_File`, or `Alias_Cache_File`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 896-901:
  `.anm` and `.txa` byte hits, both with hits referenced from `FUN_1800af8c0`.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 902 and 932-934:
  zero hits for `.fbx`, `FBX`, `Autodesk_Cache_File`, and `Alias_Cache_File`.

likely: FBX import/export handling remains primarily in `workbenchApp.exe` for
this pass; `dataExporter_v141_x64_RetailDX11.dll` appears focused on animation
export dialogs, RTM/config animation parsing, skeleton validation, and data
export support.

## RTM Animation Reader Evidence

confirmed: the DLL also contains an RTM animation reader path. `FUN_1806d3aa0`
compares against `RTM_0100` and `RTM_0101`; the old-format branch raises
`Old format used in animation %s`, and the bad-format path raises
`Bad animation file format in file '%s'.`

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 774-808:
  `RTM_0100`, `RTM_0101`, `Broken animation file`, old-format, and bad-format
  strings, all around `FUN_1806d3aa0`/reader paths.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 717-733:
  decompile compares `RTM_0100`, emits old-format error, then compares
  `RTM_0101`.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` line 884:
  bad animation format error path.

## Skeleton and Keyframe Validation

confirmed: `FUN_1806d4720` reads skeleton configuration entries named
`skeletonInherit` and `skeletonBones`, then validates entry counts and parent
relationships.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 937 and 987:
  config lookups for `skeletonInherit` and `skeletonBones`.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` line 1002:
  `Error: Bad entry count in %s skeleton`.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 784-796:
  skeleton validation strings such as duplicate bone, self-parent, invalid
  parent bone, and hierarchy-cycle errors.

confirmed: `FUN_18070cda0` parses a `#Animation#` block and requires a
`keyframe` property when keyframe animations are present.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` line 3244:
  `#Animation#` tag comparison.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 3990-3998:
  lookup of `keyframe`, `atoi`, and error `Key frame animation, no 'keyframe'
  property`.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 4013-4022:
  parser error paths `Bad format`, `Error loading tag`, and `Bad object.`

## Export Boundary

confirmed: `FUN_1800ae930` is the DLL's actual export loop reached from
`ShowAnimExportDialogThread2`. It iterates host-provided takes, matches export
profiles, creates a `TXA::Animation`, requests key data from the host object,
and calls `FUN_1800b1820` for final save.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 190-195 and 248:
  `FUN_1800ae930` identity, callers, and decompile signature.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 310-327:
  take count, take metadata, and profile matching.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 381-416:
  host prepare callback, `FUN_1800afc00`, per-channel export, and final
  `FUN_1800b1820` save call.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 873-875:
  key data is supplied by a host callback at vtable offset `0x50`.

confirmed: real export requires a host callback object. The DLL UI can be
called from C#, but a successful export is not just `inputPath -> outputPath`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 310-314, 381-383, 413,
  553-555, 873-875, and 1048 show calls through `param_2` vtable offsets
  `0x08`, `0x18`, `0x40`, `0x48`, `0x50`, `0x58`, and `0x60`.

confirmed: the final DLL save helpers are now decompiled enough to use as a
cross-check for the Workbench ANM writer.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: `FUN_1800b1820` calls text TXA
  writer `FUN_1807e4a50`, builds a binary writer context with `FUN_1807f68b0`,
  zeroes the three reduction threshold globals, and calls binary writer
  `FUN_1807f7010`.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: `FUN_1807f68b0` reads the same
  TXA animation offsets used by Workbench: FPS `+0x80`, numFrames `+0x84`,
  tracks `+0x50/+0x5c`, events `+0x60/+0x6c`, and custom properties
  `+0x70/+0x7c`.
- `ghidra-raw/ghidra-raw-dataexporter-save-deep-http.txt`: `FUN_1807f7010` emits
  `ANIM`/`SET6` with `FPS`, `HEAD`, `DATA`, optional `EVNT`, and optional
  `CPRP`.
- `ghidra-raw/ghidra-raw-dataexporter-writer-primitives-http.txt`: `FUN_1807f8510`
  quantizes clamped 16-bit float streams, and `FUN_1807f8700` writes retained
  16-bit frame/index values from writer key offset `+0x28`.

## Open Questions

- unknown: the `ShowAnimExportDialogThread2` ABI is not resolved enough for
  safe direct use; see `dataexporter-usage.md`.
- unknown: the exact relationship between DLL `FUN_1806d3aa0` and Workbench
  `FUN_140b896c0`; both read `RTM_0100`/`RTM_0101`, but this pass has not
  proven shared source identity beyond similar decompiled behavior and strings.
