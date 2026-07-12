# DayZDiag Full WeaponIK Pipeline Plan

## Goal

Build the missing DayZDiag-style WeaponIK pre-solver pipeline so imported
weapon IK animations, including AUG, reconstruct the same arm pose DayZ uses.

Current state:

- The 5-record chain solver `FUN_1400e1be0` is documented and partly ported.
- The AGR remap for player WeaponIK is documented.
- The missing part is the full `FUN_1400dec30 case 0x0c` pipeline before and
  around the solver calls.

## Work Items

1. Document the full `FUN_1400dec30 case 0x0c` pipeline before `FUN_1400e1be0`.

   Evidence to extract:

   - where the base pose/current pose is read;
   - where IK pose tracks are fetched;
   - how the primary and secondary compact chains are sampled;
   - exact order of target construction, correction, solve, and writeback.

2. Recover the exact weapon-axis correction formula.

   Evidence to extract:

   - `weaponrotator = RightArm`;
   - `weaponaxis = -x`;
   - use of command direction vector `[1..3]`;
   - use of command blend `[4]`;
   - how the correction changes `RightArm`, `RightHand_Dummy`, or target basis.

3. Recover target transform construction before solve.

   Inputs to trace:

   - `RightHand_Dummy`;
   - `RightHandOrigin`;
   - `LeftHandIKTarget`;
   - `ikpose_weaponoffset`;
   - `ikpose_chainoffset`;
   - `ikpose_secchainoffset`;
   - helper direction/origin pairs.

   Required outputs:

   - primary target transform passed to `FUN_1400e1be0`;
   - secondary target transform passed to `FUN_1400e1be0`;
   - basis used for primary helper points;
   - basis used for secondary helper points.

4. Recover command blend semantics.

   Fields to verify:

   - `command[4]`: weapon-axis / weapon-offset blend;
   - `command[5]`: primary chain blend;
   - `command[6]`: secondary chain blend.

   Required details:

   - whether blends are clamped;
   - whether `max(command[4], command[5])` is always used for primary;
   - how secondary blend differs from primary;
   - what happens when helper tracks are missing.

5. Write the final order of operations.

   Target order to confirm or correct:

   ```text
   base pose/current pose
   -> IK pose tracks
   -> weapon offset / weapon-axis correction
   -> primary helper construction
   -> primary chain solve
   -> secondary target/helper construction
   -> secondary chain solve
   -> writeback
   ```

6. Only after the above, update the Blender preview/import solver.

   Blender changes must be based on confirmed Ghidra evidence, not manual
   per-weapon offsets.

## Ghidra Targets

- `DayZDiag_x64.exe`
- `FUN_1400dec30`, branch `case 0x0c`
- `FUN_1400e17c0`
- `FUN_1400e1a30`
- helpers around:
  - `FUN_1400e33b0`
  - `FUN_1400e3240`
  - `FUN_14005eba0`
  - `FUN_14005f5a0`

## Output Files

- Raw Ghidra dumps: `anm/ghidra-raw/`
- Final documented formulas: update `anm/dayzdiag-weaponik-solver-model.md`
- Blender implementation after formulas are confirmed:
  - `external_patch/DayzAnimationTools/Utils/WeaponIKSolver.py`
  - `external_patch/DayzAnimationTools/Tools/AddSurvivorIK.py`

## Progress

### 2026-05-20: AUG/AKS-74U Offset Recheck

Current Blender scene check:

- Active armature: `_DayZ_Character`
- Active action: `aug`
- Active preview marker: `dayz_weaponik_last_solver =
  Stable visual no-stretch current-frame solver`
- `RightHand_Dummy` and `Weapon_Root` are coincident in Blender world space.
  The weapon mesh is constrained to `Weapon_Root`, so the consistent weapon
  shift is not coming from a separate visible mesh offset.

Raw `.anm` track check:

```text
aug.anm     RightHand_Dummy.P = (-0.139475,  0.019857, -0.017382)
aks74u.anm  RightHand_Dummy.P = (-0.197279,  0.042149,  0.026951)
delta                         = ( 0.057803, -0.022291, -0.044333)
delta length                  = 0.076181 m
```

This is the same scale as the observed 6-7 cm weapon/right-hand discrepancy.

Blender import sanity check:

- The visible Blender fcurve value for `RightHand_Dummy.location` in AUG is
  not the raw `.anm` vector because it is already converted through the
  importer parent/axis transform.
- Reversing the Blender parent-relative matrix through `mtxFix` reconstructs
  the raw AUG `RightHand_Dummy` value:

```text
RightHand_Dummy raw_like_from_parent_rel =
(-0.139475, 0.019857, -0.017382)
```

So the raw import of `RightHand_Dummy` is not the immediate corruption point.

Important implication:

- The current UI operator is using the stable no-stretch visual solver, which
  targets `RightHandOrigin` / `LeftHandIKTarget` directly.
- That path does not run the DayZDiag `command[4]` weapon-axis correction
  branch.
- Ghidra shows the missing branch uses `RightHand_Dummy` as
  `ikpose_weaponoffset`, composes `weaponTarget`, and then adjusts the primary
  target around that weapon target before solving the right arm.

Next implementation hypothesis:

- Keep the raw `.anm` import as-is.
- The preview/bake path must run the full DayZDiag pipeline, with
  `command[4]`/`AimOnBlend` non-zero for normal raised weapon IK.
- The current stable visual solver is useful as a fallback, but it cannot be
  used to validate AUG weapon placement because it intentionally skips
  weapon-axis correction.

Follow-up implementation recheck:

- Capturing helper transforms after clearing the arm chain is wrong in Blender,
  because `RightHand_Dummy` is parented to `RightHand`. DayZDiag reads
  `RightHand_Dummy` as a pose-buffer local `ikpose_weaponoffset` record, not as
  a child after the arm chain has been reset.
- The Blender full-pipeline preview must capture helper/offset transforms
  before clearing or replacing the arm-chain pose.
- The desired weapon direction must not be rotated by `RightArm`'s parent in
  Blender preview. Passing the shoulder/torso parent as `root_rotation` rotates
  `command[1..3]` a second time and causes a large false correction.
- The arm-chain records used by the full solver must come from
  `p_rfl_erc_idle_ras`, not from the active weapon IK action. If the active
  helper action contains `RightArm`/`RightHand` fcurves, the solver starts from
  the wrong current-end transform and the weapon jumps instead of receiving the
  small DayZ correction.

### 2026-05-20: Fresh Ghidra Pull

Raw dumps:

- `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-full-pipeline-1400dec30-fresh.txt`
- `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-full-pipeline-helpers-fresh.txt`

Confirmed first-pass order inside `FUN_1400dec30 case 0x0c`:

1. Resolve the active WeaponIK config/runtime object from command field `[7]`.
2. Refresh cached IK pose tracks through `FUN_1400e17c0`.
3. Read command blends:
   - `[4]` = weapon-axis / weapon-offset correction blend;
   - `[5]` = primary chain blend candidate;
   - `[6]` = secondary chain blend.
4. Compute primary solve blend as `max(command[4], command[5])`.
5. Sample primary chain records with `FUN_14005eba0`.
6. If secondary is enabled and `[6] > 0`, sample secondary chain records with
   `FUN_14005eba0`.
7. Build primary target from current primary chain end plus cached
   `ikpose_chainoffset`.
8. If `[4] > 0` or `outputweaponoffsettobuffer` is set, fetch or fall back to
   cached `ikpose_weaponoffset`.
9. If `[4] > 0`, apply weapon-axis correction before primary solve.
10. Build primary helper points from the corrected primary target basis.
11. Run primary `FUN_1400e1be0`.
12. Write primary chain back with `FUN_14005f5a0`.
13. If secondary is enabled and `[6] > 0`, build secondary target from the
    post-primary right-hand/weapon basis plus cached `ikpose_secchainoffset`.
14. Build secondary helper points using mixed bases:
    - `secchainmiddledir` from the post-primary secondary target basis;
    - `secchainmiddlediro` points from the pre-secondary weapon/right-hand
      basis.
15. Run secondary `FUN_1400e1be0`.
16. Write secondary chain back with `FUN_14005f5a0`.
17. If `outputweaponoffsettobuffer` is set and weapon offset was not already in
    the pose buffer, insert the cached weapon-offset record into the output
    buffer.

This first-pass list was later resolved into the formula sections below. The
remaining unknown at this point was only the source formula for
`command[1..3]`, which is now covered by the command-vector section.

### 2026-05-20: Weapon-Axis Correction Formula

Raw evidence:

- `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-full-pipeline-1400dec30-fresh.txt`,
  lines 281-430.
- `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-correction-identity-constant.txt`
  confirms `0x14111d940` is quaternion `[0, 0, 0, 1]`.
- `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-const-one.txt` confirms
  `DAT_140de2b44 = 1.0`.
- `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-slerp-threshold.txt` confirms
  the slerp linearization threshold constant near `0.999`.

Confirmed formula shape:

```text
chainTargetQ = currentEndQ * ikpose_chainoffset.Q
chainTargetP = currentEndP + rotate(currentEndQ, ikpose_chainoffset.P)

weaponTargetQ = chainTargetQ * ikpose_weaponoffset.Q
weaponTargetP = chainTargetP + rotate(chainTargetQ, ikpose_weaponoffset.P)

currentWeaponAxis = axis_vector(weaponaxis, weaponTargetQ)
desiredWeaponAxis = command[1..3]
if current pose/root quaternion exists:
    desiredWeaponAxis = rotate(currentPoseRootQ, desiredWeaponAxis)

correctionQ = quat_from_vector_to_vector(currentWeaponAxis, desiredWeaponAxis)
correctionQ = slerp(identityQ, correctionQ, command[4])
```

Two branches:

1. If `weaponrotator == 0xff`, DayZ applies `correctionQ` directly to
   `chainTargetQ`. The target position is not pivot-adjusted in this branch.

2. If `weaponrotator != 0xff`, DayZ first reads the `weaponrotator` transform
   with `FUN_14005fc20`. For player WeaponIK this is `RightArm`. Then:

   ```text
   offsetFromWeaponTargetToChainTarget = chainTargetP - weaponTargetP
   chainTargetP = weaponTargetP + rotate(correctionQ, offsetFromWeaponTargetToChainTarget)
   chainTargetQ = correctionQ * chainTargetQ
   ```

   This is important for AUG: the right hand is not only rotated; its target
   position is moved around the weapon/right-arm correction pivot before the
   primary chain solve.

Confirmed helper:

- `FUN_1400e3240(outQ, currentWeaponAxis, desiredWeaponAxis)` returns the
  quaternion rotating one vector onto the other.
- `FUN_1400e33b0(axisOut, weaponTargetQ, weaponaxis)` extracts local axis
  `0..5` from a quaternion. Player config uses `weaponaxis = -x`, id `3`.

Still open:

- Confirm whether the `weaponrotator` transform read by `FUN_14005fc20` is used
  only as a validation/presence check here or whether its value also influences
  a hidden upstream basis. In the visible decompile branch, the pivot used for
  the position update is `weaponTargetP`, while the existence of
  `weaponrotator` gates the branch.

### 2026-05-20: Target Transform Construction

Raw evidence:

- Primary target setup: `ghidra-raw-dayzdiag-weaponik-full-pipeline-1400dec30-fresh.txt`,
  lines 231-285.
- Secondary target setup: same raw file, lines 462-533.
- Cache fill: `ghidra-raw-dayzdiag-weaponik-full-pipeline-helpers-fresh.txt`,
  `FUN_1400e17c0`.

Confirmed cache meaning used by the target builder:

| Runtime field | Source track | Use |
|---:|---|---|
| `+0x10..0x2f` | `ikpose_chainoffset = RightHandOrigin` | Primary target offset from current primary chain end |
| `+0x30..0x4f` | `ikpose_secchainoffset = LeftHandIKTarget` | Secondary target offset after weapon/right-hand basis is established |
| `+0x50..0x6f` | `ikpose_weaponoffset = RightHand_Dummy` | Weapon target offset used by weapon-axis correction |
| `+0x70/+0x7c/+0x88` | right forearm helper tracks | Primary helper points |
| `+0x94/+0xa0/+0xac` | left forearm helper tracks | Secondary helper points |

Primary target:

```text
currentEnd = last record of primary compact chain

primaryTargetP = currentEnd.P + rotate(currentEnd.Q, chainoffset.P)
primaryTargetQ = currentEnd.Q * chainoffset.Q
```

For player data this means:

```text
chainoffset = RightHandOrigin
```

Weapon target for correction:

```text
weaponOffset = fetched ikpose_weaponoffset track if present
             else cached RightHand_Dummy transform from +0x50..0x6f

weaponTargetP = primaryTargetP + rotate(primaryTargetQ, weaponOffset.P)
weaponTargetQ = primaryTargetQ * weaponOffset.Q
```

Secondary target starts only after primary solve state has been updated. It uses
the post-primary `primaryTarget`/right-hand basis, then applies weapon offset
and secondary-chain offset:

```text
weaponBasisP = primaryTargetP + rotate(primaryTargetQ, weaponoffset.P)
weaponBasisQ = primaryTargetQ * weaponoffset.Q

secondaryTargetP = weaponBasisP + rotate(weaponBasisQ, secchainoffset.P)
secondaryTargetQ = weaponBasisQ * secchainoffset.Q
```

For player data:

```text
weaponoffset = RightHand_Dummy
secchainoffset = LeftHandIKTarget
```

Secondary helper basis is mixed:

```text
secondaryHelperMid = secondaryTargetP + rotate(secondaryTargetQ, secchainmiddledir)
secondaryHelperOriginA = weaponBasisP + rotate(weaponBasisQ, secchainmiddlediro0)
secondaryHelperOriginB = weaponBasisP + rotate(weaponBasisQ, secchainmiddlediro1)
```

This confirms why a simple Blender IK pole parented to the left arm is not
enough: DayZ computes the left helper plane partly from the weapon/right-hand
basis, not only from the left hand.

### 2026-05-20: Command Blend Semantics

Raw evidence:

- Consumer: `ghidra-raw-dayzdiag-weaponik-full-pipeline-1400dec30-fresh.txt`,
  lines 217-229 and 431-461.
- Writer: `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-writer-140108750-fresh.txt`.
- Smoothstep constant:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-smoothstep-const.txt`
  confirms `DAT_140de7b0c = 3.0`.

Confirmed command writer behavior:

`FUN_140108750` evaluates the three boolean/blend inputs:

```text
AimOn  = property slot +0x50
PrimOn = property slot +0x70
SecOn  = property slot +0x90
```

It ramps each value over blend-in / blend-out time, then writes smoothed values
to the command buffer:

```text
smooth(t) = t * t * (3 - 2 * t)

command[4] = smooth(AimOnBlend)
command[5] = smooth(PrimOnBlend)
command[6] = smooth(SecOnBlend)
```

`command[1..3]` is the weapon direction vector built from the two aim angle
inputs, and is only populated when `command[4]` is non-zero.

Confirmed command consumer behavior:

```text
aimBlend = command[4]
primaryRawBlend = command[5]
secondaryBlend = command[6]

primarySolveBlend = max(aimBlend, primaryRawBlend)
```

Execution gates:

```text
if primarySolveBlend > 0:
    run primary FUN_1400e1be0

if secChainCount != 0 and secondaryBlend > 0:
    sample secondary chain
    run secondary FUN_1400e1be0
```

Important implication for Blender:

- Importing an IK `.anm` as raw helper tracks is not enough.
- If the preview wants DayZ parity, the preview operator must expose or assume
  these three runtime blend values.
- For fully-applied weapon IK preview, use:

```text
command[4] = 1
command[5] = 1
command[6] = 1
```

Then:

```text
primarySolveBlend = 1
secondaryBlend = 1
```

For partial game-state preview, the addon needs separate UI controls for Aim,
Primary, and Secondary blends.

### 2026-05-20: Command Direction Vector From AimIKX/AimY

Raw evidence:

- Writer:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-writer-140108750-fresh.txt`,
  lines 139-150.
- Trig helper disassembly:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-vector-trig-140dc01e0-disasm.txt`.
- Full trig fallback:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-vector-trig-140dc0ed0-disasm.txt`.
- Trig constants:
  `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-trig-constants-bulk.txt`.

Confirmed `FUN_140dc01e0` behavior:

```text
input:  angle in XMM0
output: low32 = sin(angle), high32 = cos(angle)
```

The small-angle branch proves the output order:

```text
if abs(angle) < 0x39000000:
    low32  = angle
    high32 = 1.0 - angle * angle * 0.5
```

For larger angles the function calls `FUN_140dc0ed0`. The caller first packs:

```text
lane0 = angle
lane1 = abs(angle) + pi/2
```

Then the fallback computes sine on both lanes, which gives:

```text
lane0 = sin(angle)
lane1 = sin(abs(angle) + pi/2) = cos(angle)
```

Confirmed command-vector writer:

```text
lr = sincos(AimIKX)  # node field +0xb8 / AGR "Weapon Dir LR Angle"
ud = sincos(AimY)    # node field +0xd8 / AGR "Weapon Dir UD Angle"

command[1] = lr.sin * ud.cos
command[2] = ud.sin
command[3] = lr.cos * ud.cos
```

So the weapon desired-axis vector consumed by `case 0x0c` is:

```text
desiredWeaponAxisLocal = (
    sin(AimIKX) * cos(AimY),
    sin(AimY),
    cos(AimIKX) * cos(AimY)
)
```

This closes the main open AUG-related formula gap: the input direction for
weapon-axis correction is not a raw helper-bone vector; it is rebuilt from the
AGR `AimIKX`/`AimY` angle properties before the primary solve.

### Remaining Unknowns Before Blender Port

Current coverage is strong enough to implement a DayZ-style solver pass, but
not enough to honestly call it 100% engine parity.

Confirmed now:

- `FUN_140108750` sends the evaluated `AimIKX`/`AimY` expression results
  directly into `FUN_140dc01e0`; there is no degree-to-radian conversion in the
  WeaponIK command writer. Therefore the values consumed by this node must
  already be radians at runtime.
- Inside the visible `FUN_1400dec30 case 0x0c` branch, `weaponrotator`
  (`RightArm` for player WeaponIK) is fetched with `FUN_14005fc20` and gates
  the pivot-adjusted correction branch. The position pivot used by the visible
  correction math is still `weaponTargetP`, not the fetched `RightArm`
  transform position.

Still not 100% proven:

- Whether an upstream gameplay/graph layer converts camera aim values before
  they become the AGR `AimIKX`/`AimY` runtime variables. This does not change
  the WeaponIK node formula, but it can matter if we want to feed live gameplay
  parameters instead of imported `.anm` values.
- Whether debug/output-buffer code after the solve has any side effect needed
  for editor preview parity. It appears to be output/debug propagation, but it
  should not drive the solve itself.
- Validate the port against at least:
  `p_rfl_erc_idle_ras + aksu`, `aug.anm`, `1911.anm`, and `famas.anm`.

### 2026-07-10 Retail DayZ_x64 Cross-Check

`confirmed`: the current retail `DayZ_x64.exe` loaded in Ghidra retains the
same `AnimNodeWeaponIK` configuration surface used by the earlier DayZDiag
research.

- Program: `DayZ_x64.exe`, image base `0x140000000`.
- `AnimNodeWeaponIK` string: `0x140bbf410`, referenced at `0x1400f6130`.
- `FUN_1400f4bc0` registers the `WeaponIK` node inputs, including
  `Weapon Dir LR Angle` and `Weapon Dir UD Angle`.
- `FUN_1400f5650` is the retail WeaponIK config parser. Its decompile confirms:
  - `weapon` at node offset `+0x1b9`;
  - `weaponrotator` at `+0x1ba`;
  - primary chain ids/count at `+0x1bc` / `+0x1c6`;
  - secondary chain ids/count at `+0x1c1` / `+0x1c7`;
  - `chainaxis`, `secchainaxis`, and `weaponaxis` at `+0x1c8..+0x1c9`
    and `+0x1bb`;
  - `ikpose_chainoffset`, `ikpose_secchainoffset`, and
    `ikpose_weaponoffset` at `+0x1ca..+0x1cc`;
  - primary direction/origin ids at `+0x1cd..+0x1cf`;
  - secondary direction/origin ids at `+0x1d0..+0x1d2`;
  - `outputweaponoffsettobuffer` at `+0x1d3`.

This retail check confirms that the previously reconstructed helper roles and
field ordering still apply to the current game binary. Friendly names remain
reconstructed because the runtime functions are stripped.

### 2026-05-20 Blender Solver Port Note

Implementation update in `AddSurvivorIK.py`:

- Arm-chain input records are sampled from `p_rfl_erc_idle_ras` for the current
  frame, even when the active weapon action contains stale `RightArm` /
  `LeftArm` fcurves.
- Weapon/helper records are read from the active weapon action after applying
  that base chain in Blender, because helper bones are children of the visible
  arm hierarchy in the Blender file.
- Primary chain solves to `RightHandOrigin`; `RightHand_Dummy` / `Weapon_Root`
  remains coincident.
- Secondary chain now reads `LeftHandIKTarget` and left direction helpers after
  primary solve, then solves directly to that object-space target. Reusing a
  stale `weapon_basis + secchainoffset` target from before primary solve pushed
  the left hand down and caused the visible AUG/AKSU mismatch in Blender.
- Default preview `aim_blend` is `0.0` unless real command values are supplied;
  forcing it to `1.0` without imported command angles over-rotates the weapon
  axis correction.
- Roll bones need a Blender post-pass. The DayZ-style 5-record solve can leave
  `ArmRoll` / `ForeArmRoll` off the visible limb line in Blender, which breaks
  the mesh between elbow and wrist even when both hands hit their targets. The
  current preview first restores the main two-bone limb lengths from base pose
  (`Arm -> ForeArm`, `ForeArm -> Hand`), then restores roll records to the
  solved anatomical segment using base-pose distances before applying pose
  matrices. Checking only hand-to-target distance is insufficient; every
  adjacent chain distance must match base/rest spacing.
