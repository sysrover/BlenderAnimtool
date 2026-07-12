# DayZ GUI Layout Ghidra Findings

Raw outputs:

- `ghidra-raw/ghidra-raw-dayz-gui-project-programs.txt`
- `ghidra-raw/ghidra-raw-dayz-gui-layout-semantics.txt`
- `ghidra-raw/ghidra-raw-dayz-gui-layout-target-xrefs.txt`
- `ghidra-raw/ghidra-raw-dayz-gui-widget-property-consumers.txt`
- `ghidra-raw/ghidra-raw-dayz-gui-function-dump.txt`

## Confirmed

- `DayZDiag_x64.exe` is loaded in the Ghidra project. See
  `ghidra-raw/ghidra-raw-dayz-gui-project-programs.txt`, lines showing
  `FILE DayZDiag_x64.exe path=/DayZDiag_x64.exe type=Program`.
- `DayZDiag_x64.exe` contains the layout option strings for `halign`,
  `valign`, `center_ref`, `left_ref`, `right_ref`, `top_ref`, `bottom_ref`,
  `hexactpos`, `vexactpos`, `hexactsize`, `vexactsize`, `visible`,
  `clipchildren`, `ignorepointer`, `image0`, `src alpha`, and
  `stretch mode`. See `ghidra-raw/ghidra-raw-dayz-gui-layout-semantics.txt` lines
  2393-2476.
- `FUN_1403e0bf0` registers base `WidgetClass` properties. It registers
  `visible` default `true`, `clipchildren` default `true`,
  `ignorepointer` default `false`, `position`, `halign`, `valign`,
  `hexactpos` default `false`, `vexactpos` default `false`,
  `hexactsize` default `false`, and `vexactsize` default `false`.
  See `ghidra-raw/ghidra-raw-dayz-gui-layout-target-xrefs.txt` lines 318-562.
- `FUN_1403de7a0` consumes the registered widget properties. It reads the
  boolean flags and builds widget flags, reads `halign` and `valign`, reads
  `priority`, reads `position` and `size`, then applies them to the widget.
  See `ghidra-raw/ghidra-raw-dayz-gui-function-dump.txt` lines 301-369.
- `FUN_1403e42a0` registers `ImageWidgetClass` image properties, including
  `image0`, `imageTexture`, `mode`, `src alpha`, `stretch`, `stretch mode`,
  `flip u`, `flip v`, `filter`, `rotation`, and `pivot`. See
  `ghidra-raw/ghidra-raw-dayz-gui-function-dump.txt` lines 418-690.

## Applied Extension Rules

- `visible=0` or `visible=false` hides that widget layer and its children.
- `hexactpos`/`vexactpos` and `hexactsize`/`vexactsize` are the px-vs-parent
  percentage switches; default is false, so values are relative to parent.
- `halign`/`valign` are read before `position` and affect final placement.
- Property lookup in the preview should be case-insensitive, matching the
  Ghidra-observed property registration/lookup model.

## Unknown

- The exact enum integer mapping for `left_ref`/`center_ref`/`right_ref` was
  not recovered here; the strings are confirmed in `DayZDiag_x64.exe`, but the
  enum table/xrefs need a deeper data-structure trace.
