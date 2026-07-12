# DayZDiag Weapon IK Findings

## Source

- `DayZDiag_x64.exe`
- Raw Ghidra dumps:
  - `ghidra-raw/ghidra-raw-dayzdiag-ik-string-search.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-ik-candidates-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-ik-helper-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-ik-nearby-strings.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-deep-offset-vtable.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-vtable-methods-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-offset-candidates-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-property-table3.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-slot2-callgraph-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-slot2-callees-decompile-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-cmd-dispatch-byte3-scan.txt`

Detailed current deep-pass notes are in
`dayzdiag-animnode-weaponik-deep.md`.

Solver input order, helper-point construction, and Blender skeleton rules are
tracked in `dayzdiag-weaponik-solver-model.md`.

Latest deep pass status:

- `confirmed`: `FUN_140108750` emits a `0x20` byte command with opcode `0x0c`
  at command offset `+0x3`.
- `confirmed`: `FUN_1400dec30 case 0x0c` consumes that command and performs
  `AnimNodeWeaponIK` runtime solving.
- `confirmed`: `FUN_1400e1be0` is the core chain IK math helper called by the
  opcode `0x0c` branch.
- `confirmed`: axis ids map to local directions through `FUN_1400e33b0`:
  `0=+X`, `1=+Y`, `2=+Z`, `3=-X`, `4=-Y`, `5=-Z`.

## Confirmed Runtime Shape

- `confirmed`: `AnimNodeWeaponIK` exists in DayZDiag. The class/name string is
  returned by `FUN_1401092a0` as `"AnimNodeWeaponIK"`.
- `confirmed`: `FUN_1401093e0` parses the WeaponIK remapping/config text stored
  at object offset `+0xf8`.
- `confirmed`: DayZDiag does not contain direct strings for
  `LeftHandOrigin`, `RightHandOrigin`, `LeftHandIKTarget`,
  `LeftForeArmDirection`, or `RightForeArmDirection`. Those names are therefore
  config/asset-provided names, not hardcoded executable names.

## Config Keys Parsed by DayZDiag

`FUN_1401093e0` recognizes these keys:

- `hand`
- `weapon`
- `weaponrotator`
- `chain`
- `secchain`
- `chainaxis`
- `secchainaxis`
- `weaponaxis`
- `ikpose_chainoffset`
- `ikpose_weaponoffset`
- `ikpose_secchainoffset`
- `ikpose_chainmiddledir`
- `ikpose_secchainmiddledir`
- `ikpose_chainmiddlediro`
- `ikpose_secchainmiddlediro`
- `outputweaponoffsettobuffer`

`confirmed`: `FUN_1401099f0` resolves a single config value to a bone id and
reports `config:: %s - bone doesn't exist` when the named bone is missing.

`confirmed`: `FUN_140109a60` parses comma-separated bone lists. It accepts up to
5 bones for `chain` / `secchain`, and exactly 2 bones for the `*middlediro`
pairs.

`confirmed`: `FUN_1401098c0` parses axis strings:

- `+x`
- `+y`
- `+z`
- `-x`
- `-y`
- `-z`

## Ghidra Deep Pass Notes

`confirmed`: `FUN_140108d00` allocates `0x230` bytes for
`enf::AnimNodeWeaponIK`, installs `enf::AnimNodeWeaponIK::vftable` at
`0x140decb30`, and initializes the remap fields to `0xff` / zero before config
parse.

`confirmed`: vtable/method decompile shows `FUN_140108540` is the load/parse
method that calls `FUN_1401093e0` and reports `Error parsing remmaping table`
when remapping fails.

`confirmed`: a broad Ghidra offset scan over `DayZDiag_x64.exe` found many
unrelated stack/local offset hits, so offsets alone are not enough to identify
the solver. The useful direct class evidence remains the constructor, vtable,
load method, remap parser, and name/list resolver helpers.

`likely`: downstream solver logic is reached through the normal animation graph
node evaluation path and not by a direct static call to `FUN_140108750`; Ghidra
`get_function_callers` for `0x140108750` found no direct callers, consistent
with virtual dispatch.

`confirmed`: Ghidra property table records at `0x14111fa70` identify the
positional `AnimNodeWeaponIK` AGR fields:

- `Child`
- `Config Name`
- `Config`
- `AimOn`
- `Prim On`
- `Sec On`
- `Blend In Time`
- `Blend Out Time`
- `Weapon Dir LR Angle`
- `Weapon Dir UD Angle`

This confirms the two numeric coefficients in player AGR nodes are blend-in and
blend-out times, not skeleton-bone parameters.

## Validation

`confirmed`: after parsing, `FUN_1401093e0` succeeds only when:

- `hand` resolved: field `+0x1b8 != 0xff`
- `weapon` resolved: field `+0x1bc != 0xff`
- `ikpose_weaponoffset` resolved: field `+0x1fc != 0xff`
- primary `chain` has more than 3 entries: byte `+0x1f0 > 3`

This means a WeaponIK setup is not just an animation with arbitrary IK helper
tracks. The graph/config must point to real skeleton bones and to real tracks
inside the IK pose animation.

## Player Graph Evidence

Local player graph search found repeated `AnimNodeWeaponIK` blocks in:

- `P:\DZ\anims\workspaces\player\player_main\master.agr`
- `P:\DZ\anims\workspaces\player\player_main\locomotion.agr`
- `P:\DZ\anims\workspaces\player\player_main\actions.agr`
- `P:\DZ\anims\workspaces\player\player_main\Combat.agr`
- `P:\DZ\anims\workspaces\player\player_main\Gestures.agr`
- `P:\DZ\anims\workspaces\player\player_main\Vehicles.agr`

The player graph maps the IK pose fields like this:

- `hand = RightHand`
- `weapon = RightHand_Dummy`
- `weaponrotator = RightArm`
- `weaponaxis = -x`
- `chain = RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand`
- `chainaxis = -x`
- `secchain = LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand`
- `secchainaxis = +x`
- `ikpose_chainoffset = RightHandOrigin`
- `ikpose_weaponoffset = RightHand_Dummy`
- `ikpose_secchainoffset = LeftHandIKTarget`
- `ikpose_chainmiddledir = RightForeArmDirection`
- `ikpose_chainmiddlediro = RightHandOrigin,RightForeArmDirectionOrigin`
- `ikpose_secchainmiddledir = LeftForeArmDirection`
- `ikpose_secchainmiddlediro = LeftHandOrigin,LeftForeArmDirectionOrigin`
- `outputweaponoffsettobuffer = true` in `locomotion.agr` `NormalWeaponIK`

This matches the missing Blender helper-bone problem: the addon previously made
only part of this set.

## Original Weapon IK ANM Evidence

Local `P:\DZ\anims\anm\player\ik\weapons\*.anm` inspection shows the weapon IK
files are `ANIMSET5`, `fps = 30`, and `numFrames = 2`.

Sample files `ak101.anm`, `m4a1_ik.anm`, and `cz75.anm` contain these special
tracks:

- `LeftHand_Dummy`
- `RightHand_Dummy`
- `RightHandOrigin`
- `RightForeArmDirectionOrigin`
- `RightForeArmDirection`
- `LeftHandIKTarget`
- `LeftForeArmDirection`
- `LeftHandOrigin`
- `LeftForeArmDirectionOrigin`

This confirms `LeftHandIKTarget` is not just an optional fallback name. It is a
real pose track consumed by the player `AnimNodeWeaponIK` config.

## Addon Changes

Files changed:

- `P:\BlenderAnimtool\DayzAnimationTools\Tools\AddSurvivorIK.py`
- `P:\BlenderAnimtool\DayzAnimationTools\Export\ExportTxa.py`
- `P:\BlenderAnimtool\DayzAnimationTools\Types\Txa.py`

`Add Survivor IK Bones` now creates:

- `LeftHandOrigin`
- `LeftHandIKTarget`
- `RightHandOrigin`
- `LeftForeArmDirection`
- `LeftForeArmDirectionOrigin`
- `RightForeArmDirection`
- `RightForeArmDirectionOrigin`

`ExportTxa.py` still preserves the compatibility fallback that writes
`LeftHandIKTarget` as a copy of `LeftHandOrigin`, but only when the armature
does not already contain a real `LeftHandIKTarget` bone.

`Types\Txa.py` now includes `LeftHandIKTarget` in `SURVIVOR_IK_ANIM_BONES_L`,
so an authored/imported real `LeftHandIKTarget` is exported as its own TXA node.

## Full Player IK ANM Corpus

`confirmed`: scan of `P:\DZ\anims\anm\player\ik\` parsed 654 `.anm` files:
359 `ANIMSET5`, 295 `ANIMSET6`, all `fps = 30`. Most files are 2-frame IK
poses; only `gear/gas_cooker.anm` and `gear/morphine.anm` are 1-frame.

`confirmed`: the player IK data is not one fixed full-body helper layout. The
largest groups are:

- 385 right-hand/item-only poses:
  `RightHand_Dummy`, `RightHandOrigin`, `RightForeArmDirectionOrigin`,
  `RightForeArmDirection`.
- 192 full two-hand poses with left target/origin/direction helpers plus right
  origin/direction helpers.
- smaller minimal/legacy groups, including five files with
  `RightForeHandDirection`.

`confirmed`: `RightForeHandDirection` was found only in five `.anm` files, not
in `P:\DZ\anims\cfg\skeletons.anim.xml`, not in the player AGR remap scan, and
not in DayZDiag string search. Treat it as an import-only legacy alias for
`RightForeArmDirection`; do not export that spelling.

See `anm/player-ik-anm-corpus.md` for examples and generated CSV/JSON indexes.

## Remaining Unknowns

- `unknown`: exact transform math inside the WeaponIK solver after config parse.
- `unknown`: exact runtime consumer branch for the opcode `0x0c` command emitted
  by `FUN_140108750`. The node method itself emits a `0x20` byte command and
  does not directly read all `ikpose_*` ids.
  This needs another Ghidra pass over methods that consume fields `+0x1b8`
  through `+0x218`.
- `unknown`: exact rules for non-player or modded graphs. DayZDiag proves the
  mechanism is config-driven, so presets should eventually be read from `.agr`
  / graph config rather than hardcoded globally.
