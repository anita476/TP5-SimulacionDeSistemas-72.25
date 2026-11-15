#!/usr/bin/env python3
"""Dos peatones enfrentados: posición actual, velocidad y target del otro."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from lib.plot_style import BLUE, GREEN, VERMILLION, apply_academic_style

# Ancho de la columna de la diapositiva Sistema. La fuente queda en puntos de esa diapositiva.
SLIDE_WIDTH_IN = 7.6 / 2.54
FONT = 11


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parents[1] / "docs" / "presentation" / "images" / "targets_driving_force.png")
    parser.add_argument("--no-show", action="store_true", help="no abrir la ventana del gráfico")
    args = parser.parse_args()

    apply_academic_style()

    radius = 0.36
    p1_start = np.array([-2.05, 0.0])
    p2_start = np.array([2.05, 0.0])
    p1 = p1_start + np.array([0.78, 0.0])
    p2 = p2_start - np.array([0.78, 0.0])
    pedestrians = (
        {"name": "$i$", "velocity": "$\\mathbf{v}_i$", "here": p1, "aim": np.array([1.0, 0.0]),
         "target": p2_start, "label": "target de $i$\n$\\mathbf{r}_j(0)$", "color": BLUE},
        {"name": "$j$", "velocity": "$\\mathbf{v}_j$", "here": p2, "aim": np.array([-1.0, 0.0]),
         "target": p1_start, "label": "target de $j$\n$\\mathbf{r}_i(0)$", "color": VERMILLION},
    )

    xlim, ylim = (-3.25, 3.25), (-0.88, 1.42)
    fig_w = SLIDE_WIDTH_IN
    fig_h = fig_w * (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.subplots_adjust(0, 0, 1, 1)

    ax.plot([p1_start[0], p2_start[0]], [0, 0], color="0.55", linestyle=(0, (0.6, 1.1)),
            linewidth=1.0, zorder=1)

    for ped in pedestrians:
        here = ped["here"]
        color = ped["color"]
        ax.add_patch(Circle(here, radius, facecolor=color, edgecolor="black",
                            linewidth=0.7, zorder=4))
        ax.plot(*here, marker="o", color="black", markersize=2.4, zorder=7)

        tip = here + 0.85 * ped["aim"]
        ax.annotate("", xy=tip, xytext=here,
                    arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.35,
                                "shrinkA": 0, "shrinkB": 0, "mutation_scale": 12},
                    zorder=6)
        ax.text(tip[0], 0.16, ped["velocity"], color=color, ha="center", va="bottom",
                fontsize=FONT, zorder=7,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.15})

        target = ped["target"]
        arm = 0.18
        ax.plot([target[0] - arm, target[0] + arm], [target[1] - arm, target[1] + arm],
                color=GREEN, lw=1.7, solid_capstyle="butt", zorder=8)
        ax.plot([target[0] - arm, target[0] + arm], [target[1] + arm, target[1] - arm],
                color=GREEN, lw=1.7, solid_capstyle="butt", zorder=8)
        ax.text(target[0], 0.58, ped["label"], color=GREEN, ha="center", va="bottom",
                fontsize=FONT, linespacing=1.05, zorder=8)
        ax.text(here[0], -radius - 0.06, ped["name"], color=color, ha="center", va="top",
                fontsize=FONT, zorder=8)

    ax.set_aspect("equal")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=300, facecolor="white")
    print(f"Esquema guardado en: {args.out}")
    if not args.no_show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
