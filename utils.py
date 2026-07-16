# -*- coding: utf-8 -*-
"""公共工具:事实序列化、哈希、字节大小计算。"""
import hashlib

SEP = "\x1f"  # 保留分隔符,防止字段拼接歧义


def serialize(fact) -> bytes:
    """事实(元组)的规范序列化。"""
    return SEP.join(str(x) for x in fact).encode("utf-8")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def int_bytes(x) -> int:
    """整数按实际占用字节计。"""
    x = int(x)
    if x < 0:
        x = -x
    return max(1, (x.bit_length() + 7) // 8)
