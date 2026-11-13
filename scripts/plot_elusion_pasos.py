#!/usr/bin/env python3
"""Dos esquemas de la capa de elusión con la misma escena (geometría exacta).

Marco local de i: u hacia el destino (derecha), n = derecha de i (abajo en la imagen, y = -n).
i = (0, 0), destino = (D, 0), j = (s, l).  R = r_j + d_lat,  P = (s, l + R),
target temporal = (s, s*y'(0)) sobre la tangente a la parábola en i.
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle

from lib.plot_style import BLUE, VERMILLION, GREEN, RED, apply_academic_style

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "docs/presentation/images"
D, s, l, r, d_lat, d_act = 12.0, 5.2, -1.1, 1.0, 1.3, 9.5   # unidades arbitrarias, relaciones exactas
R = r + d_lat
Pn = l + R                                # coordenada n de P
slope = Pn * D / (s * (D - s))            # y'(0)
XLIM, YLIM = (-1.8, 13.9), (-3.3, 3.75)
FS = 28
DARK = "#004C7A"


def scene():
    apply_academic_style()
    matplotlib.rcParams["svg.fonttype"] = "path"
    fig, ax = plt.subplots(figsize=(11.6, 11.6 * (YLIM[1] - YLIM[0]) / (XLIM[1] - XLIM[0])))
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM); ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def actors(ax):
    ax.add_patch(Circle((0, 0), r, facecolor=BLUE, edgecolor="black", linewidth=1.4, zorder=5))
    ax.add_patch(Circle((s, -l), r, facecolor=VERMILLION, edgecolor="black", linewidth=1.4, zorder=5))
    ax.plot(D, 0, marker="*", markersize=30, color="black", zorder=7, clip_on=False)
    ax.text(D + 0.4, 0, "destino", fontsize=FS - 4, ha="left", va="center")
    ax.text(-r - 0.2, 0.6, "$i$", fontsize=FS, ha="right", va="center")
    ax.text(s - 0.85, -l + 0.95, "$j$", fontsize=FS, ha="right", va="center")


def arrow(ax, p, q, color="black", lw=3.0, scale=24, style="-|>", zorder=9):
    ax.annotate("", xy=q, xytext=p, zorder=zorder,
                arrowprops={"arrowstyle": style, "color": color, "lw": lw, "mutation_scale": scale,
                            "shrinkA": 0, "shrinkB": 0})


def cota(ax, p, q, half=0.15, lw=1.7, zorder=8, color="black"):
    """Segmento con topes perpendiculares en los extremos."""
    ax.plot([p[0], q[0]], [p[1], q[1]], color=color, linewidth=lw, zorder=zorder, solid_capstyle="butt")
    d = np.array(q, float) - np.array(p, float); nrm = np.array([-d[1], d[0]]) / np.hypot(*d) * half
    for pt in (p, q):
        ax.plot([pt[0] - nrm[0], pt[0] + nrm[0]], [pt[1] - nrm[1], pt[1] + nrm[1]], color=color, linewidth=lw, zorder=zorder)


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


# ---------------- Figura 1: detección del conflicto ----------------
fig, ax = scene()
ax.add_patch(Rectangle((0, -R), D, 2 * R, facecolor="0.94", edgecolor="0.7", linewidth=1.0, zorder=0))
# zona de conflicto: corredor ∩ alcance d_act
zona = Rectangle((0, -R), D, 2 * R, facecolor=BLUE, alpha=0.16, edgecolor="none", zorder=1)
ax.add_patch(zona); zona.set_clip_path(Circle((0, 0), d_act, transform=ax.transData))
ax.plot([0, D], [0, 0], color="0.45", linestyle="--", linewidth=1.8, zorder=2)
half = np.degrees(np.arcsin(R / d_act)) + 2.2
ang = np.radians(np.linspace(-half, half, 200))
ax.plot(d_act * np.cos(ang), d_act * np.sin(ang), color="0.2", linewidth=2.2, zorder=3)
a_r = np.radians(-10.5)
arrow(ax, (0, 0), (d_act * np.cos(a_r), d_act * np.sin(a_r)), lw=1.8, scale=22, style="->", zorder=8)
ax.text(6.3, -1.72, r"$d_{\mathrm{act}}$", fontsize=FS, ha="center", va="center")
actors(ax)
ax.plot(0, 0, marker="o", markersize=9, color="black", zorder=11)   # centro de i: origen de u, n y d_act
# ejes locales
arrow(ax, (0, 0), (2.4, 0)); ax.text(2.0, 0.5, r"$\hat{\mathbf{u}}$", fontsize=FS, ha="center", va="center")
arrow(ax, (0, 0), (0, -2.0)); ax.text(-0.5, -1.75, r"$\hat{\mathbf{n}}$", fontsize=FS, ha="center", va="center")
# s: de i a la proyección de j
for xg, y0 in ((0, r), (s, -l + r)):
    ax.plot([xg, xg], [y0, 3.05], color="0.45", linestyle=":", linewidth=1.3, zorder=1)
arrow(ax, (0, 2.85), (s, 2.85), lw=1.5, scale=20, style="<->")
ax.text(s / 2, 3.3, "$s$", fontsize=FS, ha="center", va="center")
# l: del eje al centro de j
ax.plot([s, s], [0, -l], color="black", linewidth=2.6, zorder=8)
ax.plot([s, s], [0, -l], linestyle="none", marker="o", markersize=6, color="black", zorder=9)
ax.text(s + 0.38, -l / 2 + 0.05, r"$\ell$", fontsize=FS, ha="center", va="center", zorder=9)
# R y D
cota(ax, (10.9, 0), (10.9, r)); ax.text(10.65, r / 2, r"$r_j$", fontsize=FS - 4, ha="right", va="center")
cota(ax, (10.9, r), (10.9, R), color=RED, lw=2.6)
ax.text(10.65, (r + R) / 2, r"$d_{\mathrm{lat}}$", fontsize=FS - 4, color=RED, ha="right", va="center")
ax.text(10.9, R + 0.5, r"$R = r_j + d_{\mathrm{lat}}$", fontsize=FS - 2, ha="center", va="center")
cota(ax, (10.9, 0), (10.9, -R)); ax.text(11.15, -R / 2, "$R$", fontsize=FS, ha="left", va="center")
arrow(ax, (0, -2.62), (D, -2.62), lw=1.5, scale=20, style="<->")
ax.plot([D, D], [-0.45, -2.8], color="0.45", linestyle=":", linewidth=1.3, zorder=1)
ax.plot([0, 0], [-2.0, -2.8], color="0.45", linestyle=":", linewidth=1.3, zorder=1)
ax.text(D / 2, -3.0, "$D$", fontsize=FS, ha="center", va="center",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})
save(fig, "elusion_deteccion")

# ---------------- Figura 2: target temporal y dirección deseada ----------------
fig, ax = scene()
ax.plot([0, D], [0, 0], color="0.45", linestyle="--", linewidth=1.8, zorder=2)
ax.add_patch(Circle((s, -l), R, facecolor="none", edgecolor=VERMILLION, linewidth=2.0, linestyle=(0, (1, 2.4)), zorder=3))
x = np.linspace(0, D, 400)
ax.plot(x, -Pn * x * (D - x) / (s * (D - s)), color=GREEN, linewidth=2.4, zorder=6)   # parábola auxiliar
actors(ax)
# dirección directa (gris) y dirección deseada (azul), con el ángulo entre ambas
L = 3.3
e = np.array([1.0, -slope]) / np.hypot(1.0, slope)
T = np.array([s, -s * slope])                                  # target temporal
arrow(ax, (0, 0), (L, 0), color="0.55", lw=3.0)
ax.plot([0, T[0]], [0, T[1]], color=DARK, linestyle="--", linewidth=1.6, zorder=7)
arrow(ax, (0, 0), tuple(L * e), color=DARK, lw=4.2, scale=30, zorder=10)
ax.add_patch(Arc((0, 0), 4.4, 4.4, theta1=-np.degrees(np.arctan(slope)), theta2=0, color="black", linewidth=1.3, zorder=8))
ax.text(1.75, -1.55, r"$\mathbf{e}_0$", fontsize=FS + 2, color=DARK, ha="center", va="center")
ax.plot(*T, marker="*", markersize=26, markerfacecolor=DARK, markeredgecolor="black", markeredgewidth=1.0, zorder=10)
ax.text(T[0] + 0.45, T[1] - 0.12, "target temporal", fontsize=FS - 4, color=DARK, ha="left", va="center")
# R = r_j + d_lat sobre la vertical de j
ax.plot([s, s], [-l, -l - r], color="black", linewidth=1.7, zorder=8)
ax.plot(s, -l, marker="o", markersize=6, color="black", zorder=9)
ax.text(s + 0.14, -l - r / 2 + 0.05, r"$r_j$", fontsize=FS - 2, ha="left", va="center", zorder=9)
cota(ax, (s, -l - r), (s, -Pn), color=RED, lw=2.8)
ax.text(s - 0.28, (-l - r - Pn) / 2 - 0.1, r"$d_{\mathrm{lat}}$", fontsize=FS, color=RED, ha="right", va="center",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2}, zorder=7)
ax.plot(s, -Pn, marker="o", markersize=13, markerfacecolor=GREEN, markeredgecolor="black", markeredgewidth=1.3, zorder=11)
ax.text(s + 0.32, -Pn + 0.48, "$P$", fontsize=FS, ha="left", va="center",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0}, zorder=7)
a_R = np.radians(38)                                            # un radio del círculo punteado, etiquetado
cR = np.array([s + R * np.cos(a_R), -l + R * np.sin(a_R)])
arrow(ax, (s, -l), tuple(cR), lw=1.5, scale=18, style="->", zorder=8)
ax.text(cR[0] + 0.3, cR[1] + 0.22, r"$R = r_j + d_{\mathrm{lat}}$", fontsize=FS - 2, ha="left", va="center")
ax.text(9.2, -1.45, "parábola auxiliar", fontsize=FS - 4, color="#007A59", ha="center", va="center")
save(fig, "elusion_activacion")
print(f"R={R}, P=(s, {Pn:.3f}), y'(0)={slope:.4f}, target temporal=(s, {s*slope:.3f})")
