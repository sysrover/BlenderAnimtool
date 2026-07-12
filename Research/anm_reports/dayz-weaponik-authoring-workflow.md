# DayZ WeaponIK Blender Authoring Workflow

## Current Artifact

```text
P:\Animation_Weapon\Weapon_template_dayz_weaponik_authoring_v3.blend
```

Untouched backup:

```text
P:\Animation_Weapon\Weapon_template_dayz_arm_fk_controls_v17_roll_y_only.pre_weaponik_rebuild_20260710.blend
```

The v3 file was rebuilt from the backup and a fresh official source:

```text
P:\DZ\anims\anm\player\ik\weapons\aks74u.anm
```

## DayZ Model

WeaponIK is applied over an already evaluated full-body base pose. It is not a
standalone replacement pose:

```text
p_rfl_erc_idle_ras base pose
-> WeaponIK helper/offset tracks
-> primary/right-arm solve
-> updated weapon basis
-> secondary/left-arm solve
```

The helper roles and primary/secondary order are backed by the recovered
`AnimNodeWeaponIK` pipeline and the retail `DayZ_x64.exe` config parser.

## Rig Contract

- `_DayZ_Character`: the only armature selected for ANM import/export.
- `DAT_DayZ_Arm_FK_Controls`: non-exported authoring rig.
- Base action: `p_rfl_erc_idle_ras`.
- Current source action: freshly imported `aks74u.002` (the numeric suffix is
  only a Blender datablock name; source metadata points to `aks74u.anm`).
- 51 total controls:
  - 10 FK arm-chain controls;
  - 7 WeaponIK helper controls;
  - 34 finger controls.
- `DAT_IK_AUTHOR_*` constraints are the only constraints evaluated as the
  editable helper/finger source during sampled IK export.
- The live Blender preview is a fixed-length, two-stage adaptation over the
  DayZ base pose. It preserves Blender rest offsets and roll-bone continuity.
- Raw ANM graph semantics and export transforms remain the Ghidra-backed DayZ
  formulas; Blender preview matrices are not exported as replacement arm keys.

## Loading Another IK ANM

1. Select `_DayZ_Character`, not the control rig.
2. Import the weapon `.anm` with `DayZ Binary Animation (.anm)`.
3. Keep `p_rfl_erc_idle_ras` available in the file as the base pose.
4. Run `Bake Current ANM To Arm Controls` from DayZ Animation Tools.
5. Edit `DAT_DayZ_Arm_FK_Controls` in Pose Mode.

Important Blender 4.5 behavior handled by the addon:

- imported Actions explicitly bind their lazily-created Action Slot;
- baked control Actions explicitly bind their Action Slot;
- missing helper position/rotation channels are decoded as zero/identity;
- helper object matrices are converted through
  `Bone.convert_local_to_pose(..., invert=True)`.

## Editing

Main helper controls:

```text
IK_RightHandOrigin.R
IK_RightElbow.R
IK_RightElbowOrigin.R
IK_LeftHandOrigin.L
IK_LeftHandTarget.L
IK_LeftElbow.L
IK_LeftElbowOrigin.L
```

Finger controls use `IK_LeftHand*` and `IK_RightHand*` names. Helper controls
drive location and rotation; finger controls drive rotation.

## Exporting

1. Select `_DayZ_Character`.
2. Export `DayZ Binary Animation (.anm)`.
3. Use animation type `IK2H`.
4. Keep translation and rotation export enabled.
5. Exported edited IK uses two frames where present and retains source format,
   FPS, and track flags.

Raw-preserve safety:

- before baking/editing, cached source bytes can be written exactly;
- baking to controls automatically sets
  `dayz_binary_anm_raw_preserve = false`;
- active `DAT_IK_AUTHOR_*` constraints also force sampled export even if an old
  export-dialog checkbox still requests raw preserve.

## Verified Gates

- v3 build: 51 controls, no missing controls, all seven helper constraints at
  influence `1.0`, live preview handler active, raw preserve disabled after
  bake. Evidence: `anm/dayz-weaponik-authoring-v3-build.json`.
- Control matrix: 41/41 helper and finger controls change their expected ANM
  track. Evidence: `anm/weaponik-all-controls-to-anm.json`.
- `aks74u`:
  - raw-preserve SHA-256 exact;
  - sampled max error `8.23e-05`;
  - edited control detected;
  - edited re-import/export max error `1.08e-04`.
- `aug`:
  - raw-preserve exact;
  - sampled max error `6.25e-05`;
  - edited control detected;
  - cycle max error `1.11e-04`.
- `famas`:
  - raw-preserve exact;
  - sampled max error `3.05e-05`;
  - edited control detected;
  - cycle max error `1.10e-04`.

`1911` validation is intentionally postponed at the user's request.

## Visual Inspection Rule

Diagnostic screenshots must hide bone names, custom/control shapes, and the
armature objects themselves. This affects only the screenshot viewport; the
saved authoring file keeps the control rig available for editing.
