with open('example2/stand_attack_0_test.txa') as f:
    lines = f.readlines()
    in_head = False
    count = 0
    for i, line in enumerate(lines):
        if '"head"' in line and '$node' in line:
            in_head = True
        if in_head:
            print(f'{i}: {line.rstrip()}')
            count += 1
            if count > 50:
                break
