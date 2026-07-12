with open('examples/stand_alerted.txa') as f:
    lines = f.readlines()
    
# Count frame entries
frame_count = sum(1 for line in lines if '$frame' in line)
print(f"Total $frame entries: {frame_count}")

# Show first 30 frame entries
frame_entries = [l for l in lines if '$frame' in l]
print("\nFirst 30 frame entries:")
for entry in frame_entries[:30]:
    print(entry.strip())
