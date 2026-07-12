# Workbench ANM Pipeline

## Evidence Summary

- confirmed: `workbenchApp.exe` was the loaded Ghidra program for both raw
  extraction scripts. See `ghidra-raw/ghidra-raw-exact-strings.txt` lines 163-164 and
  `ghidra-raw/ghidra-raw-target-functions.txt` lines 163-164.
- confirmed: Workbench contains a UI action at `FUN_140ebdce0` that selects
  `.fbx` files and shells out to an external ANM converter command:
  `FBXConverter.exe -anm -bin -simplename "%s" "%s/%s"`.
- confirmed: Workbench validates animation paths as `.anm` in `FUN_140efc710`.
  String `Wrong path to animation (has to end with .anm):` at `0x141c69108`
  is referenced from `0x140efcd3f`.
- confirmed: loaded DLL `dataExporter_v141_x64_RetailDX11.dll` contains an
  animation export save dialog path. `FUN_1800ab7a0` builds
  `Anm files (*.anm *.txa);;All files (*.*)` and `Select File for Take`, then
  calls `QFileDialog::getSaveFileName`.
- confirmed: the current Workbench in-process conversion pipeline is
  `FBXAnimResourceClassWB::slot+0xc0` (`FUN_140fc9fc0`) ->
  `FUN_140e75c10` -> `TXA::Animation` -> `FUN_141067c00` ->
  `FUN_141068360`.
- confirmed: TXA files parse into the same `TXA::Animation` object through
  `FUN_141057800` / `FUN_141058e60`, then use the same
  `FUN_141067c00` / `FUN_141068360` writer path for `.anm`.

## `.anm` Path Validation

`FUN_140efc710` is the strongest current Workbench-side `.anm` pipeline anchor.
The decompile checks a constructed/selected path extension using
`QString::operator!=(local_c0, ".anm")`; on mismatch it builds a message from
string `0x141c69108` and displays it through `QMessageBox::setText` followed by
`QDialog::exec`.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1196-1198: string/xref/function.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1464-1470: extension check and dialog.
- `ghidra-raw/ghidra-raw-target-functions.txt`: target `140efc710`.
- `ghidra-raw/ghidra-raw-dataexporter-anm-research.txt` lines 209-211: DLL filter string
  and xref from `FUN_1800ab7a0`.
- `ghidra-raw/ghidra-raw-dataexporter-functions.txt` lines 255-256: DLL decompile builds
  the filter and dialog caption.

## Serialization Direction

confirmed: `FUN_140efc710` writes structured animation fields through repeated
calls to `FUN_140ed6a50`. The function writes:

- a leading block from `param_1 + 0x80`, length `4`.
- a selected resource/index value derived from a tree/list lookup.
- scalar byte fields from offsets `0xc0`, `0xc1`, `0xc6`, `0xc2`, `0xc3`,
  `0xc5`, `0xc4`.
- a 4-byte value at `param_1 + 0x84`.
- list/tree child records via `FUN_140ef5800` and `FUN_140ef43e0`.

Evidence:

- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1248-1257: initial serializer calls.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1412-1422: scalar field writes.
- `ghidra-raw/ghidra-raw-exact-strings.txt` lines 1474-1519: recursive/list item writes.

## Open Pipeline Gaps

- likely: `FUN_140efc710` is a Workbench project/resource serializer path, not
  the final binary animation writer documented here. Its exact UI caller chain is
  lower priority for standalone converters because the Ghidra-confirmed final
  in-process binary writer is `FUN_141068360`.
- confirmed: `FUN_140eb8840` configures the `AnimFileBrowser` with `anm`,
  `txa`, and `age` filters, so TXA is visible to the Workbench animation browser.
- confirmed: the TXA parser/conversion path is now traced separately:
  `FUN_141057800` parses TXA into `TXA::Animation`, `FUN_141067c00` builds the
  writer context, and `FUN_141068360` writes binary `ANIM`/`SET6`.
- confirmed: Workbench resource registration can classify `.fbx` as either
  `FBXResourceClass` or `FBXAnimResourceClass` after an ambiguity prompt.
- confirmed: `FBXAnimResourceClassWB` has an in-process conversion path.
  Its constructor registers `AnimationName` default `Take 001` and `FPS` default
  `30`; its vtable slot `+0xc0` points to `FUN_140fc9fc0`.
- confirmed: `FUN_140fc9fc0` calls `FUN_140e75c10`, which opens/selects an FBX
  animation take, builds a `TXA::Animation`, appends `.anm`, and writes via
  `FUN_141068360`.
- confirmed: `FUN_140e75770` and `FUN_140e78260` populate TXA tracks by
  sampling FBX transforms at `frameIndex / (frameCount - 1) * duration`.
- confirmed: `FUN_141068360` writes `ANIM` -> `SET6` -> `FPS`/`HEAD`/`DATA`
  and optional `EVNT`/`CPRP` chunks, with 16-bit retained-index and quantized
  float streams.
- confirmed: the `FBXConverter.exe -anm` branch exists, but it is not the only
  FBX-to-ANM path and is likely an older/manual UI action.
- likely: `dataExporter_v141_x64_RetailDX11.dll` participates in the export UI
  side for takes/animations. Workbench-side converter implementation should use
  `workbenchApp.exe` evidence first; DLL direct-use ABI remains a separate
  runtime-host problem.

Current remaining blockers for implementation confidence:

- byte-level equivalence is confirmed for the current Workbench TXA/ANM golden
  pair; additional controlled inputs are still needed for events, custom
  properties, and less common TXA flag/range cases.
- TXA tags are parsed/stored, but current Ghidra evidence says they are not
  copied into the final `ANIM`/`SET6` writer context.
- FBX import should target FBX major 6/7 compatible with the embedded 2016.1.1
  FBX SDK; newer FBX major versions are rejected by importer code.
