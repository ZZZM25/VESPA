"""Paper figures: one single-panel PNG per (metric, dataset), for a
two-figures-per-row LaTeX layout.

All grouped bar charts with log y-axis. E2/E3/E4 use six bars
(membership dark, non-membership light); E1/E5 use one bar per scheme.
Output goes to figs/paper/ and is also copied to ../image_ex/.
"""
import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# global style: Times New Roman, black, no grid
plt.rcParams.update({
    "font.family": "Times New Roman",
    "mathtext.fontset": "stix",
    "text.color": "black",
    "axes.labelcolor": "black",
    "axes.edgecolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "axes.grid": False,
    "hatch.linewidth": 0.7,
})

OUT = ROOT / "figs" / "paper"
OUT.mkdir(exist_ok=True)
IMAGE_EX = ROOT.parent / "image_ex"

SIZES = [500, 1000, 2000, 5000, 10000]
BATCHES = [10, 50, 100, 500, 1000]
DATASETS = ["gMission", "EverySender"]
SCHEMES = ["VESTA-256", "VESTA-2048", "MHT", "SMT"]
# legend shows VESPA; data keys stay VESTA to match the CSVs and COLORS
DISPLAY = {s: s.replace("VESTA", "VESPA") for s in SCHEMES}
COLORS = {"VESTA-256": "#295A8C", "VESTA-2048": "#529442",
          "MHT": "#637384", "SMT": "#BD8C7B"}
# membership / non-membership color pair per scheme
PAIR = {
    ("VESTA-256", "mem"): "#295A8C", ("VESTA-256", "nonmem"): "#ADDEEF",
    ("VESTA-2048", "mem"): "#529442", ("VESTA-2048", "nonmem"): "#A5E7A5",
    ("MHT", "mem"): "#637384", ("MHT", "nonmem"): "#C6D6E7",
    ("SMT", "mem"): "#BD8C7B", ("SMT", "nonmem"): "#6B5242",
}
# precomputed (pre) series reuse each VESTA variant's light color
PRE_COLORS = {"VESTA-256": "#ADDEEF", "VESTA-2048": "#A5E7A5"}
# one hatch per scheme; pre series get their own so they don't collide
HATCH = {"VESTA-256": "//", "VESTA-2048": "\\\\", "MHT": "xx", "SMT": ".."}
PRE_HATCH = {"VESTA-256": "---", "VESTA-2048": "++"}

FS_LABEL = 13
FS_TICK = 12
FS_LEGEND = 11


def load(ds, fname, valcol, with_pi=True):
    rows = list(csv.DictReader(open(ROOT / "results" / f"{fname}_{ds}.csv")))
    b = defaultdict(list)
    for r in rows:
        key = (r["scheme"], int(r.get("size", r.get("batch", 0))),
               r.get("pi", "-"))
        b[key].append(float(r[valcol]))
    out = {}
    for k, vs in b.items():
        m = sum(vs) / len(vs)
        sd = (sum((v - m) ** 2 for v in vs) / len(vs)) ** 0.5
        out[k] = (m, sd)
    return out


def grouped_bar(ax, xs, series):
    """series: list of {ys, color, label}; grouped bars, no error bars."""
    n = len(series)
    total_w = 0.8
    bw = total_w / n
    idx = list(range(len(xs)))
    for i, sr in enumerate(series):
        pos = [j - total_w / 2 + bw * (i + 0.5) for j in idx]
        ax.bar(pos, sr["ys"], width=bw, label=sr.get("label"),
               color=sr["color"], edgecolor="black", linewidth=0.4,
               hatch=sr.get("hatch"))
    ax.set_xticks(idx)
    ax.set_xticklabels([str(x) for x in xs])


def style_axes(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel, fontsize=FS_LABEL)
    ax.set_ylabel(ylabel, fontsize=FS_LABEL)
    ax.set_yscale("log")
    ax.tick_params(labelsize=FS_TICK)


def finish(ax, ncol=None, gap=0.06, pair_reorder=False):
    """Legend at the inside top: shrink font until it fits, then raise the
    y-limit so the tallest bar stays clear of the legend.

    pair_reorder with ncol=2 puts one scheme per row (-M left, -NM right)."""
    handles, labels = ax.get_legend_handles_labels()
    if ncol is None:
        ncol = len(labels)
    if pair_reorder and ncol == 2 and len(labels) % 2 == 0:
        order = list(range(0, len(labels), 2)) + list(range(1, len(labels), 2))
        handles = [handles[i] for i in order]   # column-major: one scheme per row
        labels = [labels[i] for i in order]
    fig = ax.figure
    fs = FS_LEGEND
    while True:                               # shrink font until the legend fits
        leg = ax.legend(handles, labels, loc="upper center", ncol=ncol,
                        frameon=False, fontsize=fs, columnspacing=1.0,
                        handletextpad=0.4, handlelength=1.3, labelspacing=0.3)
        fig.canvas.draw()
        if leg.get_window_extent().width <= ax.get_window_extent().width * 0.96 \
                or fs <= 7:
            break
        fs -= 1
    # pad the top of the log axis so bars sit gap below the legend
    legH = leg.get_window_extent().height / ax.get_window_extent().height
    heights = [p.get_height() for p in ax.patches if p.get_height() > 0]
    if heights:
        dmax = max(heights)
        y0 = ax.get_ylim()[0]
        f_bar = max(0.5, 1.0 - legH - gap)
        ax.set_ylim(y0, y0 * (dmax / y0) ** (1.0 / f_bar))


def plot_single(ds, fname, valcol, xs, xlabel, ylabel, out_name):
    """One bar per scheme (no mem/nonmem split): E1 and E5."""
    data = load(ds, fname, valcol)
    fig, ax = plt.subplots(figsize=(3.6, 2.9))
    series = [{"ys": [data[(s, x, "-")][0] for x in xs],
               "es": [data[(s, x, "-")][1] for x in xs],
               "color": COLORS[s], "hatch": HATCH[s],
               "label": DISPLAY[s]} for s in SCHEMES]
    grouped_bar(ax, xs, series)
    style_axes(ax, xlabel, ylabel)
    finish(ax)
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=300)
    plt.close(fig)


def plot_mem_nonmem(ds, fname, valcol, ylabel, out_name):
    """Eight bars (4 schemes x mem/nonmem), labelled -M / -NM."""
    data = load(ds, fname, valcol)
    fig, ax = plt.subplots(figsize=(3.6, 2.9))
    series = []
    for s in SCHEMES:
        for pi in ("mem", "nonmem"):
            label = f"{DISPLAY[s]}-M" if pi == "mem" else f"{DISPLAY[s]}-NM"
            series.append({
                "ys": [data[(s, x, pi)][0] for x in SIZES],
                "color": PAIR[(s, pi)],
                "hatch": HATCH[s],
                "label": label,
            })
    grouped_bar(ax, SIZES, series)
    style_axes(ax, "Facts per round", ylabel)
    finish(ax, ncol=2, pair_reorder=True)   # one scheme per legend row: -M | -NM
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=300)
    plt.close(fig)


def plot_vogen(ds, out_name):
    """VO generation: 4 schemes on-demand (membership) plus the two VESTA
    variants precomputed (amortized), six bars."""
    data = load(ds, "e2_vogen", "gen_ms")          # (scheme, size, pi)
    a2 = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "results" / f"a2_batch_{ds}.csv")):
        a2[(r["scheme"], int(r["size"]))].append(float(r["amortized_ms"]))
    a2 = {k: sum(v) / len(v) for k, v in a2.items()}
    fig, ax = plt.subplots(figsize=(3.6, 2.9))
    series = [{"ys": [data[(s, x, "mem")][0] for x in SIZES],
               "color": COLORS[s], "hatch": HATCH[s],
               "label": DISPLAY[s]} for s in SCHEMES]
    for s in ("VESTA-256", "VESTA-2048"):
        series.append({"ys": [a2[(s, x)] for x in SIZES],
                       "color": PRE_COLORS[s], "hatch": PRE_HATCH[s],
                       "label": f"{DISPLAY[s]}(pre)"})
    grouped_bar(ax, SIZES, series)
    style_axes(ax, "Facts per round", "VO generation time (ms)")
    finish(ax, ncol=3)   # 6 entries -> 2 rows x 3 cols
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=300)
    plt.close(fig)


def main():
    for ds in DATASETS:
        tag = ds.lower()
        plot_single(ds, "e1_build", "build_ms", SIZES,
                    "Facts per round", "Construction time (ms)",
                    f"e1_build_{tag}.png")
        plot_vogen(ds, f"e2_vogen_{tag}.png")
        plot_mem_nonmem(ds, "e3_verify", "verify_ms",
                        "Verification time (ms)", f"e3_verify_{tag}.png")
        plot_mem_nonmem(ds, "e4_vosize", "size_bytes",
                        "VO size (bytes)", f"e4_vosize_{tag}.png")
        plot_single(ds, "e5_update", "update_ms", BATCHES,
                    "Appended batch size", "Update time (ms)",
                    f"e5_update_{tag}.png")
        print(f"{ds}: 5 figures done")

    # copy into the paper's figure directory
    if IMAGE_EX.exists():
        for p in OUT.glob("*.png"):
            shutil.copy(p, IMAGE_EX / p.name)
        print(f"copied to {IMAGE_EX}")


if __name__ == "__main__":
    main()
