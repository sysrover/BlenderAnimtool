import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from txa_to_anm import convert_txa_to_anm


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_one.py <input.txa> [output.anm]")
        sys.exit(1)
    inp = pathlib.Path(sys.argv[1]).resolve()
    if len(sys.argv) >= 3:
        outp = pathlib.Path(sys.argv[2]).resolve()
    else:
        outp = inp.with_suffix('.anm')
    convert_txa_to_anm(inp, outp)


if __name__ == "__main__":
    main()
