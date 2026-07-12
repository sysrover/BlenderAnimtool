# Player Weapon IK Blender Skeleton Status

## Status

`confirmed`: current DayZDiag evidence is enough to build the Blender authoring
skeleton architecture, but not a single fixed "final rest pose" for every
weapon. The helper positions are weapon-pose data.

Source evidence:

- DayZDiag `FUN_1400dec30 case 0x0c` consumes `AnimNodeWeaponIK` command
  `0x0c`.
- DayZDiag `FUN_1400e1be0` solves the chain IK and writes real arm-chain
  transforms back through `FUN_14005f5a0`.
- DayZDiag `FUN_1400e17c0` caches `ikpose_*` tracks from the current pose,
  not from hardcoded skeleton bones.
- Player weapon IK corpus stats:
  `player-weapon-ik-helper-transform-stats.json`.

## Important Finding

`confirmed`: IK helper track transforms vary by weapon. They are not one static
rest-pose layout.

Examples from original weapon IK `.anm` files:

- `RightHandOrigin` is zero/identity in some files such as `m4a1_ik.anm` and
  `1911.anm`.
- `RightHandOrigin` has non-zero weapon-specific offsets in files such as
  `sv98.anm`, `ak101.anm`, and `cz75.anm`.
- Direction helpers such as `RightForeArmDirectionOrigin`,
  `RightForeArmDirection`, `LeftForeArmDirectionOrigin`, and
  `LeftForeArmDirection` are usually around `0.275` units from their local
  reference, but their rotations and exact positions vary.

## Corpus Snapshot

Scan source: `P:\DZ\anims\anm\player\ik\weapons\*.anm`, 66 files.

| helper | files | median pos length | notes |
|---|---:|---:|---|
| `RightHand_Dummy` | 66 | `0.180448` | weapon-specific right-hand/weapon offset |
| `LeftHand_Dummy` | 66 | `0.108554` | present in all scanned weapon IK files |
| `RightHandOrigin` | 49 | `0.050289` | sometimes zero/identity, sometimes weapon-specific |
| `RightForeArmDirectionOrigin` | 48 | `0.274999` | stable length, varying direction/rotation |
| `RightForeArmDirection` | 49 | `0.274999` | stable length, varying direction/rotation |
| `LeftHandIKTarget` | 49 | `0.126838` | true separate target, not always equal to `LeftHandOrigin` |
| `LeftHandOrigin` | 48 | `0.116180` | weapon-specific left-hand reference |
| `LeftForeArmDirectionOrigin` | 48 | `0.275000` | stable length, varying direction/rotation |
| `LeftForeArmDirection` | 49 | `0.275000` | stable length, varying direction/rotation |

## Blender Skeleton Rule

`confirmed`: the helper bones should be treated as authoring controls/tracks,
not as fixed vanilla XOB skeleton bones.

Recommended Blender structure:

- Keep real player skeleton chains as actual deform/control chains:
  `RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand` and
  `LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand`.
- Add IK helper controls:
  `RightHandOrigin`, `RightForeArmDirectionOrigin`,
  `RightForeArmDirection`, `LeftHandOrigin`, `LeftHandIKTarget`,
  `LeftForeArmDirectionOrigin`, `LeftForeArmDirection`.
- Keep helper controls unparented in Blender authoring space to avoid
  dependency cycles.
- Export/import helper transforms graph-relative by name, matching the
  DayZDiag `AnimNodeWeaponIK` remap, not by Blender parent.

## Code Change Made

`confirmed`: fixed the addon so IK helper export conversion no longer depends
on Blender helper-bone parentage.

Changed:

- `P:\BlenderAnimtool\DayzAnimationTools\Tools\AddSurvivorIK.py`
  - `ensure_edit_bone` now clears parent when `parent_name` is `None`.
  - `LeftHandOrigin` and `LeftHandIKTarget` are created unparented.
- `P:\BlenderAnimtool\DayzAnimationTools\Export\ExportTxa.py`
  - IK helper conversion now runs by `sAnimType` and bone name before the
    generic `bone.parent is None` branch.
- `P:\BlenderAnimtool\DayzAnimationToolsBinary\Export\ExportAnm.py`
  - same fix for direct `.anm` export.

The same files were synced into the installed Blender 4.2 add-on directory.

## Still Open

`unknown`: exact Blender viewport preview solver parity with DayZDiag
`FUN_1400e1be0`. The current Blender constraints can approximate the pose, but
full parity needs a custom preview solver or more exact translation of
`FUN_1400e1be0` into Python/mathutils.

`unknown`: final treatment of `outputweaponoffsettobuffer` in Blender preview.
The DayZDiag branch is identified, but the preview tool still needs a clear UI
decision on whether to visualize/write that weapon offset.
