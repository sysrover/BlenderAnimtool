# dataExporter Runtime Probe

## Harness

Created a local x64 .NET probe:

- `tools/DataExporterProbe/DataExporterProbe.csproj`
- `tools/DataExporterProbe/Program.cs`

The probe:

- calls `SetDllDirectory` with
  `C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench`
- sets `PATH`, `QT_PLUGIN_PATH`, and `QT_QPA_PLATFORM_PLUGIN_PATH`
- sets current directory to the Workbench directory
- writes `qt.conf` beside the probe executable with `[Paths] Plugins=...`
- calls `LoadLibrary` on `dataExporter_v141_x64_RetailDX11.dll`
- resolves export names and ordinals with `GetProcAddress`
- can call ordinal `#4` / `#5` through P/Invoke

## Load Result

Command:

```powershell
dotnet run --project tools\DataExporterProbe\DataExporterProbe.csproj -- load
```

Result:

```text
qt.conf: C:\Users\sysro\diag\CsharpModVScode\tools\DataExporterProbe\bin\Debug\net9.0\win-x64\qt.conf
Mode: load
Process: x64
DLL: C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench\dataExporter_v141_x64_RetailDX11.dll
CurrentDirectory: C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench
QT_PLUGIN_PATH: C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench
QT_QPA_PLATFORM_PLUGIN_PATH: C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench\platforms
LoadLibrary: 0x7FFB552E0000
ShowExportDialog: <missing>
ShowExportDialogThread: <missing>
ShowAnimExportDialogThread2: 0x7FFB5534C1E0
?ShowExportDialog@@YAHPEAUHWND__@@@Z: 0x7FFB5534EFC0
?ShowExportDialogThread@@YAHPEAUHWND__@@@Z: 0x7FFB5534F250
ordinal 4: 0x7FFB5534EFC0
ordinal 5: 0x7FFB5534F250
ordinal 6: 0x7FFB5534C1E0
```

confirmed:

- The DLL loads successfully in a 64-bit .NET process when the Workbench
  directory is on the DLL search path.
- `ShowExportDialog` is not exported by undecorated name.
- `ShowExportDialogThread` is not exported by undecorated name.
- `ShowAnimExportDialogThread2` is exported by plain name.
- `ShowExportDialog` is callable by decorated name
  `?ShowExportDialog@@YAHPEAUHWND__@@@Z` or ordinal `#4`.
- `ShowExportDialogThread` is callable by decorated name
  `?ShowExportDialogThread@@YAHPEAUHWND__@@@Z` or ordinal `#5`.
- `ShowAnimExportDialogThread2` is ordinal `#6`.

## Dialog Call Result

Initial call without Qt plugin configuration showed:

```text
This application failed to start because it could not find or load the Qt platform plugin "windows" in "".
```

Fix applied in `tools/DataExporterProbe/Program.cs`:

- `QT_PLUGIN_PATH = C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench`
- `QT_QPA_PLATFORM_PLUGIN_PATH = C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\Workbench\platforms`
- process current directory set to the Workbench directory
- `qt.conf` written next to `DataExporterProbe.exe` with plugin root set to
  Workbench

Command:

```powershell
dotnet run --project tools\DataExporterProbe\DataExporterProbe.csproj -- show
```

confirmed runtime result:

- The native UI opens successfully.
- The window title is `TXA Export Dialog`.
- Visible controls include `All Valid`, `None`, `Current`, `Show Valid`,
  `Show All`, `Validate All`, `Create Profile`, `Reload Profiles`,
  `Plot Takes`, `Plot`, `Copy Values`, `Paste Values`, `Save Values`,
  `Export`, and `Cancel`.

Observed console output reaches:

```text
Calling ShowExportDialog(IntPtr.Zero). Close the dialog to return.
```

The dialog remains open until closed by the user.

Command:

```powershell
dotnet run --project tools\DataExporterProbe\DataExporterProbe.csproj -- thread
```

Observed output ended after:

```text
Calling ShowExportDialogThread(IntPtr.Zero). Close the dialog to return.
```

Process exit code: `1`.

Interpretation:

- confirmed: the ordinal calls transfer control into the native exports.
- confirmed: ordinal `#4` can launch the TXA export dialog in a standalone x64
  C# host when Qt plugin discovery is configured correctly.
- unknown: whether the open dialog can export useful `.txa`/`.anm` without the
  original DCC/Workbench host state populated.
- likely: the UI opens, but useful export rows require host-provided take/scene
  data or profile state.

## What We Can Do Now

confirmed practical:

- load the DLL from C# x64.
- resolve and call exported dialog functions by ordinal/decorated name.
- launch the TXA export dialog using ordinal `#4`.
- use Ghidra evidence plus runtime export resolution to map the public surface.

not yet practical:

- direct FBX-to-ANM conversion.
- direct TXA-to-ANM conversion.
- direct path-based `.anm` writer invocation.
- populated export list/profile execution without identifying the host data
  handoff.

Next practical target:

- reverse `FUN_1800ae930`, because `ShowAnimExportDialogThread2` calls it after
  export choices are collected. If that function takes resolved paths/profile
  structures, it may reveal the non-UI export boundary.
