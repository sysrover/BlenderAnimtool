# Player IK ANM corpus

Date: 2026-05-17

Scope: `P:\DZ\anims\anm\player\ik\`, 654 `.anm` files. This file uses the
file corpus to discover variants, then cross-checks runtime meaning against
DayZDiag Ghidra evidence.

## Summary

- `confirmed`: 654 IK `.anm` files were parsed with the current ANM header
  layout; no parse errors.
- `confirmed`: all corpus files use `fps = 30`.
- `confirmed`: formats are mixed, not all `ANIMSET6`:
  - `ANIMSET5`: 359 files
  - `ANIMSET6`: 295 files
- `confirmed`: almost all IK poses are 2-frame poses:
  - 652 files have `numFrames = 2` on their tracks.
  - 2 files have `numFrames = 1`: `gear/gas_cooker.anm`,
    `gear/morphine.anm`.
- `confirmed`: the corpus is not only weapon files. Categories:
  `ammunition` 30, `attachments` 92, `camping` 3, `clothing` 14,
  `explosives` 10, `gear` 294, `heavy` 11, `two_handed` 78,
  `vehicles` 56, `weapons` 66.

Raw generated indexes:

- `anm/player-ik-anm-corpus.csv`
- `anm/player-ik-anm-corpus.json`

## IK track groups

The files split into several practical authoring groups:

| Count | Tracks present | Meaning for Blender skeleton |
|---:|---|---|
| 385 | `RightHand_Dummy`, `RightHandOrigin`, `RightForeArmDirectionOrigin`, `RightForeArmDirection` | right-hand/item pose only |
| 192 | full right + left helpers: `LeftHand_Dummy`, `RightHand_Dummy`, `LeftHandIKTarget`, `LeftForeArmDirection`, `LeftHandOrigin`, `LeftForeArmDirectionOrigin`, `RightHandOrigin`, `RightForeArmDirectionOrigin`, `RightForeArmDirection` | full two-hand weapon/item IK pose |
| 46 | `RightHand_Dummy`, `RightHandOrigin`, `RightForeArmDirection` | right-hand pose without origin-direction helper |
| 17 | `LeftHand_Dummy`, `RightHand_Dummy` only | hand dummy/finger pose, no full IK helpers |
| 9 | `LeftHand_Dummy`, `RightHand_Dummy`, `LeftHandIKTarget`, `LeftForeArmDirection`, `RightHandOrigin`, `RightForeArmDirection` | two-hand pose without origin-direction helpers |
| 5 | `RightHand_Dummy`, `RightHandOrigin` only | minimal right-hand pose |

Examples:

- Full two-hand: `weapons/sv98.anm`, `explosives/fireworkslauncher.anm`,
  `heavy/55galdrum.anm`.
- Right-hand only: `ammunition/00buck_10roundbox.anm`,
  `gear/book.anm`, `attachments/light/tlrlight.anm`.
- Minimal/legacy: `attachments/muzzle/optic_m4_carryhandle.anm`,
  `gear/baked_beans.anm`.

## Special name variant

`confirmed`: five files contain `RightForeHandDirection`, not
`RightForeArmDirection`:

- `attachments/muzzle/optic_m4_carryhandle.anm`
- `attachments/support/painkillers2.anm`
- `gear/baked_beans.anm`
- `gear/chest_holster.anm`
- `gear/waterproofbag.anm`

`confirmed`: `P:\DZ\anims\cfg\skeletons.anim.xml` contains
`RightForeArmDirection`, `LeftForeArmDirectionOrigin`, and
`RightForeArmDirectionOrigin`; no `RightForeHandDirection` line was found in
the workspace scan.

`confirmed`: DayZDiag Ghidra string search also found no
`RightForeHandDirection` string, while `AnimNodeWeaponIK` remap parsing uses
the AGR-provided names such as `ikpose_chainmiddledir`.

Implementation consequence: import can treat `RightForeHandDirection` as a
legacy alias for `RightForeArmDirection`; export should keep the canonical
`RightForeArmDirection` name.

## Track flags

`confirmed`: the corpus contains only `flags = 0` and `flags = 1`.

`confirmed`: DayZDiag DATA decoding checks channel frame-index bits `0x10`
position, `0x20` rotation, and `0x40` SET6 scale. It does not use low bit
`0x01` for key timing in the ANM reader path examined here.

Impact: the eight `two_handed/*.anm` files with `flags = 1` on forearm
direction tracks do not require a special Blender/import timing mode. Writing
`flags = 0` with explicit frame indices is valid for our exporter.

Detailed Ghidra evidence: `anm/dayzdiag-anm-track-flags.md`.

## DayZDiag evidence

- `confirmed`: `FUN_14010a800` is an anim-set-instance load path. It compares
  an input key with `"ikpose"` and loads the referenced animation object into
  `param_1[0xc]`. Raw: `anm/ghidra-raw/ghidra-raw-dayzdiag-ikpose-loader-14010a800.txt`.
- `confirmed`: `FUN_1401093e0` parses `AnimNodeWeaponIK` remap text keys:
  `hand`, `weapon`, `weaponrotator`, `weaponaxis`, `chain`, `secchain`,
  `chainaxis`, `secchainaxis`, `ikpose_chainoffset`,
  `ikpose_weaponoffset`, `ikpose_secchainoffset`,
  `ikpose_chainmiddledir`, `ikpose_secchainmiddledir`,
  `ikpose_chainmiddlediro`, `ikpose_secchainmiddlediro`,
  `outputweaponoffsettobuffer`. Raw:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-remap-1401093e0-refresh.txt`.
- `confirmed`: `FUN_140543140` registers script/event string
  `"RefreshIKPose"` and initializes a block of IK-related fields near
  `0x1994..0x1a1c` to `-1`. Raw:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-refresh-ikpose-140543140.txt`.

## Blender/tooling decisions

- The Blender authoring skeleton should contain the full helper superset:
  `LeftHand_Dummy`, `RightHand_Dummy`, `LeftHandIK`, `RightHandIK`,
  `LeftHandOrigin`, `LeftHandIKTarget`, `LeftForeArmDirection`,
  `LeftForeArmDirectionOrigin`, `RightHandOrigin`,
  `RightForeArmDirection`, `RightForeArmDirectionOrigin`.
- Export mode should not require every left-hand helper for every IK file.
  The corpus proves many valid DayZ IK poses are right-hand only.
- Full weapon/two-hand authoring should still export the full helper set,
  because player AGR nodes map `ikpose_secchainoffset` to `LeftHandIKTarget`
  and secondary chain middle direction to `LeftForeArmDirection`.

## Open questions

- `unknown`: exact meaning of low bit `0x01` in flags. It appears in eight
  `two_handed/*.anm` files, but DayZDiag evidence here shows no DATA-decode or
  key-timing effect.
- `unknown`: whether the five `RightForeHandDirection` legacy files are used
  by current runtime graphs or just preserved data. Workspace/Ghidra evidence
  points to canonical `RightForeArmDirection`.
