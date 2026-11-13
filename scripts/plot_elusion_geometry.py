#!/usr/bin/env python3
"""Esquema de la capa de elusión en el marco de la partícula.

Ejes del dibujo: û apunta de la partícula i a su target final (hacia la derecha
de la página) y n̂ = (u_y, -u_x) es la derecha de la partícula (hacia abajo en la
página). El obstáculo j está en (s, ℓ) en esas coordenadas. Hay conflicto si
0 < s < D y |ℓ| < R, con R = r_min + r_j. La dirección deseada e0 es la tangente
en el origen de la parábola que pasa por (0, 0), P = (s, ℓ + R) y (D, 0), igual
que `new_desired_direction` en src/utils/quadratic_heuristic.cpp.

Uso:
    python scripts/plot_elusion_geometry.py
    python scripts/plot_elusion_geometry.py --s 3 --l 0.1 --r-min 0.25
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from plot_style import BLUE, GREEN, VERMILLION, apply_academic_style, save_figure  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--D", type=float, default=6.0, help="distancia de la partícula a su target (m)")
    parser.add_argument("--s", type=float, default=2.6, help="coordenada del obstáculo a lo largo de û (m)")
    parser.add_argument("--l", type=float, default=-0.15, help="coordenada lateral del obstáculo, + = derecha (m)")
    parser.add_argument("--r", type=float, default=0.25, help="radio de las partículas (m)")
    parser.add_argument("--r-min", type=float, default=0.3, help="parámetro r_min (m)")
    parser.add_argument("--d-a", type=float, default=4.0, help="parámetro distancia de acción d_a (m)")
    parser.add_argument("--out", type=Path, default=REPO / "docs" / "presentation" / "images" / "esquema_elusion.png")
    args = parser.parse_args()

    D, s, lat, r, d_a = args.D, args.s, args.l, args.r, args.d_a
    R = args.r_min + r
    if not (0.0 < s < D and abs(lat) < R):
        parser.error("la geometría pedida no es un conflicto: se necesita 0 < s < D y |l| < r_min + r")
    lat_p = lat + R  # coordenada lateral del punto de paso P
    slope = lat_p * D / (s * (D - s))  # y'(0) de la parábola
    e0 = np.array([1.0, slope]) / np.hypot(1.0, slope)

    apply_academic_style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    def page(x, lateral):
        """Coordenadas (û, n̂) -> página: la derecha de la partícula queda hacia abajo."""
        return x, -lateral

    fig, ax = plt.subplots(figsize=(13.0, 5.6), layout="constrained")
    font = matplotlib.rcParams["font.size"]

    # corredor de conflicto |ℓ| < R entre la partícula y su target
    ax.add_patch(Rectangle((0.0, -R), D, 2.0 * R, facecolor="0.9", edgecolor="0.6", linewidth=1.0, zorder=0))
    ax.text(D, -R - 0.1, r"corredor de conflicto: $|\ell| < R = r_{min} + r_j$", ha="right", va="top", fontsize=font)

    # recta al target final y versores
    ax.plot([0.0, D], [0.0, 0.0], color="0.35", linestyle="--", linewidth=1.5, zorder=1)
    ax.plot(D, 0.0, marker="*", color="black", markersize=20, zorder=5)
    ax.text(D + 0.12, 0.0, "target\nfinal", ha="left", va="center", fontsize=font)
    arrow = dict(arrowstyle="-|>", mutation_scale=22, linewidth=2.0, shrinkA=0, shrinkB=0)
    ax.annotate("", xy=(0.95, 0.0), xytext=(0.0, 0.0), arrowprops=dict(color="black", **arrow), zorder=6)
    ax.text(0.98, 0.07, r"$\hat{\mathbf{u}}$", ha="left", va="bottom", fontsize=font)
    ax.annotate("", xy=page(0.0, 0.8), xytext=(0.0, 0.0), arrowprops=dict(color="black", **arrow), zorder=6)
    ax.text(-0.08, -0.8, r"$\hat{\mathbf{n}}$", ha="right", va="center", fontsize=font)

    # alcance de la distancia de acción d_a
    half = np.arcsin(min(1.0, (R + 0.25) / d_a))  # el arco sobresale del corredor solo hacia arriba
    angle = np.linspace(-np.arcsin(min(1.0, R / d_a)), half, 100)
    ax.plot(d_a * np.cos(angle), d_a * np.sin(angle), color="0.35", linestyle=":", linewidth=1.8, zorder=1)
    ax.text(d_a * np.cos(half), d_a * np.sin(half) + 0.05, r"$d_a$", ha="center", va="bottom", fontsize=font)

    # partícula i, obstáculo j y su círculo de radio R
    ax.add_patch(Circle((0.0, 0.0), r, facecolor=BLUE, edgecolor="black", alpha=0.85, zorder=4))
    ax.text(-r - 0.08, 0.12, r"$i$", ha="right", va="bottom", fontsize=font)
    xj, yj = page(s, lat)
    ax.add_patch(Circle((xj, yj), r, facecolor=VERMILLION, edgecolor="black", alpha=0.85, zorder=4))
    ax.add_patch(Circle((xj, yj), R, fill=False, edgecolor=VERMILLION, linestyle=":", linewidth=1.8, zorder=3))
    ax.text(xj + 0.02, yj + r + 0.04, r"$j$", ha="center", va="bottom", fontsize=font)

    # parábola por (0,0), P y (D,0); P es el target temporal
    x = np.linspace(0.0, D, 300)
    ax.plot(x, -(lat_p * x * (D - x) / (s * (D - s))), color=GREEN, linewidth=2.5, zorder=5)
    xp, yp = page(s, lat_p)
    ax.plot(xp, yp, marker="o", color=GREEN, markeredgecolor="black", markersize=11, zorder=7)
    ax.text(xp, yp - 0.12, r"$P = (s,\ \ell + R)$", ha="center", va="top", fontsize=font)

    # dirección deseada e0: tangente a la parábola en la partícula
    tip = page(*(1.25 * e0))
    ax.annotate("", xy=tip, xytext=(0.0, 0.0), arrowprops=dict(color=BLUE, **arrow), zorder=8)
    ax.text(tip[0] + 0.05, tip[1] - 0.05, r"$\mathbf{e}^{target}_i$", ha="left", va="top", color=BLUE, fontsize=font)

    # cotas de s y de R
    dim = dict(arrowstyle="<->", color="black", linewidth=1.2, shrinkA=0, shrinkB=0)
    y_dim = R + 0.22
    ax.annotate("", xy=(s, y_dim), xytext=(0.0, y_dim), arrowprops=dim)
    ax.text(0.5 * s, y_dim + 0.04, r"$s$", ha="center", va="bottom", fontsize=font)
    ax.annotate("", xy=(xp, yp), xytext=(xj, yj), arrowprops=dim, zorder=6)
    ax.text(xj + 0.06, 0.5 * (yj - r + yp), r"$R$", ha="left", va="center", fontsize=font)

    ax.set_aspect("equal")
    ax.set_xlim(-0.75, D + 1.05)
    ax.set_ylim(-R - 0.5, R + 0.6)
    ax.axis("off")
    save_figure(fig, args.out)
    print(f"# R = {R:.3f} m, P = ({s:.2f}, {lat_p:.3f}), y'(0) = {slope:.4f}, e0 = ({e0[0]:.4f}, {e0[1]:.4f})")


if __name__ == "__main__":
    main()
