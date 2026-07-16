"""VESTA scheme adapter with the common interface used by all experiments:
build / update / gen_mem / gen_nonmem / verify / vo_size.

VO = (z, pi, wit, payload, meta), the five-tuple of Definition (VO) in 5.2.2.
"""
from utils import serialize, int_bytes
from vesta.prime import prime_rep
from vesta.accumulator import RSAAccumulator, setup

# One-time setups (fixed seed, never timed).
# 256-bit modulus: efficiency variant, matches Wu2023, not cryptographically secure.
# 2048-bit modulus: secure variant under the strong RSA assumption.
_PARAMS = {256: setup(256), 2048: setup(2048)}


class Vesta:
    def __init__(self, bits=2048):
        self.bits = bits
        N, g = _PARAMS[bits]
        self.acc = RSAAccumulator(N, g)
        self.name = f"VESTA-{bits}"

    def build(self, facts):
        primes = [prime_rep(f) for f in facts]
        self.acc.build(primes)

    def update(self, new_facts):
        primes = [prime_rep(f) for f in new_facts]
        self.acc.update(primes)

    # Element-level proofs with payload=None; a request-level `done` answer
    # composes two of these plus a 64B signature (README deviation 3).
    def gen_mem(self, fact):
        x = prime_rep(fact)
        w = self.acc.mem_witness(x)
        return {"z": fact, "pi": "mem", "wit": w, "payload": None,
                "meta": {"round": 1}}

    def gen_nonmem(self, fact):
        x = prime_rep(fact)
        wit = self.acc.nonmem_witness(x)
        return {"z": fact, "pi": "nonmem", "wit": wit, "payload": None,
                "meta": {"round": 1}}

    def batch_mem_witnesses(self):
        return self.acc.all_mem_witnesses()

    def ads_bytes(self):
        n = len(self.acc.primes)
        e_bytes = (self.acc.E.bit_length() + 7) // 8
        acc_bytes = (self.acc.N.bit_length() + 7) // 8   # one group element = modulus size
        return n * 16 + e_bytes + acc_bytes   # prime table + cached exponent + Acc

    def verify(self, vo):
        x = prime_rep(vo["z"])
        if vo["pi"] == "mem":
            return self.acc.verify_mem(x, vo["wit"])
        return self.acc.verify_nonmem(x, vo["wit"])

    def vo_size(self, vo):
        size = len(serialize(vo["z"])) + 1 + 8  # z + proof-type flag + meta (round id)
        if vo.get("payload"):
            size += len(vo["payload"])
        if vo["pi"] == "mem":
            size += int_bytes(vo["wit"])         # one group element (~256B)
        else:
            a, B = vo["wit"]
            size += int_bytes(a) + int_bytes(B)  # Bezout coefficient + group element
        return size
