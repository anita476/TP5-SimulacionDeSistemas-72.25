#!/usr/bin/env python3
"""
Dibuja las 4 curvas de recorrido (2 experimentales + 2 simuladas) en el plano (x, y).

Color: izquierda = BLUE, derecha = VERMILLION (como en anim.py).
Línea continua = experimental, línea punteada = simulado.
La partícula de la izquierda es la que empieza con menor x en la trayectoria experimental.

Uso:
    python graficar_trayectorias.py --traj prueba6.txt --sim prueba6_sim.txt
    python graficar_trayectorias.py --traj prueba6.txt prueba7.txt --sim prueba6_sim.txt prueba7_sim.txt --outdir figuras

Requiere plot_style.py y metrica_punto_cercano.py en la misma carpeta.
"""
import argparse
import os

import matplotlib

matplotlib.use("Agg")

from calculate_nearest_point import leer_real, leer_sim
from lib.plot_style import BLUE, VERMILLION, apply_academic_style, style_axes


def graficar(ruta_real, ruta_sim, outdir):
    real, sim = leer_real(ruta_real), leer_sim(ruta_sim)
    ids = [pid for pid in real if pid in sim]
    if not ids:
        raise SystemExit(f"{ruta_real}: no hay ids en común con {ruta_sim}")
    ids.sort(key=lambda pid: real[pid][1][0, 0])  # menor x inicial primero -> izquierda
    estilo = {}
    for pid, (nombre, color) in zip(ids, [("izquierda", BLUE), ("derecha", VERMILLION)]):
        estilo[pid] = (nombre, color)

    apply_academic_style()
    import matplotlib.pyplot as plt

    todos = [real[p][1] for p in ids] + [sim[p] for p in ids]
    margin = 0.2
    x0 = min(a[:, 0].min() for a in todos) - margin
    x1 = max(a[:, 0].max() for a in todos) + margin
    y0 = min(a[:, 1].min() for a in todos) - margin
    y1 = max(a[:, 1].max() for a in todos) + margin

    # Altura de la figura según la proporción de los datos (ejes con aspecto igual)
    width, left_in, right_in, top_in, bottom_in = 12.0, 1.3, 0.3, 0.3, 2.4
    ax_w = width - left_in - right_in
    ax_h = ax_w * (y1 - y0) / (x1 - x0)
    height = ax_h + top_in + bottom_in
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes((left_in / width, bottom_in / height, ax_w / width, ax_h / height))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    style_axes(ax, r"posición $x$ (m)", r"posición $y$ (m)")

    for pid in ids:
        nombre, color = estilo[pid]
        xy = real[pid][1]
        ax.plot(xy[:, 0], xy[:, 1], color=color, lw=2.0, alpha=0.9, zorder=3, label=f"{nombre} (exp.)")
        ax.plot(sim[pid][:, 0], sim[pid][:, 1], color=color, lw=2.0, ls="--", zorder=4, label=f"{nombre} (sim.)")

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=True, fancybox=False)

    base = os.path.splitext(os.path.basename(ruta_real))[0]
    os.makedirs(outdir, exist_ok=True)
  
    ruta = os.path.join(outdir, f"trayectorias_{base}.png")
    fig.savefig(ruta)
    print(f"Guardado: {ruta}")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", nargs="+", required=True, help="archivo(s) experimental(es) pruebaX.txt")
    ap.add_argument("--sim", nargs="+", required=True, help="archivo(s) simulado(s) pruebaX_sim.txt")
    ap.add_argument("--outdir", default=".", help="carpeta de salida")
    args = ap.parse_args()
    if len(args.traj) != len(args.sim):
        ap.error("--traj y --sim deben tener la misma cantidad de archivos.")
    for r, s in zip(args.traj, args.sim):
        graficar(r, s, args.outdir)


if __name__ == "__main__":
    main()