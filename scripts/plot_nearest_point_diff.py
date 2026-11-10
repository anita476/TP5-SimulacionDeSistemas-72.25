#!/usr/bin/env python3
"""
Grafica las 2 curvas de diferencia (distancia^2 mínima al punto simulado más cercano)
en función del tiempo, a partir del archivo generado por metrica_punto_cercano.py.
Las líneas punteadas horizontales marcan el promedio E2 de cada partícula.

Color: izquierda = VIOLET, derecha = RED. La partícula de la izquierda es la que
empieza con menor x_exp. El tiempo es (frame - frame inicial común) / fps.

Uso:
    python graficar_diferencias.py --diff resultados_E2.txt
    python graficar_diferencias.py --diff resultados_E2.txt --fps 15.0192 --outdir figuras

Si se quiere tomar el fps del archivo experimental: agregar --traj prueba6.txt.
Requiere plot_style.py en la misma carpeta.
"""
import argparse
import os
import re

import matplotlib
import numpy as np

matplotlib.use("Agg")

from lib.plot_style import VIOLET, RED, apply_academic_style, style_axes

FPS_DEFECTO = 15.0192


def leer_fps(ruta):
    with open(ruta) as f:
        for linea in f:
            m = re.match(r"#\s*framerate:\s*([\d.]+)", linea)
            if m:
                return float(m.group(1))
    return None


def leer_diff(ruta):
    """Devuelve {prueba: {id: {'frames','x','d2','prom'}}} leyendo el archivo de resultados."""
    pruebas, prueba, pid = {}, None, None
    with open(ruta) as f:
        for linea in f:
            s = linea.strip()
            m = re.match(r"=+\s*(\S+?)(?:\.txt)?\s+vs\s", s)
            if m:
                prueba, pid = m.group(1), None
                pruebas[prueba] = {}
                continue
            m = re.match(r"-+\s*Part[ií]cula\s+(\d+)\s*-+", s)
            if m and prueba:
                pid = int(m.group(1))
                pruebas[prueba][pid] = {"frames": [], "x": [], "d2": [], "prom": None}
                continue
            m = re.match(r"Promedio E2 part[ií]cula\s+(\d+).*:\s*([-+\d.eE]+)\s*$", s)
            if m and prueba:
                pruebas[prueba][int(m.group(1))]["prom"] = float(m.group(2))
                continue
            c = s.split()
            if pid is not None and len(c) == 6 and c[0].isdigit():
                d = pruebas[prueba][pid]
                d["frames"].append(int(c[0]))
                d["x"].append(float(c[1]))
                d["d2"].append(float(c[5]))
    return pruebas


def graficar(prueba, particulas, fps, outdir):
    ids = sorted(particulas, key=lambda p: particulas[p]["x"][0])  # menor x inicial -> izquierda
    estilo = dict(zip(ids, [("izquierda", VIOLET), ("derecha", RED)]))
    t0 = min(particulas[p]["frames"][0] for p in ids)

    apply_academic_style()
    import matplotlib.pyplot as plt

    width, height = 12.0, 7.0
    left_in, right_in, top_in, bottom_in = 1.5, 0.3, 0.3, 2.4
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes(
        (left_in / width, bottom_in / height,
         (width - left_in - right_in) / width, (height - bottom_in - top_in) / height)
    )
    style_axes(ax, r"tiempo $t$ (s)", r"$d^2_{\min}$ (m$^2$)")

    for pid in ids:
        nombre, color = estilo[pid]
        d = particulas[pid]
        t = (np.array(d["frames"]) - t0) / fps
        ax.plot(t, d["d2"], color=color, lw=2.0, zorder=3, label=nombre)
        if d["prom"] is not None:
            ax.axhline(d["prom"], color=color, ls="--", lw=1.4, alpha=0.8, zorder=2)
    ax.plot([], [], color="0.3", ls="--", lw=1.4, label="promedio $E^{(2)}$")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=True, fancybox=False)

    os.makedirs(outdir, exist_ok=True)
    
    ruta = os.path.join(outdir, f"diferencias_{prueba}.png")
    fig.savefig(ruta)
    print(f"Guardado: {ruta}")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", required=True, help="archivo generado por metrica_punto_cercano.py")
    ap.add_argument("--traj", help="(opcional) archivo experimental, solo para leer el framerate")
    ap.add_argument("--fps", type=float, help=f"cuadros por segundo (defecto {FPS_DEFECTO})")
    ap.add_argument("--outdir", default=".", help="carpeta de salida")
    args = ap.parse_args()

    fps = args.fps or (leer_fps(args.traj) if args.traj else None) or FPS_DEFECTO
    pruebas = leer_diff(args.diff)
    if not pruebas:
        raise SystemExit(f"No se encontraron datos en {args.diff}")
    for prueba, particulas in pruebas.items():
        graficar(prueba, particulas, fps, args.outdir)


if __name__ == "__main__":
    main()