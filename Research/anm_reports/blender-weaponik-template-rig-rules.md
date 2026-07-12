# Blender WeaponIK Template Rig Rules

## Status

`confirmed`: DayZDiag evidence is the source of truth for the runtime mapping.
Blender constraints are only viewport/authoring helpers and must not define the
export format.

Raw/runtime evidence is summarized in:

- `dayzdiag-weaponik-solver-model.md`
- `player-weaponik-agr-runtime-map.md`
- raw dumps under `ghidra-raw/`

## DayZDiag Runtime Mapping

`confirmed`: player `AnimNodeWeaponIK` uses these real chain bones:

```text
primary/right chain:
RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand

secondary/left chain:
LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand
```

`confirmed`: player axes:

```text
chainaxis = -x
secchainaxis = +x
```

`confirmed`: player helper/IK-pose tracks:

```text
ikpose_chainoffset = RightHandOrigin
ikpose_weaponoffset = RightHand_Dummy
ikpose_secchainoffset = LeftHandIKTarget
ikpose_chainmiddledir = RightForeArmDirection
ikpose_chainmiddlediro = RightHandOrigin, RightForeArmDirectionOrigin
ikpose_secchainmiddledir = LeftForeArmDirection
ikpose_secchainmiddlediro = LeftHandOrigin, LeftForeArmDirectionOrigin
```

## Important Consequence

`confirmed`: in DayZDiag, most `ikpose_*` names are consumed as animation pose
tracks by `FUN_1400e17c0` / `FUN_1400e1a30`, not as fixed model skeleton bones.
Their positions are not one universal rest-pose location. They are evaluated per
IK animation and then mixed by `AnimNodeWeaponIK`.

So the Blender template must separate:

- real player body bones;
- weapon/hand attachment bones;
- IK-pose helper tracks;
- viewport controls.

## Blender Template Rules

### Real body bones

Keep these as the actual deform/runtime player chain:

```text
RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand
LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand
```

Do not add authoring constraints that permanently change these bones during
export. If a preview solver modifies them, it must be bake/preview-only.

### Helper tracks

Use these names as exportable animation tracks:

```text
RightHandOrigin
RightForeArmDirection
RightForeArmDirectionOrigin
LeftHandOrigin
LeftHandIKTarget
LeftForeArmDirection
LeftForeArmDirectionOrigin
RightHand_Dummy
```

`RightHand_Dummy` is special: it is both a real weapon-side bone and the
`ikpose_weaponoffset` track.

### Controls

Viewport controls such as `WIK_L_Hand_Target` and `WIK_L_Elbow_Pole` must not
be treated as export bones.

Controls must not be parented to `Weapon_Root`, `Weapon_Magazine`,
`RightHand`, or `LeftHand` if they also drive IK/helper bones. That creates
Blender dependency cycles.

### Constraints

`confirmed from live Blender audit`: the broken scene had mixed state:

- active `aks74u` helper action;
- full-body action in NLA;
- Blender IK constraints on `LeftHand`/`RightHand`;
- manual `DayZ WIK Control*` constraints on helper bones;
- previous pose-basis overrides from solver experiments.

That combination is invalid for a template.

Correct clean imported mode:

- no `DayZ WeaponIK Preview` IK constraints;
- no active `DayZ WIK Control*` constraints;
- pose basis reset;
- full-body action in NLA;
- IK helper action can provide helper/finger tracks.

Correct manual authoring mode:

- do not use imported helper action for the same helper tracks being driven by
  controls;
- controls drive helper tracks;
- helper tracks are then baked/exported to TXA/ANM.

## Why Blender IK Looked Wrong

`confirmed`: Blender IK is not the DayZDiag solver.

DayZDiag uses `FUN_1400e1be0` on five compact records:

```text
r0 root/upper pivot
r1 real intermediate bone
r2 middle/elbow pivot
r3 real intermediate bone
r4 final/end bone
```

Blender IK with `chain_count = 5` pulled the upper arm/shoulder too strongly.
Blender IK with `chain_count = 3` improved the shoulder but still did not match
the DayZDiag forearm solve. This is expected because DayZDiag also uses helper
plane points and a final twist correction.

## Required Next Implementation

For a reliable Blender template, implement a dedicated `DayZ WeaponIK Preview`
operator/solver:

1. Evaluate full-body pose.
2. Read IK-pose helper tracks separately.
3. Build DayZ helper points:
   - primary `chainmiddledir`;
   - primary `chainmiddlediro` pair;
   - secondary `secchainmiddledir`;
   - secondary `secchainmiddlediro` pair.
4. Run the Ghidra-backed `FUN_1400e1be0` port on the real five-bone chains.
5. Apply the result as viewport preview only, or bake it only when explicitly
   requested.
6. Export helper tracks, not Blender viewport control objects.

Until this exists, Blender IK constraints are useful only as rough authoring
controls, not as a 100% DayZDiag preview.

## 2026-05-17 Live Scene Correction

`confirmed`: helper bones being visually far from the body can have two
different causes:

1. Normal DayZ behavior: `ikpose_*` tracks are helper pose data, not model rest
   bones.
2. Blender-side broken state: importing or solving while pose-basis overrides
   remain active can bake bad helper fcurves or leave the body chain distorted.

The live `Weapon_template.blend` scene had case 2 after several experiments.
It was corrected by:

- removing experimental `WIK_*` controls;
- removing `DayZ WeaponIK Preview` Blender IK constraints;
- removing `DayZ WIK Control*` helper constraints;
- resetting every pose bone's `matrix_basis`;
- reimporting `aks74u.anm` from a clean full-body base pose.

The clean reimport diagnostic is:

```text
anm/blender-reimport-weaponik-clean-base.json
```

At frame 30 after clean reimport:

```text
LeftHand          ~= 0.1385, 0.5031, 1.4029
LeftHandIKTarget  ~= 0.1475, 0.4907, 1.3439
RightHand         ~= 0.2333, 0.1960, 1.3492
RightHandOrigin   ~= 0.2143, 0.1100, 1.3541
```

These values are near the body/weapon area and are not the earlier broken
far-away helper state.

## Current Solver Gap

`confirmed`: the Ghidra-backed Python solver now reads the correct helper
snapshot before primary/right solve mutates parented helper bones. This fixed
the previous bad secondary target read where `LeftHandIKTarget` was interpreted
near `z ~= 0.61`.

`unknown`: applying the current Python `FUN_1400e1be0` port directly to Blender
pose-bone matrices does not yet visibly solve the five-bone chain. The likely
remaining issue is the adapter between:

- DayZ compact record rotations/translations, and
- Blender pose-bone parent/local/rest matrices.

This must be solved before claiming 100% DayZDiag viewport parity.

Do not return to standard Blender IK as the final solution. The next work item
is a DayZ-runtime-cache preview path, not a Blender IK pole-angle tuning pass.

## 2026-05-17 Runtime Cache Diagnostic

`confirmed`: the visible helper-bone world positions in Blender are not enough
to reproduce `AnimNodeWeaponIK`. DayZDiag does not pass those world positions
directly to `FUN_1400e1be0`.

The relevant Ghidra-backed runtime composition is:

```text
primary target = current RightHand transform * cached RightHandOrigin
primary helpers = primary target basis * cached chain middle helper vectors

weapon base = primary target * cached RightHand_Dummy
secondary target = weapon base * cached LeftHandIKTarget
secondary helper dir = secondary target basis * cached LeftForeArmDirection
secondary helper line = weapon base basis * cached LeftHandOrigin/LeftForeArmDirectionOrigin
```

`confirmed`: `tools/diagnose_dayz_weaponik_runtime_cache.py` was added to test
this without applying pose changes. It writes:

```text
anm/dayz-weaponik-runtime-cache-diagnostic.json
```

Current diagnostic result at frame 30 shows the imported Blender helper action
and the weapon mesh/helper bones are still not aligned in the same runtime
space:

```text
direct visible LeftHandIKTarget before cache path ~= 0.1475, 0.4907, 1.3439
runtime-cache secondary target                 ~= -0.0222, 0.1000, 1.2380
```

This is why applying the solver currently breaks the arms: the Blender adapter
can place bones at the solver result, but the solver result is being fed with
wrong cached-space inputs.

`next`: inspect and fix the Blender importer/exporter IK-space rules for:

- `RightHand_Dummy` / `ikpose_weaponoffset`;
- `LeftHandIKTarget` / `ikpose_secchainoffset`;
- `LeftHandOrigin` and `LeftForeArmDirectionOrigin` direction-pair export;
- whether the loaded `aks74u` action is an authoring-space preview action or a
  raw DayZ IK-pose action.
is a proper compact-record adapter:

1. build DayZ-style compact records from evaluated Blender pose;
2. run `solve_weapon_ik_chain`;
3. convert solved compact records back into Blender pose-bone local basis;
4. validate per-frame against helper target distances and DayZDiag formulas.

## Stable Debug Mode

`confirmed`: the imported `aks74u` action contains both helper tracks and
finger tracks. During solver/debug work, using the full action as the active
action can make the visible hands look like spaghetti even before the DayZ
WeaponIK preview is correct.

Stable intermediate mode:

```text
full-body action: p_rfl_erc_idle_ras in NLA, influence 1.0
active action: aks74u_helpers_only
constraints: no Blender IK, no DayZ WIK Control constraints
```

`aks74u_helpers_only` keeps only:

```text
RightHandOrigin
RightForeArmDirectionOrigin
RightForeArmDirection
LeftHandOrigin
LeftHandIKTarget
LeftForeArmDirectionOrigin
LeftForeArmDirection
RightHand_Dummy
LeftHand_Dummy
```

Finger tracks are excluded until the solver preview is correct.

## Local Pose Adapter

`confirmed`: direct assignment to `pose_bone.matrix` was not enough for a stable
DayZ preview. The correct Blender-side adapter must write `matrix_basis` using
the armature-space pose equation:

```text
pose_matrix = parent_pose * parent_rest^-1 * bone_rest * matrix_basis
matrix_basis = (parent_pose * parent_rest^-1 * bone_rest)^-1 * desired_pose
```

Implemented in:

```text
tools/apply_dayz_weaponik_preview_with_local_adapter.py
```

Current live validation at frame 30:

```text
LeftHand solver target:  0.147458, 0.490749, 1.343903
LeftHand actual head:    0.147458, 0.490749, 1.343902
RightHand solver target: 0.214272, 0.110020, 1.354113
RightHand actual head:   0.214271, 0.110020, 1.354113
```

This confirms the compact-record-to-Blender-local application path now moves
the visible chain bones to the solver output.

Remaining validation:

- visual quality of elbow/roll bones still needs comparison against DayZDiag;
- the Python solver itself may still need adjustment if the DayZDiag decompile
  has missing details around roll/twist or helper plane interpretation;
- this preview should stay separated from export data until visual validation
  passes.
