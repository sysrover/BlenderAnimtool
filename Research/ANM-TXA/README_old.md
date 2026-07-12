# ANM to TXA Converter

A standalone Python utility for converting between DayZ ANM (binary animation) and TXA (text animation) formats.

## What is it?

This toolkit converts DayZ animation files bidirectionally:
- **ANM→TXA**: Binary ANM files to human-readable TXA text format
- **TXA→ANM**: Text TXA files back to binary ANM format for use in DayZ

Supports:
- **AnimSet5** format (position and rotation keys, no scale)
- **AnimSet6** format (position, rotation, and scale keys)
- **Animation events** (per-frame game events)
- **Custom properties** (metadata)
- All 73+ character bones

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Installation

No installation needed. Just download/clone the folder and run the scripts directly.

## Usage

### ANM to TXA Conversion

Convert binary animation to text format:

```bash
python anm_to_txa.py input_file.anm [output_file.txa]
```

Example:
```bash
python anm_to_txa.py p_erc_fire_ump45_ras.anm p_erc_fire_ump45_ras.txa
```

If output filename is omitted, it defaults to the input filename with `.txa` extension.

### TXA to ANM Conversion

Convert text animation back to binary format:

```bash
python txa_to_anm.py input_file.txa [output_file.anm]
```

Example:
```bash
python txa_to_anm.py p_erc_fire_ump45_ras.txa p_erc_fire_ump45_ras.anm
```

If output filename is omitted, it defaults to the input filename with `.anm` extension.

### Drag-and-Drop Conversion

Use the drag-and-drop converter on Windows:

```bash
python anm_to_txa_dragdrop.py
```

Or run `Drag_ANM_Here.bat` and drag ANM files onto it for batch conversion.

## Input/Output

### Input
- Binary ANM files from DayZ Arma Reforger Tools
- Typically found in character animation directories

### Output
- Text-based TXA files with properly formatted animation data
- Can be imported back into DayZ Workbench for editing
- Human-readable hierarchical structure

## File Structure

```
anm_to_txa/
├── anm_to_txa.py                    # Main converter script
├── README.md                         # This file
├── DayzAnimationToolsBinary/
│   ├── __init__.py
│   ├── Types/
│   │   ├── __init__.py
│   │   └── Anm.py                  # ANM file format definition
│   └── Utils/
│       ├── __init__.py
│       ├── BinaryReader.py         # Binary data reader utility
│       └── Lz4Decoder.py           # LZ4 decompression algorithm
└── examples/
    └── (sample ANM files)
```

## How It Works

1. **Reading ANM Files**: The converter reads binary ANM files which contain:
   - Header information (FPS, frame count, format version)
   - Bone definitions with compression parameters
   - Compressed keyframe data (position, rotation, scale)
   - Events and custom properties

2. **Decompression**: Animation keyframes are stored as compressed 16-bit integers using min/max bounds:
   - Compression formula: `compressed = (value - min) * (65535 / (max - min))`
   - Decompression: Uses bone-specific scale factors and bias values

3. **Output**: Generates properly formatted TXA with:
   - Nested hierarchical structure
   - Per-bone animations with proper indentation
   - Frame-by-frame keyframe data
   - Event and property information

## Technical Details

### ANM Format
- **FORM**: Main container with animation set version
- **HEAD**: Bone definitions and compression parameters
- **DATA**: Keyframe data (compressed 16-bit integers)
- **EVNT**: Animation events (optional)
- **CPRP**: Custom properties (optional)

### TXA Format
Hierarchical text format:
```
$animation "animation_name" {
 $node "bone_name" {
  $keys t q s {
   $frame 0 {
    #t 0.0 0.0 0.0
    #q 0.0 0.0 0.0 1.0
    #s 1.0 1.0 1.0
   }
   $frame 1 { ... }
  }
 }
}
```

### Compression
- Uses SCALE_FACTOR: 1.5259022E-05 (standard 3D software conversion factor)
- LZ4 decompression for keyframe data
- Quaternion component reordering: File stores (X, Z, Y, W) → Output (X, Y, Z, W)

## Supported Features

- ✓ All bone animations (position, rotation, scale)
- ✓ AnimSet5 and AnimSet6 formats
- ✓ Animation events with custom strings
- ✓ Custom properties/metadata
- ✓ Proper quaternion normalization
- ✓ Full precision preservation

## Notes

- The converter produces byte-for-byte identical output to reference TXA files
- Round-trip conversions (ANM→TXA→ANM via Workbench) will have minor precision differences due to Workbench's re-compression (this is normal and imperceptible in animation playback)
- All 73 character bones are fully supported
- Frame data is preserved with full precision

## Credits

Reverse-engineered from DayZ Arma Reforger Tools using Ghidra decompilation.

## License

This tool is provided as-is for DayZ modding community use.
