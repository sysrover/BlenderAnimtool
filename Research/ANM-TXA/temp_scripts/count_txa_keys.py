#!/usr/bin/env python3
from pathlib import Path
import re

txa_path = Path('example2/stand_attack_0.txa')
content = txa_path.read_text(encoding='utf-8')

# Count keys per bone
lines = content.split('\n')
current_bone = None
bone_keys = {}

for line in lines:
    if '$node' in line:
        match = re.search(r'\$node "([^"]+)"', line)
        if match:
            current_bone = match.group(1)
            bone_keys[current_bone] = {'t': 0, 'q': 0, 's': 0}
    elif current_bone and '#t ' in line:
        bone_keys[current_bone]['t'] += 1
    elif current_bone and '#q ' in line:
        bone_keys[current_bone]['q'] += 1
    elif current_bone and '#s ' in line:
        bone_keys[current_bone]['s'] += 1

print('TXA Key Counts (first 10 bones):')
for i, (name, keys) in enumerate(list(bone_keys.items())[:10]):
    print(f'{i}: {name:20s} | t={keys["t"]:4d} q={keys["q"]:4d} s={keys["s"]:4d}')

total_t = sum(k['t'] for k in bone_keys.values())
total_q = sum(k['q'] for k in bone_keys.values())
total_s = sum(k['s'] for k in bone_keys.values())
print(f'Total: t={total_t}, q={total_q}, s={total_s}')
