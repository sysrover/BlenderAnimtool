# Weapon IK ANIMSET6 Reader Check

## Scope

File checked:

- `P:\DZ\anims\anm\player\ik\weapons\sv98.anm`

Main runtime source:

- `DayZDiag_x64.exe`
- `FUN_1400d4520`: ANM/SET reader
- `FUN_1400d5160`: DATA stream reader

## sv98.anm Container

`confirmed`: `sv98.anm` is `ANIMSET6`.

Header bytes:

```text
46 4F 52 4D ... 41 4E 49 4D 53 45 54 36
FORM            ANIMSET6
```

Parsed values:

- format: `6`
- fps: `30`
- file length: `3729`
- `FORM` size: `3721`
- animation payload size: `3709`
- `HEAD` size: `0x845`
- `DATA` size: `1464`
- bone records: `43`
- animation frames per track: `2`

## SET6 HEAD Layout

`confirmed`: DayZDiag `FUN_1400d4520` handles `SET6` with variable-size HEAD
records. It reads the whole HEAD chunk, then walks records by:

```text
nextRecord = currentRecord + currentRecord[0x21] + 0x22
```

That means SET6 record layout is:

```text
0x00 float posBias
0x04 float posMultiRaw
0x08 float rotBias
0x0c float rotMultiRaw
0x10 float scaleBias
0x14 float scaleMultiRaw
0x18 uint16 numFrames
0x1a uint16 numPosKeys
0x1c uint16 numRotKeys
0x1e uint16 numScaleKeys
0x20 uint8 flags
0x21 uint8 nameLen
0x22 char[nameLen] name
```

`confirmed`: `DayzAnimationToolsBinary\Types\Anm.py` `AnmBone.Read` matches
this SET6 HEAD layout:

- reads six little-endian floats;
- reads `numFrames`, `numPosKeys`, `numRotKeys`, `numScaleKeys`;
- reads one flag byte;
- reads one name-length byte;
- reads `nameLen` ASCII bytes.

## SET6 DATA Layout

`confirmed`: DayZDiag `FUN_1400d4520` reads SET6 `DATA` streams in this order:

1. translation stream via `FUN_1400d5160(..., components=3, ...)`
2. scale stream via `FUN_1400d5160(..., components=3, ...)`
3. rotation stream via `FUN_1400d5160(..., components=4, ...)`

`confirmed`: `DayzAnimationToolsBinary\Types\Anm.py` reads data in the same
order:

1. position frame indices
2. position values in stored `x,z,y` order
3. scale frame indices
4. scale values in stored `x,z,y` order
5. rotation frame indices
6. rotation values in stored `x,z,y,w` order

## sv98 Special Tracks

`confirmed`: `sv98.anm` contains the player WeaponIK special tracks:

- `LeftHand_Dummy`
- `RightHand_Dummy`
- `LeftHandIKTarget`
- `LeftForeArmDirection`
- `LeftHandOrigin`
- `LeftForeArmDirectionOrigin`
- `RightHandOrigin`
- `RightForeArmDirectionOrigin`
- `RightForeArmDirection`

All of these records have `numFrames = 2` and `flags = 0x00` in `sv98.anm`.

## Reader Fit Against DayZDiag

`confirmed`: for SET6 HEAD and DATA stream order, the Python ANM reader fits
DayZDiag.

`likely`: the Python reader's `posMulti`, `rotMulti`, and `scaleMulti`
conversion by multiplying raw range by `1.525902E-05` matches the DayZDiag
runtime conversion visible in `FUN_1400d4520`, where stored ranges are scaled
before `FUN_1400d5160` reconstructs values as:

```text
value = uint16Sample * scaledRange + bias
```

## Reader Problems To Fix

`confirmed`: importing `DayzAnimationToolsBinary.Types.Anm` directly from plain
Python fails outside Blender because the package `__init__.py` imports `bpy`.
This is not a file-format bug, but it makes command-line inspection harder.

`fixed`: `Anm.Read` used to print first decoded pos/rot values for every bone.
That debug output has been removed from
`P:\BlenderAnimtool\DayzAnimationToolsBinary\Types\Anm.py`.

`fixed`: `AnmBone.Read` now reads `numFrames`, `numPosKeys`, `numRotKeys`, and
SET6 `numScaleKeys` as unsigned 16-bit values, matching the DayZDiag reader
layout.

`fixed`: `DayzAnimationToolsBinary\Import\ImportAnm.py` now treats the full
graph-relative helper set as special import tracks:

- `RightHandOrigin`
- `RightForeArmDirectionOrigin`
- `RightForeArmDirection`
- `LeftHandOrigin`
- `LeftForeArmDirectionOrigin`
- `LeftForeArmDirection`

`fixed`: the importer no longer injects hardcoded fallback vectors when
`LeftForeArmDirection` / `RightForeArmDirection` translations decode near zero.
The imported transform now comes from the ANM data only.

`confirmed`: `LeftHandIKTarget`, `LeftHand_Dummy`, and `RightHand_Dummy` are
read by the ANM reader and can import through the normal parent-relative path
when the authoring skeleton contains those bones.

## Current Decision

The binary reader format logic now matches the DayZDiag SET6 layout covered by
this pass. The importer layer has been updated for the full player WeaponIK
helper set needed by `sv98.anm` and the player `AnimNodeWeaponIK` graph.

Validation:

- `python -m py_compile` passed for both the source tree and the installed
  Blender 4.2 add-on copy.
- Blender 4.2.20 LTS loaded
  `P:\DZ\anims\anm\player\ik\weapons\sv98.anm` successfully:
  `AnimSet6`, `fps = 30`, `numFrames = 2`, `43` bone records, all nine player
  WeaponIK special tracks found.
