"""RSA accumulator (paper 3.2 + 5.2.1): Acc, membership / non-membership
witnesses, incremental update.

The platform holds no trapdoor, so every operation below is an honest
full-length modular exponentiation.
"""
import random
import gmpy2

MOD_BITS = 2048   # default (secure variant); efficiency variant uses 256 as in Wu2023


def setup(bits: int = MOD_BITS, seed: int = 42):
    """One-time setup, run by the auditor and never timed.

    Ordinary random primes instead of safe primes; see README deviation 1."""
    rs = random.Random(seed)
    half = bits // 2
    p = gmpy2.next_prime(rs.getrandbits(half) | (1 << (half - 1)) | 1)
    q = gmpy2.next_prime(rs.getrandbits(half) | (1 << (half - 1)) | 1)
    N = p * q
    a = gmpy2.mpz(rs.randrange(2, 1 << 64))
    g = gmpy2.powmod(a, 2, N)  # square into the quadratic residue subgroup
    return N, g


def tree_prod(xs):
    """Prime product by binary-tree multiplication (as in Wu2023)."""
    if not xs:
        return gmpy2.mpz(1)
    xs = list(xs)
    while len(xs) > 1:
        nxt = [xs[i] * xs[i + 1] for i in range(0, len(xs) - 1, 2)]
        if len(xs) % 2:
            nxt.append(xs[-1])
        xs = nxt
    return xs[0]


class RSAAccumulator:
    def __init__(self, N, g):
        self.N = N
        self.g = g
        self.E = gmpy2.mpz(1)   # product of all member primes, cached by the platform
        self.acc = g

    def build(self, primes):
        self.primes = list(primes)
        self.E = tree_prod(self.primes)
        self.acc = gmpy2.powmod(self.g, self.E, self.N)
        return self.acc

    def all_mem_witnesses(self):
        """Precompute every membership witness at once (RootFactor style).

        Split in half recursively: the left half's base is raised to the
        product of the right half, and vice versa. O(log n) full-length
        exponentiations total, milliseconds per witness amortized."""
        def rec(base, xs):
            if len(xs) == 1:
                return {xs[0]: base}
            mid = len(xs) // 2
            left, right = xs[:mid], xs[mid:]
            base_l = gmpy2.powmod(base, tree_prod(right), self.N)
            base_r = gmpy2.powmod(base, tree_prod(left), self.N)
            out = rec(base_l, left)
            out.update(rec(base_r, right))
            return out
        return rec(self.g, self.primes)

    def update(self, new_primes):
        """In-round append: Acc' = Acc^(prod new) mod N.

        Primality of appended elements is checked off-chain by the
        auditor/challenger, not here; see README deviation 2."""
        pr = tree_prod(new_primes)
        self.E *= pr
        self.acc = gmpy2.powmod(self.acc, pr, self.N)
        return self.acc

    # witness generation (platform side)
    def mem_witness(self, x):
        assert self.E % x == 0, "element not in accumulator"
        return gmpy2.powmod(self.g, self.E // x, self.N)

    def nonmem_witness(self, x):
        g0, a, b = gmpy2.gcdext(self.E, x)   # a*E + b*x = 1
        assert g0 == 1, "element unexpectedly divides E"
        B = gmpy2.powmod(self.g, b, self.N)
        return (a, B)

    # verification (verifier side, needs only public N, g, acc)
    def verify_mem(self, x, w, acc=None):
        acc = self.acc if acc is None else acc
        return gmpy2.powmod(w, x, self.N) == acc

    def verify_nonmem(self, x, wit, acc=None):
        acc = self.acc if acc is None else acc
        a, B = wit
        lhs = gmpy2.powmod(acc, a, self.N) * gmpy2.powmod(B, x, self.N) % self.N
        return lhs == self.g
