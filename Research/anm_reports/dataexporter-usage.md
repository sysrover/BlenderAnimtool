# Using dataExporter_v141_x64_RetailDX11.dll

## Practical Answer

confirmed: the DLL exposes callable Windows x64 exports. Runtime testing shows
that the plain names `ShowExportDialog` and `ShowExportDialogThread` are not
exported; use decorated names or ordinals:

- `ShowExportDialog`, ordinal `4`, address `0x1800ba700`
- `ShowExportDialogThread`, ordinal `5`, address `0x1800ba990`
- `ShowAnimExportDialogThread2`, ordinal `6`, address `0x1800b7b90`

likely: `ShowExportDialog(HWND*)` is still the simplest first experiment. It constructs
its own `QApplication`, creates an `ExportDialog`, optionally parents the Qt
window to the passed `HWND`, calls `QWidget::show`, then enters
`QApplication::exec`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` line 1515: export
  `ShowExportDialog`, ordinal `4`, decorated name
  `?ShowExportDialog@@YAHPEAUHWND__@@@Z`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` line 1546:
  `QApplication::QApplication`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` line 1559:
  `QSettings::QSettings` with `Bohemia Interactive` / `BIExporterMB`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` line 1576:
  optional `SetParent(hWndChild, param_1)`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1583-1584:
  `QWidget::show` and `QApplication::exec`.
- `dataexporter-runtime-test.md`: runtime probe confirms `LoadLibrary` works
  and resolves ordinals `#4`, `#5`, and `#6`.

## Minimal C# Host Shape

Use a 64-bit process. Put the DayZ Tools `Bin\Workbench` directory on the DLL
search path before calling the export, because the DLL depends on the Workbench
Qt/runtime DLL set.

Also configure Qt plugin discovery before the first Qt/DLL call:

- set `QT_PLUGIN_PATH` to the Workbench directory.
- set `QT_QPA_PLATFORM_PLUGIN_PATH` to `Workbench\platforms`.
- set current directory to the Workbench directory.
- write `qt.conf` beside the host executable with `[Paths] Plugins=<Workbench>`.

```csharp
using System;
using System.Runtime.InteropServices;

internal static class DataExporter
{
    [DllImport(
        @"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench\dataExporter_v141_x64_RetailDX11.dll",
        EntryPoint = "#4",
        CallingConvention = CallingConvention.Cdecl)]
    internal static extern int ShowExportDialog(IntPtr parentHwnd);
}

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        // Pass IntPtr.Zero first. Passing a real HWND only changes parenting.
        int result = DataExporter.ShowExportDialog(IntPtr.Zero);
        Console.WriteLine(result);
    }
}
```

confirmed: the calling convention is `__cdecl` in the decompiler comment for
`ShowExportDialog`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1515-1521:
  `int __cdecl ShowExportDialog(HWND__ *param_1)`.

runtime caveat:

- without Qt plugin configuration, the call fails with the Qt
  `platform plugin "windows"` error.
- with `QT_QPA_PLATFORM_PLUGIN_PATH`, current directory, and `qt.conf`
  configured, `ShowExportDialog(IntPtr.Zero)` opens the `TXA Export Dialog`.
  See `dataexporter-runtime-test.md`.

## Threaded Export Dialog

confirmed: `ShowExportDialogThread(HWND*)` is exported, but its decompile does
not pass the caller's `HWND` into `CreateThread`; it creates a worker with
`LPVOID 0`, waits for it, closes the handle, restores thread priority, and
returns `1`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` line 1597: export
  `ShowExportDialogThread`, ordinal `5`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1614-1615:
  `CreateThread(..., FUN_1800baa20, (LPVOID)0x0, ...)` and
  `WaitForSingleObject`.

Usage implication:

- likely: this export is useful only if you want the DLL to own the dialog
  thread and do not need parent-window attachment.
- unknown: the worker function `FUN_1800baa20` still needs a focused decompile
  before treating this as better than direct `ShowExportDialog`.

## Animation/TXA Dialog Entry

confirmed: `ShowAnimExportDialogThread2` is exported at ordinal `6`, address
`0x1800b7b90`.

unknown: its external ABI is not resolved enough for safe direct use. Ghidra
shows five parameters:

```c
ShowAnimExportDialogThread2(
    undefined8 param_1,
    undefined8 param_2,
    char param_3,
    undefined1 *param_4,
    QWidget param_5)
```

confirmed: `param_3` chooses between direct dialog execution and a worker-thread
path. When `param_3 == 0`, the function constructs a Qt application/dialog,
shows it, and calls `QApplication::exec`. Otherwise it uses `CreateThread`,
waits for completion, and then repeats export work while a flag remains set.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1623-1628: export and decompiled
  five-argument signature.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` line 1676: `if (param_3 == '\0')`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1695-1696:
  direct path shows widget and enters `QApplication::exec`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1715-1716 and 1732-1733:
  threaded path uses `CreateThread` and `WaitForSingleObject`.
- `ghidra-raw/ghidra-raw-dataexporter-usage.txt` lines 1707 and 1727:
  export action calls `FUN_1800ae930`.

Usage implication:

- do not call `ShowAnimExportDialogThread2` from C# yet unless the first two
  pointer/object parameters and `QWidget` parameter are resolved from a caller.
  It is probably the more relevant TXA/ANM take-export UI, but the ABI is not
  stable enough from this pass alone.

## Ordinal #6 Runtime ABI Probe

confirmed: the C# probe now contains an experimental `anim-empty` mode that
allocates a minimal `IAnimExporterAcc`-shaped object with callback slots at the
offsets recovered from `FUN_1800ae930`.

Runtime result:

- `dotnet run --project tools\DataExporterProbe\DataExporterProbe.csproj --no-build -- anim-empty`
  loads the DLL and resolves ordinal `#6`, then crashes with `0xC0000005`
  before any fake callback logs.
- `anim-empty-both` and `anim-empty-4arg` were also tested and crash the same
  way before callback logging.

confirmed: the crash happens before the recovered callbacks at offsets `0x08`,
`0x18`, `0x40`, `0x48`, `0x50`, `0x58`, or `0x60` are reached.

Evidence:

- `tools\DataExporterProbe\Program.cs`: `anim-empty`, `anim-empty-both`, and
  `anim-empty-4arg` modes.
- runtime console output from the three tests: all resolve ordinal `#6` and then
  terminate with `Fatal error. 0xC0000005`.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-disasm.txt` lines 198-244:
  disassembly shows `RDX` is stored as the host/export object, `R8B` selects
  mode, `R9` is the profile-path string pointer, and the stack byte is stored at
  context offset `0x60`.

Practical implication:

- do not use ordinal `#6` directly from managed C# for real export yet.
- a native C++ shim is still the right implementation path, but it must recover
  the full caller context and any hidden state expected before
  `FUN_1800abcb0`/Qt dialog construction.

## Deeper Ordinal #6/Dialog ABI Notes

confirmed: `ShowAnimExportDialogThread2` builds a `0x68` byte context object.
The decompile stores its second argument into context offset `0x00`, stores the
profile/style path string into the context string area beginning at `0x40`, and
stores the fifth argument at context offset `0x60`.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` lines 263-289:
  `operator_new(0x68)`, `*(undefined8 *)pQVar4 = param_2`, string initialization
  at offsets `0x20`/`0x28`/`0x30`, path copy through `FUN_1800b2d40`, and
  `pQVar4[0x60] = param_5`.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` lines 291-308:
  direct mode constructs `QApplication` through `FUN_1800b9c30`, then calls
  `FUN_1800abcb0(..., *(undefined8 *)lpParameter, ..., lpParameter + 8, ...,
  lpParameter[0x60])`.

confirmed: the animation dialog constructor stores the host object in the dialog
at offset `0x148`, stores the context at offset `0x170`, and then calls
`FUN_1800afd70` during construction. That means the dialog can touch the host
before the user presses Export.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` lines 1127-1141:
  `FUN_1800abcb0` calls `QDialog::QDialog`, stores the app pointer at `+0x140`,
  and stores the context pointer at `+0x170`.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` line 1193:
  `FUN_1800abcb0` stores its host/export object parameter at dialog offset
  `+0x148`.
- `ghidra-raw/ghidra-raw-dataexporter-showanim-deep.txt` lines 1344-1384:
  constructor fills context base/profile path fields and calls
  `FUN_1800afd70(*(dialog+0x170), *(dialog+0x150), dialog)`.

confirmed: the dialog table-population path calls the host object immediately.
`FUN_1800b2260` uses dialog offset `+0x148` as the host pointer, calls vtable
offset `0x08` for take count, and calls vtable offset `0x18` once for each take
row.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1421-1428:
  table headers are `Valid`, `Exp`, `Take`, `File`, `Profile`, `DiffTarget`,
  `FPS`, and `Quant`.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1445-1455:
  if dialog byte `+0x1b8` is set, the table also adds `SFrame` and `EFrame`.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1479-1484:
  host callback at vtable offset `0x08` returns count, and callback at `0x18`
  returns the take metadata pointer.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1494-1600:
  returned take metadata fields are read at offsets `0x00`, `0x01`, `0x08`,
  `0x10`, `0x18`, and `0x20`.
- `ghidra-raw/ghidra-raw-dataexporter-dialog-populate.txt` lines 1661-1687:
  optional frame columns read metadata offsets `0x30` and `0x34`.

usage implication:

- the host object cannot be only an export-loop stub. It must also survive
  construction-time table population and return stable take metadata if the
  count is nonzero.
- the current managed empty-host should have reached the count callback if the
  ordinal `#6` call frame and host object were fully correct. Because it crashes
  before callback logging, the unresolved part is likely earlier than
  `FUN_1800b2260`: either the external ABI/call frame, a Qt object parameter,
  or a native C++ object/layout assumption around the constructor path.

## What This DLL Can and Cannot Do For ANM

confirmed useful:

- load the DLL from a C# x64 process.
- resolve dialog exports by ordinal/decorated name.
- open the TXA export dialog via ordinal `#4`.
- build `.txa`/`.anm` output filenames from selected takes.
- run the native export UI far enough to prove the Qt/runtime setup.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-callable-surface.txt` lines 393-394:
  `FUN_1800af8c0`.
- `ghidra-raw/ghidra-raw-dataexporter-callable-surface.txt` lines 483 and 489:
  selection between string data at `DAT_180900a98` and `DAT_180900aa0`,
  previously byte-searched as `.txa` and `.anm`.
- `ghidra-raw/ghidra-raw-dataexporter-callable-surface.txt` lines 497, 507, 511, 577,
  and 620: `TXAExportDialog` UI text including `TXA Export Dialog`,
  `Export Select:`, `Plot Takes`, and `Export all valid and selected takes`.

not yet proven:

- populated export rows without host-provided scene/take data.
- a clean public API to convert FBX to `.anm`.
- a clean public API to convert TXA to `.anm`.
- a direct public writer API accepting input/output paths.

## Result Of Tracing The Next Boundary

confirmed: `FUN_1800ae930` is the export boundary called by
`ShowAnimExportDialogThread2`. It is not a path-only converter. It consumes a
host callback object through `param_2`, then asks that object for take count,
take metadata, key data, cleanup, and differential-pose data.

Evidence:

- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 310-314:
  callbacks at vtable offsets `0x08` and `0x18`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 381-383:
  callback at `0x40`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 413, 873-875, 1048:
  callbacks at `0x48`, `0x50`, and `0x58`.
- `ghidra-raw/ghidra-raw-dataexporter-ae930-trace.txt` lines 553-555:
  differential-pose callback at `0x60`.

Practical conclusion:

- direct C# `P/Invoke` can open the dialog, but cannot perform real export
  unless we also provide the host callback interface expected by the DLL.
- the next usable implementation path is a native x64 shim that implements the
  callback vtable and reproduces the missing host-side state after its ABI is
  fully recovered from Ghidra.
- see `dataexporter-export-boundary.md` for the decompiled export loop and
  current callback map.
