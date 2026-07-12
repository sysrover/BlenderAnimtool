import sys
sys.path.insert(0, r'C:\Users\sysro\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons')

from DayzAnimationTools.Types.Txa import Txa, TxaImportSettings

try:
    txa = Txa.CreateFromFile(r'c:\Users\sysro\anm_to_txa\examples\p_erc_fire_ump45_ras.txa', TxaImportSettings())
    print("SUCCESS: File parsed correctly!")
    print(f"Animations: {len(txa.animations)}")
    for name, anim in txa.animations.items():
        print(f"  {name}: {anim.numFrames} frames, {len(anim.rootBones)} root bones")
except AssertionError as e:
    print(f"ASSERTION FAILED at line: {sys.exc_info()[2].tb_lineno}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
