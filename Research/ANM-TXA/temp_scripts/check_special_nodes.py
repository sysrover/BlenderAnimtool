#!/usr/bin/env python3
with open('example2/stand_attack_0.txa') as f:
    content = f.read()
    
# Find pin_lookat section
start = content.find('pin_lookat')
if start > 0:
    next_node = content.find('$node', start+1)
    sec = content[start:next_node if next_node > 0 else len(content)]
    lines = sec.split('\n')[:50]
    print('=== pin_lookat ===')
    for line in lines:
        if line.strip():
            print(line)

# Find entityposition
start = content.find('entityposition')
if start > 0:
    next_idx = content.find('$animation', start+1) if 'entityposition' in content[start:] else len(content)
    sec = content[start:next_idx if next_idx > 0 else len(content)]
    lines = sec.split('\n')[:50]
    print('\n=== entityposition ===')
    for line in lines:
        if line.strip():
            print(line)
