#!/usr/bin/env python3
"""
Métrica 1

Para cada partícula i:
    E_i = (1/Nm) * sum_k [ (x_exp(tk) - x_sim(tk))^2 + (y_exp(tk) - y_sim(tk))^2 ]

Uso:
    python calculate_equal_time.py --traj prueba6.txt --sim prueba6_sim.txt
    python calculate_equal_time.py --traj prueba6.txt prueba7.txt --sim prueba6_sim.txt prueba7_sim.txt -o resultados.txt
(--traj y --sim deben tener la misma cantidad de archivos, en el mismo orden)
"""
import argparse
import os
import re
from collections import defaultdict

import numpy as np

from calculate_nearest_point import leer_real

FPS_DEFECTO = 15.0192


def leer_fps(ruta):
    with open(ruta) as f:
        for linea in f:
            m = re.match(r"#\s*framerate:\s*([\d.]+)", linea)
            if m:
                return float(m.group(1))
    return FPS_DEFECTO


def leer_sim_con_tiempo(ruta):
    """Formato: particle_id time x y vx vy. Devuelve {id: (tiempos S, puntos Sx2)}."""
    datos = defaultdict(list)
    with open(ruta) as f:
        for linea in f:
            c = linea.split()
            if not c or not c[0].lstrip("-").isdigit():
                continue  # encabezado o línea vacía
            datos[int(c[0])].append((float(c[1]), float(c[2]), float(c[3])))
    return {k: (np.array(v)[:, 0], np.array(v)[:, 1:3]) for k, v in datos.items()}


def verificar_tiempos(pid, tiempos, dt, rel_tol=1e-3):
    """La fila k debe tener time = k*dt (fila 0 = estado inicial). Una fila corrida da error relativo 1."""
    k = np.arange(len(tiempos))
    peor = np.max(np.abs(tiempos - k * dt)) / dt
    if peor > rel_tol:
        raise SystemExit(
            f"id {pid}: la columna time no es k*dt (desvío máximo {peor:.3g} dt). "
            "El motor tiene que escribir la fila 0 con el estado inicial y t = k*dt."
        )


def procesar(ruta_real, ruta_sim):
    real = leer_real(ruta_real)
    sim = leer_sim_con_tiempo(ruta_sim)
    dt = 1.0 / leer_fps(ruta_real)
    f0 = min(int(frames.min()) for frames, _ in real.values())  # inicio común del evento
    resultados = {}
    for pid in sorted(real):
        if pid not in sim:
            print(f"[aviso] {os.path.basename(ruta_real)}: id {pid} no está en la simulación.")
            continue
        frames, exp = real[pid]
        tiempos, puntos = sim[pid]
        verificar_tiempos(pid, tiempos, dt)
        idx = frames - f0  # fila simulada de cada cuadro experimental
        con_par = idx < len(puntos)
        cercano = np.full_like(exp, np.nan)
        cercano[con_par] = puntos[idx[con_par]]
        d2 = ((exp - cercano) ** 2).sum(axis=1)  # nan donde no hay fila
        if (~con_par).any():
            print(f"[aviso] {os.path.basename(ruta_real)}: id {pid}: {int((~con_par).sum())} cuadros sin fila simulada.")
        resultados[pid] = (frames, exp, cercano, d2)
    return resultados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", nargs="+", required=True, help="archivo(s) experimental(es) pruebaX.txt")
    ap.add_argument("--sim", nargs="+", required=True, help="archivo(s) simulado(s) pruebaX_sim.txt")
    ap.add_argument("-o", "--out", default="resultados_E1.txt", help="archivo de salida")
    args = ap.parse_args()

    if len(args.traj) != len(args.sim):
        ap.error("--traj y --sim deben tener la misma cantidad de archivos.")

    L = ["# Métrica E(1): iguales tiempos (distancia^2, unidades m^2)", ""]
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
            L.append(f"{'frame':>7} {'x_exp':>10} {'y_exp':>10} {'x_sim':>11} {'y_sim':>11} {'dist2':>13}")
            for fr, (xe, ye), (xs, ys), d in zip(frames, exp, cerc, d2):
                L.append(f"{fr:>7d} {xe:>10.5f} {ye:>10.5f} {xs:>11.5f} {ys:>11.5f} {d:>13.6e}")
            e_i = float(np.nanmean(d2))
            promedios_part.append(e_i)
            L.append(f"Promedio E1 partícula {pid} (N={int(np.isfinite(d2).sum())}): {e_i:.6e}")
            L.append("")
        total = float(np.mean(promedios_part))
        promedios_prueba.append(total)
        L.append(f"PROMEDIO TOTAL {os.path.basename(ruta_real)} (todas las partículas): {total:.6e}")
        L.append("")

    if len(promedios_prueba) > 1:
        L.append(f"PROMEDIO GLOBAL de todas las pruebas: {np.mean(promedios_prueba):.6e}")

    with open(args.out, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"Resultados guardados en {args.out}")
    print("\n".join(l for l in L if l.startswith(("Promedio", "PROMEDIO"))))


if __name__ == "__main__":
    main()
