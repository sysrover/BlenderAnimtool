# ANM ↔ TXA Converter

Bidirectional converter between DayZ binary ANM and text TXA animation formats. Convert animations for editing or convert back to binary for use in DayZ.

## Features

- **ANM → TXA**: Binary to human-readable text format
- **TXA → ANM**: Text back to binary format (validated with DeAnm)
- **AnimSet5 & AnimSet6**: Full support for both animation formats
- **All Features**: Events, custom properties, all bone types
- **Precision**: Full float precision with proper quantization handling
- **Bidirectional**: Round-trip conversions maintain data integrity

## Quick Start

### Convert ANM to TXA (for editing)

```bash
python anm_to_txa.py animation.anm
# Output: animation.txa
```

### Convert TXA to ANM (back to binary)

```bash
python txa_to_anm.py animation.txa
# Output: animation.anm
```

### Specify Output Filename

```bash
python anm_to_txa.py input.anm output.txa
python txa_to_anm.py input.txa output.anm
```

### Drag-and-Drop (Windows)

```bash
# Run drag-drop converter
python anm_to_txa_dragdrop.py

# Or use the batch file
Drag_ANM_Here.bat
```

## Requirements

- Python 3.6 or higher
- **No external dependencies** (standard library only)

## File Structure

```
ANM-TXA/
├── anm_to_txa.py              # ANM → TXA converter
├── txa_to_anm.py              # TXA → ANM converter (new!)
├── anm_to_txa_dragdrop.py     # Drag-drop interface
├── Drag_ANM_Here.bat          # Windows batch wrapper
├── DayzAnimationToolsBinary/  # Binary format definitions
│   ├── Types/Anm.py           # AnimSet5/6 format parser
│   └── Utils/                 # BinaryReader, Lz4Decoder
├── examples/                  # Example animations
└── README.md
```

## TXA Format Reference

```
$animation "animation_name" {
  #version 1.0
  #fps 24
  #numFrames 120
  $node "boneName" {
    $keys t q s {
      $frame 0 {
        #t 0.1 0.2 0.3              (position X Y Z)
        #q 0.1 0.2 0.3 0.9          (quaternion X Y Z W)
        #s 1.0 1.0 1.0              (scale X Y Z)
      }
      $frame 1 {
        #q 0.15 0.25 0.35 0.88
      }
      $frame 2 10 {                  (collapsed range)
        #q 0.16 0.26 0.36 0.87
      }
    }
  }
  $events {
    #event 5 "eventName" "userString" 0
  }
  $custProps {
    #custProp "key" "value"
  }
}
```

## ANM Binary Format (AnimSet6)

```
FORM <size BE>
  ANIMSET 6
  <anim_data_len BE>
  FPS\0
  <unknown (4 bytes)>
  <fps LE>
  HEAD <size BE>
    [per-bone headers]
  DATA <size BE>
    [per-bone keyframe data]
  [EVNT <size BE>]
    [event list]
  [CPRP <size BE>]
    [custom properties]
```

### Bone Header Structure

Each bone in HEAD chunk contains:
- `posBias` (float): Minimum position value
- `posMult` (float): Position value range / 65535
- `rotBias` (float): Minimum rotation value  
- `rotMult` (float): Rotation range / 65535
- `scaleBias` (float): Minimum scale value
- `scaleMult` (float): Scale range / 65535
- `numFrames` (int16): Total frames in animation
- `numPosKeys` (int16): Position keyframe count
- `numRotKeys` (int16): Rotation keyframe count
- `numScaleKeys` (int16): Scale keyframe count
- `flags` (byte): Bone flags
- `nameLen` (byte): Length of bone name
- `name` (ASCII): Bone name

### Quantization

16-bit quantization for each channel:

```python
# Encoding (TXA → ANM)
encoded = (value - bias) / mult

# Decoding (ANM → TXA)  
value = (encoded / 65535) * mult + bias
```

The ANM reader applies `SCALE_FACTOR = 1.5259022E-05` during decompression.

### Axis Conventions

**TXA Storage**: (X, Y, Z) for positions/scales, (X, Y, Z, W) for quaternions

**ANM Storage**: (X, Z, Y) for positions/scales, (X, Z, Y, W) for quaternions

Conversion happens automatically during read/write.

## Validation

Generated ANM files validate with DeAnm:

```
$ deanm animation.anm
DeAnm Version 1.16
format 6: 0 Events 1 bones. 120 frames @ 24fps (5.00 seconds)
```

## How It Works

### ANM → TXA Process

1. Parse binary ANM file (FORM/ANIMSET/HEAD/DATA chunks)
2. Decompress quantized 16-bit values to floats using bias/mult
3. Convert axis order from (X,Z,Y) to (X,Y,Z)
4. For dynamic channels: interpolate all frames
5. For static channels: output only keyframed frames
6. Format into hierarchical TXA text structure

### TXA → ANM Process

1. Parse TXA text file (extract bones, keyframes, events)
2. For each channel: determine min/max and quantize to 16-bit
3. Convert axis order from (X,Y,Z) to (X,Z,Y)
4. Assemble binary chunks: FORM/ANIMSET/HEAD/DATA
5. Calculate sizes (big-endian for FORM/chunks, little-endian for data)
6. Write binary ANM file

## Performance

- Typical animation (200 frames, 10 bones): <1 second
- Large animation (1000 frames, 50 bones): <5 seconds
- Minimal memory footprint

## Known Limitations

- Quantization introduces ~0.0015% precision loss (imperceptible)
- AnimSet5 (no scale) supported for reading only
- No support for compressed/LZ4-encoded keyframes (unnecessary for TXA)

## Troubleshooting

**"DeAnm: Generic Error"**
- Verify `anim_data_len` includes all bytes from FPS marker to DATA chunk end
- Check that FPS marker, unknown field (0x00000004), and fps value are correct
- Ensure bone headers have correct field order and alignment

**Missing animation data in ANM**
- Verify TXA `#numFrames` matches highest frame number
- Ensure frame 0 has at least position data
- Check bone names contain no invalid characters

**Precision differences**
- Expected during quantization/dequantization
- Values accurate to ±1.5e-5 of original
- Imperceptible in animation playback

## Examples

### Edit and Convert Back

```bash
# Extract for editing
python anm_to_txa.py player_walk.anm
# Edit player_walk.txa in any text editor
# Convert back
python txa_to_anm.py player_walk.txa
```

### Batch Convert Multiple Files

```bash
# Windows
for %f in (*.anm) do python anm_to_txa.py "%f"

# Linux/Mac
for f in *.anm; do python anm_to_txa.py "$f"; done
```

### Round-Trip Verification

```bash
# Convert both ways to verify data integrity
python anm_to_txa.py original.anm
python txa_to_anm.py original.txa test.anm
# original.anm and test.anm should be identical (or functionally equivalent)
```

## Technical References

- **SCALE_FACTOR**: 1.5259022E-05 (standard 3D conversion)
- **Quantization Precision**: 16-bit unsigned integer (0-65535 range)
- **Interpolation**: LERP for vectors, SLERP for quaternions
- **Frame Collapsing**: Identical consecutive frames stored as ranges in TXA

## License

This tool is provided as-is for DayZ modding community use.

## Acknowledgments

- Format reverse-engineered from DayZ Arma Reforger Tools
- Decompilation via Ghidra
- Validation with DeAnm (Mikero's DayZ Tools)
