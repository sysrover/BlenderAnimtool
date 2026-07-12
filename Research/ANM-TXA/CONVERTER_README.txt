# ANM to TXA Converter - Silent Conversion Edition

## How to Use

### Easiest Method - Drag & Drop
1. **Drag your .anm files directly onto** `Drag_ANM_Here.bat`
2. The conversion runs silently in the background
3. See the conversion summary when done
4. The .txa file appears in the same folder as your .anm file

### Alternative - Command Line
```cmd
ANM_to_TXA_Converter.exe animation.anm
```

## Features
✓ Drag-and-drop conversion
✓ Silent operation (no popup windows)
✓ Batch processing (convert multiple files at once)
✓ Console output showing progress
✓ Quaternion interpolation (SLERP)
✓ Smart frame range detection
✓ Standalone executable

## What It Does
- Converts DayZ binary `.anm` animation files to text `.txa` format
- Automatically names output based on input (e.g., `animation.anm` → `animation.txa`)
- Handles position, rotation, and scale keyframe interpolation
- Preserves animation metadata (events, custom properties)

## File Structure
```
anm_to_txa/
├── dist/
│   └── ANM_to_TXA_Converter.exe    (The executable)
├── Drag_ANM_Here.bat                (Use this for drag-and-drop!)
├── anm_to_txa.py                    (Original CLI version)
├── DayzAnimationToolsBinary/        (ANM reader library)
└── examples/                        (Sample ANM files)
```

## Output
When you run a conversion, you'll see:
```
✓ Converted: animation.anm → animation.txa
```

If there's an error:
```
✗ Error converting animation.anm: [error details]
```

## Requirements
- Windows 7 or later
- No Python installation needed (standalone executable)
