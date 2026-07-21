#!/usr/bin/env python3
"""Generate Stage C final RF-U overlay figures (H0/H1/H2/refined-v3).

Does not require Abaqus. Uses frozen RF-U CSVs.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_rfu(path: Path):
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            u = rf = None
            for k, v in row.items():
                if k is None:
                    continue
                kl = k.lower()
                if kl in ("u2", "u", "displacement"):
                    u = float(v)
                if kl in ("rf2", "rf", "force"):
                    rf = abs(float(v))
            if u is None:
                vals = list(row.values())
                u, rf = float(vals[0]), abs(float(vals[1]))
            rows.append((u, rf))
    # unique sorted
    d = {}
    for u, f in rows:
        d[round(u, 12)] = f
    return sorted(d.items())


def plot_overlay(series, out: Path, title: str, xlim=None, ylim=None):
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for label, rows, style in series:
        us = [u for u, _ in rows]
        fs = [f for _, f in rows]
        ax.plot(us, fs, style, label=label, linewidth=1.8)
    ax.set_xlabel("U2 (mm)")
    ax.set_ylabel("|RF2| (kN)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h0", type=Path, required=True)
    ap.add_argument("--h1", type=Path, required=True)
    ap.add_argument("--h2", type=Path, required=True)
    ap.add_argument("--refined", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    h0 = load_rfu(args.h0)
    h1 = load_rfu(args.h1)
    h2 = load_rfu(args.h2)
    r3 = load_rfu(args.refined)

    out = args.out_dir
    plot_overlay(
        [
            ("H0", h0, "-"),
            ("H1", h1, "-"),
            ("H2-PUB", h2, "-"),
            ("Refined-v3", r3, "--"),
        ],
        out / "01_rf_u_h0_h1_h2_refined_v3.png",
        "RF–U overlay: H0 / H1 / H2-PUB / refined-v3",
    )
    # pre-peak focus (U <= 0.0058)
    def pre(rows):
        return [(u, f) for u, f in rows if u <= 0.0058 + 1e-9]

    plot_overlay(
        [("H1", pre(h1), "-"), ("Refined-v3", pre(r3), "--")],
        out / "02_rf_u_h1_vs_refined_v3_prepeak.png",
        "H1 vs refined-v3 — pre-peak / peak focus",
        xlim=(0, 0.0062),
    )
    # post-peak
    def post(rows):
        return [(u, f) for u, f in rows if u >= 0.0058 - 1e-9]

    plot_overlay(
        [("H1", post(h1), "-"), ("Refined-v3", post(r3), "--")],
        out / "03_rf_u_h1_vs_refined_v3_postpeak.png",
        "H1 vs refined-v3 — post-peak (limited equivalence)",
        xlim=(0.0055, 0.0072),
    )
    print("figures_done", out)


if __name__ == "__main__":
    main()
