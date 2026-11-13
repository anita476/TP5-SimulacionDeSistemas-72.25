#!/usr/bin/env python3
"""Esquema del sistema: dos peatones enfrentados, cada uno con su velocidad deseada hacia su destino."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from lib.plot_style import BLUE, VERMILLION, apply_academic_style

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs/presentation/images/cuadro_inicial.png"


def create_figure(separation: float, radius: float):
    """Condición inicial de un evento, sin parámetros de la capa de elusión.

    El destino de cada peatón es la posición inicial del otro (como en main.cpp),
    así que la trayectoria directa de ambos es el mismo segmento.
    """
    half = separation / 2
    apply_academic_style()
    fig, ax = plt.subplots(figsize=(11, 3.4))

    ax.plot([-half, half], [0, 0], color="0.45", linestyle="--", linewidth=1.8, zorder=1)
    arrow_length = 0.22 * separation
    for center_x, direction, color, name, other in (
        (-half, 1, BLUE, "Peatón 1", 2),
        (half, -1, VERMILLION, "Peatón 2", 1),
    ):
        ax.add_patch(Circle((center_x, 0), radius, facecolor=color, edgecolor="black", linewidth=1.2, zorder=5))
        start = center_x + direction * (radius + 0.08)
        ax.annotate("", xy=(start + direction * arrow_length, 0), xytext=(start, 0), zorder=6,
                    arrowprops={"arrowstyle": "-|>", "color": color, "lw": 3.2, "mutation_scale": 26,
                                "shrinkA": 0, "shrinkB": 0})
        ax.text(start + direction * arrow_length / 2, 0.14, rf"$v_{{d{name[-1]}}}$", color=color,
                ha="center", va="bottom", fontsize=24)
        ax.text(center_x, -radius - 0.12, name, color=color, ha="center", va="top")
        ax.text(center_x, -radius - 0.52, f"destino de {other}", color="0.3", ha="center", va="top", fontsize=17)

    margin = 3.4 * radius
    ax.set_xlim(-half - margin, half + margin)
    ax.set_ylim(-radius - 1.0, radius + 0.55)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--separation", type=float, default=5.0,
                        help="distancia inicial dibujada entre centros, en metros (default: 5)")
    parser.add_argument("--radius", type=float, default=0.25,
                        help="radio dibujado para cada partícula, en metros (default: 0.25)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT,
                        help=f"PNG de salida (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    if args.separation <= 2 * args.radius:
        parser.error("--separation debe ser mayor que dos radios")
    if args.radius <= 0:
        parser.error("--radius debe ser mayor que 0")

    output = args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    figure = create_figure(args.separation, args.radius)
    figure.savefig(output, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(figure)
    print(f"PNG guardado en: {output}")


if __name__ == "__main__":
    main()
