# DayZ IK1H right-arm workflow — Blender 4.5

## 1. Import the base animation

1. Select the DayZ armature `_DayZ_Character`.
2. Use `File > Import > DayZ Binary Animation (.anm)`.
3. Import `P:\BlenderAnimtool\examples\p_1hd_erc_idle_low.anm`.
4. Enable `Rotation Keys`.
5. Disable `Translation Keys` and `Scale Keys` for the base animation.

## 2. Import the one-hand IK animation

1. Keep `_DayZ_Character` selected.
2. Import the desired file from `P:\BlenderAnimtool\examples\ik`.
3. Enable `Translation Keys` and `Rotation Keys`.
4. Disable `Scale Keys`.

The importer automatically records the action active before the IK import as
`dayz_weaponik_base_action`. For example, importing `apple.anm` after the base
records `p_1hd_erc_idle_low`.

## 3. Build the controls

1. Switch the armature to Pose Mode.
2. Open `DayZ Animation Tools` in the 3D View header.
3. Click `Build DayZ 1H IK Controls`.

The command creates and selects the control rig. Only two animator controls are
visible by default:

- `CTRL_RightHand`: move to reposition the wrist; rotate to orient the wrist.
- `CTRL_RightElbow`: move to change the elbow bend plane/direction.

The hidden mechanism is a non-stretch two-bone proxy chain. Moving the elbow
does not move the wrist. Do not animate the hidden `MCH_`, `IK_`, FK, helper or
roll controls directly for this workflow.

## 4. Edit and key the controls

At frame 0 and/or frame 1, move or rotate the two controls and insert keys on
the changed channels:

- wrist movement: Location on `CTRL_RightHand`;
- wrist orientation: Rotation on `CTRL_RightHand`;
- elbow direction: Location on `CTRL_RightElbow`.

Use `I > Location` or `I > Rotation` as appropriate. The Python preview syncs
the proxy result to the original DayZ arm/roll hierarchy interactively.

## 5. Bake back to DayZ helper tracks

In Pose Mode open `DayZ Animation Tools` and click
`Bake DayZ 1H Controls To Helpers`.

This writes the edited result to the original right-side DayZ IK/helper/finger
tracks and disables raw-ANM preservation for the edited action.

## 6. Export

Use `File > Export > DayZ Binary Animation (.anm)` with:

- Animation Type: `Survivor IK 1h` (`IK1H`)
- Translation Keys: enabled
- Rotation Keys: enabled
- Scale Keys: disabled
- Preserve Imported Raw ANM: disabled

The IK1H exporter includes only the required right-hand helper/hand/finger
tracks. Preview constraints and proxy bones are not exported.

