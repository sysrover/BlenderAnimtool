# Player XOB IK Bones And DayZDiag Findings

## Scope

Checked model:

- `P:\DZ\anims\workspaces\player\models\player_f_editorpreview.xob`
- `P:\DZ\anims\workspaces\player\models\player_m_editorpreview.xob`

Runtime source:

- `DayZDiag_x64.exe`
- `enf::AnimNodeWeaponIK` vtable at `0x140decb30`
- `FUN_1401093e0`: WeaponIK remapping parser
- `FUN_1401099f0`: name resolver helper
- `FUN_14010a800`: `IAnimSetInstance` loader, including `ikpose`

Raw Ghidra outputs:

- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-vtable-decompile.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-offset-scan.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-animset-ikpose-decompile.txt`

## XOB Skeleton Check

`confirmed`: `player_f_editorpreview.xob` contains these relevant existing
model/skeleton names:

- `LeftHandIK`
- `RightHandIK`
- `LeftHand_Dummy`
- `RightHand_Dummy`
- normal arm/hand/finger chains

Parsed parent evidence from `player_f_editorpreview.xob`:

- `LeftHand_Dummy`: parent `LeftHand`
- `RightHand_Dummy`: parent `RightHand`
- `RightHandIK`: parent `RightHand_Dummy`
- `LeftHandIK`: parent `RightHand_Dummy`

`confirmed`: `player_f_editorpreview.xob` does not contain these WeaponIK pose
helper names as model skeleton strings:

- `LeftHandOrigin`
- `LeftHandIKTarget`
- `RightHandOrigin`
- `LeftForeArmDirection`
- `LeftForeArmDirectionOrigin`
- `RightForeArmDirection`
- `RightForeArmDirectionOrigin`

`confirmed`: `player_m_editorpreview.xob` is similar, but also has
`RightHandIK_Helper`.

Parsed parent evidence from `player_m_editorpreview.xob`:

- `LeftHand_Dummy`: parent `LeftHand`
- `RightHand_Dummy`: parent `RightHand`
- `RightHandIK_Helper`: parent `Spine3`
- `RightHandIK`: parent `RightHandIK_Helper`
- `LeftHandIK`: parent `RightHandIK_Helper`

## DayZDiag Runtime Split

`confirmed`: `FUN_14010a800` parses `IAnimSetInstance` files and recognizes
the key `ikpose`. It resolves that value as `enf::Animation::RTTI_Type_Descriptor`
and stores it at `param_1[0xc]`.

This matches local `.asi` files such as:

```text
#ikpose "{...}DZ/anims/anm/player/ik/weapons/izh18.anm"
```

`confirmed`: only some weapon `.asi` files override `#ikpose` directly. Other
weapon instances inherit through their parent/template chain or use a default
from the loaded anim set instance.

## What `AnimNodeWeaponIK` Resolves

`confirmed`: `FUN_1401093e0` parses the graph remapping text and stores the
resolved ids into the `AnimNodeWeaponIK` object:

- `hand` -> `+0x1b8`
- `weapon` -> `+0x1bc`
- `weaponrotator` -> `+0x1c0`
- `weaponaxis` -> `+0x1c4`
- `chain` -> `+0x1c8`, count at `+0x1f0`
- `secchain` -> `+0x1dc`, count at `+0x1f1`
- `chainaxis` -> `+0x1f2`
- `secchainaxis` -> `+0x1f3`
- `ikpose_secchainoffset` -> `+0x1f8`
- `ikpose_weaponoffset` -> `+0x1fc`
- `ikpose_chainmiddledir` -> `+0x200`
- `ikpose_chainmiddlediro` -> `+0x204/+0x208`
- `ikpose_secchainmiddledir` -> `+0x20c`
- `ikpose_secchainmiddlediro` -> `+0x210/+0x214`
- `outputweaponoffsettobuffer` -> `+0x218`

`confirmed`: the constructor `FUN_140108d00` initializes these fields to
`0xff`/zero before parsing.

`confirmed`: the parser validates only:

- `hand != 0xff`
- `weapon != 0xff`
- `ikpose_weaponoffset != 0xff`
- primary `chain` count is greater than `3`

## Important Interpretation

`likely`: the special `ikpose_*` names are intended to be tracks in the loaded
IK pose animation, not necessarily bones in the XOB model skeleton. The evidence:

- player XOB lacks most `ikpose_*` helper names;
- weapon `.anm` IK pose files contain those names as animation tracks;
- `IAnimSetInstance` has an explicit `#ikpose` animation slot;
- player `.agr` maps `ikpose_*` fields to those ANM track names.

`confirmed`: `LeftHand_Dummy` and `RightHand_Dummy` are real model skeleton
names in `player_f_editorpreview.xob`. They should stay as normal skeleton
bones in Blender/TXO.

`likely`: `LeftHandOrigin`, `LeftHandIKTarget`, `RightHandOrigin`,
`LeftForeArmDirection`, and the direction-origin tracks should be added in
Blender/TXO as authoring/helper bones so the addon can import, edit, and export
the IK pose tracks, even though they are not part of the vanilla player XOB
skeleton.

## TXO Direction

For our Blender/TXO workflow, the model should contain:

- all vanilla player skeleton bones from `player_f_editorpreview.xob` /
  `player_m_editorpreview.xob`;
- real existing weapon attachment bones:
  - `LeftHand_Dummy`
  - `RightHand_Dummy`
  - `LeftHandIK`
  - `RightHandIK`
- added helper/authoring bones:
  - `LeftHandOrigin`
  - `LeftHandIKTarget`
  - `RightHandOrigin`
  - `LeftForeArmDirection`
  - `LeftForeArmDirectionOrigin`
  - `RightForeArmDirection`
  - `RightForeArmDirectionOrigin`

Do not assume these added helper bones are required in the packed game XOB. They
are required in Blender so ANM/TXA IK pose tracks can be represented and edited.

Recommended runtime/export interpretation:

- preserve vanilla parents for existing XOB bones;
- export `LeftHandOrigin` and `LeftHandIKTarget` relative to `RightHand_Dummy`;
- export `RightHandOrigin` relative to `RightHand`;
- export `LeftForeArmDirection` and `LeftForeArmDirectionOrigin` relative to
  `LeftHand`;
- export `RightForeArmDirection` and `RightForeArmDirectionOrigin` relative to
  `RightHand`.

Blender authoring parentage is different from the export-relative-space rule.
The helper/pole bones used by Blender IK constraints must not be children of the
controlled hand chains, otherwise Blender creates dependency cycles. Current
addon behavior:

- create missing `LeftHand_Dummy` under `LeftHand`;
- create missing `RightHand_Dummy` under `RightHand`;
- create missing `LeftHandIK` and `RightHandIK` under `RightHand_Dummy`;
- create `LeftHandOrigin` and `LeftHandIKTarget` under `RightHand_Dummy`;
- create `RightHandOrigin`, `LeftForeArmDirection`,
  `LeftForeArmDirectionOrigin`, `RightForeArmDirection`, and
  `RightForeArmDirectionOrigin` as unparented authoring helpers.

Runtime WeaponIK still uses the graph remapping and the IK pose ANM tracks.
The TXA exporter performs the relative-space conversion explicitly, so these
unparented Blender helpers can still export into the DayZ graph layout.

## Open Ghidra Work

- Identify the downstream runtime function that consumes the parsed
  `AnimNodeWeaponIK` fields after graph load. A direct offset scan found the
  constructor and parser, but not yet the final solver path.
- Confirm whether the global name resolver used by `FUN_1401099f0` indexes only
  skeleton bones, only animation tracks, or a merged bone/track dictionary.
