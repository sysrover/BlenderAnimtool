# DayZ IK1H workflow completion evidence — 2026-07-11

## Live Blender 4.5 evidence

Checked through `blender-remote`, not inferred from files:

```text
Blender: 4.5.11 LTS
Blend: P:\Animation_Weapon\saved\Weapon_template_dayz_clean_pose.blend
Active IK action: apple
Remembered base action: p_1hd_erc_idle_low
Controls: CTRL_RightHand, CTRL_RightElbow
Proxy: MCH_RightArm_IK, MCH_RightForeArm_IK, MCH_RightHand_IK
IK chain count: 2
IK stretch: false
Effector: CTRL_RightHand
Pole: CTRL_RightElbow
Build operator registered: true
Bake operator registered and pollable: true
ANM export operator registered: true
Visible control-rig bones: CTRL_RightHand, CTRL_RightElbow
```

During a live edit, the wrist control was moved by `(0.16, 0.0, 0.08)` metres
in control-rig space. The evaluated DayZ wrist followed by
`(0.15999994, 0.0, 0.07999969)` metres. Proxy-to-DayZ errors were:

```text
wrist:  2.81155e-7 m
elbow:  3.87430e-7 m
```

The live controls were restored after the capture.

### Roll and wrist-orientation checks

The corpus test was extended to inspect the evaluated original DayZ bones, not
only the proxy. On `apple`, a 0.03 m hand-target edit produced world-orientation
changes of `0.0804074 rad` on `RightArmRoll` and `0.0768776 rad` on
`RightForeArmRoll`, proving that the visible roll hierarchy follows the solved
chain. Their scale errors remained `2.06477e-7` and `3.57628e-7` respectively,
so the roll hierarchy does not stretch.

A 15 degree (`0.261799 rad`) wrist-control rotation produced
`0.261799 rad` on the evaluated original `RightHand`, with zero
proxy-to-DayZ angular error and zero wrist-position drift. The disabled
right-arm FK constraints remain available for FK authoring but have influence
`0.0` in IK mode; they do not override the Python-synchronized result.

Screenshots:

- initial clean authoring pose:
  `P:\BlenderAnimtool\Research\anm_reports\screenshots\ik1h-apple-controls-clean-20260711.png`
- visibly edited pose:
  `P:\BlenderAnimtool\Research\anm_reports\screenshots\ik1h-apple-controls-edited-20260711.png`

## Automated Blender 4.5 corpus

Fresh background runs used the installed Blender 4.5 add-ons and the real
template blend. All six files passed import, base-action capture, control build,
hand movement, hand rotation, elbow movement, fixed-length checks, bake, IK1H
export, reimport and numeric re-export comparison.

| IK | Initial pose error (m) | Hand target error (m) | Max length error (m) | Elbow wrist drift (m) | Rotation wrist drift (m) | Round-trip max error | Missing tracks |
|---|---:|---:|---:|---:|---:|---:|---|
| 9v_battery | 3.42717e-5 | 3.72529e-8 | 1.20831e-7 | 0 | 0 | 2.89437e-4 | none |
| apple | 3.42422e-5 | 6.00685e-8 | 6.50320e-8 | 0 | 0 | 1.95425e-5 | none |
| banana | 3.42032e-5 | 1.49012e-8 | 4.29532e-8 | 0 | 0 | 3.02896e-4 | none |
| bark_oak | 3.42791e-5 | 3.07195e-8 | 1.41304e-7 | 0 | 0 | 2.50910e-5 | none |
| book | 3.43477e-5 | 5.96046e-8 | 6.50320e-8 | 0 | 0 | 3.70714e-4 | none |
| candle | 3.40790e-5 | 6.36578e-8 | 2.93045e-8 | 0 | 0 | 3.31388e-4 | none |

Authoritative JSON reports:
`P:\BlenderAnimtool\Research\anm_reports\ik1h-corpus-20260711`

Test implementation:
`C:\Users\sysro\diag\CsharpModVScode\tools\test_dayz_ik1h_proxy_workflow.py`

The source and installed Blender 4.5 copies of `AddSurvivorIK.py` were compared
after the final visibility change and are byte-identical (SHA-256
`4D17E76D5D1E9AC703E59009F8E85942C040308205A104A44A01FC87DF2CD625`).
The source/installed importer, exporter and registration module are likewise
byte-identical. Both add-on copies pass `py_compile`.

## Runtime semantics evidence

Ghidra evidence and the reconstructed target-composition formula are stored in:

- `P:\BlenderAnimtool\Research\anm_reports\ghidra-raw-ik1h-offset-verification-20260711.txt`
- `P:\BlenderAnimtool\Research\anm_reports\dayz-ik1h-hybrid-proxy-workflow.md`

The evidence confirms that `RightHandOrigin` and the forearm-direction values
are offsets composed through the already evaluated base-pose chain end, not
absolute Blender world-space targets.
