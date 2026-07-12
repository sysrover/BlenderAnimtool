import pathlib
import sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from anm_to_txa import load_anm

def summarize(path):
    anm = load_anm(path)
    pos = rot = scale = 0
    per_bone = []
    for b in anm.bones:
        pos += len(b.posKeys)
        rot += len(b.rotKeys)
        scale += len(b.scaleKeys)
        per_bone.append((b.name, len(b.posKeys), len(b.rotKeys), len(b.scaleKeys)))
    return {'anm': anm, 'counts': (pos, rot, scale), 'bones': per_bone}

def compare(label, a_new: pathlib.Path, a_orig: pathlib.Path):
    res_new = summarize(a_new)
    res_orig = summarize(a_orig)
    print(f"[{label}] new: pos={res_new['counts'][0]}, rot={res_new['counts'][1]}, scale={res_new['counts'][2]}")
    print(f"[{label}] orig: pos={res_orig['counts'][0]}, rot={res_orig['counts'][1]}, scale={res_orig['counts'][2]}")
    print("first 15 bone names (orig vs new):")
    for (n1, *_), (n2, *_) in zip(res_orig['bones'][:15], res_new['bones'][:15]):
        print(f"  {n1}  |  {n2}")
    def find(name, bones):
        for idx, (bn, *_rest) in enumerate(bones):
            if bn == name:
                return idx
        return -1
    print("indexes: entityposition -> orig", find('entityposition', res_orig['bones']), "new", find('entityposition', res_new['bones']))
    mism = []
    for (n1, p1, r1, s1), (n2, p2, r2, s2) in zip(res_orig['bones'], res_new['bones']):
        if n1 != n2:
            mism.append((n1, n2, 'name'))
            continue
        if p1 != p2 or r1 != r2 or s1 != s2:
            mism.append((n1, p1, p2, r1, r2, s1, s2))
    print(f"bone mismatches: {len(mism)}")
    for row in mism[:15]:
        print(row)


def main():
    compare('generated_txa->anm', pathlib.Path('example2/stand_alerted.anm'), pathlib.Path('example2/stand_alerted_original.anm'))
    print('\n---\n')
    compare('orig_txa->anm', pathlib.Path('example2/stand_alerted_from_txa.anm'), pathlib.Path('example2/stand_alerted_original.anm'))

if __name__ == '__main__':
    main()
