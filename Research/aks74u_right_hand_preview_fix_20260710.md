# AKS-74U right-hand Blender preview fix (2026-07-10)

## Symptom

After layering `aks74u.anm` over the rotation-only import of
`p_rfl_erc_idle_ras.anm`, the raw Blender pose keeps the weapon and hands close
to the expected locations, but the right wrist/weapon basis is rotated down.

## Evidence

- Existing raw-vs-golden diagnostics show exact imported helper placement for
  `RightHandOrigin` and `RightForeArmDirection`.
- The unsolved `RightHand` differs from the golden result by about 11.2607
  degrees.
- Ghidra research confirms primary/right solve first, updated weapon basis
  second, and secondary/left solve last.

## Root cause

The button operator called `_dayz_weaponik_solve_current_frame` first. That
compact-record path derives local DayZ offsets from helper bones that
`ImportAnm` has already evaluated into Blender object space. This double space
conversion can throw the right arm over the head.

## Fix

An initial two-stage fixed-length preview was rejected because it moved the
right wrist closer to the body even though the imported wrist head was already
correct. The final display fix is deliberately rotation-only:

1. preserve the complete right-arm chain;
2. preserve the exact `RightHand` head/location and scale;
3. copy only the evaluated `RightHandOrigin` orientation to `RightHand`.

Golden diagnostics justify this narrower correction: raw `RightHand.head` has
zero error, while only the tail/orientation differs (`11.2607` degrees).

The ANM importer/exporter and source actions are not modified.

The missing operator classes were also added to `Tools/__init__.py`, so
`Enable DayZ IK Preview Solver` is registered after a normal add-on reload.

## Validation

- Operator result: `FINISHED`.
- Solver marker: `RightHand rotation-only correction from imported RightHandOrigin`.
- Measured wrist-head movement: approximately `2.15e-7` Blender units (float noise).
- Test scene: `P:/Animation_Weapon/Weapon_template_aks74u_rotation_only_preview.blend`.
