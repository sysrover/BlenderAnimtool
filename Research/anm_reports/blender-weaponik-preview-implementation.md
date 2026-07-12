# Blender WeaponIK Preview Implementation

## Status

`implemented`: added a safer DayZ WeaponIK preview path to the Blender 4.2+
addon without changing TXA/ANM export bytes.

Changed source files:

- `P:\BlenderAnimtool\DayzAnimationTools\Tools\AddSurvivorIK.py`
- `P:\BlenderAnimtool\DayzAnimationTools\Tools\__init__.py`
- `P:\BlenderAnimtool\DayzAnimationTools\Utils\WeaponIKSolver.py`

Synced installed Blender 4.2 addon files:

- `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationTools\Tools\AddSurvivorIK.py`
- `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationTools\Tools\__init__.py`
- `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationTools\Utils\WeaponIKSolver.py`

## Preview Constraint Fix

`confirmed from DayZDiag/AGR`: player secondary/left chain uses:

```text
ikpose_secchainoffset = LeftHandIKTarget
secchain = LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand
secchainaxis = +x
```

The old Blender preview constraint targeted `LeftHandOrigin`. The preview now
targets `LeftHandIKTarget`, which matches the player `AnimNodeWeaponIK`
configuration.

New menu operator:

```text
Tools > Refresh DayZ Weapon IK Preview
```

It rebuilds only the preview constraints:

- `RightHand` target: `RightHandOrigin`
- `RightHand` pole: `RightForeArmDirection`
- `LeftHand` target: `LeftHandIKTarget`
- `LeftHand` pole: `LeftForeArmDirection`
- both chains: `chain_count = 5`, `use_rotation = true`, `use_stretch = false`

This keeps helper bones unparented/exportable and avoids adding solver output
back into the same dependency chain.

## Solver Port

`implemented`: `Utils\WeaponIKSolver.py` contains a readable Python/mathutils
port of the core `FUN_1400e1be0` model:

- `IkXform`: compact `0x20` DayZ transform record model.
- `axis_vector`: DayZ axis ids `0..5` -> `+x,+y,+z,-x,-y,-z`.
- `slerp_dayz`: quaternion blend with threshold `0.999`.
- `quat_from_to`: equivalent role to `FUN_1400e3240`.
- `rotate_vector`: equivalent role to `FUN_14013fa00`.
- `solve_weapon_ik_chain`: mutates five shifted chain records:
  `r0/root`, `r1`, `r2/middle`, `r3`, `r4/final`.

The solver module is intentionally not called by import/export yet. It is the
next foundation for a bake operator or live modal preview handler.

`updated`: the solver now includes the deeper DayZDiag formula pass:

- reach clamp uses `(upper_len + lower_len) * 0.9800000190734863`, then clamps
  against `abs(upper_len - lower_len)`;
- `slerp_dayz` uses the exact decoded threshold `0.9990000128746033`;
- final `r3` correction uses the DayZDiag twist projection:
  `delta = targetQ * inverse(r4Q)`, project `delta.xyz` onto `r2 -> r4`,
  normalize the twist quaternion, sign-flip when the projection is negative,
  then slerp `r3` to `r3 * twist` by `0.5`.

Evidence is tracked in
`anm/dayzdiag-weaponik-solver-model.md` and raw Ghidra files under
`anm/ghidra-raw/`.

`updated`: live/bake preview now routes helper targets through the recovered
`FUN_1400dec30 case 0x0c` target pipeline:

- `RightHandOrigin` is adapted back into `ikpose_chainoffset`;
- `RightHand_Dummy` is used as `ikpose_weaponoffset`;
- optional weapon-axis correction uses
  `command[1..3] = (sin(AimIKX) * cos(AimY), sin(AimY), cos(AimIKX) * cos(AimY))`;
- `LeftHandIKTarget` is applied as `ikpose_secchainoffset` after the primary
  weapon/right-hand basis is built.

For imported `.anm` files the default `dayz_weaponik_aim_blend` is `0.0`,
because those actions do not carry live gameplay `AimIKX/AimY` variables. Set
`scene["dayz_weaponik_aim_blend"]`, `scene["dayz_weaponik_aim_ik_x"]`, and
`scene["dayz_weaponik_aim_y"]` only when intentionally previewing the runtime
weapon-axis correction.

## Not Yet Done

`pending`: build an operator that converts current Blender pose bones into
five `IkXform` records, calls `solve_weapon_ik_chain`, and writes/bakes the
solved pose to preview-only controls or action keyframes.

`pending`: visual/per-frame comparison against DayZDiag output is still needed
to confirm Blender coordinate-space wiring around the solver. The internal
numeric formula is now Ghidra-backed; the remaining risk is how Blender bones
are converted into and out of the five compact records.
