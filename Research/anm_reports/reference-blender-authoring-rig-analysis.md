# Reference Blender Authoring Rig Analysis

Source reference file: `C:\Users\sysro\Downloads\BlenderPoses.blend`

## Confirmed Structure

- The file has two armatures:
  - `Armature`: 156 bones, target/export-style skeleton.
  - `rig`: 734 bones, animator/control rig.
- The reference does not put human-facing IK controls directly into the export skeleton.
- The visible arm controls live on `rig`; the export-style `Armature` follows by copy/apply transform scripts and constraints.
- Rigify-style arm IK uses:
  - hand controls: `hand_ik.L`, `hand_ik.R`;
  - elbow/pole controls: `upper_arm_ik_target.L`, `upper_arm_ik_target.R`;
  - hidden mechanism bones: `MCH-forearm_ik.L/R`, `MCH-upper_arm_ik_target.L/R`;
  - IK chain count: `2` on the reference two-bone arm mechanism.
- The reference has separate display layers/collections. Most mechanism bones are hidden; animator sees a small control set.

## Reference Scripts

- `Text.txt` copies transforms from `Pose RPG` to `Armature` bones and applies constraints.
- `Text.001.txt` maps these authoring helpers:
  - `RightHandOriginPose` -> `RightHand`
  - `RightForeArmDirectionOriginPose` -> `RightForeArm`
  - `LeftHandOriginPose` -> `LeftHand`
  - `LeftForeArmDirectionOriginPose` -> `LeftForeArm`
- `Text.002.txt` applies copy location and copy rotation from the same helper bones to the target `Armature`.
- These `OriginPose` bones are authoring helpers in the reference file, not DayZ runtime bones.

## Ghidra Boundary Check

Ghidra MCP was connected with:

- current: `workbenchApp.exe`
- also open: `DayZDiag_x64.exe`

Raw string probe saved to:

`anm/ghidra-raw/ghidra-raw-bone-name-string-probes-2026-05-18.json`

Confirmed from string probes:

- `workbenchApp.exe` contains DayZ bone names such as `LeftHand`, `RightHand`, `LeftForeArm`, `RightForeArm`, `LeftForeArmRoll`, and `RightForeArmRoll`.
- `DayZDiag_x64.exe` contains `RightHand` and `LeftHand_Dummy` / `RightHand_Dummy` strings in the probed string table.
- Neither `DayZDiag_x64.exe` nor `workbenchApp.exe` matched `RightHandOriginPose` or `LeftHandOriginPose` in this probe.

Conclusion: use DayZ/Workbench names for export/runtime skeleton. Use `OriginPose`-style names only as Blender authoring controls if needed.

## Applied Design Decision

The better DayZ Blender authoring setup should be:

- `_DayZ_Character`: clean export skeleton, no human controls inside it.
- `DAT_ControlRigV3`: non-export control rig.
- Visible animator controls:
  - `CTRL_Hand.L`
  - `CTRL_Hand.R`
  - `CTRL_Elbow.L`
  - `CTRL_Elbow.R`
- Hidden mechanism bones:
  - `DRV_UpperArm.L/R`
  - `DRV_ForeArm.L/R`
  - `DRV_Hand.L/R`
- IK lives on the hidden control rig mechanism, not directly on DayZ hand bones.
- DayZ arm, forearm, hand, and roll bones follow the evaluated control rig through copy transforms and can be baked before export.

Generated file:

`P:\Animation_Weapon\Weapon_template_controlrig_v3_refstyle.blend`

