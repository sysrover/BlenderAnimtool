import bpy, json, sys
out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else r'C:\Users\sysro\diag\CsharpModVScode\anm\blender-loaded-skeleton-dump.json'
data = {'file': bpy.data.filepath, 'armatures': []}
for obj in bpy.data.objects:
    if obj.type != 'ARMATURE':
        continue
    arm = obj.data
    bones = []
    for b in arm.bones:
        bones.append({
            'name': b.name,
            'parent': b.parent.name if b.parent else None,
            'head_local': list(b.head_local),
            'tail_local': list(b.tail_local),
            'use_connect': bool(b.use_connect),
        })
    pose_bones = []
    for pb in obj.pose.bones:
        pose_bones.append({
            'name': pb.name,
            'rotation_mode': pb.rotation_mode,
            'constraints': [{'name': c.name, 'type': c.type, 'target': c.target.name if getattr(c, 'target', None) else None, 'subtarget': getattr(c, 'subtarget', '')} for c in pb.constraints],
        })
    data['armatures'].append({
        'object': obj.name,
        'data': arm.name,
        'matrix_world': [list(row) for row in obj.matrix_world],
        'bone_count': len(bones),
        'bones': bones,
        'pose_bones': pose_bones,
    })
with open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print('DUMPED_SKELETON_JSON', out, 'armatures', len(data['armatures']))
