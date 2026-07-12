# FBX SDK Reference Notes

Date: 2026-05-17

Purpose: capture official Autodesk FBX SDK 2016 reference points that are useful
for building the FBX input side of the converter. These notes are not proof of
Workbench `.txa` or `.anm` internals. Workbench-specific claims remain tied to
Ghidra evidence in the other research files.

## Official Documentation Pages

- `confirmed`: Autodesk FBX 2016 Developer Help entry page:
  `https://help.autodesk.com/cloudhelp/2016/ENU/FBX-Developer-Help/files/GUID-105ED19A-9A5A-425E-BFD7-C1BBADA67AAB.htm`
- `confirmed`: Supported file formats:
  `https://help.autodesk.com/cloudhelp/2016/ENU/FBX-Developer-Help/files/GUID-0B122E01-7DB8-48E3-AADA-5E85A197FEE1.htm`
- `confirmed`: Supported scene elements:
  `https://help.autodesk.com/cloudhelp/2016/ENU/FBX-Developer-Help/files/GUID-2F7D6FDB-82D6-41EC-977C-01FFCA5EC382.htm`
- `confirmed`: Platform requirements:
  `https://help.autodesk.com/cloudhelp/2016/ENU/FBX-Developer-Help/files/GUID-B67EE33C-B913-4CAB-A39B-F929BA592B67.htm`

The user-provided wrapper URL points to the same topic but returns a JavaScript
shell through `help.autodesk.com/view/FBX/2016/ENU`. The static `cloudhelp/2016`
URLs above expose the actual page HTML.

## File Versions

- `confirmed`: Autodesk says FBX SDK 2016 can import FBX file format versions
  `7.5`, `7.4`, `7.3`, `7.2`, `7.1`, `7.0`, `6.1`, and `6.0`.
- `confirmed`: Autodesk says FBX SDK 2016 can export FBX file format versions
  `7.5`, `7.4`, `7.3`, `7.2`, `7.1`, `7.0`, and `6.1`.
- `confirmed`: Autodesk states the FBX file format itself is not documented and
  applications should use the FBX SDK for import/export.

Converter implication:

- Use the SDK parser/evaluator for `.fbx`, not a homegrown FBX file parser.
- Treat FBX `6.0` import as possible through SDK, but do not expect SDK export
  back to `6.0`.
- Workbench’s ANM/TXA conversion logic still comes from Ghidra, not from Autodesk
  docs.

## Scene Data Relevant to Animation Conversion

Autodesk lists these supported scene elements that matter for our converter:

- `FbxScene`
- `FbxNode`
- `FbxSkeleton`
- `FbxAnimCurve`
- `FbxPose`
- `FbxGlobalSettings`
- `FbxAxisSystem`

Converter implication:

- Load an `FbxScene`.
- Walk `FbxNode` hierarchy.
- Select skeleton nodes through `FbxSkeleton`.
- Use `FbxAnimStack`/animation curve data and SDK evaluation APIs.
- Read global settings for time mode, axis, and unit scale, then apply the
  Workbench transform/order rules already traced in Ghidra.

## Installed SDK/Ghidra Status

- `confirmed`: Installed SDK path:
  `tools/fbx-sdk-cache/fbx20161_vs2015`
- `confirmed`: Ghidra imported the SDK runtime DLL:
  `/sdk/libfbxsdk.dll`
- `confirmed`: Imported DLL path:
  `tools/fbx-sdk-cache/fbx20161_vs2015/lib/vs2015/x64/release/libfbxsdk.dll`
- `confirmed`: Ghidra found named exports/functions including:
  - `FbxImporter::Initialize`
  - `FbxImporter::Import`
  - `FbxNode::EvaluateGlobalTransform`
  - `FbxNode::GetAnimationInterval`
- `unknown`: Ghidra fuzzy matching from `libfbxsdk.dll` to Workbench timed out on
  the full Workbench binary, so no automatic symbol transfer was completed.

## Practical Converter Direction

Use the installed SDK only for the FBX side:

1. Create `FbxManager`.
2. Create `FbxIOSettings`.
3. Create `FbxImporter`.
4. Call `FbxImporter::Initialize(path, -1, ios)`.
5. Import into `FbxScene`.
6. Enumerate animation stacks/takes.
7. Enumerate skeleton nodes.
8. Sample/evaluate node transforms with SDK evaluator APIs.
9. Convert sampled transforms into the Workbench internal/TXA shape using the
   Ghidra-derived Workbench rules.
10. Serialize ANM with the Ghidra-derived ANM writer rules.

This gives a realistic path for our application: depend on Autodesk FBX SDK for
FBX parsing/evaluation, and implement only the DayZ Workbench-specific
FBX-to-TXA and TXA-to-ANM layers ourselves.
