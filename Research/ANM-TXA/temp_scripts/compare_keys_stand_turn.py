import pathlib
import sys

sys.path.insert(0, 'p:/ANM-TXA')
from DayzAnimationToolsBinary.Types.Anm import Anm


def load(path: pathlib.Path):
    return Anm.CreateFromFile(str(path))


def main():
    orig_path = pathlib.Path('examples/stand_turn_ls_90_original.anm')
    gen_path = pathlib.Path('examples/stand_turn_ls_90.anm')
    orig = load(orig_path)
    gen = load(gen_path)

    diffs = []
    for b1, b2 in zip(orig.bones, gen.bones):
        dp = len(b2.posKeys) - len(b1.posKeys)
        dr = len(b2.rotKeys) - len(b1.rotKeys)
        ds = len(b2.scaleKeys) - len(b1.scaleKeys)
        if dp or dr or ds:
            diffs.append((b1.name, dp, dr, ds))

    print(f"Total bones: {len(orig.bones)}")
    print(f"Diff bones: {len(diffs)}")
    for name, dp, dr, ds in diffs:
        print(f"{name}: pos {dp:+}, rot {dr:+}, scale {ds:+}")

    orig_totals = (sum(len(b.posKeys) for b in orig.bones),
                   sum(len(b.rotKeys) for b in orig.bones),
                   sum(len(b.scaleKeys) for b in orig.bones))
    gen_totals = (sum(len(b.posKeys) for b in gen.bones),
                  sum(len(b.rotKeys) for b in gen.bones),
                  sum(len(b.scaleKeys) for b in gen.bones))
    print("orig totals pos/rot/scale", orig_totals)
    print("gen  totals pos/rot/scale", gen_totals)


if __name__ == '__main__':
    main()
