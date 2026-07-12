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
including five-bone Blender IK attempts and separate finger controls. When
those notes conflict with this file, this file wins.

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

Confirmed corpus inventory: every track present in the decoded retail IK corpus
has at least one position key. This inventory fact does not define the current
custom IK1H Bake/export transition policy below.

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

Current IK1H Bake/export rule after retail validation:

- all 22 canonical IK1H tracks retain a translation/position channel;
- all 22 canonical tracks retain a rotation channel, including identity
  `RightHandRing` and `RightHandPinky`;
- the attempted five-translation-track rule was rejected after retail DayZ
  twisted the fingers into an invalid pose. Do not reintroduce it.
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

Superseded historical live export evidence:

- `toy_ik`: 22 exported tracks;
- 22/22 tracks had position channels under the superseded exporter;
- `RightHand` has a position key;
- no missing position tracks.

Evidence retained for history only:
`anm_reports/toy-ik-live-position-verify-20260711.json`.

Rejected experiment evidence:
`anm_reports/ik1h-five-translation-tracks-20260711.json`.

Current restored evidence:
`anm_reports/ik1h-transitions-restored-20260711.json`.

### 2.2 Rotation limits during export

Confirmed from the live `RightHandThumb1` failure and corrected binary export:

- `LIMIT_ROTATION` constraints are part of the authored visible pose and must
  never be disabled while ANM tracks are sampled;
- viewport IK/FK/ref-bake constraints may be disabled for clean sampling, but
  every already-enabled, unmuted `LIMIT_ROTATION` with nonzero influence stays
  evaluated;
- the former exporter disabled `RightHandThumb1.Limit Rotation`, so DayZ
  received the raw quaternion while Blender displayed the constrained result;
- the measured constraint contribution on `RightHandThumb1` is
  `54.0773 degrees`, which appears approximately as a 90-degree axis flip in
  the retail character pose because of the thumb's local rest basis;
- with the fix, the exported Thumb1 quaternion changes by `54.0784 degrees`,
  the constraint remains enabled after export, and channel inventory remains
  exactly five translation tracks plus 22 rotation tracks.

Evidence:
`anm_reports/ik1h-rotation-limits-export-20260711.json`.

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
- Retail visual validation on the current DayZ skeleton/template established
  `35 deg` as the Blender proxy IK pole-angle calibration. The former automatic
  fit selected `91.9 deg`: it reproduced the already imported Blender elbow,
  but did not match the elbow plane observed in retail DayZ. Build therefore
  uses `35 deg` by default. A skeleton-specific override can be stored as the
  Scene custom property `dayz_proxy_pole_angle_degrees`.
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

### 10.1 Clean IK1 Authoring without an imported item ANM

Confirmed live in Blender 4.5:

- `Clean IK1 Authoring` uses `p_1hd_erc_idle_low.001` as the only unmuted
  internal NLA base reference;
- it creates `DAT_Clean_IK1H`, a two-frame `AnimSet6` action containing the
  canonical 22 right-hand IK1H tracks;
- raw `RightHandOrigin` starts as identity, therefore the Ghidra-confirmed
  composition `currentEnd * inverse(rawChainOffset)` starts at `currentEnd`;
- the mode immediately enables proxy synchronization and sets both armature
  and control rig authoring mode to `IK`;
- `CTRL_RightHand`, `CTRL_RightElbow`, and `IK_RightHandDummy.R` are visible;
- clean Build no-jump maximum was `1.59002e-5 m`, with `0 deg` rotation error;
- an edited Bake preserved visible `RightHand` and `RightHand_Dummy` exactly;
- before ANM quantization, exported `RightHandOrigin` reconstructed the desired
  primary target within `1.50679e-7 m / 0 deg` using the retail Ghidra formula;
- before quantization, `primaryTarget * cachedDummy` reconstructed the Blender
  dummy within `2.10734e-8 m / 0 deg`.

Machine-readable evidence:
`anm_reports/clean-ik1-authoring-live-20260711.json`.

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
- the exported IK1H contains the canonical 22 tracks;
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
- all 22 canonical tracks are present with position channels. This rule was
  restored after the five-transition experiment failed in retail DayZ.

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

## 20. Rejected runtime-preview/finger experiment (2026-07-11)

**REJECTED BY RETAIL DAYZ. Do not reintroduce these changes.**

The experiment below was internally consistent in Blender and through decoded
ANM comparisons, but the user loaded the resulting `cable2.anm` in retail
DayZ. The hand/fingers collapsed and the elbow plane became much worse. Retail
output supersedes the offline inference.

Rejected changes:

- exporting IK finger tracks directly from Blender `matrix_basis`/`location`;
- replacing the interactive Blender proxy pole with the locally reconstructed
  Ghidra helper-plane result;
- applying the runtime `0.98` reach limit directly inside the Blender authoring
  proxy;
- forcing the full experimental solver from the live handler;
- removing the existing post-solve roll-record stabilization.

All five changes were rolled back in both source and installed Blender 4.5
copies. The live pose returned to the pre-experiment proxy with measured elbow
and wrist errors below `8e-7 m` against its controls.

The failed Bake also exposed a separate confirmed clean-workflow bug:
`DAT_Clean_IK1H` had no `dayz_binary_anm_track_keys_json`, so the exporter could
not actually preserve `RightForeArmDirectionOrigin` despite its preservation
branch. The structural track was restored from the last pre-experiment artifact
`current_clean_pose_reexport.anm`. The rollback export matches that artifact to
`1.45727e-5` maximum decoded component error; the structural-origin error is
`4.16597e-6`, with the catastrophic `~6.9e-3` change removed.

The remaining text in this section documents the disproven hypothesis for
change-control history only; it is not canonical implementation guidance.

Confirmed from the user's live `DAT_Clean_IK1H` pose, the two supplied retail
screenshots, current-retail `DayZ_x64.exe` Ghidra output, and the saved
DayZDiag `FUN_1400e1be0` evidence:

- Blender's former native two-bone proxy reached the complete limb length and
  therefore did not reproduce DayZ's `0.9800000190734863 * (a + b)` clamp;
- the interactive preview must derive its elbow plane from the runtime triple
  `RightForeArmDirection`, `RightHandOrigin`, and
  `RightForeArmDirectionOrigin`, rather than use the Blender pole location as
  the final solved plane directly;
- the old proxy and the corrected runtime preview differed by `0.0069632 m` at
  the wrist and `0.0695363 m` at the elbow in this near-full-reach pose;
- the full preview handler must not stop after a RightHand-only rotation
  correction because that omits the reach clamp, helper plane, two roll
  records, and final projected twist;
- post-solve stabilization must not overwrite record 3 rotation: Ghidra shows
  that record carries the projected final twist with DayZ slerp weight `0.5`;
- imported `RightHandOrigin` includes a Blender display-tail offset. Remove the
  tail before using it as the already inverted runtime primary target; the raw
  ANM transform itself is still inverted by retail `FUN_1400c8e60` through
  `FUN_1400c5500`.

Confirmed finger-channel rule:

- ordinary IK finger tracks are direct Blender pose deltas on import:
  `ImportAnm` writes their position to `pose_bone.location` and quaternion to
  `pose_bone.rotation_quaternion`;
- export must therefore sample finger `location` and `matrix_basis` rotation
  directly, then apply only the existing DayZ handedness sign in
  `gen_rot_key`;
- exporting `parent^-1 * child` for fingers includes the rest-bone transform
  and is not the inverse of the importer. This was the cause of the retail
  thumb pose differing from Blender;
- the corrected 17 right-finger tracks decode back to the authored Blender
  rotations up to quaternion sign/ANM quantization; maximum decoded location
  error is `6.63824e-7 m`;
- repeated Bake does not move controls (`0.0`) and changes the visible finger
  matrices only by `2.38419e-7`; two subsequent exports differ by only
  `2.23517e-8` in one decoded `RightForeArmDirectionOrigin` component.

This section proves code/math and Bake/export stability. Final visual parity of
this exact corrected artifact still requires loading it in retail DayZ; do not
replace that gate with a Blender round-trip claim.

Machine-readable evidence:
`Research/anm_reports/cable2-runtime-preview-finger-fix-20260711.json`.
