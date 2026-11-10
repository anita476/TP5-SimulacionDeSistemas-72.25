#!/usr/bin/env python3
"""
Métrica del punto más cercano entre trayectorias experimentales y simuladas.

Para cada partícula i:
    E_i = (1/Nm) * sum_k  min_j [ (x_exp(tk) - x_sim(tj))^2 + (y_exp(tk) - y_sim(tj))^2 ]

El archivo de salida contiene:
  - el valor mínimo (distancia^2 al punto simulado más cercano) para cada punto experimental,
  - el promedio E_i de cada partícula,
  - el promedio total (promedio de los E_i de todas las partículas).

Uso:
    python calculate_nearest_point.py --traj prueba6.txt --sim prueba6_sim.txt
    python calculate_nearest_point.py --traj prueba6.txt prueba7.txt --sim prueba6_sim.txt prueba7_sim.txt
    python calculate_nearest_point.py --traj prueba6.txt --sim prueba6_sim.txt -o resultados.txt
(--traj y --sim deben tener la misma cantidad de archivos, en el mismo orden)
"""
import argparse
import os
from collections import defaultdict

import numpy as np


def leer_real(ruta):
    """Formato: id frame x y markerID (las líneas con # son comentarios).
    Devuelve {id: (frames, puntos Nx2)}."""
    datos = defaultdict(list)
    with open(ruta) as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            c = linea.split()
            datos[int(c[0])].append((int(c[1]), float(c[2]), float(c[3])))
    salida = {}
    for k, v in datos.items():
        a = np.array(v)
        salida[k] = (a[:, 0].astype(int), a[:, 1:3])
    return salida


def leer_sim(ruta):
    """Formato: particle_id time x y vx vy (con una línea de encabezado)."""
    datos = defaultdict(list)
    with open(ruta) as f:
        for linea in f:
            c = linea.split()
            if not c or not c[0].lstrip("-").isdigit():
                continue  # encabezado o línea vacía
            datos[int(c[0])].append((float(c[2]), float(c[3])))
    return {k: np.array(v) for k, v in datos.items()}


def minimos_por_punto(exp, sim):
    """Para cada punto experimental: (distancia^2 mínima, punto simulado más cercano)."""
    diff = exp[:, None, :] - sim[None, :, :]       # (Nexp, Nsim, 2)
    d2 = (diff ** 2).sum(axis=2)                   # (Nexp, Nsim)
    idx = d2.argmin(axis=1)
    return d2[np.arange(len(exp)), idx], sim[idx]


def procesar(ruta_real, ruta_sim):
    real, sim = leer_real(ruta_real), leer_sim(ruta_sim)
    resultados = {}
    for pid in sorted(real):
        if pid not in sim:
            print(f"[aviso] {os.path.basename(ruta_real)}: id {pid} no está en la simulación.")
            continue
        frames, exp = real[pid]
        d2, cercano = minimos_por_punto(exp, sim[pid])
        resultados[pid] = (frames, exp, cercano, d2)
    return resultados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", nargs="+", required=True, help="archivo(s) experimental(es) pruebaX.txt")
    ap.add_argument("--sim", nargs="+", required=True, help="archivo(s) simulado(s) pruebaX_sim.txt")
    ap.add_argument("-o", "--out", default="resultados_E2.txt", help="archivo de salida")
    args = ap.parse_args()

    if len(args.traj) != len(args.sim):
        ap.error("--traj y --sim deben tener la misma cantidad de archivos.")

    L = ["# Métrica E(2): punto más cercano (distancia^2, unidades m^2)", ""]
    promedios_prueba = []
    for ruta_real, ruta_sim in zip(args.traj, args.sim):
        res = procesar(ruta_real, ruta_sim)
        if not res:
            continue
        L.append(f"===== {os.path.basename(ruta_real)} vs {os.path.basename(ruta_sim)} =====")
        L.append("")
        promedios_part = []
        for pid, (frames, exp, cerc, d2) in res.items():
            L.append(f"--- Partícula {pid} ---")
            L.append(f"{'frame':>7} {'x_exp':>10} {'y_exp':>10} {'x_sim_cerc':>11} {'y_sim_cerc':>11} {'min_dist2':>13}")
            for fr, (xe, ye), (xs, ys), d in zip(frames, exp, cerc, d2):
                L.append(f"{fr:>7d} {xe:>10.5f} {ye:>10.5f} {xs:>11.5f} {ys:>11.5f} {d:>13.6e}")
            e_i = float(d2.mean())
            promedios_part.append(e_i)
            L.append(f"Promedio E2 partícula {pid} (N={len(d2)}): {e_i:.6e}")
            L.append("")
        total = float(np.mean(promedios_part))
        promedios_prueba.append(total)
        L.append(f"PROMEDIO TOTAL {os.path.basename(ruta_real)} (todas las partículas): {total:.6e}")
        L.append("")

    if len(promedios_prueba) > 1:
        L.append(f"PROMEDIO GLOBAL de todas las pruebas: {np.mean(promedios_prueba):.6e}")

    with open(args.out, "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[:12]) + "\n...")
    print(f"\nResultados guardados en {args.out}")
    print("\n".join(l for l in L if l.startswith(("Promedio", "PROMEDIO"))))


if __name__ == "__main__":
    main()