# -*- coding: utf-8 -*-
"""环境测试脚本:检查 Python 版本、依赖库、数据文件是否就绪。"""
import sys
import hashlib
import time
from pathlib import Path

print("=" * 50)
print("Python 版本:", sys.version)
print("=" * 50)

# 1. 检查依赖库
for lib in ["gmpy2", "matplotlib", "numpy"]:
    try:
        m = __import__(lib)
        print(f"[OK]   {lib:12s} 版本 {getattr(m, '__version__', '?')}")
    except ImportError:
        print(f"[缺失] {lib:12s} -> pip install {lib}")

# 2. 简单算一下(顺便测大数运算)
h = hashlib.sha256(b"hello VESTA").hexdigest()
print("\nSHA256 测试:", h[:16], "...")

try:
    import gmpy2
    t0 = time.perf_counter()
    p = gmpy2.next_prime(int(h, 16) >> 128)   # 取128位找素数
    t1 = time.perf_counter()
    print(f"next_prime 测试: {p} ({(t1-t0)*1000:.2f} ms)")
except ImportError:
    pass

# 3. 检查数据文件
data = Path(__file__).parent / "gMission" / "data_00.txt"
if data.exists():
    lines = data.read_text().splitlines()
    print(f"\n数据文件 OK: {data.name},共 {len(lines)} 行")
    print("首行(头部):", lines[0])
    print("第二行(样例):", lines[1])
else:
    print(f"\n[缺失] 数据文件未找到: {data}")

print("\n环境测试完成。")
