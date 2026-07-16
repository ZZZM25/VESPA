"""Simulation layer: plays the platform, turning the gMission event stream
into one round's fact stream (untimed).

Fact types (one-to-one with paper Chapter 5):
  ("Task", tid, rid, com_l, r, e, d)      publication record (5.1)
  ("TaskKey", tid)                         publication record (5.1)
  ("TaskCount", k, n_k)                    end-of-round count (5.1)
  ("Priority", wid, pb)                    round-start snapshot (5.2.1)
  ("Load", wid, cb)                        round-start snapshot (5.2.1)
  ("Eligible", tid, wid)                   assignment fact (5.2.1)
  ("Assign", tid, wid)                     assignment fact (5.2.1)
  ("Done", tid, wid, h_sig)                completion fact (5.3.1)
  ("DoneKey", tid, wid)                    completion fact (5.3.1)
"""
import math
import random
import hashlib

from sim.loader import load_stream, TaskEvent, WorkerEvent

# bucket boundaries (public system parameters, m_P = m_L = 5)
PRIORITY_BOUNDS = [7200, 3600, 1800, 600]   # seconds; waiting >= 7200s -> bucket 1 (highest)
LOAD_CAP = 4                                 # load 0/1/2/3/>=4 -> buckets 1..5


def beta_p(waiting: float) -> int:
    for i, b in enumerate(PRIORITY_BOUNDS):
        if waiting >= b:
            return i + 1
    return 5


def beta_l(load: int) -> int:
    return min(load, LOAD_CAP) + 1


class _Worker:
    __slots__ = ("wid", "x", "y", "cap", "radius", "online_from", "online_to",
                 "success", "load", "last_assign")

    def __init__(self, wid, ev: WorkerEvent):
        self.wid = wid
        self.x, self.y = ev.x, ev.y
        self.cap = ev.cap
        self.radius = ev.radius
        self.online_from = ev.arrival
        self.online_to = ev.arrival + ev.dur
        self.success = ev.success
        self.load = 0           # assigned-but-unfinished count (c_w in 5.2.1)
        self.last_assign = None  # time of last assignment (basis of priority p_w)

WARMUP_FRAC = 0.1  # first 10% of events form "historical rounds" that build up real load/waiting


def _try_assign(t: TaskEvent, pool, rng, e_ddl):
    """Eligibility predicate + greedy pick; returns (candidates, chosen worker or None, done?)."""
    cands = []
    for w in pool:
        if w.online_from <= e_ddl and w.online_to >= t.arrival:
            if math.hypot(w.x - t.x, w.y - t.y) <= w.radius:
                cands.append(w)
    avail = [w for w in cands if w.load < w.cap]
    if not avail:
        return cands, None, False
    w_star = min(avail, key=lambda w: math.hypot(w.x - t.x, w.y - t.y))
    done = rng.random() < w_star.success
    return cands, w_star, done


def generate_round(target_n: int, start_file: int, k: int = 1, seed: int = 42,
                   dataset: str = "gMission"):
    """Generate one settlement round with exactly target_n facts.

    The first WARMUP_FRAC of events are replayed silently (workers join,
    tasks get assigned and completed without emitting facts) so that the
    round-start Priority/Load snapshot carries the 5.2.1 semantics:
    c_w = unfinished assignments from history, p_w = waiting time since
    the last assignment."""
    rng = random.Random(seed * 1000 + start_file)
    stream = load_stream(start_file, dataset=dataset)
    facts = []
    pool = []          # workers registered with the platform
    wid_seq = 0
    j = 0              # in-round task counter (dense numbering)

    # silent warm-up, no facts emitted
    n_warm = max(1, int(len(stream) * WARMUP_FRAC))
    for ev in stream[:n_warm]:
        if isinstance(ev, WorkerEvent):
            wid_seq += 1
            pool.append(_Worker(f"w{wid_seq}", ev))
        else:
            _, w_star, done = _try_assign(ev, pool, rng,
                                          ev.arrival + ev.dur)
            if w_star is not None:
                w_star.last_assign = ev.arrival
                if done:
                    pass            # completed tasks never count as unfinished load
                else:
                    w_star.load += 1

    round_start = stream[n_warm].arrival

    # round-start snapshot: Priority / Load of registered workers (5.2.1)
    for w in pool:
        since = w.last_assign if w.last_assign is not None else w.online_from
        waiting = max(0.0, round_start - since)
        facts.append(("Priority", w.wid, beta_p(waiting)))
        facts.append(("Load", w.wid, beta_l(w.load)))

    # consume this round's events in order
    for ev in stream[n_warm:]:
        if len(facts) >= target_n - 1:
            break
        if isinstance(ev, WorkerEvent):
            wid_seq += 1
            pool.append(_Worker(f"w{wid_seq}", ev))
            continue

        # task publication (5.1)
        t: TaskEvent = ev
        j += 1
        tid = f"{k}-{j}"
        rid = f"r{rng.randrange(100)}"
        com_l = hashlib.sha256(
            f"{t.x:.6f},{t.y:.6f},{rng.getrandbits(128)}".encode()).hexdigest()
        e_ddl = t.arrival + t.dur
        facts.append(("Task", tid, rid, com_l, t.reward, round(e_ddl, 1),
                      t.dur))
        facts.append(("TaskKey", tid))

        # assignment facts (5.2.1): eligibility predicate + greedy pick
        cands, w_star, done = _try_assign(t, pool, rng, e_ddl)
        for w in cands:
            facts.append(("Eligible", tid, w.wid))
        if w_star is not None:
            facts.append(("Assign", tid, w_star.wid))
            w_star.load += 1
            w_star.last_assign = t.arrival
            # completion facts (5.3.1); auditor signature simulated with random
            # bytes; Done and DoneKey inserted atomically as Chapter 6 assumes
            if done:
                sig = rng.getrandbits(512).to_bytes(64, "big")
                h_sig = hashlib.sha256(sig).hexdigest()
                facts.append(("Done", tid, w_star.wid, h_sig))
                facts.append(("DoneKey", tid, w_star.wid))
                w_star.load -= 1   # finished, no longer unfinished load

    # end-of-round count, then truncate to exactly target_n
    facts.append(("TaskCount", k, j))
    return facts[:target_n]


def make_absent_elements(facts, m: int, seed: int = 42):
    """Build m elements guaranteed absent from the fact set (for non-membership proofs)."""
    rng = random.Random(seed + 7)
    present = set(facts)
    out = []
    i = 0
    while len(out) < m:
        i += 1
        z = ("DoneKey", f"9-{rng.randrange(10**6)}", f"wx{i}")
        if z not in present:
            out.append(z)
    return out
