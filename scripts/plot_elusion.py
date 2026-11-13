#!/usr/bin/env python3
"""Generate a schematic PNG of two particles and their avoidance paths."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

from lib.plot_style import BLUE, VERMILLION, apply_academic_style

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs/presentation/images/cuadro_inicial.png"


def create_figure(action_distance: float, r_min: float, radius: float):
    """Esquema del sistema: dos peatones enfrentados a la distancia de acción.

    Cada uno esquiva por su derecha. Al cruzarse, el centro de uno queda a r_min
    del borde del otro, o sea a r + r_min entre centros, que es a lo que apunta
    la capa de elusión (R = r_min + r_j en quadratic_heuristic.cpp).
    """
    half_distance = action_distance / 2
    separation = radius + r_min           # distancia entre centros al cruzarse
    amplitude = separation / 2            # desvío lateral de cada peatón
    x = np.linspace(-half_distance, half_distance, 400)
    progress = (x + half_distance) / action_distance
    offset = amplitude * 4 * progress * (1 - progress)

    apply_academic_style()
    fig, ax = plt.subplots(figsize=(11, 4.2))

    ax.plot(x, np.zeros_like(x), color="0.45", linestyle="--", linewidth=1.5,
            label="trayectoria directa")
    # peatón 1 (azul) camina hacia +x y esquiva por su derecha (abajo); el 2, al revés
    ax.plot(x, -offset, color=BLUE, linewidth=2.5)
    ax.plot(x, offset, color=VERMILLION, linewidth=2.5)
    ax.annotate("", xy=(x[112], -offset[112]), xytext=(x[100], -offset[100]),
                arrowprops={"arrowstyle": "->", "color": BLUE, "lw": 2})
    ax.annotate("", xy=(x[288], offset[288]), xytext=(x[300], offset[300]),
                arrowprops={"arrowstyle": "->", "color": VERMILLION, "lw": 2})

    for center_x, color in ((-half_distance, BLUE), (half_distance, VERMILLION)):
        ax.add_patch(Circle((center_x, 0), radius, facecolor=color, edgecolor="black",
                            linewidth=1.2, zorder=5))
    # posiciones al cruzarse
    for center_y, color in ((-amplitude, BLUE), (amplitude, VERMILLION)):
        ax.add_patch(Circle((0, center_y), radius, facecolor=color, edgecolor="black",
                            linewidth=1.2, linestyle="--", alpha=0.35, zorder=4))

    dimension_y = amplitude + radius + 0.45
    for center_x in (-half_distance, half_distance):
        ax.plot([center_x, center_x], [radius, dimension_y], color="0.4",
                linestyle=":", linewidth=1)
    ax.annotate("", xy=(half_distance, dimension_y), xytext=(-half_distance, dimension_y),
                arrowprops={"arrowstyle": "<->", "color": "black", "lw": 1.4})
    ax.text(0, dimension_y + 0.06, r"activación de la elusión: distancia $d_a$", ha="center", va="bottom")

    if r_min > 0:
        # r_min: del centro del peatón 1 al borde del peatón 2, al cruzarse
        y_from, y_to = -amplitude, amplitude - radius
        ax.plot([0, 0], [y_from, y_to], color="black", linewidth=1.8, zorder=8)
        for y_tick in (y_from, y_to):
            ax.plot([-0.06, 0.06], [y_tick, y_tick], color="black", linewidth=1.8, zorder=8)
        ax.annotate(r"$r_{\min}$", xy=(0.03, (y_from + y_to) / 2),
                    xytext=(0.16 * action_distance, -amplitude - radius - 0.22),
                    fontsize=22, ha="left", va="center",
                    arrowprops={"arrowstyle": "-", "color": "0.25", "lw": 1.2}, zorder=9)

    ax.text(-half_distance, -radius - 0.12, "Peatón 1", color=BLUE, ha="center", va="top")
    ax.text(half_distance, -radius - 0.12, "Peatón 2", color=VERMILLION, ha="center", va="top")

    x_margin = max(2.4 * radius, 0.1 * action_distance)
    ax.set_xlim(-half_distance - x_margin, half_distance + x_margin)
    ax.set_ylim(-amplitude - radius - 0.5, dimension_y + 0.4)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], marker="o", linestyle="none", markersize=16, markerfacecolor="0.75",
                          markeredgecolor="black"))
    labels.append("posiciones al cruzarse")
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=2,
              frameon=False, columnspacing=2.0, handlelength=2.2)
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
