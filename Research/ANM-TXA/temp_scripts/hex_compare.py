import pathlib
import itertools

def main():
    p1 = pathlib.Path('example2/stand_alerted.anm')
    p2 = pathlib.Path('example2/stand_alerted_original.anm')
    a = p1.read_bytes()
    b = p2.read_bytes()
    print(f"len {p1.name}={len(a)}, len {p2.name}={len(b)}, delta={len(a)-len(b)}")
    mism = []
    for i, (ba, bb) in enumerate(itertools.zip_longest(a, b, fillvalue=None)):
        if ba != bb:
            mism.append((i, ba, bb))
            if len(mism) >= 40:
                break
    print(f"first {len(mism)} mismatches (offset, new, orig):")
    for off, ba, bb in mism:
        print(f"{off:08X}: {ba} {bb}")

    def dump(label: str, data: bytes, length: int = 64):
        print(label)
        for i in range(0, length, 16):
            chunk = data[i:i+16]
            hexs = ' '.join(f"{b:02X}" for b in chunk)
            print(f"{i:04X}: {hexs}")

    dump('head new', a)
    dump('head orig', b)

if __name__ == '__main__':
    main()
