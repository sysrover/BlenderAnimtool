import pathlib
import sys
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from anm_to_txa import load_anm

def load(path: pathlib.Path):
    anm = load_anm(path)
    return anm

def main():
    p_new = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('example2/stand_alerted_from_txa.anm')
    p_orig = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path('example2/stand_alerted_original.anm')
    new = load(p_new)
    orig = load(p_orig)
    print(f"bones new/orig: {len(new.bones)}/{len(orig.bones)}")
    name_mismatches = []
    count_mismatches = []
    for idx, (bn, bo) in enumerate(zip(new.bones, orig.bones)):
        if bn.name != bo.name:
            name_mismatches.append((idx, bn.name, bo.name))
            continue
        cp = (len(bn.posKeys), len(bo.posKeys))
        cr = (len(bn.rotKeys), len(bo.rotKeys))
        cs = (len(bn.scaleKeys), len(bo.scaleKeys))
        if cp[0] != cp[1] or cr[0] != cr[1] or cs[0] != cs[1]:
            count_mismatches.append((idx, bn.name, cp, cr, cs))
    print(f"name mismatches: {len(name_mismatches)}")
    for m in name_mismatches[:15]:
        print(m)
    print(f"count mismatches: {len(count_mismatches)}")
    for m in count_mismatches[:20]:
        idx, name, cp, cr, cs = m
        print(f"{idx:02d} {name}: pos {cp[0]} vs {cp[1]} | rot {cr[0]} vs {cr[1]} | scale {cs[0]} vs {cs[1]}")

if __name__ == '__main__':
    main()
