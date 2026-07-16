"""Fact -> prime representative (paper 5.2.1).

Canonical serialization -> SHA-256 -> truncate to 128 bits -> smallest
prime not less than that integer.
"""
import gmpy2
from utils import serialize, sha256

PRIME_BITS = 128


def prime_rep(fact):
    h = sha256(serialize(fact))
    x = int.from_bytes(h[: PRIME_BITS // 8], "big")
    # 5.2.1 asks for the smallest prime >= x, so keep x itself if prime
    if gmpy2.is_prime(x):
        return gmpy2.mpz(x)
    return gmpy2.next_prime(x)
