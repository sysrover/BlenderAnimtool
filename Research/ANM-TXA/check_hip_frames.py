import re

with open('examples/stand_walk_fwd.txa', 'r') as f:
    content = f.read()

# Find hip node section
hip_start = content.find('$node "hip"')
hip_end = content.find('$node ', hip_start + 10)
hip_section = content[hip_start:hip_end]

# Find frame declarations
ranges = re.findall(r'\$frame (\d+) (\d+)', hip_section)
singles = re.findall(r'\$frame (\d+) \{', hip_section)

print("Ranges (frame start end):", ranges[:10])
print("Single frames (first 20):", sorted(map(int, singles))[:20])
print("Total single frame declarations:", len(singles))
print("Range total frames:", sum(int(e) - int(s) + 1 for s, e in ranges))
