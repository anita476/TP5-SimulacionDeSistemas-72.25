#!/usr/bin/env python3
"""
Grafica las 2 curvas de diferencia (distancia^2 mínima al punto simulado más cercano)
en función del tiempo, a partir del archivo generado por metrica_punto_cercano.py.
Las líneas punteadas horizontales marcan el promedio E2 de cada partícula.

Color: izquierda = BLUE, derecha = VERMILLION (como en plot_traj.py). La partícula de la izquierda es la que
empieza con menor x_exp. El tiempo es (frame - frame inicial común) / fps.

Uso:
    python graficar_diferencias.py --diff resultados_E2.txt
    python graficar_diferencias.py --diff resultados_E2.txt --fps 15.0192 --outdir figuras
    python plot_nearest_point_diff.py --diff E1_15.txt E1_11.txt --paneles evol_E1.png   # paneles, para diapositiva

Si se quiere tomar el fps del archivo experimental: agregar --traj prueba6.txt.
Requiere plot_style.py en la misma carpeta.
"""
import argparse
import re
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.ticker import MultipleLocator

matplotlib.use("Agg")

from lib.plot_style import (
    BLUE,
    VERMILLION,
    apply_academic_style,
    new_figure,
    place_legend_below,
    save_figure,
    style_axes,
)

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
            # archivos de ambas métricas: "Promedio E1 ..." (iguales tiempos) y "Promedio E2 ..." (punto más cercano)
            m = re.match(r"Promedio E[12] part[ií]cula\s+(\d+).*:\s*([-+\d.eE]+)\s*$", s)
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


def leer_metrica(ruta):
    """1 si el archivo es de la Métrica 1 (cabecera "# Métrica E(1)"), 2 en cualquier otro caso."""
    with open(ruta) as f:
        return 1 if "E(1)" in f.readline() else 2


def potencia_de_10(maximo):
    """Exponente que va en el rótulo del eje, no flotando arriba del eje (guía 1.9); 0 = valores sin factor."""
    orden = int(np.floor(np.log10(maximo))) if maximo > 0 else 0
    return orden if orden < -1 else 0


def nombre_eje(metrica, orden):
    unidad = f"10$^{{{orden}}}$ m$^2$" if orden else "m$^2$"
    nombre = "Distancia cuadrática" if metrica == 1 else "Distancia cuadrática mínima"
    return f"{nombre} ({unidad})"


def curvas(ax, particulas, fps, escala, metrica):
    """Las dos curvas d^2(t) y el promedio de cada peatón (línea punteada de su color)."""
    ids = sorted(particulas, key=lambda p: particulas[p]["x"][0])  # menor x inicial -> izquierda
    estilo = dict(zip(ids, [("peatón izquierdo", BLUE), ("peatón derecho", VERMILLION)]))
    t0 = min(particulas[p]["frames"][0] for p in ids)
    for pid in ids:
        nombre, color = estilo[pid]
        d = particulas[pid]
        t = (np.array(d["frames"]) - t0) / fps
        ax.plot(t, np.array(d["d2"]) / escala, color=color, lw=2.0, zorder=3, label=nombre)
        if d["prom"] is not None:
            ax.axhline(d["prom"] / escala, color=color, ls="--", lw=1.4, alpha=0.8, zorder=2)
    ax.plot([], [], color="0.3", ls="--", lw=1.4, label=rf"promedio $E^{{({metrica})}}_i$")
    ax.set_xlim(left=0)


def graficar(prueba, particulas, fps, outdir, metrica=2):
    orden = potencia_de_10(max(np.nanmax(particulas[p]["d2"]) for p in particulas))
    fig, ax = new_figure()
    style_axes(ax, "Tiempo (s)", nombre_eje(metrica, orden))
    curvas(ax, particulas, fps, 10.0**orden, metrica)
    ax.set_ylim(bottom=0)
    place_legend_below(ax, ncol=3)
    save_figure(fig, Path(outdir) / f"diferencias_{prueba}.png")


def graficar_paneles(pruebas, fps, salida, metrica, figsize):
    """Un panel por evento, lado a lado: un solo rótulo por eje (misma magnitud y unidad) y una sola leyenda
    centrada debajo (como fv_paneles del TP4). El número de evento va arriba de cada panel."""
    import matplotlib.pyplot as plt

    apply_academic_style()
    maximo = max(np.nanmax(d["d2"]) for particulas in pruebas.values() for d in particulas.values())
    orden = potencia_de_10(maximo)
    escala = 10.0**orden
    # misma magnitud y unidad en todos los paneles, pero cada uno con su escala: con escala común, un evento
    # de error chico queda aplastado contra cero (en la métrica 2, 0.025 m^2 contra 0.25 m^2)
    fig, axes = plt.subplots(1, len(pruebas), figsize=figsize, layout="constrained")
    axes = np.atleast_1d(axes)
    for ax, (prueba, particulas) in zip(axes, pruebas.items()):
        style_axes(ax, "", "")
        curvas(ax, particulas, fps, escala, metrica)
        ax.set_ylim(bottom=0)
        ax.ticklabel_format(axis="y", style="plain")
        ax.set_title(f"Evento {re.sub(r'[^0-9]', '', prueba)}")
        ax.xaxis.set_major_locator(MultipleLocator(2))
    tamano = matplotlib.rcParams["axes.labelsize"]  # sup*label usa por defecto un tamaño mayor que los rótulos de eje
    xlabel = fig.supxlabel("Tiempo (s)", fontsize=tamano)
    ylabel = fig.supylabel(nombre_eje(metrica, orden), fontsize=tamano)

    # la leyenda va debajo del rótulo x: se fija la disposición y se la ubica bajo el rótulo
    fig.canvas.draw()
    fig.set_layout_engine("none")
    renderer = fig.canvas.get_renderer()
    debajo = xlabel.get_window_extent(renderer).y0 - 0.05 * fig.dpi
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="upper center", ncol=len(labels),
                        bbox_to_anchor=(0.5, debajo / fig.bbox.height))
    save_figure(fig, Path(salida), extra=(legend, xlabel, ylabel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", required=True, nargs="+", help="archivo(s) generado(s) por calculate_*.py")
    ap.add_argument("--traj", help="(opcional) archivo experimental, solo para leer el framerate")
    ap.add_argument("--fps", type=float, help=f"cuadros por segundo (defecto {FPS_DEFECTO})")
    ap.add_argument("--outdir", default=".", help="carpeta de salida (una figura por prueba)")
    ap.add_argument("--paneles", type=Path, metavar="PNG",
                    help="en vez de una figura por prueba, una sola con un panel por prueba, en el orden de --diff")
    ap.add_argument("--figsize", nargs=2, type=float, default=(9.6, 4.2), metavar=("ANCHO", "ALTO"),
                    help="tamaño de la figura de --paneles, en pulgadas (defecto: 9.6 4.2)")
    args = ap.parse_args()

    fps = args.fps or (leer_fps(args.traj) if args.traj else None) or FPS_DEFECTO
    pruebas, metricas = {}, set()
    for ruta in args.diff:
        leidas = leer_diff(ruta)
        if not leidas:
            raise SystemExit(f"No se encontraron datos en {ruta}")
        pruebas.update(leidas)
        metricas.add(leer_metrica(ruta))
    if len(metricas) != 1:
        raise SystemExit(f"--diff mezcla archivos de métricas distintas: {sorted(metricas)}")
    metrica = metricas.pop()
    if args.paneles:
        graficar_paneles(pruebas, fps, args.paneles, metrica, args.figsize)
    else:
        for prueba, particulas in pruebas.items():
            graficar(prueba, particulas, fps, args.outdir, metrica)


if __name__ == "__main__":
    main()