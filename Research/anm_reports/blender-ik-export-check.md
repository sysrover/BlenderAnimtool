# Blender IK TXA Export Check

## Result

- `confirmed`: DayZDiag reads the final ANM as normal `ANIM/SET6` tracks. The
  reader path documented in `dayzdiag-anm-reader.md` consumes `HEAD` and `DATA`
  records and does not expose a separate IK-only ANM stream format.
- `confirmed`: Blender `DayzAnimationTools` exports IK through normal TXA
  `$node` / `$keys t q s` blocks, then our `TxaAnmPrototype` converts those TXA
  tracks into Workbench-style `ANIM/SET6`.
- `fixed`: the TXA exporter previously sampled only the first IK frame but left
  `#numFrames` based on the full action range. It also hard-coded new IK
  keyframes to `frameEnd = 1`. This could produce an IK TXA whose declared frame
  count and sampled key data did not match.

## Patch

File:

- `P:\BlenderAnimtool\DayzAnimationTools\Export\ExportTxa.py`

Changes:

- IK exports now clamp `txaAnimation.numFrames` to `min(2, numFrames)`.
- IK exports now sample up to two frames instead of breaking after frame `0`.
- New keyframes use `frameEnd = frame`; unchanged second-frame values still
  extend the first key to `$frame 0 1` through the existing duplicate-key logic.

This matches the existing intent visible in
`P:\BlenderAnimtool\DayzAnimationToolsBinary\Export\ExportAnm.py`, where IK
exports are limited to two frames.

## Current Compatibility

- `likely`: exported IK TXA is structurally readable by our converter and by
  DayZDiag after conversion to ANM.
- `likely`: static IK poses still export as `$frame 0 1` with `#numFrames 2`
  when the first two sampled frames are identical.
- `confirmed`: `LeftHandOrigin` is duplicated as `LeftHandIKTarget`, matching
  the existing sample `DayzAnimationToolsBinary\example\export.txa`.

## Remaining IK-Semantic Questions

- `unknown`: whether `RightHandIKTarget` is required by any game-side IK
  profile. Existing sample TXA contains `LeftHandIKTarget`, not
  `RightHandIKTarget`.
- `unknown`: whether specific game assets require `LeftForeArmDirectionOrigin`
  and `RightForeArmDirectionOrigin` in addition to `LeftForeArmDirection` and
  `RightForeArmDirection`. The sample TXA contains both direction and
  direction-origin nodes.
- `confirmed`: our TXA-to-ANM converter can carry these node names if the
  Blender exporter emits them; DayZDiag reads them as normal named tracks.

## Verification

- `python -m py_compile` passed for the changed Blender addon files.
- `dotnet build tools\TxaAnmPrototype\TxaAnmPrototype.csproj` passed.
