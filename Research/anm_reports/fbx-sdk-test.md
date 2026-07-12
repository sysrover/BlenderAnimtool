# Autodesk FBX SDK Test

Date: 2026-05-17

## Selected SDK

- `confirmed`: Best practical SDK found for converter prototyping is Autodesk FBX SDK 2016.1 VS2015.
- `confirmed`: Official Autodesk download URL used:
  `http://images.autodesk.com/adsk/files/fbx20161_fbxsdk_vs2015_win0.exe`
- `confirmed`: Local installer path:
  `tools/fbx-sdk-cache/fbx20161_fbxsdk_vs2015_win0.exe`
- `confirmed`: SHA256:
  `8002B21B94D06B58DE563D39F28A825EDB11AB5F620D025840C328A4F5CF96E2`
- `confirmed`: Windows Authenticode signature is valid and signed by `Autodesk, Inc`.
- `confirmed`: Installer metadata says `Autodesk FBX SDK 2016.1`.

## Install Test

- `confirmed`: Silent install succeeded with exit code `0`.
- `confirmed`: Install path:
  `tools/fbx-sdk-cache/fbx20161_vs2015`
- `confirmed`: Installed headers include:
  `tools/fbx-sdk-cache/fbx20161_vs2015/include/fbxsdk.h`
- `confirmed`: Installed x64 release library set includes:
  `tools/fbx-sdk-cache/fbx20161_vs2015/lib/vs2015/x64/release/libfbxsdk.dll`
  `tools/fbx-sdk-cache/fbx20161_vs2015/lib/vs2015/x64/release/libfbxsdk.lib`
  `tools/fbx-sdk-cache/fbx20161_vs2015/lib/vs2015/x64/release/libfbxsdk-md.lib`
  `tools/fbx-sdk-cache/fbx20161_vs2015/lib/vs2015/x64/release/libfbxsdk-mt.lib`
- `confirmed`: `LoadLibraryW()` succeeds for the x64 release `libfbxsdk.dll` on this machine.
- `unknown`: No C++ compile test was run because `cl`, `cmake`, `msbuild`, and `vswhere` were not found on PATH or in the standard Visual Studio installer path.

## Version Match

- `confirmed`: Installed header `include/fbxsdk/fbxsdk_version.h` reports:
  - `FBXSDK_VERSION_MAJOR 2016`
  - `FBXSDK_VERSION_MINOR 1`
  - `FBXSDK_VERSION_POINT 0`
  - release date `2015-06-30`
- `confirmed`: Workbench Ghidra evidence found FBX SDK string `2016.1.1` and build/date string `20150824`.
- `likely`: This official `2016.1.0` package is the closest usable public SDK baseline found so far, but it is not an exact version match to Workbench.
- `unknown`: Exact Autodesk FBX SDK `2016.1.1` installer was not found in this pass.

## Converter Use

- `confirmed`: SDK samples include VS2015 project files targeting `PlatformToolset v140`.
- `confirmed`: `samples/ImportScene` demonstrates scene import, animation stacks, skeleton display, and animation curve traversal.
- `confirmed`: `samples/ViewScene/GetPosition.cxx` uses `FbxNode::EvaluateGlobalTransform(pTime)`, matching the evaluator-style path Workbench uses from Ghidra evidence.
- `likely`: For our converter, this SDK can handle the FBX parse/evaluate layer. The remaining converter-specific work is still Workbench algorithm replication: skeleton filtering/order, sampled transform conversion, TXA model construction, and ANM writer packing as documented in the Ghidra research files.

## Practical Build Notes

Use the dynamic x64 release configuration first:

- include path:
  `tools/fbx-sdk-cache/fbx20161_vs2015/include`
- library path:
  `tools/fbx-sdk-cache/fbx20161_vs2015/lib/vs2015/x64/release`
- link library:
  `libfbxsdk.lib`
- runtime DLL:
  `libfbxsdk.dll`
- expected MSVC toolset:
  VS2015 `v140`, or a newer MSVC toolset able to link the import library.

If using the `-md` sample configuration, link `libfbxsdk-md.lib` instead. The SDK sample project uses `libfbxsdk-md.lib` for dynamic runtime configurations and `libfbxsdk.lib` for DLL import configurations.
