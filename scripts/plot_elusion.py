#!/usr/bin/env python3
"""Generate a schematic PNG of two particles and their avoidance paths."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from lib.plot_style import BLUE, VERMILLION, apply_academic_style, style_axes

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs/presentation/images/cuadro_inicial.png"


def create_figure(action_distance: float, r_min: float, radius: float):
    half_distance = action_distance / 2
    clearance = radius + r_min
    x = np.linspace(-half_distance, half_distance, 400)
    progress = (x + half_distance) / action_distance
    offset = clearance * 4 * progress * (1 - progress)

    apply_academic_style()
    fig, ax = plt.subplots(figsize=(11, 5))

    ax.plot(x, np.zeros_like(x), color="0.45", linestyle="--", linewidth=1.5,
            label="trayectoria directa")
    ax.plot(x, offset, color=BLUE, linewidth=2.5, label="trayectoria partícula 1")
    ax.plot(x, -offset, color=VERMILLION, linewidth=2.5,
            label="trayectoria partícula 2")
    ax.add_patch(
        Circle(
            (0, 0),
            radius,
            fill=False,
            edgecolor="0.35",
            linestyle=":",
            linewidth=1.4,
            label="borde del obstáculo",
            zorder=2,
        )
    )

    arrow_index = 180
    ax.annotate(
        "",
        xy=(x[arrow_index + 12], offset[arrow_index + 12]),
        xytext=(x[arrow_index], offset[arrow_index]),
        arrowprops={"arrowstyle": "->", "color": BLUE, "lw": 2},
    )
    ax.annotate(
        "",
        xy=(x[220], -offset[220]),
        xytext=(x[232], -offset[232]),
        arrowprops={"arrowstyle": "->", "color": VERMILLION, "lw": 2},
    )

    for center_x, color in ((-half_distance, BLUE), (half_distance, VERMILLION)):
        ax.add_patch(Circle((center_x, 0), radius, facecolor=color, edgecolor="black",
                            linewidth=1.2, zorder=5))

    dimension_y = 2.8 * clearance
    for center_x in (-half_distance, half_distance):
        ax.plot([center_x, center_x], [0, dimension_y], color="0.4",
                linestyle=":", linewidth=1)
    ax.annotate(
        "",
        xy=(half_distance, dimension_y),
        xytext=(-half_distance, dimension_y),
        arrowprops={"arrowstyle": "<->", "color": "black", "lw": 1.4},
    )
    ax.text(
        0,
        dimension_y + 0.12 * clearance,
        r"$\mathrm{action\ distance}$",
        ha="center",
        va="bottom",
    )

    if r_min > 0:
        ax.add_patch(
            Circle((0, 0), clearance, fill=False, edgecolor="0.35",
                   linestyle=":", linewidth=1.4, zorder=2)
        )
        dimension_x = clearance + 0.12 * radius
        ax.plot([0, dimension_x], [radius, radius], color="0.25",
                linestyle=":", linewidth=1.4)
        ax.plot([0, dimension_x], [clearance, clearance], color="0.25",
                linestyle=":", linewidth=1.4)
        ax.annotate(
            "",
            xy=(dimension_x, clearance),
            xytext=(dimension_x, radius),
            arrowprops={
                "arrowstyle": "<->",
                "color": "black",
                "lw": 1.8,
                "mutation_scale": 9,
            },
            zorder=8,
        )
        ax.annotate(
            r"$r_{\min}$",
            xy=(dimension_x, (radius + clearance) / 2),
            xytext=(dimension_x + 0.15 * action_distance,
                    clearance + 0.12 * action_distance),
            fontsize=22,
            ha="left",
            va="center",
            arrowprops={"arrowstyle": "-", "color": "0.25", "lw": 1.2},
        )
    else:
        ax.text(0.18 * action_distance, 1.5 * clearance, r"$r_{\min}$",
                ha="left", va="center")

    ax.text(-half_distance, -1.35 * clearance, "Partícula 1", color=BLUE,
            ha="center", va="top")
    ax.text(half_distance, -1.35 * clearance, "Partícula 2", color=VERMILLION,
            ha="center", va="top")

    x_margin = max(radius, 0.08 * action_distance)
    ax.set_xlim(-half_distance - x_margin, half_distance + x_margin)
    ax.set_ylim(-1.8 * clearance, 3.5 * clearance)
    ax.set_aspect("equal", adjustable="box")
    style_axes(ax, r"posición $x$ (m)", r"posición $y$ (m)")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(axis="both", which="both", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False)
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action-distance", "--action_distance", type=float, default=5.0,
                        help="distancia de centros que activa la elusión, en metros (default: 5)")
    parser.add_argument("--r-min", "--r_min", type=float, default=0.30,
                        help="distancia mínima de elusión, en metros (default: 0.30)")
    parser.add_argument("--radius", type=float, default=0.25,
                        help="radio dibujado para cada partícula, en metros (default: 0.25)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT,
                        help=f"PNG de salida (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    if args.action_distance <= 0:
        parser.error("--action-distance debe ser mayor que 0")
    if args.r_min < 0:
        parser.error("--r-min no puede ser negativo")
    if args.radius <= 0:
        parser.error("--radius debe ser mayor que 0")

    output = args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    figure = create_figure(args.action_distance, args.r_min, args.radius)
    figure.savefig(output, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(figure)
    print(f"PNG guardado en: {output}")


if __name__ == "__main__":
    main()
