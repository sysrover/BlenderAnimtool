import sys
import pathlib

sys.path.insert(0, 'p:/ANM-TXA')
from DayzAnimationToolsBinary.Types.Anm import Anm


def load(path: str):
    return Anm.CreateFromFile(path)


def find_bone(anm, name: str):
    return next((b for b in anm.bones if b.name == name), None)


def summarize(bone):
    return {
        'pos_count': len(bone.posKeys),
        'rot_count': len(bone.rotKeys),
        'scale_count': len(bone.scaleKeys),
        'pos_frames': [k.frame for k in bone.posKeys],
        'rot_frames': [k.frame for k in bone.rotKeys],
        'scale_frames': [k.frame for k in bone.scaleKeys],
    }


def main():
    orig = load('examples/stand_alerted_original.anm')
    gen = load('examples/stand_alerted.anm')
    name = 'tail'
    b_orig = find_bone(orig, name)
    b_gen = find_bone(gen, name)

    if not b_orig or not b_gen:
        print('Bone not found in one of the files')
        return

    s_orig = summarize(b_orig)
    s_gen = summarize(b_gen)

    print('Bone:', name)
    print('Original:', s_orig)
    print('Generated:', s_gen)


if __name__ == '__main__':
    main()
