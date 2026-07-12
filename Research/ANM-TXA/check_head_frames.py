with open('example2/stand_attack_0_test.txa') as f:
    lines = f.readlines()
    in_head = False
    frame_numbers = []
    
    for i, line in enumerate(lines):
        if '"head"' in line and '$node' in line:
            in_head = True
        if not in_head:
            continue
        if line.strip() == '}' and i > 0 and 'head' in lines[i-20]:
            break
        if '$frame' in line:
            parts = line.strip().split()
            frame_numbers.append(int(parts[1]))
    
    print(f'Frame numbers in head node: {frame_numbers}')
    print(f'Total frames: {len(frame_numbers)}')
    print(f'Last frame: {max(frame_numbers) if frame_numbers else None}')
