import pathlib, sys
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from txa_to_anm import parse_txa

def summarize(path):
    txa = parse_txa(path)
    pos = rot = scale = 0
    has_scale = 0
    has_pos = 0
    has_rot = 0
    for node in txa.nodes.values():
        pos += len(node.t)
        rot += len(node.q)
        scale += len(node.s)
        has_pos += 1 if node.t else 0
        has_rot += 1 if node.q else 0
        has_scale += 1 if node.s else 0
    return {
        'nodes': len(txa.nodes),
        'pos': pos,
        'rot': rot,
        'scale': scale,
        'nodes_pos': has_pos,
        'nodes_rot': has_rot,
        'nodes_scale': has_scale,
    }

def main():
    for label, path in [('generated', 'example2/stand_alerted_generated.txa'), ('original', 'example2/stand_alerted_original.txa')]:
        s = summarize(pathlib.Path(path))
        print(f"{label}: nodes={s['nodes']} posKeys={s['pos']} rotKeys={s['rot']} scaleKeys={s['scale']} nodes_with_scale={s['nodes_scale']}")

if __name__ == '__main__':
    main()
