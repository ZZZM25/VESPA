"""Environment check: Python version, dependencies, data files."""
import sys
import hashlib
import time
from pathlib import Path

print("=" * 50)
print("Python version:", sys.version)
print("=" * 50)

# dependencies
for lib in ["gmpy2", "matplotlib", "numpy"]:
    try:
        m = __import__(lib)
        print(f"[OK]      {lib:12s} version {getattr(m, '__version__', '?')}")
    except ImportError:
        print(f"[MISSING] {lib:12s} -> pip install {lib}")

# quick sanity check, also exercises bignum arithmetic
h = hashlib.sha256(b"hello VESTA").hexdigest()
print("\nSHA256 test:", h[:16], "...")

try:
    import gmpy2
    t0 = time.perf_counter()
    p = gmpy2.next_prime(int(h, 16) >> 128)   # find a prime near a 128-bit value
    t1 = time.perf_counter()
    print(f"next_prime test: {p} ({(t1-t0)*1000:.2f} ms)")
except ImportError:
    pass

# data files
data = Path(__file__).parent / "gMission" / "data_00.txt"
if data.exists():
    lines = data.read_text().splitlines()
    print(f"\nData file OK: {data.name}, {len(lines)} lines")
    print("Header line:", lines[0])
    print("Sample line:", lines[1])
else:
    print(f"\n[MISSING] data file not found: {data}")

print("\nEnvironment check done.")
