# DayZ IK1H Hybrid Proxy Workflow (Blender 4.5)

## Confirmed runtime/authoring model

DayZ evaluates a one-hand WeaponIK pose on top of an already evaluated base
player animation.  The Blender importer therefore remembers the action that was
active immediately before the IK ANM import as `dayz_weaponik_base_action`.

Primary player chain from the player AGR/AnimNodeWeaponIK research:

```text
RightArm, RightArmRoll, RightForeArm, RightForeArmRoll, RightHand
chainaxis = -x
ikpose_chainoffset = RightHandOrigin
ikpose_weaponoffset = RightHand_Dummy
ikpose_chainmiddledir = RightForeArmDirection
ikpose_chainmiddlediro = RightHandOrigin, RightForeArmDirectionOrigin
```

`RightArmRoll` and `RightForeArmRoll` distribute roll/twist. They are not extra
anatomical joints for a Blender IK constraint.

## Hybrid Blender preview

The addon creates an internal fixed-length proxy chain:

```text
MCH_RightArm_IK: RightArm.head -> RightForeArm.head
MCH_RightForeArm_IK: RightForeArm.head -> RightHand.head
MCH_RightHand_IK: wrist orientation only
```

- Native Blender IK runs on `MCH_RightForeArm_IK` with `chain_count = 2`.
- Stretch is disabled.
- `CTRL_RightHand` is the animator position/rotation target and starts at the
  already visible imported `RightHand` pose.
- `CTRL_RightElbow` is the animator pole target and starts in the already
  visible shoulder-elbow-wrist bend plane.
- `IK_RightHandOrigin.R`, `IK_RightElbow.R`, and
  `IK_RightElbowOrigin.R` are separate hidden export-helper controls.
- The hidden controls are parented to animator controls, so animator edits are
  exported as deltas without treating DayZ local offsets as world targets.
- `MCH_RightHand_IK` copies world rotation from `CTRL_RightHand` independently,
  so wrist rotation cannot change the effector position.
- A lightweight depsgraph sync aligns the original `RightArm` and
  `RightForeArm` true-joint vectors to the already solved proxy shoulder,
  elbow, and wrist points. Roll bones remain in the native hierarchy and
  inherit the result; they are never IK joints or absolute rotation targets.
- The Python sync is disabled while ANM data is sampled for export.
- Original helper tracks use `DAT_IK_AUTHOR_` constraints and remain the actual
  export source.

## User workflow

1. Select `_DayZ_Character`.
2. Import `p_1hd_erc_idle_low.anm` with Translation off, Rotation on, Scale off.
3. Import an IK ANM from `P:\BlenderAnimtool\examples\ik` with Translation and
   Rotation on, Scale off.
4. Open `DayZ Animation Tools > Tools` and click
   `Build DayZ 1H IK Controls`.
5. Edit frames 0/1 using:
   - `CTRL_RightHand`: move and rotate the wrist;
   - `CTRL_RightElbow`: change the bend plane without moving the wrist.
6. Insert control keys as needed.
7. Click `Bake DayZ 1H Controls To Helpers`.
8. Export ANM with:
   - Type: `Survivor IK 1h`;
   - Translation Keys: on;
   - Rotation Keys: on;
   - Scale Keys: off;
   - Preserve Imported Raw ANM: off.

IK1H export contains only `RightHand`, right fingers, `RightHand_Dummy`,
`RightHandOrigin`, `RightForeArmDirectionOrigin`, and
`RightForeArmDirection`. Left-hand tracks are excluded.

## Verification

Automated Blender 4.5 test:

`C:\Users\sysro\diag\CsharpModVScode\tools\test_dayz_ik1h_proxy_workflow.py`

Corpus tested:

- `9v_battery.anm`
- `apple.anm`
- `banana.anm`
- `bark_oak.anm`
- `book.anm`
- `candle.anm`

All corpus cases pass position, elbow isolation, fixed-length, wrist rotation,
IK1H filtering, bake, re-import, and numeric re-export checks. For the recorded
`apple` test the maximum decoded ANM round-trip error is approximately
`0.00001955`, with no missing tracks.

## Ghidra verification: local offsets, not world targets

Live Ghidra program: `DayZ_x64.exe`.

- `AnimNodeWeaponIK` string: `0x140bbf410`, referenced by
  `FUN_1400f6130`.
- `ikpose_chainoffset` string: `0x140bbf380`, referenced by parser
  `FUN_1400f5650`.
- Retail runtime evaluator: `FUN_1400ca870`.

Confirmed evaluator order:

```text
load current primary chain-end transform
rotate/compose cached param_3+0x20 through that end transform
add the rotated offset to the current end position
```

This matches the previously reconstructed formula:

```text
primaryTargetP = currentEnd.P + rotate(currentEnd.Q, chainoffset.P)
primaryTargetQ = currentEnd.Q * chainoffset.Q
```

The same evaluator rotates middle-direction cached points by the current target
basis before adding its position. Therefore `RightHandOrigin` and
`RightForeArmDirection` must not be used directly as Blender world-space hand
and elbow controls.

Raw decompiler evidence:

`P:\BlenderAnimtool\Research\anm_reports\ghidra-raw-ik1h-offset-verification-20260711.txt`

## Visual verification

- User-provided expected `apple` pose: right arm almost straight at the side.
- Raw base+apple capture:
  `C:\Users\sysro\diag\CsharpModVScode\anm\ik1h_apple_raw_front.png`
- Final calibrated proxy capture:
  `C:\Users\sysro\diag\CsharpModVScode\anm\ik1h_apple_final_front.png`

For `apple`, automatic pole calibration selected approximately `1.6022123 rad`
(`91.8 deg`). Recorded initial elbow fit error was approximately `0.0000342 m`.
The automated test additionally requires the maximum initial joint-position
change caused by building controls to remain below `0.0001 m`.

### Clean authoring view (2026-07-11)

The live Blender 4.5 scene was checked through `blender-remote`. The main
deformation armature bones and all FK/export/helper/proxy bones were hidden
from the authoring view; only `CTRL_RightHand` and `CTRL_RightElbow` remain
visible. Bone labels, relationship lines and transform gizmos are disabled.

Screenshot:
`P:\BlenderAnimtool\Research\anm_reports\screenshots\ik1h-apple-controls-clean-20260711.png`

Live scene evidence at capture time:

```text
blend: P:\Animation_Weapon\saved\Weapon_template_dayz_clean_pose.blend
mode: POSE
visible control-rig bones: CTRL_RightHand, CTRL_RightElbow
selected control: CTRL_RightHand
hidden deformation bones: 163
```

## Finger authoring correction (2026-07-11)

The intermediate `IK_RightHand*` / `IK_LeftHand*` finger controls were removed.
The original DayZ finger bones already contain animator-authored local
`Limit Rotation` constraints and are used directly by Quick Finger Collision.
The former control rig added `Copy Rotation` after those limits and could
therefore overwrite the limited result.

Current behavior:

- original DayZ finger bones are edited and keyed directly;
- their existing `Limit Rotation` constraints are preserved;
- no `DAT_IK_AUTHOR_*` constraints remain on finger bones;
- only the seven true IK helper tracks use `IK_*` proxy controls;
- right finger tracks are still exported directly from the original bones;
- the live control rig contains 22 bones instead of 56;
- the current `apple` pose was baked before migration (119 right-finger
  f-curves preserved).

The updated `apple` Blender 4.5 export/reimport/re-export test passes with no
missing tracks. Source and installed addon copies match at SHA-256
`C1B0194A949ADE8954D184144CB3315BBD87807E0D4435DD164A1232EDA20285`.

## Import-menu registration correction (2026-07-11)

Binary ANM entries could either appear twice after a hot reload or disappear
from `DayZ Animation Tools > Import` after restart, depending on whether the
binary or human-readable addon registered first. Both import packages now use
idempotent callback registration. When the binary addon starts first, the main
tools addon adds the already registered binary callbacks to its custom menu.
Live verification after the fix found exactly one `ImportAnmMenu` and one
`ImportXobMenu` callback in both the custom import menu and Blender's File
Import menu; `import_scene.anm` remained registered.

## Bake unkeyed-control reset correction (2026-07-11)

`Bake DayZ 1H Controls To Helpers` previously called `scene.frame_set()` before
committing interactive control edits. If the animator moved
`CTRL_RightHand`/`CTRL_RightElbow` without manually inserting keys, the frame
change evaluated the older control action and reset the arm to the base pose;
directly edited finger bones remained unchanged.

The Bake operator now:

- automatically keys Location and Rotation of both animator controls at the
  current frame before sampling frames 0–1;
- performs an explicit final proxy-to-DayZ synchronization after returning to
  the original frame;
- declares Blender Undo support.

The automated test deliberately leaves a 15-degree wrist edit unkeyed before
Bake. Current results are `bake_control_reset_error = 0` and
`bake_dayz_reset_error = 0`; the full export/reimport/re-export test passes.

## IK1H per-track translation rule (2026-07-11)

Correction: an earlier revision incorrectly classified `RightHand` and finger
tracks as rotation-only. The decoded `player/ik` corpus proves that every track
present in an IK1H file has a position channel. "Not every bone" means only the
IK1H whitelist is exported, not that some tracks inside that whitelist omit
position.

Corpus evidence includes `RightHand` in 453/453 applicable files, every right
finger track in 654/654, `RightHand_Dummy` in 654/654,
`RightHandOrigin` in 637/637, `RightForeArmDirection` in 632/632 and
`RightForeArmDirectionOrigin` in 577/577. All counts have `pos > 0`.

The exporter therefore creates at least one position key for every whitelisted
IK1H track, including zero-valued constant channels. A decoded live `toy_ik`
export has 22 tracks, 22 position tracks, no missing position tracks and one
position key on `RightHand`.

### Mandatory two-frame helper bake

The live `toy_ik` audit showed that the original file omitted
`RightForeArmDirectionOrigin`, while `RightHand_Dummy` had rotation but no
location curve. Bake now creates/samples all four required right-side tracks
regardless of whether they were keyed in the imported action. A hidden
`IK_RightHandDummy.R` control preserves the dummy's relation to
`CTRL_RightHand`.

After the live migration, each of `RightHandOrigin`,
`RightForeArmDirection`, `RightForeArmDirectionOrigin` and `RightHand_Dummy`
has both `location` and `rotation_quaternion` keys at frames 0 and 1 in
`toy_ik`. The character armature was made active so the Dope Sheet displays
the baked action rather than `toy_ik_controls`.

Evidence screenshot:
`P:\BlenderAnimtool\Research\anm_reports\screenshots\toy-ik-helpers-baked-keys-20260711.png`
