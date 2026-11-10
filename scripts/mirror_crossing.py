#!/usr/bin/env python3
"""
Espeja las trayectorias respecto de una recta horizontal y = y_eje:  y' = 2*y_eje - y.
La partícula que pasaba por encima pasa por debajo y viceversa; x no cambia.

Eje por defecto: promedio de la y de los puntos inicial y final de todas las partículas
(las trayectorias empiezan y terminan sobre la "línea del pasillo", así los extremos casi
no se mueven). Se puede fijar a mano con --eje.

El archivo de salida conserva exactamente el formato del original (comentarios, columnas,
orden, x, frame, ids); solo cambia la columna y, escrita con 6 cifras significativas
como en los archivos de entrada.

Uso:
    python espejar_trayectorias.py --traj prueba10.txt
    python espejar_trayectorias.py --traj prueba10.txt --out prueba10_espejo.txt
    python espejar_trayectorias.py --traj prueba10.txt --eje 2.0
"""
import argparse
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", required=True, help="archivo experimental pruebaX.txt")
    ap.add_argument("--out", help="archivo de salida (defecto: pruebaX_espejo.txt)")
    ap.add_argument("--eje", type=float, help="y de la recta de espejado (defecto: automático)")
    args = ap.parse_args()

    with open(args.traj, newline="") as f:
        lineas = f.readlines()

    # Índices de las líneas de datos y puntos extremos de cada partícula
    datos = [i for i, l in enumerate(lineas) if l.strip() and not l.lstrip().startswith("#")]
    extremos = {}  # id -> [primera y, última y]
    for i in datos:
        c = lineas[i].split()
        y = float(c[3])
        extremos.setdefault(c[0], [y, y])[1] = y

    if args.eje is not None:
        y_eje = args.eje
    else:
        ys = [y for par in extremos.values() for y in par]
        y_eje = sum(ys) / len(ys)

    salida = list(lineas)
    for i in datos:
        l = lineas[i]
        fin = l.rstrip("\r\n")
        salto = l[len(fin):]
        c = fin.split(" ")
        c[3] = f"{2 * y_eje - float(c[3]):.6g}"
        salida[i] = " ".join(c) + salto

    out = args.out or os.path.splitext(args.traj)[0] + "_espejo.txt"
    with open(out, "w", newline="") as f:
        f.writelines(salida)
    print(f"Eje de espejado: y = {y_eje:.6f} m")
    print(f"Guardado: {out}")


if __name__ == "__main__":
    main()