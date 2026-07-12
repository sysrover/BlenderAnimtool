import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from DayzAnimationToolsBinary.Types.Anm import Anm


def load(path: pathlib.Path):
    try:
        anm = Anm.CreateFromFile(str(path))
        print(f"OK: {path} format {anm.format} fps {anm.fps} frames {anm.numFrames} bones {len(anm.bones)} events {len(anm.events)}")
        return True
    except Exception as e:
        print(f"FAIL: {path}: {e}")
        return False


def main():
    files = sys.argv[1:]
    if not files:
        files = ["examples/stand_turn_ls_90_original.anm", "examples/stand_turn_ls_90.anm"]
    for f in files:
        load(pathlib.Path(f).resolve())


if __name__ == "__main__":
    main()
