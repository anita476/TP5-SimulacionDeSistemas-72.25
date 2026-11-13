#!/usr/bin/env python3
"""Esquema del sistema: dos peatones enfrentados y los dos parámetros de la capa de elusión.

d_act: distancia entre centros a la que se activa la elusión.
d_lat: margen entre el borde del otro peatón y el punto auxiliar P (R = r + d_lat).
Unidades arbitrarias; la dirección e0 de cada peatón sale de la misma fórmula que usa el motor.
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from lib.plot_style import BLUE, GREEN, RED, VERMILLION, apply_academic_style

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs/presentation/images/cuadro_inicial.png"
DARK_BLUE, DARK_ORANGE = "#004C7A", "#B34A00"
FS = 26


def create_figure(d_act: float, d_lat: float, radius: float, beyond: float):
    """Instante de activación: centros a d_act, cada destino `beyond` más allá del otro peatón."""
    R = radius + d_lat
    s, D = d_act, d_act + beyond
    slope = R * D / (s * (D - s))                      # y'(0) con l = 0
    e = np.array([1.0, slope]) / np.hypot(1.0, slope)  # (a lo largo, hacia la derecha propia)

    apply_academic_style()
    fig, ax = plt.subplots(figsize=(11, 5.6))

    # d_act: entre centros
    ax.annotate("", xy=(d_act, 0), xytext=(0, 0), zorder=7,
                arrowprops={"arrowstyle": "<->", "color": "black", "lw": 1.8, "mutation_scale": 22,
                            "shrinkA": 0, "shrinkB": 0})
    ax.text(d_act / 2, 0.14, r"$d_{\mathrm{act}}$", fontsize=FS + 2, ha="center", va="bottom")

    # (centro, sentido de avance, lado derecho propio en pantalla, colores, nombre)
    peatones = (
        (0.0, 1, -1, BLUE, DARK_BLUE, "Peatón 1"),
        (d_act, -1, 1, VERMILLION, DARK_ORANGE, "Peatón 2"),
    )
    for (cx, fwd, right, color, dark, name), (ox, *_rest) in zip(peatones, peatones[::-1]):
        ax.add_patch(Circle((cx, 0), radius, facecolor=color, edgecolor="black", linewidth=1.3, zorder=5))
        ax.plot(cx, 0, marker="o", markersize=6, color="black", zorder=8)
        # nombre del lado de su propia derecha, donde no hay cota
        ax.text(cx, right * (R + 0.42), name, color=color, ha="center", va="center", fontsize=FS - 2)
        # dirección deseada: tangente a la parábola auxiliar, hacia la derecha propia
        tip = (cx + fwd * 1.9 * e[0], right * 1.9 * e[1])
        ax.annotate("", xy=tip, xytext=(cx, 0), zorder=9,
                    arrowprops={"arrowstyle": "-|>", "color": dark, "lw": 3.6, "mutation_scale": 26,
                                "shrinkA": 0, "shrinkB": 0})
        ax.text(tip[0] + fwd * 0.28, tip[1] + right * 0.12, r"$\mathbf{e}_0$", color=dark,
                fontsize=FS, ha="center", va="center")
        # sobre el OTRO peatón: círculo de radio R y margen d_lat hasta el punto auxiliar P
        ax.add_patch(Circle((ox, 0), R, facecolor="none", edgecolor="0.35", linewidth=1.6,
                            linestyle=(0, (1, 2.4)), zorder=3))
        y0, y1 = right * radius, right * R
        ax.plot([ox, ox], [y0, y1], color=RED, linewidth=2.8, zorder=8, solid_capstyle="butt")
        ax.plot([ox - 0.11, ox + 0.11], [y0, y0], color=RED, linewidth=2.8, zorder=8)
        ax.plot(ox, y1, marker="o", markersize=11, markerfacecolor=GREEN, markeredgecolor="black",
                markeredgewidth=1.2, zorder=10)
        ax.text(ox - fwd * 0.16, (y0 + y1) / 2 + right * 0.04, r"$d_{\mathrm{lat}}$", color=RED, fontsize=FS,
                ha="right" if fwd > 0 else "left", va="center")

    ax.set_xlim(-R - 0.3, d_act + R + 0.3)
    ax.set_ylim(-R - 0.8, R + 0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d-act", type=float, default=5.0, help="distancia de activación dibujada (default: 5)")
    parser.add_argument("--d-lat", type=float, default=0.9, help="margen lateral dibujado (default: 0.9)")
    parser.add_argument("--radius", type=float, default=0.5, help="radio dibujado de cada peatón (default: 0.5)")
    parser.add_argument("--beyond", type=float, default=3.0,
                        help="distancia del destino más allá del otro peatón, fija la inclinación de e0 (default: 3)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help=f"PNG de salida (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()
    if min(args.d_act, args.radius, args.beyond) <= 0 or args.d_lat < 0:
        parser.error("d_act, radius y beyond deben ser positivos y d_lat no negativo")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    figure = create_figure(args.d_act, args.d_lat, args.radius, args.beyond)
    figure.savefig(args.out, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(figure)
    print(f"PNG guardado en: {args.out}")


if __name__ == "__main__":
    main()
