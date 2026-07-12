import sys, pathlib
sys.path.insert(0,'p:/ANM-TXA')
from DayzAnimationToolsBinary.Types.Anm import Anm

def totals(p):
    anm=Anm.CreateFromFile(str(p))
    return sum(len(b.posKeys) for b in anm.bones), sum(len(b.rotKeys) for b in anm.bones), sum(len(b.scaleKeys) for b in anm.bones)

orig=pathlib.Path('examples/stand_alerted_original.anm')
gen =pathlib.Path('examples/stand_alerted.anm')
print('orig totals', totals(orig))
print('gen  totals', totals(gen))

anm1=Anm.CreateFromFile(str(orig))
anm2=Anm.CreateFromFile(str(gen))
diffs=[]
for b1,b2 in zip(anm1.bones, anm2.bones):
    dp=len(b2.posKeys)-len(b1.posKeys)
    dr=len(b2.rotKeys)-len(b1.rotKeys)
    ds=len(b2.scaleKeys)-len(b1.scaleKeys)
    if dp or dr or ds:
        diffs.append((b1.name,dp,dr,ds))
print('diff bones', len(diffs))
for name,dp,dr,ds in diffs[:12]:
    print(f'{name}: pos{dp:+}, rot{dr:+}, scale{ds:+}')
