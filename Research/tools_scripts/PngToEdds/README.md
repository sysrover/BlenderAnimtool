# PngToEdds

Small CLI writer for Enfusion-style `.edds` texture files.

The implementation is based on the DayZ Workbench texture writer path observed in
`workbenchApp.exe` and on real `.edds` files from `P:\`:

- file starts with a standard `DDS ` header
- DDS reserved header bytes at offset `0x24` contain the Enfusion marker `ENF1`
- raw GUI-style textures use 32-bit BGRA masks
- after the 128-byte DDS header there is a mip chunk table
- chunk table entries are `COPY` or `LZ4 ` plus payload size, ordered smallest mip to largest
- pixel payload follows the table in the same smallest-to-largest order
- mip generation follows Workbench's NVTT `Box` filter path and keeps the chain
  in float data until each mip is written as BGRA32
- LZ4 sub-block sizes use Workbench's end-of-stream marker: only the last
  sub-block in a mip payload has the high bit set
- EDDS readers rebuild normal DDS order by prepending decoded blocks

This version writes BGRA32 data. It emits `LZ4 ` chunks for mips where LZ4 is
smaller than raw `COPY`, otherwise it keeps the Workbench-compatible `COPY`
fallback. It does not yet emit DXT/BC compressed payloads.

## Usage

```powershell
dotnet run --project tools\PngToEdds\PngToEdds.csproj -- input.png output.edds
```

Single-file exe:

```powershell
tools\PngToEdds\single\PngToEdds.exe input.png output.edds
```

Disable mip generation:

```powershell
dotnet run --project tools\PngToEdds\PngToEdds.csproj -- input.png output.edds --no-mips
```

Build:

```powershell
dotnet build tools\PngToEdds\PngToEdds.csproj
```
