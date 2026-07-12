# Player Weapon IK Blender Workflow

## Source Of Truth

- `confirmed`: DayZDiag `FUN_1401093e0` parses `AnimNodeWeaponIK` config text.
- `confirmed`: DayZDiag `FUN_1401099f0` resolves each configured name to a bone
  id and reports `config:: %s - bone doesn't exist` when a configured bone is
  missing.
- `confirmed`: DayZDiag `FUN_140109a60` parses `chain`, `secchain`, and the
  two `*middlediro` pairs. `chain` / `secchain` accept up to 5 bones.
- `confirmed`: player graphs in
  `P:\DZ\anims\workspaces\player\player_main\*.agr` provide the actual player
  WeaponIK mapping.

## Runtime Mapping

Player `AnimNodeWeaponIK` uses:

- primary hand: `RightHand`
- weapon offset: `RightHand_Dummy`
- weapon rotator: `RightArm`
- primary chain: `RightArm`, `RightArmRoll`, `RightForeArm`,
  `RightForeArmRoll`, `RightHand`
- secondary chain: `LeftArm`, `LeftArmRoll`, `LeftForeArm`,
  `LeftForeArmRoll`, `LeftHand`
- primary axis: `-x`
- secondary axis: `+x`
- weapon axis: `-x`

The IK pose animation must provide these special tracks:

- `RightHandOrigin`
- `RightHand_Dummy`
- `LeftHandIKTarget`
- `RightForeArmDirection`
- `RightForeArmDirectionOrigin`
- `LeftForeArmDirection`
- `LeftHandOrigin`
- `LeftForeArmDirectionOrigin`

Original weapon IK files under `P:\DZ\anims\anm\player\ik\weapons` also contain
`LeftHand_Dummy` / `RightHand_Dummy` and finger pose tracks. Most checked files
are `ANIMSET5`, `fps = 30`, `numFrames = 2`.

## Blender Authoring Setup

1. Import or build the player skeleton from
   `P:\DZ\anims\workspaces\player\models\player_m_editorpreview.xob`.
2. Run `Tools > Add Survivor IK Bones`.
3. Author the pose with these helper bones present:
   - `LeftHandOrigin`
   - `LeftHandIKTarget`
   - `RightHandOrigin`
   - `LeftForeArmDirection`
   - `LeftForeArmDirectionOrigin`
   - `RightForeArmDirection`
   - `RightForeArmDirectionOrigin`
4. For Blender authoring constraints:
   - `LeftHand` IK target: `LeftHandOrigin`
   - `LeftHand` pole: `LeftForeArmDirection`
   - `RightHand` IK target: `RightHandOrigin`
   - `RightHand` pole: `RightForeArmDirection`
   - chain length: 5

The Blender constraints are only an authoring aid. DayZ runtime uses the
`AnimNodeWeaponIK` graph mapping above, not Blender constraints.

## Export

Use TXA export with animation type `IK2H` for two-hand weapon IK. The exporter
now:

- keeps IK exports at two frames;
- emits real `LeftHandIKTarget` when the armature has that bone;
- falls back to duplicating `LeftHandOrigin` as `LeftHandIKTarget` only when the
  armature does not have a real `LeftHandIKTarget`;
- can convert TXA to ANM through `TxaAnmPrototype`;
- exposes ANM accuracy mode as `optimized` or `exact`.

## Practical Meaning

For player weapon IK, do not treat `LeftHandIKTarget` as optional. DayZDiag
requires `ikpose_weaponoffset` to resolve, player graph uses
`ikpose_secchainoffset = LeftHandIKTarget`, and original weapon IK ANMs include
that track.

