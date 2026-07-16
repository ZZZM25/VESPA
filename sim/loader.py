"""gMission data parsing.

File format:
  header:      <n_workers> <n_tasks> <param> <n_records>
  task line:   arrival t x y dur reward
  worker line: arrival w x y cap radius dur success
"""
from dataclasses import dataclass
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class TaskEvent:
    arrival: float
    x: float
    y: float
    dur: float      # deadline window (e = arrival + dur)
    reward: float


@dataclass
class WorkerEvent:
    arrival: float
    x: float
    y: float
    cap: int
    radius: float
    dur: float      # online duration
    success: float  # completion success rate


def load_file(idx: int, dataset: str = "gMission"):
    """Read data_{idx:02d}.txt, return events sorted by arrival time."""
    path = DATA_ROOT / dataset / f"data_{idx:02d}.txt"
    events = []
    with open(path) as f:
        lines = f.read().splitlines()
    for line in lines[1:]:  # skip header
        tok = line.split()
        if len(tok) < 2:
            continue
        if tok[1] == "t":
            events.append(TaskEvent(float(tok[0]), float(tok[2]), float(tok[3]),
                                    float(tok[4]), float(tok[5])))
        elif tok[1] == "w":
            events.append(WorkerEvent(float(tok[0]), float(tok[2]), float(tok[3]),
                                      int(float(tok[4])), float(tok[5]),
                                      float(tok[6]), float(tok[7])))
    events.sort(key=lambda e: e.arrival)
    return events


def load_stream(start_idx: int, n_files: int = 10, dataset: str = "gMission"):
    """Concatenate n_files starting at data_{start_idx} into one event stream.

    Later files are time-shifted so arrival times stay monotone."""
    stream = []
    offset = 0.0
    for i in range(n_files):
        evs = load_file((start_idx + i) % 10, dataset)
        for e in evs:
            e.arrival += offset
        stream.extend(evs)
        offset = stream[-1].arrival + 1.0
    return stream
