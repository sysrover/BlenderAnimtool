# DayZDiag WeaponIK Solver Model

## Джерела

- Бінарник: `DayZDiag_x64.exe`
- Основний runtime consumer: `FUN_1400dec30 case 0x0c`
- Основний solver: `FUN_1400e1be0`
- Helper/cache loader: `FUN_1400e17c0`, `FUN_1400e1a30`
- Raw Ghidra:
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-bufferflow-consumer-1400dec30-case0c-long-slice.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e1be0-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-1400e1be0-disasm.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-1400e1be0-formula-notes.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-constants-targeted.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-140140750-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e17c0-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e1a30-decompile.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e1a30-disasm.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-inputs-http.txt`
  - `ghidra-raw/ghidra-raw-dayzdiag-weaponik-constants-memory.txt`

## Confirmed Callsite Model

`confirmed`: `AnimNodeWeaponIK` не рухає кістки прямо у `FUN_140108750`.
Він пише команду `0x20` bytes з opcode `0x0c`; реальний solve виконує
`FUN_1400dec30 case 0x0c`.

`confirmed`: primary/right chain читається через:

```text
FUN_14005eba0(..., lVar8 + 0xc8, *(byte *)(lVar8 + 0xf0), local_398)
FUN_1400e1be0((float *)(abStack_37c + 4),
              *(byte *)(lVar8 + 0xf2),
              0,
              &local_5b8,
              primary_helper_a,
              primary_helper_b,
              primary_helper_c,
              max(command[4], command[5]),
              debug_buffer)
FUN_14005f5a0(..., local_398, chainCount + 1)
```

`confirmed`: secondary/left chain читається через:

```text
FUN_14005eba0(..., lVar8 + 0xdc, *(byte *)(lVar8 + 0xf1), local_198)
FUN_1400e1be0(local_178,
              *(byte *)(lVar8 + 0xf3),
              0,
              &local_5b8,
              secondary_helper_a,
              secondary_helper_b,
              secondary_helper_c,
              command[6],
              debug_buffer)
FUN_14005f5a0(..., local_198, secChainCount + 1)
```

`confirmed`: `FUN_1400e1be0` receives a compact transform array where each
record is `0x20` bytes: quaternion `float[4]`, translation `float[3]`, and
metadata bytes at `+0x1c..+0x1f`. The primary solver pointer is shifted by one
record: `abStack_37c + 4` is equivalent to `local_398 + 0x20`. The write-back
still writes `chainCount + 1`, so the array includes an extra parent/root
record before the solved chain.

`confirmed`: inside `FUN_1400e1be0`, the five records are the actual configured
chain records:

| Solver record | Role |
|---|---|
| `r0` | chain root / upper pivot; first rotation is applied here |
| `r1` | real intermediate chain bone |
| `r2` | middle/elbow pivot; segment lengths use `r0 -> r2` and `r2 -> r4` |
| `r3` | real intermediate chain bone; receives the final twist correction |
| `r4` | final/end chain bone; blended to the target transform |

`confirmed`: `r1` and `r3` are not hidden sentinels. They come from the
configured `chain[5]` / `secchain[5]` lists. Evidence: `FUN_1401093e0` stores
`chain` at config `+0x1c8..+0x1db`, count at `+0x1f0`, and accepts up to five
entries; `FUN_14005eba0` samples those ids into the compact records before
`FUN_1400e1be0`.

`confirmed`: compact record metadata for this runtime path:

| Record byte | Meaning in WeaponIK path |
|---:|---|
| `+0x1c` | parent/carry source byte; standalone lookup writes `0xff` |
| `+0x1d` | sampled compact record index used by write-back |
| `+0x1e` | requested/config bone id |
| `+0x1f` | copied through helpers but not used by `FUN_1400e1be0` |

## Helper Track Cache

`confirmed`: `FUN_1400e17c0` caches the AGR `ikpose_*` tracks into the runtime
config object before `case 0x0c` solves the chains.

Runtime cached layout:

| Config offset | AGR meaning |
|---:|---|
| `lVar8 + 0x10..0x2f` | `ikpose_chainoffset` transform |
| `lVar8 + 0x30..0x4f` | `ikpose_secchainoffset` transform |
| `lVar8 + 0x50..0x6f` | `ikpose_weaponoffset` transform |
| `lVar8 + 0x70` | cached `ikpose_chainmiddledir` point |
| `lVar8 + 0x7c` | cached first `ikpose_chainmiddlediro` point |
| `lVar8 + 0x88` | cached second `ikpose_chainmiddlediro` point |
| `lVar8 + 0x94` | cached `ikpose_secchainmiddledir` point |
| `lVar8 + 0xa0` | cached first `ikpose_secchainmiddlediro` point |
| `lVar8 + 0xac` | cached second `ikpose_secchainmiddlediro` point |

`confirmed`: `FUN_1400e1a30` is the helper-point builder for the middle
direction triples. It:

- initializes outputs to sentinel `0xff7fffff` / `-3.4028235e+38`;
- refuses to build points if any of the three track ids is `0xff`;
- resolves each track id through `FUN_1400d3b50`;
- copies transforms through `FUN_1400d39f0`;
- outputs:
  - `param_4`: translation of the direction track;
  - `param_5`: translation of the first origin track;
  - `param_6`: first origin translation plus the first origin rotation applied
    to the second origin/direction track translation.

`confirmed`: the `FUN_1400e1a30` decompile looks confusing because the third
track output is decoded into a local stack transform. The disassembly confirms
the vector passed to `FUN_14013fa00` is the decoded third-track translation at
`RSP + 0x80`, not an always-zero vector. This means the `*middlediro` pair is a
real two-track direction/origin pair.

## Config And Runtime Layout

`confirmed`: `FUN_1401093e0` parses the `AnimNodeWeaponIK` config text into the
node object:

| Node offset | Config key |
|---:|---|
| `+0x1b8` | `hand` |
| `+0x1bc` | `weapon` |
| `+0x1c0` | `weaponrotator` |
| `+0x1c4` | `weaponaxis` |
| `+0x1c8..+0x1db` | `chain[5]` |
| `+0x1dc..+0x1ef` | `secchain[5]` |
| `+0x1f0` | primary chain count |
| `+0x1f1` | secondary chain count |
| `+0x1f2` | `chainaxis` |
| `+0x1f3` | `secchainaxis` |
| `+0x1f8` | `ikpose_secchainoffset` |
| `+0x1fc` | `ikpose_weaponoffset` |
| `+0x200` | `ikpose_chainmiddledir` |
| `+0x204`, `+0x208` | `ikpose_chainmiddlediro[2]` |
| `+0x20c` | `ikpose_secchainmiddledir` |
| `+0x210`, `+0x214` | `ikpose_secchainmiddlediro[2]` |
| `+0x218` | `outputweaponoffsettobuffer` |

`confirmed`: `case 0x0c` uses a compact runtime object `lVar8` with this
layout:

| Runtime offset | Meaning |
|---:|---|
| `+0x10..+0x2b` | cached `ikpose_chainoffset` transform |
| `+0x30..+0x4b` | cached `ikpose_secchainoffset` transform |
| `+0x50..+0x6f` | cached `ikpose_weaponoffset` fallback transform |
| `+0x70`, `+0x7c`, `+0x88` | primary helper points |
| `+0x94`, `+0xa0`, `+0xac` | secondary helper points |
| `+0xbc` | `ikpose_weaponoffset` remapped id |
| `+0xc0` | `weaponrotator` remapped id |
| `+0xc4` | `weaponaxis` selector |
| `+0xc8..+0xdb` | primary chain ids |
| `+0xdc..+0xef` | secondary chain ids |
| `+0xf0` | primary chain count |
| `+0xf1` | secondary chain count |
| `+0xf2` | primary chain solve axis |
| `+0xf3` | secondary chain solve axis |
| `+0x118` | output weapon-offset flag |

`confirmed`: command fields consumed by `case 0x0c`:

| Command field | Meaning |
|---:|---|
| `[1..3]` | input weapon direction vector |
| `[4]` | weapon-axis/weapon-offset blend amount |
| `[5]` | primary chain blend amount |
| `[6]` | secondary chain blend amount |
| `[7]` | config selector used to retrieve `lVar8` |

`confirmed`: `command[1..3]` is generated by `FUN_140108750` from the two AGR
weapon direction angle inputs:

| Node field | AGR property | Meaning |
|---:|---|---|
| `param_1 + 0xb8` | `Weapon Dir LR Angle` / `AimIKX` | left/right weapon aim angle |
| `param_1 + 0xd8` | `Weapon Dir UD Angle` / `AimY` | up/down weapon aim angle |

Raw evidence:

- writer callsite:
  `ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-writer-140108750-fresh.txt`,
  lines 139-150;
- trig helper:
  `ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-vector-trig-140dc01e0-disasm.txt`;
- trig fallback:
  `ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-vector-trig-140dc0ed0-disasm.txt`.

`confirmed`: `FUN_140dc01e0(angle)` returns packed `sin/cos`:

```text
low32  = sin(angle)
high32 = cos(angle)
```

The small-angle branch proves the lane order because it returns:

```text
low32  = angle
high32 = 1.0 - angle * angle * 0.5
```

The command writer then builds:

```text
lr = sincos(AimIKX)
ud = sincos(AimY)

command[1] = lr.sin * ud.cos
command[2] = ud.sin
command[3] = lr.cos * ud.cos
```

So the desired weapon-axis vector before root-space rotation is:

```text
desiredWeaponAxisLocal = (
    sin(AimIKX) * cos(AimY),
    sin(AimY),
    cos(AimIKX) * cos(AimY)
)
```

`confirmed`: there is no degree-to-radian conversion between
`FUN_1400e59a0` evaluating the AGR expression and `FUN_140dc01e0` consuming the
angle. The WeaponIK node expects the evaluated runtime values to already be in
radians.

## Primary Chain Helper Points

`confirmed`: `case 0x0c` only passes primary helper points into
`FUN_1400e1be0` when all three cached points are valid:

```text
lVar8 + 0x70 != DAT_140de8cc0
lVar8 + 0x7c != DAT_140de8cc0
lVar8 + 0x88 != DAT_140de8cc0
```

`confirmed`: primary helper world/current-pose points are built by rotating the
cached vectors by the current primary end quaternion `local_5b8`, then adding
the current primary end translation `local_5a8/local_5a4/local_5a0`:

```text
local_4e8 = current_end_pos + rotate(current_end_rot, *(lVar8 + 0x70))
local_4c8 = current_end_pos + rotate(current_end_rot, *(lVar8 + 0x7c))
local_4d8 = current_end_pos + rotate(current_end_rot, *(lVar8 + 0x88))
```

`confirmed`: these are passed to the solver as:

```text
param_5 = &local_4e8
param_6 = &local_4c8
param_7 = &local_4d8
```

`likely`: in solver math, `param_5` is the desired middle/pole direction point,
while `param_6 -> param_7` is a reference line used to define the pole plane.
Evidence: `FUN_1400e1be0` computes cross products using
`param_7 - param_6`, then compares/project-aligns `param_5` against that plane.

## Secondary Chain Helper Points

`confirmed`: secondary helper points are also optional and require all three
sentinel checks to pass:

```text
lVar8 + 0x94 != DAT_140de8cc0
lVar8 + 0xa0 != DAT_140de8cc0
lVar8 + 0xac != DAT_140de8cc0
```

`confirmed`: secondary passes:

```text
param_5 = &local_4b8
param_6 = &local_498
param_7 = &local_4a8
```

`confirmed`: unlike primary, secondary uses two bases:

- `local_4b8` is built from primary/current hand basis `local_5b8/local_5a8`.
- `local_498` and `local_4a8` are built from secondary target basis
  `local_588/local_578`.

This is why a Blender preview cannot treat the left-hand helpers as a simple
static pole vector parented under the left hand. DayZDiag mixes weapon/right
hand basis and secondary target basis.

## Solver Behavior

`confirmed`: `FUN_1400e1be0` does a two-stage chain solve:

1. It computes the vector from chain root to target:
   `param_4[4..6] - param_1[4..6]`.
2. It computes chain segment lengths from the compact transform records:
   root to middle/end area and middle to final area.
3. If helper points exist, it builds a pole-plane correction using
   `param_5`, `param_6`, and `param_7`.
4. It maps the configured local chain axis through `FUN_1400e33b0`.
5. It builds quaternions with `FUN_1400e3240` to rotate the current local axis
   toward the desired chain direction.
6. It rotates child record positions around the chain root with
   `FUN_14013fa00`.
7. It aligns the last record to `param_4` and blends final rotation and
   translation by `param_8`.

`confirmed`: `param_8` is not a coordinate tolerance. It is the solver blend
weight. The solver uses `1.0 - param_8` and `param_8` repeatedly for quaternion
slerp/lerp and final translation blending.

`confirmed`: `_DAT_140de9234` is the quaternion slerp threshold `0.999`
from memory bytes `77 be 7f 3f`. It only chooses lerp vs slerp when rotations
are almost identical.

## Solver Formula Details

`confirmed`: targeted Ghidra memory reads decoded these constants used by
`FUN_1400e1be0`:

| Address | Value | Role |
|---|---:|---|
| `DAT_140de84d0` | `0.9800000190734863` | reach limit multiplier |
| `DAT_140de84bc` | `0.25` | squared half term in law-of-cosines block |
| `DAT_140de2ec8` | `0.5` | half scalar and final twist slerp amount |
| `DAT_140de5a84` | `0.00009999999747378752` | length threshold before final re-normalization |
| `_DAT_140de9234` | `0.9990000128746033` | slerp-vs-lerp threshold |
| `DAT_14111d940` | `(0, 0, 0, 1)` | identity quaternion in DayZ `x,y,z,w` order |

`confirmed`: the chain reach clamp is not the full segment sum. DayZDiag uses:

```text
a = root-to-middle length
b = middle-to-end length
dist = root-to-target length

reach = max(abs(a - b), min(dist, (a + b) * 0.9800000190734863))
doubledX = (a*a - b*b) / reach + reach
x = doubledX * 0.5
h = sqrt(a*a - doubledX*doubledX*0.25)
```

`confirmed`: `FUN_140140750` is the quaternion blend helper. It clamps `t`,
flips the second quaternion when the dot product is negative, uses linear
interpolation when `dot >= 0.9990000128746033`, otherwise uses acos/sin slerp.

`confirmed`: the final `r3` phase is not a generic half-blend to the target
rotation. It projects the end-target rotation delta onto the current
`r2 -> r4` segment and applies that as a twist to `r3`:

```text
delta = targetQ * inverse(r4Q)
p = r4Pos - r2Pos
proj = dot(p, delta.xyz)
twist.xyz = p * proj / dot(p, p)
twist.w = delta.w
twist = normalize(twist)
if proj < 0:
    twist = -twist
r3TargetQ = r3Q * twist
r3Q = slerp_dayz(r3Q, r3TargetQ, 0.5)
```

Evidence: `ghidra-raw-dayzdiag-weaponik-helper-1400e1be0-decompile.txt`
lines around the final `FUN_140140750(param_1 + 0x18, &local_118, &local_f0,
DAT_140de2ec8)` call, plus the targeted formula notes in
`ghidra-raw-dayzdiag-weaponik-1400e1be0-formula-notes.txt`.

## Weapon Aim Correction And Target Construction

`confirmed`: before primary/secondary chain solve, `case 0x0c` builds targets
from the current chain end plus cached IK pose tracks, then optionally applies a
weapon-axis correction.

Raw evidence:

- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-full-pipeline-1400dec30-fresh.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-full-pipeline-helpers-fresh.txt`
- `ghidra-raw/ghidra-raw-dayzdiag-weaponik-command-writer-140108750-fresh.txt`

Primary target construction:

```text
currentEnd = last record of primary compact chain

primaryTargetP = currentEnd.P + rotate(currentEnd.Q, ikpose_chainoffset.P)
primaryTargetQ = currentEnd.Q * ikpose_chainoffset.Q
```

For player WeaponIK:

```text
ikpose_chainoffset = RightHandOrigin
```

Weapon target construction:

```text
weaponOffset = fetched ikpose_weaponoffset track if present
             else cached ikpose_weaponoffset from the runtime config

weaponTargetP = primaryTargetP + rotate(primaryTargetQ, weaponOffset.P)
weaponTargetQ = primaryTargetQ * weaponOffset.Q
```

For player WeaponIK:

```text
ikpose_weaponoffset = RightHand_Dummy
```

Weapon-axis correction:

```text
currentWeaponAxis = axis_vector(weaponaxis, weaponTargetQ)
desiredWeaponAxis = command[1..3]
if current/root pose quaternion is available:
    desiredWeaponAxis = rotate(currentRootQ, desiredWeaponAxis)

correctionQ = quat_from_vector_to_vector(currentWeaponAxis, desiredWeaponAxis)
correctionQ = slerp(identityQ, correctionQ, command[4])
```

If `weaponrotator == 0xff`, DayZDiag applies `correctionQ` directly to
`primaryTargetQ`.

If `weaponrotator != 0xff`, DayZDiag first verifies that the configured
`weaponrotator` transform can be read with `FUN_14005fc20`. For player
WeaponIK this is `RightArm`. Then it also rotates the target position around
the weapon target:

```text
offset = primaryTargetP - weaponTargetP
primaryTargetP = weaponTargetP + rotate(correctionQ, offset)
primaryTargetQ = correctionQ * primaryTargetQ
```

This is one of the likely missing pieces for AUG: the right hand target is
moved around the weapon/right-hand basis before the primary chain solve, not
only rotated in place.

Secondary target construction starts after the primary chain target/basis has
been corrected:

```text
weaponBasisP = primaryTargetP + rotate(primaryTargetQ, weaponOffset.P)
weaponBasisQ = primaryTargetQ * weaponOffset.Q

secondaryTargetP = weaponBasisP + rotate(weaponBasisQ, ikpose_secchainoffset.P)
secondaryTargetQ = weaponBasisQ * ikpose_secchainoffset.Q
```

For player WeaponIK:

```text
ikpose_secchainoffset = LeftHandIKTarget
```

Secondary helper construction uses mixed bases:

```text
secondaryHelperMid = secondaryTargetP + rotate(secondaryTargetQ, secchainmiddledir)
secondaryHelperA = weaponBasisP + rotate(weaponBasisQ, secchainmiddlediro0)
secondaryHelperB = weaponBasisP + rotate(weaponBasisQ, secchainmiddlediro1)
```

So the left-hand helper plane is partly weapon/right-hand based. A static
Blender pole target under the left arm cannot match this exactly.

`confirmed`: `FUN_1400e3240(outQ, currentWeaponAxis, desiredWeaponAxis)` builds
the correction quaternion from two vectors.

`confirmed`: `FUN_1400e33b0(axisOut, quaternion, axisId)` extracts local
`+x,+y,+z,-x,-y,-z` axis vectors from a quaternion.

`confirmed`: command blends are written by `FUN_140108750` as smoothstep values:

```text
smooth(t) = t * t * (3 - 2 * t)

command[4] = smooth(AimOnBlend)
command[5] = smooth(PrimOnBlend)
command[6] = smooth(SecOnBlend)
```

`confirmed`: `case 0x0c` consumes them as:

```text
primarySolveBlend = max(command[4], command[5])
secondarySolveBlend = command[6]
```

`confirmed`: player AGR uses:

```text
weapon = RightHand_Dummy
weaponrotator = RightArm
weaponaxis = -x
chainaxis = -x
secchainaxis = +x
```

Axis id mapping is confirmed through `FUN_1400e33b0`:

| id | axis |
|---:|---|
| `0` | `+x` |
| `1` | `+y` |
| `2` | `+z` |
| `3` | `-x` |
| `4` | `-y` |
| `5` | `-z` |

## Blender Skeleton Rules

`confirmed`: the special WeaponIK names are pose/remap tracks, not fixed XOB
skeleton bones. DayZDiag resolves them by AGR config and current IK pose data.

For Blender authoring:

- Real arm chains should stay as real skeleton/control bones:
  `RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand` and
  `LeftArm, LeftArmRoll, LeftForeArm, LeftForeArmRoll, LeftHand`.
- Helper controls should exist as exportable pose tracks:
  `RightHandOrigin`, `RightHand_Dummy`,
  `RightForeArmDirectionOrigin`, `RightForeArmDirection`,
  `LeftHandOrigin`, `LeftHandIKTarget`,
  `LeftForeArmDirectionOrigin`, `LeftForeArmDirection`.
- `RightHand_Dummy` / `LeftHand_Dummy` can also exist as real model bones.
  For player data, `RightHand_Dummy` is a real weapon bone under `RightHand`
  and the IK pose also contains a track with the same name for
  `ikpose_weaponoffset`.
- Helper controls should be unparented or parented only to non-solved
  control roots in Blender, because DayZDiag resolves them from pose data and
  then uses them as solver inputs. Parenting them into the solved arm chains can
  create dependency cycles that DayZDiag does not have.
- Export must preserve helper transforms graph-relative by name. It must not
  drop them because they are unparented Blender bones.
- Export/preview should treat `LeftHandIKTarget` as the secondary-chain target
  in the weapon/right-hand frame, not as a copy of `LeftHandOrigin`.
- `*ForeArmDirectionOrigin` and `*ForeArmDirection` are direction pairs:
  DayZDiag decodes both tracks and builds the guide point as
  `originTranslation + originRotation * directionTranslation`.

For Blender preview parity:

- Use right-hand/weapon target correction first.
- Solve primary chain with `chainaxis = -x`.
- Then solve secondary chain with `secchainaxis = +x`.
- Do not use a fixed pole-bone position. Compute pole/helper points from the
  imported IK pose tracks each frame, matching the DayZDiag basis rules above.
- A normal Blender IK constraint can preview the broad shape, but exact
  DayZDiag parity needs a custom Python/mathutils solver that ports
  `FUN_1400e1be0`.

## Still Not 100 Percent

`confirmed`: we now have the runtime order, config-offset table, helper-track
mapping, compact record layout, axis mapping, blend parameters, sentinel
behavior, chain reach/law-of-cosines block, DayZ slerp helper, and final `r3`
twist projection formula.

`unknown`: exact symbolic/engine class names are still missing because the
target binary is stripped. The numeric transform formula above is decompiler
and memory-backed.

`confirmed`: `outputweaponoffsettobuffer` maps to node offset `+0x218` and
runtime flag `lVar8 + 0x118`. In `case 0x0c`, when this flag is set and no
existing offset was fetched, DayZDiag writes/inserts the weapon offset for the
configured `ikpose_weaponoffset` id.

`unknown`: exact symbolic/engine class names for the runtime object fields are
not available in the stripped binary. Their behavior and offsets are
Ghidra-backed, but the friendly names are reconstructed.
