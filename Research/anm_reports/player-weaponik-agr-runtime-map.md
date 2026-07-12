# Player WeaponIK AGR Runtime Map

## Scope

Runtime source:

- `DayZDiag_x64.exe`
- `enf::AnimNodeWeaponIK::vftable` at `0x140decb30`
- `FUN_140108f80`: property table provider
- `FUN_1401093e0`: remapping/config parser

Asset source:

- `P:\DZ\anims\workspaces\player\player_main\*.agr`

Raw Ghidra evidence:

- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-property-table3.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-vtable-methods-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-deep-offset-vtable.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-remap-1401093e0-refresh.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-bufferflow-consumer-1400dec30-case0c-long-slice.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e17c0-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e1a30-disasm.txt`

## AnimNodeWeaponIK Positional Properties

`confirmed`: Ghidra property table at `0x14111fa70` defines these
`AnimNodeWeaponIK` fields in order:

| Index | Property | Runtime evidence |
| --- | --- | --- |
| 0 | `Child` | property table record 00 |
| 1 | `Config Name` | property table record 01 |
| 2 | `Config` | property table record 02 |
| 3 | `AimOn` | property table record 03 |
| 4 | `Prim On` | property table record 04 |
| 5 | `Sec On` | property table record 05 |
| 6 | `Blend In Time` | property table record 06 |
| 7 | `Blend Out Time` | property table record 07 |
| 8 | `Weapon Dir LR Angle` | property table record 08 |
| 9 | `Weapon Dir UD Angle` | property table record 09 |

So this AGR line:

```text
"NormalWeaponIK" "" "AimObstructionT" "isbitset(ArmIK, 0)" "isbitset(ArmIK, 1)" "isbitset(ArmIK, 2)" 0.36 0.15 "AimIKX" "AimY" "WeaponIKTest" "..."
```

means:

| AGR position | Meaning |
| --- | --- |
| `"AimObstructionT"` | child node |
| `isbitset(ArmIK, 0)` | `AimOn` |
| `isbitset(ArmIK, 1)` | `Prim On` |
| `isbitset(ArmIK, 2)` | `Sec On` |
| `0.36` | `Blend In Time` |
| `0.15` | `Blend Out Time` |
| `"AimIKX"` | `Weapon Dir LR Angle` |
| `"AimY"` | `Weapon Dir UD Angle` |
| `"WeaponIKTest"` | graph/config variable name after the two angle inputs |
| final quoted text block | `Config` remap text parsed by `FUN_1401093e0` |

## Player AGR Instances

`confirmed`: player main AGR files contain these WeaponIK node timing settings:

| File | Line | Node | Blend In | Blend Out | `outputweaponoffsettobuffer` |
| --- | ---: | --- | ---: | ---: | --- |
| `actions.agr` | 1633 | `AnimNodeWeaponIK` | 0.36 | 0.15 | false |
| `actions.agr` | 2001 | `DeployCancelIK` | 0.36 | 0.15 | false |
| `actions.agr` | 2041 | `DeployInIK` | 0.36 | 0.15 | false |
| `actions.agr` | 4623 | `KneelingIK` | 0.3 | 0.2 | false |
| `actions.agr` | 5203 | `PlacingIK` | 0.36 | 0.15 | false |
| `actions.agr` | 6864 | `ActionOnceIK` | 0.1 | 0.1 | false |
| `actions.agr` | 7621 | `StruggleIK` | 0.3 | 0.2 | false |
| `Combat.agr` | 3 | `DamageFullBodyIK` | 0.36 | 0.15 | false |
| `Combat.agr` | 709 | `MeleeWeaponIK` | 0.36 | 0.15 | false |
| `Gestures.agr` | 417 | `UnconsciousIK` | 0.3 | 0.2 | false |
| `locomotion.agr` | 960 | `FallMasterIK` | 0.3 | 0.2 | false |
| `locomotion.agr` | 2565 | `NormalWeaponIK` | 0.36 | 0.15 | true |
| `master.agr` | 23 | `InventoryIK` | 0.24 | 0.24 | false |
| `Vehicles.agr` | 2014 | `VehicleWeaponIK` | 0.3 | 0.24 | false |

## Bone And Track Interpretation

`confirmed`: `FUN_1401093e0` resolves the text remap keys with
`FUN_1401099f0` / `FUN_140109a60`. The remap used by player graphs is stable:

```text
hand = RightHand
weapon = RightHand_Dummy
weaponrotator = RightArm
weaponaxis = -x
chain = RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand
chainaxis = -x
secchain = LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand
secchainaxis = +x
ikpose_chainoffset = RightHandOrigin
ikpose_weaponoffset = RightHand_Dummy
ikpose_secchainoffset = LeftHandIKTarget
ikpose_chainmiddledir = RightForeArmDirection
ikpose_chainmiddlediro = RightHandOrigin,RightForeArmDirectionOrigin
ikpose_secchainmiddledir = LeftForeArmDirection
ikpose_secchainmiddlediro = LeftHandOrigin,LeftForeArmDirectionOrigin
```

`confirmed`: `locomotion.agr` `NormalWeaponIK` also sets:

```text
outputweaponoffsettobuffer = true
```

`confirmed`: `hand`, `weapon`, `weaponrotator`, `chain`, and `secchain` are the
real runtime player skeleton bones. `FUN_14005eba0` samples the configured
chain ids into compact `0x20` transform records before `FUN_1400e1be0`.

`confirmed`: `ikpose_*` names are resolved through the same name-id namespace,
but are consumed as tracks from the current IK pose animation. `FUN_1400e17c0`
uses `FUN_1400d3b50(ikposeAnim, id)` and `FUN_1400d39f0` to decode their
transforms. This matches the fact that `player_f_editorpreview.xob` lacks most
helper names while `P:\DZ\anims\anm\player\ik\weapons\*.anm` contains them as
tracks.

## Runtime Offset Map

`confirmed`: `FUN_1401093e0` stores player remap fields in the
`AnimNodeWeaponIK` object like this:

| Offset | Field |
|---:|---|
| `+0x1b8` | `hand` |
| `+0x1bc` | `weapon` |
| `+0x1c0` | `weaponrotator` |
| `+0x1c4` | `weaponaxis` |
| `+0x1c8..+0x1db` | `chain[5]` |
| `+0x1dc..+0x1ef` | `secchain[5]` |
| `+0x1f0` | `chain` count |
| `+0x1f1` | `secchain` count |
| `+0x1f2` | `chainaxis` |
| `+0x1f3` | `secchainaxis` |
| `+0x1f8` | `ikpose_secchainoffset` |
| `+0x1fc` | `ikpose_weaponoffset` |
| `+0x200` | `ikpose_chainmiddledir` |
| `+0x204`, `+0x208` | `ikpose_chainmiddlediro[2]` |
| `+0x20c` | `ikpose_secchainmiddledir` |
| `+0x210`, `+0x214` | `ikpose_secchainmiddlediro[2]` |
| `+0x218` | `outputweaponoffsettobuffer` |

`confirmed`: in `case 0x0c`, `outputweaponoffsettobuffer` becomes runtime flag
`lVar8 + 0x118`. When set, DayZDiag writes/inserts the current weapon offset for
the configured `ikpose_weaponoffset` id if it was not already fetched from the
pose buffer.

## Blender Skeleton Direction

For Blender 4.2+ we need an authoring skeleton, not a literal vanilla XOB
skeleton:

- keep the real player chain bones exactly as in the model:
  `RightArm`, `RightArmRoll`, `RightForeArm`, `RightForeArmRoll`, `RightHand`,
  `LeftArm`, `LeftArmRoll`, `LeftForeArm`, `LeftForeArmRoll`, `LeftHand`;
- keep or create `RightHand_Dummy`, `LeftHand_Dummy`, `RightHandIK`,
  `LeftHandIK`;
- add authoring helper bones/tracks:
  `RightHandOrigin`, `RightForeArmDirection`,
  `RightForeArmDirectionOrigin`, `LeftHandOrigin`, `LeftHandIKTarget`,
  `LeftForeArmDirection`, `LeftForeArmDirectionOrigin`;
- do not parent Blender pole/helper controls under the controlled hand chain,
  because Blender IK then reports dependency cycles;
- let the TXA exporter convert the unparented Blender helpers into the
  DayZ-relative spaces used by the AGR remap.
- preserve/export `RightHand_Dummy` both as the real weapon bone and as the IK
  pose track name used by `ikpose_weaponoffset`;
- do not collapse `LeftHandIKTarget` into `LeftHandOrigin` when a real target
  track exists. `LeftHandIKTarget` is the secondary-chain target in the
  weapon/right-hand-side frame.
- export `*ForeArmDirectionOrigin` plus `*ForeArmDirection` as pairs. DayZDiag
  builds the helper point as
  `originTranslation + originRotation * directionTranslation`.

## Remaining Work

- Add a Blender-side preset that stores this player WeaponIK graph mapping as
  metadata, so exported TXA/ANM can be validated against the player graph.
- Validate the Blender coordinate-space adapter visually/per-frame against
  DayZDiag. The DayZDiag runtime formula and remap layout are now covered; the
  remaining risk is the Blender-side conversion into those spaces.
