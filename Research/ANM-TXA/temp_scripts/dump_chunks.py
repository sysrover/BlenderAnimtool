import struct
import sys
import pathlib


def read_u32_be(data, offset):
    return struct.unpack_from('>I', data, offset)[0]

def read_u16_le(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def main(path):
    data = pathlib.Path(path).read_bytes()
    pos = 0
    print(f"file: {path} size={len(data)}")
    if data[:4] != b'FORM':
        print("not FORM")
        return
    form_size = read_u32_be(data, 4)
    print(f"FORM size field={form_size} actual={len(data)-8}")
    pos = 8
    print(f"magic: {data[pos:pos+7]}")
    pos += 7
    format_char = data[pos]
    print(f"format char={format_char} ({chr(format_char)})")
    pos += 1
    anim_data_len = read_u32_be(data, pos)
    pos += 4
    print(f"anim_data_len={anim_data_len}")
    const_block = data[pos:pos+8]
    pos += 8
    fps = struct.unpack_from('<i', data, pos)[0]
    pos += 4
    print(f"const_block={const_block} fps={fps}")
    # HEAD
    head_magic = data[pos:pos+4]
    head_size = read_u32_be(data, pos+4)
    print(f"HEAD magic={head_magic} size={head_size}")
    pos += 8
    head_start = pos
    pos = head_start + head_size
    # DATA
    data_magic = data[pos:pos+4]
    data_size = read_u32_be(data, pos+4)
    print(f"DATA magic={data_magic} size={data_size}")
    pos += 8 + data_size
    # Next chunk
    while pos < len(data):
        chunk_magic = data[pos:pos+4]
        if len(chunk_magic) < 4:
            break
        chunk_size = read_u32_be(data, pos+4)
        print(f"Chunk {chunk_magic.decode(errors='ignore')} size={chunk_size}")
        pos += 8 + chunk_size


if __name__ == '__main__':
    paths = sys.argv[1:] or ["examples/stand_turn_ls_90_original.anm", "examples/stand_turn_ls_90.anm"]
    for p in paths:
        main(p)
        print()
