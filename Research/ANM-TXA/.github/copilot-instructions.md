# Copilot Instructions
IPMPORTANT!!!!! NEVER USE TERMINAL FOR DIRECT PYTHON CODE, ALWAYS MAKE TEMP SCRIPT IN TEMP FOLDER AND EXECUTE IN TERMNMINAL
IMPORTANT !!!!! - **Stand_alerted workflow (important)**: Always generate `examples/stand_alerted.anm` from `examples/stand_alerted.txa` by P:\ANM-TXA\txa_to_anm.py , validate with Mikero `deanm -P -L `, hex-compare against `examples/stand_alerted_original.anm`, and adjust `txa_to_anm.py` to match the original.

- **Project scope**: Converts DayZ binary ANM animations to text TXA. Two entrypoints: CLI [anm_to_txa.py](../anm_to_txa.py) and drag/drop [anm_to_txa_dragdrop.py](../anm_to_txa_dragdrop.py); logic is identical.
- **Core flow**: Load ANM via shipped binary reader [DayzAnimationToolsBinary/Types/Anm.py](../DayzAnimationToolsBinary/Types/Anm.py) (uses [BinaryReader.py](../DayzAnimationToolsBinary/Utils/BinaryReader.py) and [Lz4Decoder.py](../DayzAnimationToolsBinary/Utils/Lz4Decoder.py)), then serialize to TXA in `_write_txa`.
- **Axis/ordering quirks**: Position and rotation keys swap Y/Z when writing to TXA. Rotations reorder to `x y z w` but source stores `x z y w`; positions write `x z y`. Preserve this swap if adding code.
- **Float formatting**: Use `_fmt_precise` (9 decimals, trims trailing zeros, normalizes -0) via `FVector.__str__` and `FQuaternion.__str__` to avoid importer snapping; keep it for new outputs.
- **Interpolation rules**: `_interpolate_value` lerps vectors and slerps quaternions only when a channel is dynamic (has keys beyond frame 0/max). Static channels emit only keyed frames; dynamic channels are sampled across all frames.
- **Frame collapsing**: Frames with identical (pos, rot, scale) are collapsed into `$frame start end` ranges. Maintain equality semantics of `FVector`/`FQuaternion` when changing data structures.
- **Frame bounds**: `_frame_bounds` inspects all keys and events to set `numFrames`; events extend range.
- **Events/custom props**: Events and custom properties are passed through verbatim; custom props are quoted key/value pairs in `$custProps`.
- **Formats supported**: AnimSet5/6; AnimSet6 adds scale keys. Scaling uses per-bone bias/multiplier; remember SCALE_FACTOR adjustments in [Anm.py](../DayzAnimationToolsBinary/Types/Anm.py).
- **Usage**: `python anm_to_txa.py input.anm [output.txa]`; default output is sibling with `.txa`. Drag/drop version auto-writes beside each input.
- **Samples**: Reference inputs/outputs in [examples](../examples) for expected TXA layout and naming.
- **Build (PyInstaller)**: Use [ANM_to_TXA_Converter.spec](../ANM_to_TXA_Converter.spec); run `pyinstaller ANM_to_TXA_Converter.spec` to produce console exe. Data folder `DayzAnimationToolsBinary` must be bundled (already specified in spec).
- **Dependencies**: Standard library only; no external pip packages. Target Python 3.6+.
- **Testing**: No formal tests; sanity-check by converting sample ANMs and diffing TXA against known outputs. [test_parser.py](../test_parser.py) is legacy and depends on an external Blender addon path.
- **Windows focus**: Drag/drop BAT and packaging assume Windows paths; keep scripts path-safe for Windows.
- **When extending**: Match existing string formatting and channel ordering; avoid changing TXA schema. If adding new data, keep `$animation`/`$node` indentation and quoting patterns.

