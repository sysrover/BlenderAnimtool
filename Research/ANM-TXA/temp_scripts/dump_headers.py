import pathlib

orig = pathlib.Path('examples/stand_turn_ls_90_original.anm').read_bytes()
gen = pathlib.Path('examples/stand_turn_ls_90.anm').read_bytes()

print("Original first 80 bytes:")
print(orig[:80].hex())
print("\nGenerated first 80 bytes:")
print(gen[:80].hex())

print("\n\nOriginal first 80 (ASCII):")
print(' '.join(f"{b:02x}" for b in orig[:80]))
print("\nGenerated first 80 (ASCII):")
print(' '.join(f"{b:02x}" for b in gen[:80]))
