#!/usr/bin/env python3
"""Esquema minimalista de la capa de elusión: cómo se toman r_o, d_lat y d_act."""
import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

plt.rcParams["mathtext.fontset"] = "cm"

BLUE, ORANGE, GREEN, GRAY = "#0072B2", "#D55E00", "#009E73", "#4d4d4d"
R_P, R_O, D_LAT = 0.40, 0.40, 1.00   # R_P solo para dibujar la partícula
R = D_LAT + R_O                       # distancia de paso: borde del obstáculo -> centro de la partícula = d_lat
P, O, T = np.array([1.5, 2.5]), np.array([5.0, 2.5]), np.array([9.3, 2.5])


def arrow(ax, p, q, **kw):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(
        arrowstyle=kw.pop("style", "<->"), color=kw.pop("color", "k"), lw=kw.pop("lw", 1.8),
        shrinkA=0, shrinkB=0, **kw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="diagrama_elusion.png")
    ap.add_argument("--no-show", action="store_true")
    a = ap.parse_args()

    fig, ax = plt.subplots(figsize=(10, 6.6))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 10, 5, fc="#f7f7f5", ec="k", lw=3.5))

    # trayectoria directa y trayectoria con elusión
    ax.plot([P[0], T[0]], [2.5, 2.5], color="#999999", ls="--", lw=1.6, zorder=1)
    s = np.linspace(P[0], T[0], 200)
    x0, x1, x2 = P[0], O[0], T[0]
    y = 2.5 - R * (s - x0) * (s - x2) / ((x1 - x0) * (x1 - x2))
    ax.plot(s, y, color="k", lw=2.2, zorder=2)
    tangent_slope = -R * (x0 - x2) / ((x1 - x0) * (x1 - x2))
    e0 = np.array([1.0, tangent_slope])
    e0 /= np.linalg.norm(e0)

    # target: cruz verde inclinada 45 grados
    h = 0.35 / np.sqrt(2)
    for sgn in (1, -1):
        ax.plot([T[0] - h, T[0] + h], [T[1] - sgn * h, T[1] + sgn * h],
                color=GREEN, lw=7, solid_capstyle="butt", zorder=3)

    # d_act: del centro de la partícula al centro del obstáculo
    d_act, y_act = O[0] - P[0], 3.7
    for x in (P[0], P[0] + d_act):
        ax.plot([x, x], [2.5, y_act + 0.15], color="#777777", ls=":", lw=1.6, zorder=1)
    arrow(ax, (P[0], y_act), (P[0] + d_act, y_act))
    ax.text(P[0] + d_act / 2, y_act + 0.15, r"$d_{\mathrm{act}}$", fontsize=26, ha="center")

    # partícula
    ax.add_patch(Circle(P, R_P, fc=BLUE, ec="k", lw=1.5, zorder=4))
    ax.plot(*P, ".", color="k", ms=5, zorder=6)
    e0_tip = P + 1.65 * e0
    arrow(ax, P, e0_tip, style="-|>", color=BLUE, lw=2.6, mutation_scale=22)
    ax.text(e0_tip[0] + 0.08, e0_tip[1] - 0.12, r"$e_0$",
            color=BLUE, fontsize=24, ha="left", va="top")

    # obstáculo y radio r_o
    ax.add_patch(Circle(O, R_O, fc=ORANGE, ec="k", lw=1.5, zorder=4))
    ax.plot(*O, ".", color="k", ms=5, zorder=6)

    # partícula al pasar: su centro queda a d_lat del borde del obstáculo
    G = np.array([O[0], O[1] - R])
    ax.add_patch(Circle(G, R_P, fc="none", ec=BLUE, ls="--", lw=2, zorder=4))
    ax.plot(*G, ".", color=BLUE, ms=6, zorder=5)

    # d_lat: del borde del obstáculo al CENTRO de la partícula
    y_top, y_bot = O[1] - R_O, G[1]
    arrow(ax, (O[0], y_top), (O[0], y_bot))
    ax.text(O[0] + 0.2, y_top - 0.3, r"$d_{\mathrm{lat}}$", fontsize=26, va="center")

    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-1.6, 5.2)

    fig.savefig(a.out, dpi=150, bbox_inches="tight")
    print(f"Guardado en {a.out}")
    if not a.no_show:
        plt.show()


if __name__ == "__main__":
    main()