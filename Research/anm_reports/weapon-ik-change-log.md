# Weapon IK Change Log

## 2026-05-17

### Findings

- `confirmed`: `P:\DZ\anims\anm\player\ik\weapons\sv98.anm` is `ANIMSET6`,
  not `ANIMSET5`.
- `confirmed`: player weapon IK directory contains both SET5 and SET6 files.
  Focused scan counted:
  - SET5: `39`
  - SET6: `27`
- `confirmed`: full `P:\DZ\anims\anm\player\ik\` corpus contains 654 files,
  no parse failures:
  - SET5: `359`
  - SET6: `295`
  - `fps = 30` for all files
  - 652 files are 2-frame IK poses; `gear/gas_cooker.anm` and
    `gear/morphine.anm` are 1-frame.
- `confirmed`: the corpus has several valid helper-track profiles: full
  two-hand IK, right-hand-only IK, minimal hand dummy poses, and a five-file
  legacy spelling variant `RightForeHandDirection`.
- `confirmed`: DayZDiag ANM DATA decoding uses flags bits `0x10`, `0x20`, and
  `0x40` to omit explicit frame-index arrays for position, rotation, and SET6
  scale. The player IK corpus only has flags `0` and `1`, so corpus
  `flags = 1` does not change key timing.
- `confirmed`: `sv98.anm` contains the wider helper-track set needed by player
  `AnimNodeWeaponIK`, including `LeftHandIKTarget`,
  `RightForeArmDirectionOrigin`, and `LeftForeArmDirectionOrigin`.
- `confirmed`: DayZDiag `FUN_1400d4520` reads SET6 HEAD as variable-length
  records where `record[0x21]` is the bone-name length.
- `confirmed`: `DayzAnimationToolsBinary\Types\Anm.py` has the same SET6 record
  order as DayZDiag.

### Code Changes

- `P:\BlenderAnimtool\DayzAnimationTools\Types\Txa.py`
  - Added `LeftHandIKTarget` to `SURVIVOR_IK_ANIM_BONES_L`.
- `P:\BlenderAnimtool\DayzAnimationToolsBinary\Types\Anm.py`
  - Removed per-bone debug prints from `Anm.Read`.
- `P:\BlenderAnimtool\DayzAnimationTools\Tools\AddSurvivorIK.py`
  - Now builds missing `LeftHand_Dummy`, `RightHand_Dummy`, `LeftHandIK`, and
    `RightHandIK` for custom/minimal authoring skeletons.
  - Creates `RightHandOrigin` and forearm direction helper bones as unparented
    authoring helpers. Blender 4.2 showed dependency cycles when those pole
    helpers were parented under the controlled hand chains.
  - Names IK constraints `DayZ Left Hand IK` / `DayZ Right Hand IK` and reuses
    existing constraints when the operator is run again.
- `P:\BlenderAnimtool\DayzAnimationTools\Export\ExportTxa.py`
  - Validates required IK authoring bones before IK TXA export and reports the
    exact missing names.
- `P:\BlenderAnimtool\DayzAnimationTools\Import\ImportTxa.py`
  - No longer silently skips missing IK helper tracks except `Scene_Root`.
- `P:\BlenderAnimtool\DayzAnimationToolsBinary\Types\Anm.py`
  - Removed remaining ANM read/write debug prints from the source tree version.
  - Reads ANM record counts as unsigned 16-bit values to match DayZDiag SET5/6
    layout.
  - Accepts either an `AnmImportSettings` object or legacy numeric argument in
    `CreateFromFile`.
- `P:\BlenderAnimtool\DayzAnimationToolsBinary\Import\ImportAnm.py`
  - Uses the full graph-relative WeaponIK helper import set:
    `RightHandOrigin`, `RightForeArmDirectionOrigin`,
    `RightForeArmDirection`, `LeftHandOrigin`,
    `LeftForeArmDirectionOrigin`, `LeftForeArmDirection`.
  - Removed hardcoded fallback vectors for forearm direction tracks.
  - Maps legacy imported track `RightForeHandDirection` to canonical
    `RightForeArmDirection`. Export keeps the canonical name.
- Installed Blender 4.2 add-on copy was synced for:
  - `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationToolsBinary\Types\Anm.py`
  - `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\DayzAnimationToolsBinary\Import\ImportAnm.py`

### Documentation Changes

- Added `anm/player-weapon-ik-blender-workflow.md`.
- Updated `anm/dayzdiag-weapon-ik.md` with player graph evidence.
- Added `anm/weapon-ik-anmset6-reader-check.md`.
- Updated `anm/player-xob-ik-bones-ghidra-findings.md` with the split between
  runtime/export relative space and Blender-safe authoring parentage.
- Added `anm/player-weaponik-agr-runtime-map.md` with player AGR node timings
  and Ghidra property-table evidence for `AnimNodeWeaponIK`.
- Added `anm/player-ik-anm-corpus.md`, plus generated
  `anm/player-ik-anm-corpus.csv` and `anm/player-ik-anm-corpus.json`.
- Added `anm/dayzdiag-anm-track-flags.md`.
- Added this change log.
- Updated `anm/dayzdiag-animnode-weaponik-deep.md` with the confirmed
  `AnimNodeWeaponIK` command-stream consumer, solver helper roles, and axis-id
  mapping from DayZDiag Ghidra decompile.
- Added new raw Ghidra dumps under `anm/ghidra-raw/` for the command-stream
  buffer flow, candidate rejection pass, solver helpers, and axis helper
  functions.
- Added `anm/player-weapon-ik-blender-skeleton-status.md`.
- Added `anm/player-weapon-ik-helper-transform-stats.json` from 66 original
  player weapon IK `.anm` files.

### Validation

- `python -m py_compile` passed for the changed addon files.
- Blender 4.2.20 LTS background test created a minimal armature, ran
  `AddSurvivorIK.load()`, verified all required IK authoring bones, and no
  dependency cycle was reported after unparenting pole/helper bones.
- Blender 4.2.20 LTS read-test loaded
  `P:\DZ\anims\anm\player\ik\weapons\sv98.anm` as `AnimSet6`, `fps = 30`,
  `numFrames = 2`, `43` bones, with all nine player WeaponIK special tracks
  present.
- `python -m py_compile` passed after the `RightForeHandDirection` import alias
  change in both source and installed Blender 4.2 add-on copies.
- Ghidra HTTP confirmed the runtime path:
  `FUN_140108750 -> FUN_1400da470` emits opcode `0x0c`,
  `FUN_1400dec30 case 0x0c` consumes it, and
  `FUN_1400e1be0` performs the chain IK solve before `FUN_14005f5a0` writes
  solved transforms back.
- `python -m py_compile` passed for the source and installed Blender 4.2 add-on
  copies of `AddSurvivorIK.py`, `ExportTxa.py`, and `ExportAnm.py`.

### Open Work

- Decide whether the main Blender 4.2+ workflow should import `.anm` directly or
  convert `.anm` to `.txa` first and reuse the main TXA importer.
- Confirm in Blender viewport that the unparented helper-bone workflow is
  ergonomic for posing, not only valid in background dependency-graph tests.
- Build a Blender 4.2+ viewport preview that mirrors DayZDiag
  `AnimNodeWeaponIK`: use helper target tracks as authoring controls, map
  `chainaxis/secchainaxis/weaponaxis` through the confirmed `0..5` local-axis
  table, and solve the real arm chains without dependency cycles.

### 2026-05-17 Follow-up Fix

- `P:\BlenderAnimtool\DayzAnimationTools\Tools\AddSurvivorIK.py`
  - `ensure_edit_bone` now clears existing parentage when `parent_name` is
    `None`, so rerunning the operator can fix old parented helper bones.
  - `LeftHandOrigin` and `LeftHandIKTarget` are now created unparented.
- `P:\BlenderAnimtool\DayzAnimationTools\Export\ExportTxa.py`
  - IK helper transform conversion now runs before the generic
    `bone.parent is None` branch. This keeps export correct for unparented
    helper controls.
- `P:\BlenderAnimtool\DayzAnimationToolsBinary\Export\ExportAnm.py`
  - Applied the same unparented-helper export fix for direct `.anm` export.
  - Removed old per-bone IK compression debug prints.
- Synced all three files into
  `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons`.

### 2026-05-17 DayZDiag Solver Model Pass

- Added `anm/dayzdiag-weaponik-solver-model.md`.
- Added raw Ghidra HTTP dumps:
  - `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-inputs-http.txt`
  - `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-constants-memory.txt`
- Confirmed from DayZDiag decompile that `FUN_1400e1a30` builds the three
  optional middle-direction helper points from pose tracks and initializes
  missing helpers with sentinel `0xff7fffff`.
- Confirmed primary `FUN_1400e1be0` call order:
  `chain array + 0x20`, `chainaxis`, target transform, three optional helper
  points, `max(command[4], command[5])`, debug buffer.
- Confirmed secondary `FUN_1400e1be0` call order:
  secondary chain array, `secchainaxis`, shared target transform, three
  optional helper points, `command[6]`, debug buffer.
- Documented the Blender rule that helper controls should be exportable pose
  tracks and not parented into solved arm chains if that creates dependency
  cycles.

### 2026-05-17 Blender WeaponIK Preview Implementation

- Added `anm/blender-weaponik-preview-implementation.md`.
- Updated `P:\BlenderAnimtool\DayzAnimationTools\Tools\AddSurvivorIK.py`.
  - Added `RefreshWeaponIKPreviewOperator`.
  - Added `Tools > Refresh DayZ Weapon IK Preview`.
  - Changed left-hand preview target from `LeftHandOrigin` to
    `LeftHandIKTarget`, matching the player AGR/DayZDiag secondary-chain
    mapping.
  - Preview constraints are now named `DayZ WeaponIK Preview` and use
    `chain_count = 5`, `use_rotation = true`, `use_stretch = false`.
- Updated `P:\BlenderAnimtool\DayzAnimationTools\Tools\__init__.py` to
  register the new preview-refresh operator.
- Added `P:\BlenderAnimtool\DayzAnimationTools\Utils\WeaponIKSolver.py`.
  - Contains a readable Python/mathutils port scaffold for `FUN_1400e1be0`:
    `IkXform`, DayZ axis mapping, `0.999` slerp threshold,
    helper-plane correction, and five-record chain solve.
- Synced the changed/additional files into the installed Blender 4.2 addon
  directory under `%APPDATA%`.
- Updated `P:\BlenderAnimtool\DayzAnimationToolsBinary\Export\ExportAnm.py`
  and installed copy to remove leftover per-bone IK debug prints.
- `python -m py_compile` passed for the changed source and installed copies.

### 2026-05-17 DayZDiag Formula Completion Pass

- Ghidra HTTP confirmed the deeper `FUN_1400e1be0` constants and formulas:
  - reach multiplier `DAT_140de84d0 = 0.9800000190734863`;
  - half-square scalar `DAT_140de84bc = 0.25`;
  - final twist blend `DAT_140de2ec8 = 0.5`;
  - slerp threshold `_DAT_140de9234 = 0.9990000128746033`.
- Added/used raw dumps under `anm/ghidra-raw/`:
  - `ghidra-raw-dayzdiag-weaponik-1400e1be0-disasm.txt`
  - `ghidra-raw-dayzdiag-weaponik-1400e1be0-formula-notes.txt`
  - `ghidra-raw-dayzdiag-weaponik-constants-targeted.txt`
  - `ghidra-raw-dayzdiag-weaponik-helper-140140750-decompile.txt`
- Updated `anm/dayzdiag-weaponik-solver-model.md` with the confirmed reach
  clamp, law-of-cosines block, DayZ slerp helper, and final `r3` twist
  projection formula.
- Updated `P:\BlenderAnimtool\DayzAnimationTools\Utils\WeaponIKSolver.py`:
  - replaced full segment-sum reach with DayZDiag `(a + b) * 0.98` clamp;
  - replaced approximate `r3 -> target` half-blend with the Ghidra-backed
    twist projection correction.
- Synced `WeaponIKSolver.py` into the installed Blender 4.2 addon copy.
- Validation:
  - `python -m py_compile` passed for source and installed solver copies;
  - Blender 4.2.20 LTS background import/solve smoke test passed and returned
    `WEAPONIK_SOLVER_IMPORT_TEST True`.

### 2026-05-17 DayZDiag WeaponIK Completion Pass

- Closed the remaining DayZDiag WeaponIK gaps with three focused agent passes:
  compact solver records, `case 0x0c` runtime/config layout, and Blender helper
  track wiring.
- Added raw Ghidra dump:
  - `anm/ghidra-raw/ghidra-raw-dayzdiag-weaponik-helper-1400e1a30-disasm.txt`
- Updated `anm/dayzdiag-weaponik-solver-model.md`:
  - confirmed `r0..r4` solver record roles;
  - confirmed `r1` and `r3` are real configured chain bones;
  - documented compact record metadata bytes `+0x1c..+0x1f`;
  - added `AnimNodeWeaponIK` config offset table;
  - added `case 0x0c` runtime `lVar8` offset table;
  - corrected `FUN_1400e1a30`: `*middlediro` pairs build
    `originTranslation + originRotation * directionTranslation`.
- Updated `anm/player-weaponik-agr-runtime-map.md`:
  - promoted `ikpose_*` interpretation from likely to confirmed for the
    DayZDiag path;
  - documented `outputweaponoffsettobuffer` as node `+0x218` / runtime
    `lVar8 + 0x118`;
  - clarified Blender export rules for `RightHand_Dummy`, `LeftHandIKTarget`,
    and forearm direction pairs.

### 2026-05-17 Loaded Blender Skeleton Check

- Connected to the open Blender 4.2 scene through `tools/blender_codex_bridge.py`
  and dumped live scene data to `anm/blender-live-skeleton-dump.json`.
- Current loaded file: `P:\Animation_Weapon\Weapon_template.blend`.
- Current armature: `_DayZ_Character`, `162` bones.
- Confirmed scene issues before fix:
  - missing `LeftHandIKTarget`;
  - `LeftHand` IK constraint targeted `LeftHandOrigin`, but player
    DayZDiag/AGR maps secondary chain target to `LeftHandIKTarget`;
  - `RightHand` IK target already used `RightHandOrigin`;
  - `RightHand_Dummy` existed under `RightHand`, which matches player weapon
    bone usage.
- Added `tools/fix_loaded_weaponik_scene.py` for the open Blender scene. It:
  - creates `LeftHandIKTarget` from `LeftHandOrigin`/`LeftHand`;
  - unparents helper controls that should not live inside solved arm chains;
  - rebuilds right/left hand IK preview constraints using the DayZDiag mapping.
- Synced the current `AddSurvivorIK.py` into the installed Blender 4.2 addon
  copy. Source and installed copies passed `py_compile`.
- After relaunching the bridge, ran `tools/fix_loaded_weaponik_scene.py` inside
  the live Blender scene through the bridge `exec` command.
- Verified live scene after fix:
  - all required player WeaponIK bones/tracks are present;
  - `RightHandOrigin`, `RightForeArmDirection`,
    `RightForeArmDirectionOrigin`, `LeftHandOrigin`, `LeftHandIKTarget`,
    `LeftForeArmDirection`, and `LeftForeArmDirectionOrigin` are unparented
    Blender helper controls;
  - `RightHand` has `DayZ WeaponIK Preview` targeting `RightHandOrigin` with
    pole `RightForeArmDirection`;
  - `LeftHand` has `DayZ WeaponIK Preview` targeting `LeftHandIKTarget` with
    pole `LeftForeArmDirection`;
  - `RightHand_Dummy` remains parented to `RightHand`, and `LeftHand_Dummy`
    remains parented to `LeftHand`.

### 2026-05-17 AKS74U Import Repair

- Found the cause of the weird AK pose in Blender after importing the full-body
  hold animation plus `aks74u` weapon IK:
  - `aks74u.anm` contains `LeftHandIKTarget`;
  - `DayzAnimationToolsBinary.Import.ImportAnm` did not include
    `LeftHandIKTarget` in the special IK import order;
  - `DayzAnimationTools.Import.ImportTxa` listed the bone as a survivor IK
    name, but did not route it through the same weapon-space transform handling
    as `LeftHandOrigin`.
- Patched source addon files:
  - `P:\BlenderAnimtool\DayzAnimationToolsBinary\Import\ImportAnm.py`
  - `P:\BlenderAnimtool\DayzAnimationTools\Import\ImportTxa.py`
- Synced patched files to Blender 4.2 installed addon copies under
  `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons`.
- Import behavior change:
  - `LeftHandIKTarget` is now imported through the same `RightHand_Dummy`
    weapon-space path as `LeftHandOrigin`;
  - active full-body action pushdown creates an enabled NLA strip with
    `influence = 1.0`.
- Repaired the live Blender file `P:\Animation_Weapon\Weapon_template.blend`
  through `tools\blender_codex_bridge.py`:
  - restored helper hierarchy needed by imported IK tracks;
  - removed the old bad `aks74u` action;
  - reimported `P:\DZ\anims\anm\player\ik\weapons\aks74u.anm`;
  - wrote diagnostics to `anm/blender-ak-import-diagnostic-repaired.json`.
- Validation after repair:
  - full-body `p_rfl_erc_idle_ras` NLA strip is enabled with influence `1.0`;
  - `LeftHandIKTarget` no longer drops near the ground on frames 1/10/30 and
    stays near the weapon/left-hand target area.

### 2026-05-17 Left Hand Preview Offset Check

- Live Blender diagnostics showed `LeftHand` IK was solving, but with Blender
  IK `use_tail = True` the tail of the `LeftHand` bone was placed exactly on
  `LeftHandIKTarget`; the visible wrist/head stayed about one hand-bone length
  away.
- Switched the left-hand preview constraint to `use_tail = False` so Blender
  preview targets the wrist/head side of `LeftHand`.
- This is a Blender preview/rigging decision only. It does not change the ANM
  or TXA data tracks; export should still write the actual helper tracks.

### 2026-05-17 Live WeaponIK Artist Controls

- Added `tools/add_live_weaponik_controls.py` and ran it in the open Blender
  scene through the bridge.
- The script creates/selects four visible controls in collection
  `DayZ WeaponIK Controls`:
  - `WIK_L_Hand_Target` drives `LeftHandIKTarget`;
  - `WIK_L_Elbow_Pole` drives `LeftForeArmDirection`;
  - `WIK_R_Hand_Target` drives `RightHandOrigin`;
  - `WIK_R_Elbow_Pole` drives `RightForeArmDirection`.
- `WIK_L_Hand_Target` is parented to armature bone `Weapon_Magazine`, so it
  follows the weapon and can be moved locally to tune the left-hand grip.
- Pole controls are world-space controls to avoid dependency cycles and to give
  direct visual elbow direction control.
- Current limitation: Blender IK preview is still an approximation of the
  DayZDiag custom `AnimNodeWeaponIK` solver. Elbow pose can be tuned with pole
  controls, but exact runtime parity needs a dedicated custom preview solver.

### 2026-05-17 WeaponIK Template Rig Rebuild

- Rebuilt the live Blender controls after the first control pass created an IK
  dependency cycle by parenting a control to `Weapon_Magazine`.
- Added and ran `tools/rebuild_weaponik_template_rig.py`.
- The rebuilt template has two explicit modes:
  - `Imported Playback`: default; imported ANM/TXA helper tracks drive the
    preview, and `WIK_*` controls are visible reference handles only.
  - `Manual Authoring`: unmute `DayZ WIK Control*` constraints so `WIK_*`
    controls drive the helper bones.
- All `WIK_*` controls are world-space on purpose. They are not parented to
  `Weapon_Root`, `Weapon_Magazine`, or hand bones because those bones are part
  of the IK dependency graph.
- Added `tools/set_weaponik_authoring_mode.py` to switch the constraints
  between `Imported Playback` and `Manual Authoring`.

### 2026-05-17 Blender Preview Shoulder Fix

- User reported the left shoulder/upper arm was being pulled into the face.
- Diagnosed the Blender parent chain:
  `LeftHand -> LeftForeArmRoll -> LeftForeArm -> LeftArmRoll -> LeftArm -> LeftShoulder`.
- `chain_count = 5` is too broad for Blender preview on this rig because it
  lets the solver rotate the upper-arm/roll chain too aggressively.
- Added and ran `tools/rebuild_weaponik_anatomical_preview.py`.
- Current preview settings:
  - `LeftHand` IK target: `LeftHandIKTarget`;
  - `LeftHand` pole target: world-space `WIK_L_Elbow_Pole`;
  - `LeftHand` chain count: `3`;
  - `LeftHand` uses `use_tail = False`;
  - right hand uses the same shorter preview chain count `3`.
- This is only for Blender viewport preview. The export/helper tracks still
  remain the DayZ/Workbench-style bones.

### 2026-05-17 Left Hand Grip Snap

- User reported that after the shoulder fix the left hand still did not touch
  the weapon and the forearm shape was not satisfactory.
- Added and ran `tools/snap_left_hand_to_weapon_grip.py`:
  - finds the nearest visible weapon mesh point to the left hand;
  - moves `WIK_L_Hand_Target` there;
  - un-mutes `LeftHandIKTarget` manual control constraints;
  - switches the armature to `Manual Authoring`.
- Added and ran `tools/solve_left_hand_to_grip_point.py`:
  - compensates Blender IK solver offset so the visible `LeftHand` head reaches
    the selected weapon surface point;
  - final measured error was approximately `0.000005 m`.
- Current state is an authoring preview state. The target empty may be offset
  from the weapon point because it compensates Blender IK behavior; the visible
  hand is what is solved onto the weapon.

### 2026-05-17 Constraint Audit And Clean Reset

- User reported the left hand reached the weapon but the forearm remained bent
  incorrectly.
- Full live-scene constraint audit was written to
  `anm/blender-full-constraint-audit.json`.
- The bad state was caused by mixed preview modes:
  - active `aks74u` helper/finger action;
  - full-body `p_rfl_erc_idle_ras` in NLA;
  - active Blender IK constraints on `LeftHand`/`RightHand`;
  - active/manual `DayZ WIK Control*` constraints on helper tracks;
  - leftover pose-basis overrides from earlier solver experiments.
- Confirmed `aks74u` action groups do not key the real arm chain bones
  directly; it keys fingers plus helper/weapon IK tracks. Action group dump:
  `anm/aks74u-action-groups-current.json`.
- Added and ran `tools/reset_weaponik_template_to_clean_imported.py`:
  - removed experimental `WIK_*` controls;
  - removed `DayZ WeaponIK Preview` and `DayZ WIK Control*` constraints;
  - reimported `aks74u.anm`.
- Added and ran `tools/reset_pose_basis_after_weaponik_experiments.py`:
  - reset all pose-bone basis overrides;
  - re-evaluated animation at the current frame.
- Added `anm/blender-weaponik-template-rig-rules.md` to document the correct
  template architecture from DayZDiag evidence.

### 2026-05-17 Clean Reimport And Helper Snapshot Fix

- User noted that several helper bones were far from the body.
- Confirmed two separate cases:
  - expected: `ikpose_*` tracks are helper pose data and can be away from the
    model rest skeleton;
  - broken: previous Blender experiments left pose-basis overrides and mixed
    constraints, causing genuinely bad helper positions.
- Added and ran `tools/reimport_weaponik_helpers_from_clean_base_pose.py`.
  Result: `anm/blender-reimport-weaponik-clean-base.json`.
- Clean frame 30 helper positions are now near the body/weapon area:
  - `LeftHandIKTarget ~= (0.1475, 0.4907, 1.3439)`;
  - `RightHandOrigin ~= (0.2143, 0.1100, 1.3541)`.
- Fixed `tools/apply_dayz_weaponik_preview_current_frame.py`:
  - resets pose basis before solve;
  - reads pose-bone `head` for compact-record translation instead of raw
    `matrix.translation`;
  - snapshots helper tracks before primary/right chain solve so parented
    `LeftHandIKTarget` is not read after `RightHand_Dummy` changes.
- Remaining gap: the Python DayZ solver reads the correct helper snapshot, but
  applying solved compact records back to Blender pose bones still needs a
  correct compact-record-to-Blender-local adapter.

### 2026-05-17 Helper-Only Debug Action

- User reported the hands still looked like spaghetti.
- Restored the live scene to a stable full-body-only state with
  `tools/restore_clean_fullbody_no_weaponik_preview.py`.
- Added and ran `tools/create_weaponik_helper_only_action.py`.
- Created active action `aks74u_helpers_only` from `aks74u`, copying only
  helper/weapon IK tracks and excluding all finger tracks.
- Current live state:
  - full-body `p_rfl_erc_idle_ras` is enabled in NLA;
  - active action is `aks74u_helpers_only`;
  - no Blender IK preview constraints;
  - no manual `DayZ WIK Control*` constraints.
- Current state audit:
  - `anm/blender-helper-only-current-state.json`
  - helper targets remain near the body/weapon area;
  - finger bones are no longer driven by `aks74u`.

### 2026-05-17 Viewport Lock Preview With Left-Hand Offset

- User reported that in helper-only mode the hands were no longer locked to
  the weapon and the left hand was 2-3 cm too high.
- Added and ran `tools/apply_safe_weaponik_viewport_lock_preview.py`.
- This creates a preview-only lock mode:
  - full-body action stays in NLA;
  - active action remains `aks74u_helpers_only`;
  - Blender IK is used only for viewport checking;
  - left viewport target is offset down by `0.025 m`.
- Added an iterative live compensation pass for `WIK_L_Viewport_Target` so the
  visible `LeftHand` head reaches the desired lowered target point.
- Compensation diagnostic:
  - `anm/blender-safe-lock-left-compensation.json`
  - final left-hand error to desired lowered point was approximately
    `0.000004 m`.
- This mode is explicitly not export truth; it is a practical viewport lock
  until the DayZ compact-record-to-Blender-pose adapter is finished.

### 2026-05-17 Emergency Restore After Broken Arms

- User reported the arms were broken after viewport lock experiments.
- Re-ran `tools/restore_clean_fullbody_no_weaponik_preview.py`.
- Live scene is back to `Clean FullBody Only`:
  - active action is `null`;
  - only full-body `p_rfl_erc_idle_ras` remains in NLA with influence `1.0`;
  - no weapon IK preview constraints remain on hands;
  - no `WIK_*` controls remain active.
- Audit written to `anm/blender-clean-fullbody-audit.json`.
- The only remaining pose constraint is the existing `DZ_FirstPersonCamera`
  `Child Of` constraint to `Head`.

### 2026-05-17 DayZ Local Adapter Preview

- Added and ran `tools/apply_dayz_weaponik_preview_with_local_adapter.py`.
- Implemented the Blender local pose adapter using:
  `pose = parent_pose * parent_rest^-1 * bone_rest * matrix_basis`.
- The script runs in the intended debug state:
  - full-body action in NLA;
  - active `aks74u_helpers_only`;
  - no Blender IK constraints;
  - no `DayZ WIK Control*` constraints.
- Current frame 30 validation shows the adapter now applies solver output to
  visible Blender bones:
  - `LeftHand` solver target/result:
    `0.147458, 0.490749, 1.343903`;
  - actual `LeftHand` head:
    `0.147458, 0.490749, 1.343902`;
  - `RightHand` solver target/result:
    `0.214272, 0.110020, 1.354113`;
  - actual `RightHand` head:
    `0.214271, 0.110020, 1.354113`.
- Diagnostic written to `anm/blender-dayz-local-adapter-preview.json`.
- Remaining risk is now solver/visual parity, not Blender matrix application.

### 2026-05-17 Runtime Cache Diagnostic After Broken Arms

- User reported that the arms were still broken after applying the local
  adapter preview.
- Restored the live scene again with
  `tools/restore_clean_fullbody_no_weaponik_preview.py`.
- Current live scene is back to stable `Clean FullBody Only`:
  - active action is `null`;
  - full-body `p_rfl_erc_idle_ras` remains in NLA at influence `1.0`;
  - no preview IK constraints or `WIK_*` controls are active.
- Added and ran `tools/diagnose_dayz_weaponik_solver_variants.py`.
  Result: many variants can reach the hand target, but elbow/forearm shape
  depends on DayZ helper-plane/twist interpretation.
- Added and ran `tools/diagnose_dayz_weaponik_runtime_cache.py`.
  This tests the Ghidra `case 0x0c` cache composition without applying a pose.
- Diagnostic written to:
  - `anm/dayz-weaponik-solver-variant-diagnostic.json`
  - `anm/dayz-weaponik-runtime-cache-diagnostic.json`
- New finding: direct Blender helper world positions are not the correct
  DayZDiag runtime inputs. DayZ composes cached IK-pose local transforms through
  current right-hand/weapon bases before calling `FUN_1400e1be0`.
- Current blocker: the imported `aks74u_helpers_only` action and the visible
  weapon/helper bones are not yet aligned in the same DayZ runtime cache space.
  Do not apply solver output to the live armature until this cache-space issue
  is fixed.

### 2026-05-17 ANM Import Path, Full Fingers Restored

- User clarified that this workflow is importing from `.anm`, not TXA.
- Copied the patched ANM import/export addon files into both:
  - `P:\BlenderAnimtool\DayzAnimationToolsBinary\...`
  - Blender 4.2 active addon folder in `%APPDATA%`.
- Reverted the attempted `keyframe_points.add(len(keys)-1)` change because
  Blender 4.2 fcurves start with zero keyframes in this addon path; the change
  caused an import-time `IndexError`.
- Reimported `P:\DZ\anims\anm\player\ik\weapons\aks74u.anm` through the live
  Blender bridge.
- Active action is now the full `aks74u` imported ANM action, not
  `aks74u_helpers_only`.
- Finger animation is restored:
  - action `aks74u`;
  - `301` fcurves;
  - left/right finger tracks are present alongside WeaponIK helper tracks.
- Saved a separate Blender copy:
  `P:\Animation_Weapon\Weapon_template_aks74u_anm_full_import.blend`.
- Important remaining finding: the broken-arm preview is not fixed by Blender
  constraints. The raw `.anm` import contains valid finger/helper tracks, but
  the DayZ runtime WeaponIK solver still needs a correct ANM-cache-to-Blender
  preview adapter before applying arm pose changes to the viewport.

### 2026-05-17 Safe Addon Mode And IK2H Export Structure

- Patched `DayzAnimationTools/Tools/AddSurvivorIK.py`.
- The menu item formerly named `Refresh DayZ Weapon IK Preview` now prepares a
  safe ANM authoring mode instead of adding Blender IK constraints.
- Safe mode behavior:
  - removes `DayZ WeaponIK Preview`, `DayZ WIK Control*`, `DayZ Left Hand IK`,
    and `DayZ Right Hand IK` constraints;
  - shows/select-enables `LeftHand*` and `RightHand*` bones;
  - marks the armature as `ANM authoring mode; DayZDiag preview solver not
    applied`;
  - does not solve or move arms.
- Saved live test copy:
  `P:\Animation_Weapon\Weapon_template_aks74u_anm_safe_authoring.blend`.
- Test result:
  `anm/blender-safe-weaponik-addon-operator-test.json`
  - active action: `aks74u`;
  - fcurves: `301`;
  - visible hand/finger bones: `53`;
  - unsafe constraints: `0`.

### 2026-05-17 IK2H Binary ANM Export Filter Fix

- Patched `DayzAnimationToolsBinary/Export/ExportAnm.py`.
- Binary IK export now uses a hardcoded ANM helper set instead of relying only
  on `DayzAnimationTools.Types.Txa`, because the active Blender TXA list had
  `LeftHandIKTarget` commented out.
- Binary IK export now preserves:
  - `RightHandOrigin`;
  - `RightForeArmDirection`;
  - `RightForeArmDirectionOrigin`;
  - `RightHand_Dummy`;
  - `LeftHandOrigin`;
  - `LeftHandIKTarget`;
  - `LeftForeArmDirection`;
  - `LeftForeArmDirectionOrigin`;
  - `LeftHand_Dummy`;
  - hand/finger tracks.
- Binary IK export now excludes terminal `Thumb4/Index4/Middle4/Ring4/Pinky4`
  bones for this weapon IK ANM path, matching `aks74u.anm` structure.
- Round-trip structural test:
  `anm/aks74u-anm-export-roundtrip.json`
  - original bone count: `43`;
  - exported bone count: `43`;
  - original finger count: `34`;
  - exported finger count: `34`;
  - missing bones: none;
  - extra bones: none;
  - missing helpers: none.
- Numeric round-trip test:
  `anm/aks74u-anm-numeric-roundtrip.json`
  - structure is fixed;
  - numeric parity is not yet fixed;
  - largest differences are still in helper-space reconstruction, especially
    `LeftHandIKTarget`, `LeftHandOrigin`, and `RightHandOrigin`.
- Current conclusion: the addon is now safe for preserving the correct IK2H
  bone set and finger tracks, but not yet a byte/numeric round-trip exporter
  for imported weapon IK `.anm`.

### 2026-05-17 Imported ANM Raw Preserve Path

- Patched `DayzAnimationToolsBinary/Import/ImportAnm.py`.
- Imported `.anm` actions now cache the original binary ANM bytes inside the
  `.blend` as a text datablock:
  - action property `dayz_binary_anm_source`;
  - action property `dayz_binary_anm_raw_text`;
  - action property `dayz_binary_anm_raw_preserve = true`.
- Patched `DayzAnimationToolsBinary/Export/ExportAnm.py`.
- Binary ANM export now has `Preserve Imported Raw ANM` in the export panel.
  When enabled for an imported action, it writes the cached source `.anm`
  bytes exactly instead of resampling Blender pose-space.
- Reason: DayZ weapon IK helper tracks are runtime solver inputs, not normal
  Blender arm constraints. Until the DayZDiag cache-space preview adapter is
  finished, resampling helper bones through Blender can change frame 0 and
  helper-space values.
- Live Blender addon was reloaded successfully:
  `anm/blender-binary-anm-addon-reload.json`
  - property before reload: `false`;
  - property after reload: `true`;
  - errors: none.
- Round-trip byte tests:
  - `anm/aks74u-anm-raw-preserve-export.json`;
  - `anm/aks74u-bpyops-raw-preserve-export.json`;
  - original `P:\DZ\anims\anm\player\ik\weapons\aks74u.anm`: `3579` bytes;
  - exported: `3579` bytes;
  - byte-identical: `true`.
- Saved Blender copy with raw cache:
  `P:\Animation_Weapon\Weapon_template_aks74u_anm_safe_authoring_rawcache.blend`.
- Important usage note: keep `Preserve Imported Raw ANM` enabled for
  unmodified imported DayZ IK `.anm` files. Disable it after editing keys,
  because then the exporter must sample the edited Blender action.

### 2026-05-18 Blender Arm IK Authoring Controls

- Added a clean Blender authoring preset for weapon/hand posing:
  `tools/create_dayz_arm_ik_authoring_controls.py`.
- Saved the current scene as:
  `P:\Animation_Weapon\Weapon_template_arm_ik_controls.blend`.
- Created/updated four visible controls:
  - `DAT_CTRL_L_Hand`;
  - `DAT_CTRL_R_Hand`;
  - `DAT_CTRL_L_Elbow`;
  - `DAT_CTRL_R_Elbow`.
- The visible working set is now only 16 bones:
  arm bones, four `DAT_CTRL_*` controls, and key weapon attach bones.
- Hidden technical helpers now auto-follow the controls:
  - `LeftHandIKTarget`, `LeftHandOrigin`, `LeftHandIK`, `LeftHand_Dummy`;
  - `LeftForeArmDirection`, `LeftForeArmDirectionOrigin`;
  - `RightHandOrigin`, `RightHandIK`, `RightHand_Dummy`;
  - `RightForeArmDirection`, `RightForeArmDirectionOrigin`.
- Added export safety:
  - binary ANM exporter skips `DAT_CTRL_*` and `WIK_*`;
  - TXA exporter skips `DAT_CTRL_*` and `WIK_*`.
- This is a Blender authoring rig only. The technical DayZ helper bones still
  exist and remain available to the import/export pipeline, but they are no
  longer exposed as manual controls in the viewport.

### 2026-05-18 Reverted Broken Blender IK Control Attempt

- User reported the Blender IK control attempt broke the skeleton.
- Added `tools/restore_clean_dayz_weapon_authoring_scene.py`.
- Restored the live Blender scene to a safe no-Blender-IK state:
  - removed/avoided `DAT_CTRL_*` authoring bones;
  - removed/avoided `DAT Arm Authoring` and old `DayZ WeaponIK Preview`
    constraints;
  - hid the `zJD_*` custom shape objects;
  - left only arm bones, DayZ helper bones, and key weapon bones visible for
    inspection.
- Saved clean copy:
  `P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend`.
- Current conclusion: controls must not be injected into the real DayZ export
  skeleton as direct IK constraints. The safer next design is a separate
  non-export control rig/object layer that drives/bakes DayZ helper tracks,
  while the real DayZ skeleton remains untouched.

### 2026-05-18 Separate Non-Export Control Rig Prototype

- Analyzed the reference file `C:\Users\sysro\Downloads\BlenderPoses.blend`.
- Reference rig structure:
  - `rig` is the animator/control armature;
  - `Armature` is the target/export skeleton;
  - scripts copy/apply transforms between the two instead of putting animator
    controls inside the export skeleton.
- Extracted reference scripts to:
  `anm/ref-blender-texts/`.
- Wrote reference analysis:
  `anm/ref-rig-arm-control-analysis.md`.
- Added `tools/create_dayz_separate_control_rig.py`.
- Generated a new DayZ authoring file:
  `P:\Animation_Weapon\Weapon_template_separate_controlrig.blend`.
- New file contains:
  - export skeleton `_DayZ_Character`;
  - separate non-export armature `DAT_ControlRig`;
  - animator bones:
    - `CTRL_Hand.L`;
    - `CTRL_Hand.R`;
    - `CTRL_Elbow.L`;
    - `CTRL_Elbow.R`.
- Preview constraints:
  - `_DayZ_Character.LeftHand` IK targets `DAT_ControlRig.CTRL_Hand.L`;
  - `_DayZ_Character.RightHand` IK targets `DAT_ControlRig.CTRL_Hand.R`;
  - elbow poles are `CTRL_Elbow.L/R`;
  - helper bones follow hand/elbow controls for viewport preview.
- Added text datablock `DAT_Bake_Preview_To_Action.py` to the `.blend`.
  It defines `bake_preview_constraints_to_action()` for baking the preview
  pose into a normal action before final export.
- Important: this is still a prototype. It follows the reference two-armature
  design and no longer adds control bones into the DayZ export skeleton, but
  elbow pole angles and helper-space baking still need visual tuning against
  DayZDiag/reference behavior.

### 2026-05-18 Control Rig Chain Fix

- User reported `CTRL_Hand.L/R` only controlled the hand and the hands looked
  wrong.
- Diagnosed live `Weapon_template_separate_controlrig.blend`:
  - `LeftHand`/`RightHand` IK constraints had `chain_count = 2`;
  - DayZ arm hierarchy includes roll bones:
    `Hand -> ForeArmRoll -> ForeArm -> ArmRoll -> Arm`;
  - `chain_count = 2` only reaches the wrist/near roll bone, not the whole arm.
- Added `tools/fix_dayz_controlrig_chain_orientation.py`.
- Saved fixed file:
  `P:\Animation_Weapon\Weapon_template_separate_controlrig_v2.blend`.
- Fixes:
  - `LeftHand` IK target remains `DAT_ControlRig.CTRL_Hand.L`;
  - `RightHand` IK target remains `DAT_ControlRig.CTRL_Hand.R`;
  - both arm IK constraints now use `chain_count = 5`;
  - control hand bones are reoriented to match the DayZ hand bones instead of
    using vertical helper-bone orientation.
- Verified dump:
  `anm/blender-dayz-controlrig-v2-dump.json`
  - `LeftHand` IK `chain_count = 5`;
  - `RightHand` IK `chain_count = 5`.

### 2026-05-18 Reference-Style Control Rig V3

- Performed a full dump of the reference file:
  `C:\Users\sysro\Downloads\BlenderPoses.blend`.
- Outputs:
  - `anm/ref-blender-deep-dump.json`;
  - `anm/ref-blender-deep-analysis.md`;
  - `anm/reference-blender-authoring-rig-analysis.md`.
- Confirmed reference architecture:
  - `rig` is the human-facing control rig;
  - `Armature` is the target/export-style skeleton;
  - hidden MCH/DEF/ORG bones perform the mechanism;
  - scripts copy/apply transforms to the export armature.
- Ghidra boundary check:
  - `workbenchApp.exe` and `DayZDiag_x64.exe` were open in Ghidra MCP;
  - raw string probe saved to
    `anm/ghidra-raw/ghidra-raw-bone-name-string-probes-2026-05-18.json`;
  - `workbenchApp.exe` contains DayZ arm/hand/roll bone names;
  - `RightHandOriginPose` and `LeftHandOriginPose` were not found in the
    probed DayZ/Workbench strings, so those names are treated as Blender-only
    authoring helpers from the reference file.
- Added `tools/create_dayz_refstyle_controlrig_v3.py`.
- Generated a new clean file from
  `P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend`:
  `P:\Animation_Weapon\Weapon_template_controlrig_v3_refstyle.blend`.
- New v3 design:
  - `_DayZ_Character` remains the export skeleton;
  - `DAT_ControlRigV3` is a separate non-export control rig;
  - visible controls are only:
    `CTRL_Hand.L`, `CTRL_Hand.R`, `CTRL_Elbow.L`, `CTRL_Elbow.R`;
  - hidden mechanism bones are:
    `DRV_UpperArm.L/R`, `DRV_ForeArm.L/R`, `DRV_Hand.L/R`;
  - IK constraints exist only on `DAT_ControlRigV3.DRV_Hand.L/R`;
  - DayZ arm, forearm, hand, and roll bones follow with `COPY_TRANSFORMS`.
- Verified dump:
  `anm/blender-dayz-controlrig-v3-dump.json`
  - `_DayZ_Character` has 163 bones;
  - `DAT_ControlRigV3` has 10 bones;
  - no direct IK constraints are on `_DayZ_Character.LeftHand` or
    `_DayZ_Character.RightHand`;
  - the only visible control rig bones are the four hand/elbow controls.

### 2026-05-18 Full-Clone Control Rig V4

- User reported v3 still produced broken arms.
- Diagnosis: v3 used a simplified three-bone mechanism and copied it into the
  DayZ skeleton. That can still mismatch DayZ's real rest hierarchy and bone
  axes.
- Added `tools/create_dayz_fullclone_controlrig_v4.py`.
- Generated:
  `P:\Animation_Weapon\Weapon_template_controlrig_v4_fullclone.blend`.
- New v4 design:
  - `DAT_ControlRigV4` is a full clone of the DayZ armature data;
  - it has the same DayZ rest skeleton plus four visible controls:
    `CTRL_Hand.L`, `CTRL_Elbow.L`, `CTRL_Hand.R`, `CTRL_Elbow.R`;
  - IK runs on the clone's real DayZ `LeftHand` / `RightHand` chains;
  - IK `chain_count = 5`, covering
    `Hand -> ForeArmRoll -> ForeArm -> ArmRoll -> Arm`;
  - `_DayZ_Character` follows matching clone bones in pose space with
    `COPY_TRANSFORMS`, instead of receiving direct IK constraints.
- Verification:
  - `anm/blender-dayz-controlrig-v4-dump.json`;
  - `anm/dayz-controlrig-v4-eval-check.json`;
  - `_DayZ_Character` and `DAT_ControlRigV4` evaluated arm matrices matched
    for the copied arm bones with zero matrix delta in the sanity check;
  - only four control bones are visible on `DAT_ControlRigV4`.

### 2026-05-18 Proxy IK Control Rig V5

- User reported v4 was still visually wrong.
- Diagnosis update: direct IK over the full DayZ chain still lets Blender solve
  through DayZ roll bones as if they were real elbow/wrist joints. Matching
  matrices after copy is not enough if the source IK solve itself is wrong.
- Added `tools/create_dayz_proxyik_controlrig_v5.py`.
- Generated:
  `P:\Animation_Weapon\Weapon_template_controlrig_v5_proxyik.blend`.
- New v5 design:
  - `DAT_ControlRigV5` contains a clean three-bone proxy chain per arm:
    `IK_Arm.* -> IK_ForeArm.* -> IK_Hand.*`;
  - roll bones are not part of the IK chain;
  - visible controls remain only:
    `CTRL_Hand.L`, `CTRL_Elbow.L`, `CTRL_Hand.R`, `CTRL_Elbow.R`;
  - `_DayZ_Character.LeftArm/LeftForeArm/LeftHand` and right-side equivalents
    use rotation-only follow from the proxy chain;
  - DayZ roll bones are left unconstrained by the IK preview to avoid treating
    them as bend joints.
- Verified dump:
  `anm/blender-dayz-controlrig-v5-dump.json`
  - `_DayZ_Character` has no IK constraints;
  - `DAT_ControlRigV5.IK_Hand.L/R` have IK `chain_count = 3`;
  - only the four `CTRL_*` controls are visible.

### 2026-05-18 V6/V7 Rejected After Geometry Checks

- User reported the v5 result was still wrong and asked to check directly.
- Geometry dump:
  `anm/dayz-controlrig-current-arm-geometry-check.json`.
- Found a concrete v5 error:
  - proxy bones were created from DayZ bone tails while DayZ has roll bones
    between real joints;
  - with `use_connect = true`, `IK_ForeArm.L` expanded to about `0.288`
    instead of matching the intended forearm segment;
  - this means the proxy IK source was already wrong before DayZ copied it.
- Added `tools/create_dayz_truejoint_controlrig_v6.py`.
- Generated:
  `P:\Animation_Weapon\Weapon_template_controlrig_v6_truejoint.blend`.
- v6 used true anatomical joints:
  `Arm.head -> ForeArm.head -> Hand.head`.
- Geometry check:
  `anm/dayz-controlrig-v6-geometry-check.json`.
- Found the next issue:
  - proxy chain lengths were correct;
  - but `_DayZ_Character` still has roll bones between arm and forearm;
  - leaving roll bones unconstrained produced visible hierarchy gaps.
- Added `tools/create_dayz_truejoint_controlrig_v7_rollfollow.py`.
- Generated:
  `P:\Animation_Weapon\Weapon_template_controlrig_v7_truejoint_rollfollow.blend`.
- Continuity check:
  `anm/dayz-controlrig-v7-continuity-check.json`.
- v7 was also rejected:
  - even with roll-follow constraints, DayZ arm/roll/forearm hierarchy still
    showed large gaps, especially on the right arm chain.
- Conclusion:
  - `_DayZ_Character` is not a clean connected animator rig and should not be
    used directly as a live Blender IK doll;
  - the correct next direction is a separate real authoring/deform rig, then a
    bake/retarget step into DayZ export/helper tracks.
- Restored safe clean file:
  `P:\Animation_Weapon\Weapon_template_clean_no_blender_ik.blend`.
