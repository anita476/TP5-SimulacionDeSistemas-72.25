#!/usr/bin/env python3
"""Esquema básico de targets, movimiento actual y driving force para dos partículas."""

import argparse
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from lib.plot_style import BLUE, GREEN, VERMILLION, apply_academic_style


def arrow(ax, start, vector, color, label, label_offset=(0.0, 0.0), lw=2.2):
    end = start + vector
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "-|>", "color": color, "lw": lw,
                    "shrinkA": 0, "shrinkB": 0, "mutation_scale": 18},
        zorder=6,
    )
    ax.text(end[0] + label_offset[0], end[1] + label_offset[1], label,
            color=color, ha="center", va="center", fontsize=16,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parents[1] / "docs" / "presentation" / "images" / "targets_driving_force.png")
    parser.add_argument("--no-show", action="store_true", help="no abrir la ventana del gráfico")
    args = parser.parse_args()

    apply_academic_style()
    fig, ax = plt.subplots(figsize=(11.5, 6.0), layout="constrained")

    radius = 0.32
    travel_distance = 0.75
    p1_x0, p1_y0 = -2.0, 0.0
    p2_x0, p2_y0 = 2.0, 0.0
    p1_initial = np.array([p1_x0, p1_y0])
    p2_initial = np.array([p2_x0, p2_y0])
    p1_direction = (p2_initial - p1_initial) / np.linalg.norm(p2_initial - p1_initial)
    p2_direction = (p1_initial - p2_initial) / np.linalg.norm(p1_initial - p2_initial)
    particles = (
        {"name": "$p_1$", "position": p1_initial + travel_distance * p1_direction,
         "target": p2_initial, "target_coords": "$(px_{2_{0}}, py_{2_0})$",
         "color": BLUE},
        {"name": "$p_2$", "position": p2_initial + travel_distance * p2_direction,
         "target": p1_initial, "target_coords": "$(px_{1_0}, py_{1_0})$",
         "color": VERMILLION},
    )

    ax.plot([p1_initial[0], p2_initial[0]], [p1_initial[1], p2_initial[1]],
            color="0.55", linestyle=":", linewidth=1.6, zorder=1)

    for particle in particles:
        position = particle["position"]
        target = particle["target"]
        color = particle["color"]
        direction = target - position
        direction /= np.linalg.norm(direction)

        ax.add_patch(Circle(position, radius, facecolor=color, edgecolor="black",
                            linewidth=1.2, alpha=0.9, zorder=4))
        ax.plot(*position, marker="o", color="black", markersize=4, zorder=5)
        ax.text(position[0], -0.30, particle["name"], ha="center", va="top",
            color=color, fontsize=17)

        cross_half = 0.16
        ax.plot([target[0] - cross_half, target[0] + cross_half],
            [target[1] - cross_half, target[1] + cross_half],
            color=GREEN, lw=3.0, solid_capstyle="butt", zorder=8)
        ax.plot([target[0] - cross_half, target[0] + cross_half],
            [target[1] + cross_half, target[1] - cross_half],
            color=GREEN, lw=3.0, solid_capstyle="butt", zorder=8)
        ax.text(target[0], 0.50,
            f"target {particle['name']}\n{particle['target_coords']}",
            color=GREEN, ha="center", va="bottom", fontsize=15)

        arrow(ax, position, 1 * direction, color, "v",
              (0.0, 0.16), lw=2.2)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-1.4, 1.6)
    ax.axis("off")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=300, facecolor="white", bbox_inches="tight")
    print(f"Esquema guardado en: {args.out}")
    if not args.no_show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()