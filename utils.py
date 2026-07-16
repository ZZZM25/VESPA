"""Shared helpers: fact serialization, hashing, byte-size accounting."""
import hashlib

SEP = "\x1f"  # unit separator, avoids ambiguity when joining fields


def serialize(fact) -> bytes:
    return SEP.join(str(x) for x in fact).encode("utf-8")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def int_bytes(x) -> int:
    x = int(x)
    if x < 0:
        x = -x
    return max(1, (x.bit_length() + 7) // 8)
