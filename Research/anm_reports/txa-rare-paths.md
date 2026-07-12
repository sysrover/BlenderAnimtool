# TXA Rare Paths: CPRP, nodeDiff, and keys flags

Date: 2026-05-17

Scope: Workbench `workbenchApp.exe` static evidence only. Raw HTTP output is
saved in `anm/ghidra-raw/ghidra-raw-rare-txa-cprp-nodediff-keys-http.txt`.

## Summary

- `confirmed`: `custProps { custProp <name> <value> }` maps into the
  `TXA::Animation` custom-property array, then into the optional `CPRP` ANM
  chunk.
- `confirmed`: `nodeDiff <name> { ... }` is parsed by the same node parser as
  `node`, then sets the track byte at offset `+0x28`; `FUN_141067c00` maps that
  byte directly to writer flag bit `0x01`.
- `confirmed`: `keys` with no arguments enables both channel groups.
- `confirmed`: `keys t` enables only the translation channel group.
- `confirmed`: `keys q`, `keys s`, or `keys q s` enable the shared
  rotation/scale channel group.
- `confirmed`: no TXA parser path found in this pass sets the third track byte
  `+0x2b` to zero; all `FUN_141055e40` callers found pass the third channel
  byte as `1`, so writer bit `0x08` should stay clear for normal TXA/FBX-created
  tracks.

## Parser Evidence

`FUN_141057e50` is the top-level TXA animation block dispatcher:

- `animation` installs `TXA::ParseAnimation::vftable` at `0x141ca35c8`.
- `node` and `nodeDiff` install `TXA::ParseNode::vftable` at `0x141ca35a8`.
- `events` installs `TXA::ParseEvents::vftable` at `0x141ca3568`.
- `custProps` installs `TXA::ParseCustomProperties::vftable` at `0x141ca3588`.

`FUN_141057bb0` handles `event` records. It requires at least three parameters,
stores frame/name, and optionally stores value/user value before calling
`FUN_141055b40`.

`FUN_141057b30` handles `custProp` records. It requires at least three
parameters and calls `FUN_141055a40(param_2, name, value)`.

`FUN_141058410` handles nested `node`/`nodeDiff` and `keys` inside a node:

- For nested `node`/`nodeDiff`, it calls
  `FUN_141055e40(param_2, name, parentIndex, 0, 1, 1, 1)` and then writes
  `track + 0x28 = (token == "nodeDiff")`.
- For `keys` with only the command token, it writes both `track + 0x29 = 1` and
  `track + 0x2a = 1`.
- For `keys` with arguments, it first clears `track + 0x29` and `track + 0x2a`,
  then scans each argument:
  - first character `t` sets `track + 0x29 = 1`
  - first character `q` or `s` sets `track + 0x2a = 1`

`FUN_141057c80` handles fields inside `frame`:

- `q` writes quaternion fields at key offsets `+0x00..+0x0c`.
- `t` writes translation fields at key offsets `+0x10..+0x18`.
- `s` writes scale fields at key offsets `+0x1c..+0x24`.

## Writer Mapping

`FUN_141055e40` allocates a TXA track and stores its channel bytes:

- `param_5 -> track + 0x29`
- `param_6 -> track + 0x2a`
- `param_7 -> track + 0x2b`

`FUN_141067c00` converts the TXA track into the final writer context:

- `track + 0x28` maps directly into writer flag bit `0x01`.
- if `track + 0x29 == 0`, writer flag bit `0x02` is set.
- if `track + 0x2a == 0`, writer flag bit `0x04` is set.
- if `track + 0x2b == 0`, writer flag bit `0x08` is set.

The discovered callers of `FUN_141055e40` are:

- `FUN_141057e50` - top-level TXA node parser, passes `1,1,1`.
- `FUN_141058410` - nested TXA node parser, passes `1,1,1`.
- `FUN_140e75770` - FBX recursive node import path, passes `1,1,1`.
- `FUN_140e78260` - FBX differential/root path, passes the first channel byte
  from a live value but still passes the second and third bytes as `1,1`.

No discovered TXA syntax writes `track + 0x2b = 0`.

## Converter Impact

The current prototype behavior matches the decompiled TXA paths:

- `nodeDiff` sets ANM track flag `0x01`.
- absent translation keys set ANM track flag `0x02`.
- absent rotation/scale keys set ANM track flag `0x04`.
- `0x08` remains clear because Workbench does not expose a TXA parser token for
  clearing `track + 0x2b` in the observed paths.
- `custProps`/`custProp` should serialize as optional `CPRP` with a 16-bit count
  and two length-prefixed, null-terminated strings per record, matching
  `FUN_141068360`.

## Remaining Validation

`confirmed from Ghidra`: parser and writer mapping for these paths.

`not yet byte-validated`: a Workbench-generated TXA/ANM golden pair containing
`custProps`, `nodeDiff`, and isolated `keys t` / `keys q` / `keys s` channel
combinations. Such a pair would validate byte output for rare cases, but the
static algorithm is now covered by direct decompiler evidence.
