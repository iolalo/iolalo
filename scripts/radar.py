#!/usr/bin/env python3
"""Generate a skill radar chart (dark + light SVG) from a JSON file of {label: 0-100}."""
import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ACCENT = "#F2C811"  # Power BI yellow


def load_data(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_chart(data, out_path, dark):
    labels = list(data.keys())
    values = list(data.values())
    n = len(labels)
    angles = [i / n * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    values = values + values[:1]

    fg = "#c9d1d9" if dark else "#24292f"
    grid = "#30363d" if dark else "#d0d7de"

    fig = plt.figure(figsize=(4.5, 4.5))
    ax = fig.add_subplot(111, polar=True)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=fg, size=10)

    ax.set_rlabel_position(0)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels([])
    ax.set_ylim(0, 100)

    ax.spines["polar"].set_color(grid)
    ax.grid(color=grid, linewidth=0.6)

    ax.plot(angles, values, color=ACCENT, linewidth=2)
    ax.fill(angles, values, color=ACCENT, alpha=0.25)

    fig.tight_layout()
    fig.savefig(out_path, transparent=True)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="path to a JSON file of {label: 0-100}")
    parser.add_argument("-o", "--output", required=True, help="output prefix, e.g. assets/radar")
    args = parser.parse_args()

    data = load_data(args.data)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    make_chart(data, f"{out}-dark.svg", dark=True)
    make_chart(data, f"{out}-light.svg", dark=False)


if __name__ == "__main__":
    main()
