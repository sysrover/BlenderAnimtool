import itertools
import pathlib
import struct
import sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from anm_to_txa import load_anm

def chunk_map(data: bytes):
    pos = 0
    chunks = []
    if data[:4] != b'FORM':
        return chunks
    form_size = struct.unpack('>I', data[4:8])[0]
    pos = 8
    if data[pos:pos+7] != b'ANIMSET':
        return chunks
    version = data[pos+7:pos+8]
    pos += 8
    anim_data_len = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4
    chunks.append(('FORM', form_size, version, anim_data_len, 0, 0))
    while pos + 8 <= len(data):
        tag = data[pos:pos+4]
        size = struct.unpack('>I', data[pos+4:pos+8])[0]
        start = pos + 8
        end = start + size
        chunks.append((tag.decode('ascii', errors='replace'), size, start, end))
        pos = end
    return chunks

def mismatch_ranges(a: bytes, b: bytes, limit: int = 10):
    ranges = []
    i = 0
    max_len = max(len(a), len(b))
    while i < max_len and len(ranges) < limit:
        ba = a[i] if i < len(a) else None
        bb = b[i] if i < len(b) else None
        if ba == bb:
            i += 1
            continue
        start = i
        vals = []
        while i < max_len:
            ba = a[i] if i < len(a) else None
            bb = b[i] if i < len(b) else None
            if ba == bb:
                break
            vals.append((ba, bb))
            i += 1
        end = i
        ranges.append((start, end - 1, end - start))
    return ranges

def summarize_anm(path: pathlib.Path):
    anm = load_anm(path)
    pos = sum(len(b.posKeys) for b in anm.bones)
    rot = sum(len(b.rotKeys) for b in anm.bones)
    scale = sum(len(b.scaleKeys) for b in anm.bones)
    return {
        'bones': len(anm.bones),
        'pos': pos,
        'rot': rot,
        'scale': scale,
    }

def main():
    p_new = pathlib.Path('example2/stand_alerted.anm')
    p_orig = pathlib.Path('example2/stand_alerted_original.anm')
    a = p_new.read_bytes()
    b = p_orig.read_bytes()
    print(f"len new={len(a)}, len orig={len(b)}, delta={len(a)-len(b)}")

    # Chunk maps
    c_new = chunk_map(a)
    c_orig = chunk_map(b)
    print('\nChunks (new):')
    for c in c_new[:6]:
        print(c)
    print('...')
    print('Chunks (orig):')
    for c in c_orig[:6]:
        print(c)
    print('...')

    # Head vs data sizes if available
    def find_chunk(chunks, name):
        for c in chunks:
            if c[0] == name:
                return c
        return None
    head_new = find_chunk(c_new, 'HEAD')
    head_orig = find_chunk(c_orig, 'HEAD')
    data_new = find_chunk(c_new, 'DATA')
    data_orig = find_chunk(c_orig, 'DATA')
    print('\nHEAD size new/orig:', head_new[1] if head_new else None, head_orig[1] if head_orig else None)
    print('DATA size new/orig:', data_new[1] if data_new else None, data_orig[1] if data_orig else None)

    # Mismatch ranges
    ranges = mismatch_ranges(a, b, limit=10)
    print('\nFirst mismatch ranges (start-end, len):')
    for r in ranges:
        print(r)

    # ANM summaries
    s_new = summarize_anm(p_new)
    s_orig = summarize_anm(p_orig)
    print('\nANM key totals:')
    print('new ', s_new)
    print('orig', s_orig)

if __name__ == '__main__':
    main()
