import struct
import sys
sys.path.insert(0, 'p:/ANM-TXA')
from DayzAnimationToolsBinary.Types.Anm import SCALE_FACTOR

# What we compute
mult_computed = 1.0 / SCALE_FACTOR
print(f"1.0 / SCALE_FACTOR = {mult_computed:.20e}")

# Pack to float32
packed = struct.pack('<f', mult_computed)
print(f"Packed bytes: {packed.hex()}")

# Unpack back
unpacked = struct.unpack('<f', packed)[0]
print(f"Unpacked: {unpacked:.20e}")

# When reader multiplies by SCALE_FACTOR
final = unpacked * SCALE_FACTOR
print(f"After * SCALE_FACTOR: {final:.20e}")

# What it should be
print(f"\nSCALE_FACTOR = {SCALE_FACTOR:.20e}")
