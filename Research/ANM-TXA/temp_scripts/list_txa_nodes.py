import pathlib
import sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

def dump(path: pathlib.Path, label: str):
    txa = parse_txa(path)
    print(f"{label} ({len(txa.nodes)} nodes) first 20:")
    for name in list(txa.nodes.keys())[:20]:
        print(" ", name)


def main():
    dump(pathlib.Path('example2/stand_alerted_generated.txa'), 'generated')
    dump(pathlib.Path('example2/stand_alerted_original.txa'), 'original')

if __name__ == '__main__':
    main()
