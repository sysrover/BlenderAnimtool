import pathlib, sys
from collections import Counter
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

def main():
    txa = parse_txa(pathlib.Path('example2/stand_alerted_original.txa'))
    for bone in ['leftindex', 'leftarm', 'leftforearm']:
        node = txa.nodes[bone]
        uniq_rot = len(set(node.q.values()))
        uniq_pos = len(set(node.t.values()))
        uniq_scale = len(set(node.s.values()))
        print(f"bone {bone}: frames t={len(node.t)} q={len(node.q)} s={len(node.s)} unique t={uniq_pos} q={uniq_rot} s={uniq_scale}")

if __name__ == '__main__':
    main()
