# DayZ vs Reference Arm Rig Comparison

## Reference chain that matters

The reference rig does not drive the deform/export arm directly from `hand_ik`.

For each side:

- `hand_ik.*` is a visible user control.
- `MCH-upper_arm_ik_target.*` copies location from `hand_ik.*`.
- `MCH-forearm_ik.*` has IK constraints targeting `MCH-upper_arm_ik_target.*` with `chain_count = 2` and pole target `upper_arm_ik_target.*`.
- `ORG-upper_arm.*`, `ORG-forearm.*`, `ORG-hand.*` switch from FK copy targets to IK copy targets:
  - `ORG-upper_arm.*` copies `upper_arm_ik.*`.
  - `ORG-forearm.*` copies `MCH-forearm_ik.*`.
  - `ORG-hand.*` copies `MCH-upper_arm_ik_target.*`.
- Deform bones are not the same as ORG bones. They follow tweak bones:
  - `DEF-upper_arm.*` copies `upper_arm_tweak.*` and stretches to `upper_arm_tweak.*.001`.
  - `DEF-upper_arm.*.001` copies `upper_arm_tweak.*.001` and stretches to `forearm_tweak.*`.
  - `DEF-forearm.*` copies `forearm_tweak.*` and stretches to `forearm_tweak.*.001`.
  - `DEF-forearm.*.001` copies `forearm_tweak.*.001` and stretches to `hand_tweak.*`.
  - `DEF-hand.*` copies `hand_tweak.*`.

## What was wrong in our earlier DayZ rig

- Export copy constraints were duplicated during pole-angle tuning. This made the file slow and could corrupt evaluation.
- `DRV_Hand` copied full transforms from `CTRL_Hand`, which could detach the hand from the solved forearm chain.
- `ArmRoll` and `ForeArmRoll` had no explicit follow targets, so they only inherited parent motion while child bones were being world-copied.
- A direct attempt to copy the reference tweak-blend onto DayZ roll bones failed: `RightArmRoll` and `RightForeArmRoll` flipped about 180 degrees in neutral. DayZ roll bones are export hierarchy bones, not separate Rigify DEF segments.

## Current stable implementation

File:

`P:\Animation_Weapon\Weapon_template_aks74u_refstyle_twobone_controls_v2.blend`

Script:

`tools/create_dayz_refstyle_twobone_controls_v2.py`

Current control rig:

- Visible controls:
  - `CTRL_Hand.L`
  - `CTRL_Elbow.L`
  - `CTRL_Hand.R`
  - `CTRL_Elbow.R`
- Hidden driver bones:
  - `DRV_Arm.*`
  - `DRV_ForeArm.*`
  - `DRV_Hand.*`
- Hidden output/follow bones:
  - `OUT_Arm.*`
  - `OUT_ArmRoll.*`
  - `OUT_ForeArm.*`
  - `OUT_ForeArmRoll.*`
  - `OUT_Hand.*`

Current verified state:

- Each driven DayZ export bone has exactly one `DAT_REF2B_COPY_*` constraint.
- Neutral pose is clean: max rotation delta `0.0` degrees.
- Large direct Rigify-style tweak blending was rejected because it breaks DayZ roll bones.

## Next missing piece

The remaining difference from the reference is the full tweak/DEF distribution layer.

For DayZ this cannot be copied literally onto `ArmRoll`/`ForeArmRoll`. The next pass should build a separate preview/deform helper layer that distributes twist/stretch visually, then bake only final DayZ export bones.

## Rotation-follow v3

File:

`P:\Animation_Weapon\Weapon_template_aks74u_refstyle_rotation_follow_v3.blend`

Script:

`tools/create_dayz_refstyle_rotation_follow_v3.py`

Reason for v3:

- v2 used world `Copy Transforms` from helper bones into DayZ export bones.
- That made the helper IK reach the target, but it could move DayZ joint positions in world space.
- When DayZ parent/child joint distances changed, the mesh stretched.

v3 change:

- DayZ export bones use `COPY_ROTATION`, not full `COPY_TRANSFORMS`.
- Local DayZ hierarchy lengths stay stable.
- The control rig still solves IK through hidden `DRV_*` bones.

Verified:

- Neutral max rotation delta: `0.0` degrees.
- Neutral max location drift: about `0.00000016`.
- Chain gap drift after a large `CTRL_Hand` move: about `0.000000083`.
- Moving `CTRL_Hand.*` on X/Y/Z moves the arm while preserving joint continuity.

## IK/FK v10

File:

`P:\Animation_Weapon\Weapon_template_aks74u_refstyle_ikfk_v10.blend`

Script:

`tools/create_dayz_refstyle_ikfk_v10.py`

Reason:

- Rotating `OUT_ForeArm.*` in IK mode is an absolute tweak. `OUT_Hand.*` keeps its own world orientation, so the hand does not naturally follow like an FK child.
- Reference rigs solve this with IK/FK. IK is for moving the hand target; FK is for rotating joints as a parent chain.

Added:

- `FK_LeftArm.L`
- `FK_LeftArmRoll.L`
- `FK_LeftForeArm.L`
- `FK_LeftForeArmRoll.L`
- `FK_LeftHand.L`
- matching right-side FK controls
- rig custom properties:
  - `IK_FK_L`
  - `IK_FK_R`

Usage:

- `IK_FK_* = 1.0`: IK mode, use `CTRL_Hand.*` and `CTRL_Elbow.*`.
- `IK_FK_* = 0.0`: FK mode, rotate `FK_*` controls. Child FK controls follow parent FK controls.
