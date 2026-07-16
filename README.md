# VESPA
Fact set / complete element construction, VO construction, verification.

## Run

```bash
pip install gmpy2 matplotlib numpy
python experiments/run.py --exp all          # full run
python experiments/run.py --exp e1 --sizes 500 --reps 2   # quick smoke test
```

Output: `results/*.csv` (raw data), `figs/*.png` (300 dpi), `results/e6_leakage.tex` (LaTeX table).

## Code ↔ Paper Chapter 5 Mapping

| Code | Paper |
|---|---|
| `sim/simulator.py` fact generation | 5.1 Task/TaskKey/TaskCount; 5.2.1 four types of assignment facts (round-start snapshot); 5.3.1 Done/DoneKey (atomic insertion) |
| `vesta/prime.py` | 5.2.1 Prime representation (delimiter concatenation → SHA256 → truncate to 128 bits → smallest prime not less than it) |
| `vesta/accumulator.py` | 3.2 accumulator definition; 5.2.1 Accumulation (one Acc per round) and Update (Acc'=Acc^∏x) |
| `vesta/scheme.py` VO five-tuple (z, π, wit, payload, meta) | 5.2.2 Definition (VO) |
| `baselines/mht.py` | sorted Merkle tree (non-membership proof exposes two neighbors in plaintext, i.e. the leakage criticized in Intro Challenge 2) |
| `baselines/smt.py` | sparse Merkle tree, depth 256, no compression |
| `experiments/run.py` | six groups of metrics in the experiment chapter |

## Data

`gMission/data_0x.txt` (GOMA repository format):
Task line `arrival t x y dur reward`; worker line `arrival w x y cap radius dur success`.
10 files = 10 independent repetitions (the r-th run concatenates starting from data_0r).
