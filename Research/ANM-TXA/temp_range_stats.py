import re, pathlib
text=pathlib.Path('examples/stand_alerted.txa').read_text()
frames=[line.strip() for line in text.splitlines() if line.strip().startswith('$frame')]
with_ranges=[f for f in frames if re.search(r'\$frame\s+\d+\s+\d+', f)]
print('total frame entries', len(frames))
print('range entries', len(with_ranges))
from collections import Counter
rng_lengths=[]
for f in with_ranges:
    parts=f.split()
    if len(parts)>=3 and parts[2].isdigit():
        rng_lengths.append(int(parts[2])-int(parts[1])+1)
if rng_lengths:
    print('range length stats: count', len(rng_lengths), 'min', min(rng_lengths), 'max', max(rng_lengths))
    print('top lengths', Counter(rng_lengths).most_common(5))
