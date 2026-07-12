# DayZ IK1H canonical ground truth

Last verified: 2026-07-11  
Scope: Blender 4.5 one-hand/right-arm DayZ IK authoring and binary ANM
import/export.

This file is the canonical source of truth for the current IK1H workflow. Do
not change production IK code from memory, a chat answer, a screenshot, or an
old research note. First check this file and the primary evidence it cites.

## 1. Evidence policy

Evidence priority is:

1. Decoded retail ANM corpus for exact file, track and channel inventory.
2. Ghidra decompiler/disassembly for runtime transform and solver behavior.
3. Numeric Blender import/Bake/export/reimport tests.
4. Live Blender inspection through `blender-remote`.
5. Working notes and visual hypotheses.

Only levels 1–4 may establish a fact in this file. Raw Ghidra output does not
by itself define which tracks are present in retail files; it establishes how
runtime data is consumed. The decoded corpus is authoritative for track and
channel inventory.

Historical files under `Research/anm_reports` may contain superseded designs,
including five-bone Blender IK attempts, separate finger controls, and the
incorrect claim that `RightHand`/finger tracks are rotation-only. When those
notes conflict with this file, this file wins.

Status words:

- **confirmed**: directly established by corpus, Ghidra, numeric test or live
  inspection.
- **implementation**: true of the current Blender addon, but not necessarily
  identical to DayZ runtime internals.
- **unknown**: not proven and must not be converted into a production rule.

## 2. Retail IK ANM corpus

Primary evidence:

- `anm_reports/player-ik-anm-corpus.json`
- `anm_reports/player-ik-anm-corpus.md`

Confirmed corpus facts:

- 654 files under `P:\DZ\anims\anm\player\ik` parse successfully.
- Every file uses 30 FPS.
- 359 files are `ANIMSET5`; 295 are `ANIMSET6`.
- 652 files contain two frames; `gear/gas_cooker.anm` and
  `gear/morphine.anm` contain one frame.
- Valid files do not all carry the same optional helper set.
- Five legacy files use `RightForeHandDirection`; the current skeleton/runtime
  name is `RightForeArmDirection`. Import may alias the legacy spelling;
  export uses the canonical spelling.
- Corpus track flags are only `0` and `1`.

### 2.1 Position channels

Confirmed: every track present in a retail IK file has at least one position
key. "Not every bone has translation" means non-IK skeleton bones are absent
from the IK file; it does not mean `RightHand` or fingers are rotation-only.

| Track class | Files containing track | Files with position |
|---|---:|---:|
| `RightHand` | 453 | 453 |
| each right finger track | 654 | 654 |
| `RightHand_Dummy` | 654 | 654 |
| `RightHandOrigin` | 637 | 637 |
| `RightForeArmDirection` | 632 | 632 |
| `RightForeArmDirectionOrigin` | 577 | 577 |

Equivalent left-side tracks also have position channels whenever present.
`Weapon_Root` is a known exception outside the right-hand IK1H whitelist: it
appears in 17 corpus files and has no position keys there.

Current IK1H export rule:

- every exported IK1H track must retain at least one position key;
- a constant zero position still receives a channel/key;
- `Translation Keys` must be enabled;
- non-IK body bones are filtered before sampling.
- `RightHand_Dummy` is animator-editable through `IK_RightHandDummy.R`; export
  must sample the baked track and must never restore its imported raw source
  channel as a supposedly stable structural helper.
- `RightHand_Dummy` is exported relative to the current authored primary hand
  target (`CTRL_RightHand`) with the ANM axis fix. DayZ later computes
  `weaponBase = primaryTarget * cachedDummy`; using the decoded/base RightHand
  during edited export bakes the hand rotation into cachedDummy and applies it
  twice at runtime. Raw imports without controls fall back to decoded
  `RightHand`.
- `RightForeArmDirectionOrigin` is a stable local vector-record consumed under
  the current primary target. Bake must not restore its imported *world*
  matrix after the hand control moves; its control follows the primary target
  with the same local offset. Export preserves the imported raw translation
  and rotation channels. Runtime uses
  `RightHandOrigin.rotation * RightForeArmDirectionOrigin.translation` for the
  guide; the direction-origin bone's own display rotation is not that basis.
- `RightForeArmDirection` is sampled relative to the current authored primary
  target. A changed `CTRL_RightHand` invalidates the imported item-specific
  direction even if `CTRL_RightElbow` itself was not moved; in that case do not
  restore the source `RightForeArmDirection` track.
- Import order/space: decode `RightHandOrigin` first, recover the runtime
  primary target by removing its Blender display-tail offset, then compose
  `RightForeArmDirectionOrigin` and `RightForeArmDirection` under that target.
  Composing these tracks under the pre-IK `RightHand` is incorrect and makes a
  freshly imported item-specific ANM start from the wrong helper basis.
- Blender display rule for `RightForeArmDirectionOrigin`: compose its raw
  translation under the decoded primary target, but display it with the
  primary-target rotation. Runtime uses this track's translation under
  `RightHandOrigin.rotation`; its own raw rotation is retained only in action
  metadata for exact re-export and must not visually tilt the imported helper.
- For parented primary guide bones, convert the already composed object-space
  runtime matrix explicitly with `basis_from_object_matrix`. Assigning
  `PoseBone.matrix` and later keying its channels allows parent/action
  re-evaluation to apply another transform; the observed failure placed RHO
  6.5 cm off the hand-to-RFDO line at a 40.54-degree angle.
- Build-control capture rule: capture evaluated object-space matrices for
  `RightForeArmDirectionOrigin` and `RightForeArmDirection` before restoring
  the proxy/base arm. Restoring the parent `RightHand` first changed the
  freshly imported aligned origin from 0 degrees to the old 38.65-degree
  cereal rotation before it reached the control rig.
- when rebuilding controls from an imported IK1H, capture the evaluated
  `RightHand_Dummy` object-space matrix before restoring the proxy base chain;
  restoring `RightHand` first otherwise drags the parented dummy and destroys
  the imported offset before it reaches `IK_RightHandDummy.R`.

### 2.2 Rotation and scale

Confirmed:

- right hand, helpers, dummy and finger tracks carry rotation channels when
  the source pose needs them;
- some base ring/pinky tracks have no rotation in a minority of retail files,
  so identity rotation does not need to be forced;
- player IK corpus tracks have no scale keys;
- IK1H export must use `Scale Keys = off`.

### 2.3 Track flags

Ghidra-backed reader facts:

- bit `0x10`: position frames are implicit dense frames;
- bit `0x20`: rotation frames are implicit dense frames;
- bit `0x40`: SET6 scale frames are implicit dense frames;
- with those bits clear, explicit `uint16` frame indices are stored;
- corpus low bit `0x01` does not alter DATA position/rotation timing in the
  reader/samplers examined;
- writing `flags = 0` with explicit indices is valid;
- exact runtime meaning of low bit `0x01` remains unknown.

Evidence: `anm_reports/dayzdiag-anm-track-flags.md` and
`anm_reports/dayzdiag-anm-reader.md`.

## 3. Canonical IK1H output tracks

The current right-hand canonical superset is 22 tracks:

```text
RightHand
RightHandRing
RightHandRing1
RightHandRing2
RightHandRing3
RightHandThumb1
RightHandThumb2
RightHandThumb3
RightHandMiddle1
RightHandMiddle2
RightHandMiddle3
RightHandIndex1
RightHandIndex2
RightHandIndex3
RightHandPinky
RightHandPinky1
RightHandPinky2
RightHandPinky3
RightHand_Dummy
RightForeArmDirectionOrigin
RightHandOrigin
RightForeArmDirection
```

Excluded:

- all left-side tracks in `IK1H` mode;
- terminal finger segment `*4`;
- proxy/control/mechanism bones;
- arm/roll/forearm body bones;
- unrelated skeleton bones;
- scale channels.

Confirmed live export evidence:

- `toy_ik`: 22 exported tracks;
- 22/22 tracks have position channels;
- `RightHand` has a position key;
- no missing position tracks.

Evidence: `anm_reports/toy-ik-live-position-verify-20260711.json`.

## 4. DayZ runtime WeaponIK mapping

Primary evidence:

- `anm_reports/dayzdiag-weaponik-solver-model.md`
- `anm_reports/blender-weaponik-template-rig-rules.md`
- `anm_reports/player-weaponik-agr-runtime-map.md`
- `anm_reports/ghidra-raw-ik1h-offset-verification-20260711.txt`

Confirmed player mapping:

```text
primary hand       = RightHand
weapon offset      = RightHand_Dummy
weapon rotator     = RightArm
primary chain      = RightArm, RightArmRoll, RightForeArm,
                     RightForeArmRoll, RightHand
secondary chain    = LeftArm, LeftArmRoll, LeftForeArm,
                     LeftForeArmRoll, LeftHand
primary chainaxis  = -X
secondary chainaxis= +X
weapon axis        = -X
```

Confirmed IK-pose mapping:

```text
ikpose_chainoffset       = RightHandOrigin
ikpose_weaponoffset      = RightHand_Dummy
ikpose_chainmiddledir    = RightForeArmDirection
ikpose_chainmiddlediro   = RightHandOrigin,
                           RightForeArmDirectionOrigin
ikpose_secchainoffset    = LeftHandIKTarget
ikpose_secchainmiddledir = LeftForeArmDirection
ikpose_secchainmiddlediro= LeftHandOrigin,
                           LeftForeArmDirectionOrigin
```

## 5. Runtime composition semantics

Confirmed: WeaponIK is evaluated on top of the already evaluated player/base
pose. IK-pose helper values are not absolute Blender world coordinates.

Retail primary target composition. Important: `chainoffset` below is the
runtime-cached transform, not the raw transform stored in the ANM:

```text
primaryTargetP = currentEnd.P + rotate(currentEnd.Q, chainoffset.P)
primaryTargetQ = currentEnd.Q * chainoffset.Q
```

Confirmed from the current retail `DayZ_x64.exe`:

```text
rawChainOffset = decode ANM track RightHandOrigin
chainoffset = inverse(rawChainOffset)
primaryTarget = currentEnd * chainoffset
```

Evidence:

- `FUN_1400c8e60` decodes the configured primary chain-offset track with
  `FUN_1400c04c0`, then immediately calls `FUN_1400c5500` on that transform;
- `FUN_1400c5500` conjugates quaternion XYZ and replaces translation with the
  rotated negative translation, i.e. a rigid-transform inverse;
- `FUN_1400ca870` then rotates/adds the already inverted cached translation and
  multiplies its quaternion with the current primary chain end;
- raw dumps:
  `anm_reports/ghidra-raw-dayz-current-weaponik-cache-1400c8e60-20260711.txt`,
  `anm_reports/ghidra-raw-dayz-current-transform-inverse-1400c5500-20260711.txt`,
  and its disassembly companion.

Confirmed: primary helper points are rotated by the current primary end/target
basis and added to its current translation. The right-hand origin and
forearm-direction data must therefore be preserved in their graph-relative
spaces.

Confirmed high-level evaluation order:

```text
evaluate full-body/base pose
load/cache IK-pose offsets and direction points
solve primary/right chain
compose weapon basis/offset
solve secondary/left chain when configured
write solved real chain transforms back to the pose
```

## 6. Runtime solver facts

Confirmed from DayZDiag `FUN_1400dec30 case 0x0c` and
`FUN_1400e1be0`:

- the configured player chain has five real records, not two anatomical bones;
- records correspond to root, roll/intermediate, elbow/middle,
  roll/intermediate and final hand;
- `RightArmRoll` and `RightForeArmRoll` are real runtime chain records;
- segment lengths use the anatomical root/middle/end points;
- optional middle-direction triples define the pole/reference plane;
- configured `chainaxis` selects the local solve axis;
- solver blend weight controls quaternion/translation blending;
- reach is clamped to `0.98 * (a + b)` and not the full segment sum;
- final twist is projected onto the middle-to-end segment and applied to the
  fourth record with a `0.5` DayZ slerp;
- quaternion slerp/lerp threshold is approximately `0.999`;
- the runtime writes solved real chain transforms back to the pose buffer.

Important distinction: these are DayZ runtime facts. They do not mean a
standard Blender five-bone IK constraint reproduces DayZ.

## 7. Blender 4.5 hybrid preview

Implementation, verified in the current addon:

```text
MCH_RightArm_IK:
    RightArm.head -> RightForeArm.head
MCH_RightForeArm_IK:
    RightForeArm.head -> RightHand.head
MCH_RightHand_IK:
    wrist orientation
```

- Blender IK runs only on the two anatomical proxy segments.
- `chain_count = 2`.
- stretch is disabled.
- `CTRL_RightHand` is the effector and wrist-rotation control.
- `CTRL_RightElbow` is the pole/bend-plane control.
- rotating `CTRL_RightHand` does not move the wrist.
- moving `CTRL_RightElbow` does not move the wrist target.
- Python aligns the original DayZ anatomical joint vectors to the solved proxy.
- DayZ roll bones remain in their native hierarchy and are not Blender IK
  joints.
- helper/export controls are separate from animator controls.
- proxy constraints and proxy bones are never exported.

This preview is an authoring approximation designed for speed and stable
interaction. It is not claimed to be an exact port of DayZ's five-record
solver. Exact ANM output comes from the original DayZ IK tracks after Bake,
not from exporting proxy bones as body animation.

## 8. Finger authoring

Confirmed current rule:

- edit original DayZ finger bones directly;
- preserve their local `Limit Rotation` constraints;
- Quick Finger Collision operates on those original bones;
- no `IK_RightHand*` or `IK_LeftHand*` finger proxy controls are created;
- no `DAT_IK_AUTHOR_*` Copy Rotation constraints remain on finger bones;
- right finger tracks are sampled directly during IK1H export.

Reason: the old finger proxy constraints executed after the original
`Limit Rotation` constraints and could overwrite the limited result.

## 9. Base and IK import

Correct clean workflow:

1. Select `_DayZ_Character`.
2. Import the full-body/base ANM with:
   - Translation off;
   - Rotation on;
   - Scale off;
   - full frame range unless a deliberately reduced diagnostic pose is needed.
3. Keep that base action active immediately before importing IK.
4. Import the IK ANM with:
   - Translation on;
   - Rotation on;
   - Scale off;
   - first two frames only for IK primary-pose authoring.
5. The importer stores the previous base action as
   `dayz_weaponik_base_action` when the new action contains the IK signature.

Blender 4.4/4.5 action slots are bound explicitly after import. Missing source
tracks are not evidence that their runtime role does not exist; retail IK files
have valid optional helper variants.

The preset `DayZ IK Primary Pose (.anm)` now imports Translation and Rotation,
disables Scale and keeps frames 0–1.

## 10. Building and editing controls

After base and IK import:

1. Enter Pose Mode.
2. Run `Build DayZ 1H IK Controls`.
3. Move/rotate `CTRL_RightHand`.
4. Move `CTRL_RightElbow` to change the elbow plane.
5. Edit original right finger bones directly.

The current rig also contains hidden export-helper controls for:

```text
RightHandOrigin
RightForeArmDirection
RightForeArmDirectionOrigin
RightHand_Dummy
```

`IK_RightHandDummy.R` preserves the dummy/object-offset relation to
`CTRL_RightHand`.

## 11. Bake contract

`Bake DayZ 1H Controls To Helpers` must satisfy all of these invariants:

- commit the currently visible, even unkeyed, Location/Rotation of
  `CTRL_RightHand`, `CTRL_RightElbow`, and `IK_RightHandDummy.R` before any
  frame change;
- IK1 authoring is a static pose: duplicate the current visible controls and
  direct right-finger pose onto both service frames 0 and 1. Never leave frame
  1 carrying the imported source item's dummy/hand pose after editing frame 0;
- sample frames 0 and 1;
- write Location and Rotation keys at frames 0 and 1 for:
  - `RightHandOrigin`;
  - `RightForeArmDirection`;
  - `RightForeArmDirectionOrigin`;
  - `RightHand_Dummy`;
- leave finger channels under the original finger bones and automatically
  commit the currently visible, even unkeyed, right-finger pose at the current
  frame before Bake changes frames;
- perform final proxy-to-DayZ synchronization after returning to the original
  frame;
- keep the visible arm in the edited pose;
- disable raw-ANM preservation after editing;
- support Blender Undo.

Dope Sheet detail: helper keys live on `_DayZ_Character`'s IK action. If the
control rig is active, the Dope Sheet instead shows the control action. Make
`_DayZ_Character` active to inspect baked helper keys.

Confirmed boundary: Bake automatically protects unkeyed edits on
`CTRL_RightHand`, `CTRL_RightElbow`, `IK_RightHandDummy.R`, and direct
right-finger bone edits. It must not
restore `IK_RightHandDummy.R` from the imported helper matrix while sampling,
because that would erase the animator's weapon/object rotation. Automatic
right-finger pose is keyed on the original DayZ action, not on the proxy rig.

## 12. Export contract

Use:

```text
Animation Type: Survivor IK 1h / IK1H
Translation Keys: on
Rotation Keys: on
Scale Keys: off
Preserve Imported Raw ANM: off after editing
```

Confirmed/current behavior:

- output contains only the canonical right IK1H whitelist;
- every exported track receives a position channel;
- identity rotation may remain omitted;
- output uses at most two frames;
- imported source format, FPS and track flags are retained when metadata is
  available;
- without source format metadata, IK defaults to `ANIMSET6`;
- preview/proxy/FK constraints are disabled or isolated while sampling;
- left tracks and mechanism bones are excluded;
- binary ANM raw passthrough is disabled in the exporter; every export is
  sampled from the current Blender action/pose. The legacy operator property
  remains hidden only for script/preset compatibility and is ignored.

## 13. Clean template

Prepared reusable file:

`P:\Animation_Weapon\saved\Weapon_template_dayz_IK1H_ready_clean.blend`

Verified contents at creation:

- zero Actions;
- no NLA/animation data on `_DayZ_Character`;
- no generated IK control rig or DAT authoring constraints;
- all pose `matrix_basis` values are identity;
- meshes, original skeleton and EntityPosition remain;
- 15 right-finger `Limit Rotation` constraints remain;
- `_DayZ_Character` is selected for import.

## 14. Numeric verification

Current Blender 4.5 regression test:

`C:\Users\sysro\diag\CsharpModVScode\tools\test_dayz_ik1h_proxy_workflow.py`

Current `apple` result:

```text
pass                         = true
initial/default pose error   = 3.4242211e-05 m
hand target error            = 6.0068501e-08 m
elbow edit wrist drift       = 1.4901161e-08 m
unkeyed Bake control reset   = 0
unkeyed Bake DayZ reset      = 0
helper two-frame T/R keys     = true
exported tracks              = 22
position tracks              = 22
missing position tracks      = 0
round-trip max error         = 2.0916648e-05
```

The six-case suite (`9v_battery`, `apple`, `banana`, `bark_oak`, `book`,
`candle`) previously passed control movement, elbow isolation, fixed lengths,
wrist rotation, Bake, filtering and numeric re-export. Re-run the complete
suite after any change to transform math, filtering or Bake.

## 15. Live visual evidence

Relevant screenshots:

- `anm_reports/screenshots/ik1h-apple-controls-clean-20260711.png`
- `anm_reports/screenshots/ik1h-apple-controls-edited-20260711.png`
- `anm_reports/screenshots/toy-ik-helpers-baked-keys-20260711.png`
- `anm_reports/screenshots/ik1h-ready-clean-file-20260711.png`

Screenshots are supporting evidence only. Numeric/corpus/Ghidra evidence takes
priority when a visual interpretation conflicts with decoded data.

## 16. Current code identity

At this verification point, source and installed Blender 4.5 copies match:

```text
AddSurvivorIK.py
DF1AE39F1E7F620C2FBBAA5C2B4D58E74240556920CCFE3115E18B6CF9957467

ImportAnm.py
EA3D445E4ED369303961829EB62E1AD205F1CA71AEE46E0F7743E2460356BE96

ExportAnm.py
B37EC86CBD8BD9B4656FE1B4C975F640D6DAC0F3F5F6AA5586595F0A89063B0A
```

These hashes are audit evidence, not permanent constants. Update them after a
verified code change.

## 17. Known unknowns and non-claims

Do not silently promote these to facts:

- exact semantic purpose of ANM track flag low bit `0x01`;
- exact visual parity of the Blender proxy preview with every DayZ runtime
  five-record solve;
- complete IK2H/secondary-chain Blender authoring parity;
- whether every optional helper variant should be preserved as a minimal
  source track set instead of emitting the canonical right-hand superset;
- visual correctness for all 654 retail files.

The Ghidra solver model is substantially recovered, but the current Blender
interactive preview remains a hybrid approximation. Export correctness and
preview parity are separate claims and must be tested separately.

## 18. Change-control checklist

Before modifying IK1H code:

1. State which canonical rule is changing.
2. Cite corpus/Ghidra/test/live evidence.
3. Update this file in the same change.
4. Update or add a regression assertion.
5. Run `py_compile` on source and installed copies.
6. Run the `apple` full round-trip test at minimum.
7. For transform/filter/Bake changes, run all six regression files.
8. Verify source and installed addon hashes match.
9. When visual state matters, inspect the live scene through
   `blender-remote` and save a screenshot.

## 19. Toy lifted-hand round-trip regression (2026-07-11)

Reproducible live-Blender test:
`tools/test_toy_ik_lift_bake_roundtrip.py`.

Confirmed passing invariants:

- moving `CTRL_RightHand` by `+0.06 m` on world Z moves the visible DayZ hand
  by the same amount;
- `Bake DayZ 1H Controls To Helpers` does not move the visible pose during the
  Bake (`0.0 m`, `0.0 rad` measured error in the latest run);
- the exported IK1H contains the canonical 22 tracks and every emitted track
  has a position channel;
- all four required helper/dummy tracks have translation and rotation keys on
  frames 0 and 1.

Confirmed full round-trip result from the final live-Blender run:

- test result: `PASS`;
- Bake pose error: `0.0 m`, `0.0 rad`;
- rebuilt visible hand/finger maximum: `1.1143e-5 m`, `0.0 rad`;
- rebuilt `CTRL_RightHand` error: `1.2857e-6 m`;
- rebuilt visible `RightHand` error: `1.1858e-6 m`;
- raw `RightHand` cycle error: `1.0700e-6 m`, `0.0 rad`;
- decoded export -> reimport -> Bake -> export cycle maximum error:
  `1.8387e-5`, with no missing or extra tracks;
- all 22 canonical tracks are present and all 22 have position channels.

Implementation rule confirmed by this regression:

- decode `RightHandOrigin` from the raw engine-space keys retained on import;
- use the same importer-evaluated `RightHand` graph-parent matrix when encoding
  and exporting the helper;
- do not judge helper correctness by parented Blender world matrices after
  rebuild; judge visible anatomy/control targets and decoded ANM channels;
- preserve unchanged structural origin/dummy tracks from decoded source data;
- preserve `RightForeArmDirection` when the elbow control was not edited, but
  resample it when the elbow was edited.

Runtime-target regression rule (added after the `toy_ik2` in-game backward-arm
failure):

- import/reimport symmetry is insufficient proof because an inverse or doubled
  Blender helper basis can round-trip through the same incorrect conversion;
- assert the exported engine-space `RightHandOrigin` against
  `inverse(F * currentEnd^-1 * desiredTarget * F^-1)`. The outer inverse is
  mandatory because the DayZ cache loader inverts the raw ANM track before
  target composition;
- `IK_RightHandOrigin.R` must be an unparented world-space export control. If it
  is parented to `CTRL_RightHand`, Blender 4.5 re-evaluation preserves its keyed
  local quaternion but changes its world quaternion; the observed `toy_ik2`
  error was about `0.539 rad`, producing a backward primary target in game;
- the earlier direct-transform check was superseded by in-game evidence and
  current-retail Ghidra evidence; it tested the wrong, non-inverted raw value;
- after implementing the cache-loader inverse, the user's exact pose measured
  `4.65e-6` maximum position-component error and `0.0 rad` quaternion error
  against the corrected runtime formula.

Final in-game validation:

- the repacked corrected `P:\UARP_Items_2\Anm\toy_ik2.anm` was loaded by DayZ;
- the user confirmed that the hand now moves forward and the game pose matches
  the Blender-authored pose;
- this confirms the raw-ANM inverse rule above with actual retail runtime
  behavior, not only Blender round-trip or offline math;
- a slightly extended shoulder remains visible at this authored reach, but the
  previous backward-hand/sign failure is resolved. Treat shoulder/reach tuning
  separately from `RightHandOrigin` encoding.

Frame-scrub invariant confirmed in the live authoring file:

- proxy control synchronization must run from both `depsgraph_update_post`
  (interactive control movement) and `frame_change_post` (timeline scrubbing);
- Blender re-evaluates the armature action during a frame change, so relying on
  depsgraph updates alone restores the source hand pose even though the control
  keys and baked helper keys are still present;
- with both handlers registered, the sequence `frame 0 -> frame 1 -> frame 0`
  restores the exact keyed control pose on each frame.

Machine-readable evidence:
`Research/anm_reports/toy-ik-lift-bake-roundtrip-20260711.json`.

Fresh `box_cereal.anm` import and Build invariant (2026-07-11):

- the freshly decoded `RightHandOrigin` and `RightForeArmDirectionOrigin`
  matrices have identical rotation (`0.0 deg` difference); their positional
  vector is nearly along the origin Y axis (`6.4858 deg`, the remaining angle
  is encoded by the ANM translation itself);
- `IK_RightForeArmDirectionOrigin.R` must be unparented in the Blender control
  rig. Parenting it to `CTRL_RightHand` applies the hand transform a second
  time during Build, producing the reproduced bad result: `38.6458 deg`
  rotation difference and `60.2927 deg` axis/vector difference;
- Build must cache `RightHandOrigin`, `RightForeArmDirectionOrigin`, and
  `RightForeArmDirection` object-space matrices before it creates authoring
  constraints, then seed the export controls from those cached matrices;
- verified live after the fix: before/after Build distance
  `0.16539953 / 0.16539951`, axis/vector angle
  `6.4857645 / 6.4857645 deg`, and origin rotation difference `0.0 / 0.0 deg`.

Clean IK-primary import must include runtime solve preview (2026-07-11):

- a raw helper-track import alone is not the final DayZ-visible pose: with
  `p_1hd_erc_idle_low` as the base and a freshly decoded `box_cereal.anm`, the
  unsolved anatomical `RightHand` remained `38.645777 deg` away from the
  correctly decoded primary target/origins;
- this is expected from the runtime order established above: decode the ANM
  offsets on the base pose, then solve the primary chain onto that target;
- therefore the dedicated `DayZ IK Primary Pose (.anm)` / first-two-frames
  import now automatically calls the same IK1 control/proxy build stage after
  successful decoding. The ordinary `DayZ Binary Animation (.anm)` importer
  remains a plain importer;
- verified from a completely cleared live armature by importing
  `p_1hd_erc_idle_low.anm` without translation and then `box_cereal.anm` with
  translation + first two frames: `RightHand` versus `RightHandOrigin` rotation
  difference `0.0 deg`, axis/vector angle `0.0 deg`; `RightHandOrigin` versus
  `RightForeArmDirectionOrigin` rotation difference `0.0 deg` and encoded
  axis/vector angle `6.486006 deg`;
- visual OpenGL viewport evidence (bone names and custom shapes disabled):
  `Research/screenshots/box_cereal_clean_import_aligned_opengl_20260711.png`.
