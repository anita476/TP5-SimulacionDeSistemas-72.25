#!/usr/bin/env python3
"""Convergencia en el paso de integración dt.

Para cada caso (prueba, r_min, action_distance) corre el motor con dt = DT2/n,
n pasos de integración por cuadro impreso, y calcula las dos métricas con las
mismas funciones `procesar` que usa la calibración. Grafica E1 y E2 en función
de dt en escala log-log e imprime la tabla.

Uso:
    python scripts/plot_dt_convergence.py
    python scripts/plot_dt_convergence.py --cases 13,0.2,3 19,0.3,5 --steps 1 2 4 8 16 67 133
"""

import argparse
import contextlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from matplotlib.ticker import LogLocator, NullFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))  # calculate_* scripts
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import calculate_equal_time  # noqa: E402
import calculate_nearest_point  # noqa: E402
from plot_style import MARKERS, SERIES, apply_academic_style, save_figure, style_axes  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DT2 = 1.0 / 15.0192  # paso de impresión del motor (s), igual al muestreo experimental
DEFAULT_STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 14, 20, 40, 67]
DEFAULT_CASES = ["6,0.2,2.5", "7,0.1,7", "19,0.3,5"]


def parse_case(text):
    trial, r_min, d_a = text.split(",")
    return int(trial), r_min, d_a


def run_case(sim, trial, r_min, d_a, n, initial_velocity, out):
    """Corre el motor con n pasos por cuadro; devuelve (E1, E2, rapidez máxima)."""
    traj = REPO / "data" / "cruces_evento" / f"prueba{trial}.txt"
    cmd = [
        str(sim),
        "--traj_path", str(traj),
        "--r_min", r_min,
        "--action_distance", d_a,
        "--initial_velocity", initial_velocity,
        "--dt", repr(DT2 / n),
        "--out-path", str(out),
    ]
    subprocess.run(cmd, check=True, cwd=REPO, stdout=subprocess.DEVNULL)
    with contextlib.redirect_stdout(io.StringIO()):  # silencia los [aviso] de las métricas
        m1 = calculate_equal_time.procesar(str(traj), str(out))
        m2 = calculate_nearest_point.procesar(str(traj), str(out))
    e1 = float(np.mean([np.nanmean(d2) for _, _, _, d2 in m1.values()]))
    e2 = float(np.mean([np.mean(d2) for _, _, _, d2 in m2.values()]))
    v = np.loadtxt(out, comments="#", usecols=(4, 5), skiprows=1)
    return e1, e2, float(np.hypot(v[:, 0], v[:, 1]).max())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", nargs="+", default=DEFAULT_CASES, metavar="PRUEBA,R_MIN,D_A")
    parser.add_argument("--steps", nargs="+", type=int, default=DEFAULT_STEPS, metavar="N",
                        help="pasos de integración por cuadro impreso (dt = DT2/N)")
    parser.add_argument("--initial-velocity", default="experimental", choices=["zero", "experimental"])
    parser.add_argument("--sim", type=Path, default=REPO / "build" / "ElusionSIM")
    parser.add_argument("--out", type=Path, default=REPO / "docs" / "presentation" / "images" / "dt_convergencia.png")
    args = parser.parse_args()

    steps = sorted(set(args.steps))
    dts = np.array([DT2 / n for n in steps])
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sim.txt"
        for case in args.cases:
            trial, r_min, d_a = parse_case(case)
            print(f"# prueba {trial}, r_min = {r_min} m, d_a = {d_a} m")
            print("# n dt_s E1_m2 E2_m2 vmax_m_s")
            rows = []
            for n in steps:
                e1, e2, vmax = run_case(args.sim, trial, r_min, d_a, n, args.initial_velocity, out)
                rows.append((e1, e2, vmax))
                print(f"{n} {DT2 / n:.6f} {e1:.6e} {e2:.6e} {vmax:.3f}")
            results[case] = np.array(rows)
            if len(rows) >= 2:
                last, prev = results[case][-1], results[case][-2]
                print(f"# cambio relativo entre los dos dt más chicos: "
                      f"E1 {abs(last[0] - prev[0]) / last[0]:.2%}, E2 {abs(last[1] - prev[1]) / last[1]:.2%}")

    apply_academic_style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.2, w_pad=0.2)
    for column, (ax, ylabel) in enumerate(zip(axes, ("Error métrica 1 (m$^2$)", "Error métrica 2 (m$^2$)"))):
        for k, case in enumerate(args.cases):
            trial, r_min, d_a = parse_case(case)
            label = f"Evento {trial}: $r_{{min}}$ = {r_min} m, $d_a$ = {d_a} m"
            ax.plot(dts, results[case][:, column], marker=MARKERS[k % len(MARKERS)],
                    color=SERIES[k % len(SERIES)], linestyle="-", linewidth=1.0, label=label)
        ax.set_xscale("log")
        ax.set_yscale("log")
        style_axes(ax, "Paso de integración (s)", ylabel)
        # el eje y va en décadas enteras, así siempre hay al menos dos potencias de 10 rotuladas
        ax.set_xlim(dts.min() * 0.7, 10.0 ** np.ceil(np.log10(dts.max())))
        values = np.concatenate([results[case][:, column] for case in args.cases])
        ax.set_ylim(10.0 ** np.floor(np.log10(values.min())), 10.0 ** np.ceil(np.log10(values.max())))
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(LogLocator(base=10, numticks=12))
            axis.set_minor_locator(LogLocator(base=10, subs=range(2, 10), numticks=12))
            axis.set_minor_formatter(NullFormatter())
        ax.tick_params(axis="both", which="minor", length=3.5, width=0.9)

    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="outside lower center", ncol=1)
    save_figure(fig, args.out, extra=(legend,))


if __name__ == "__main__":
    main()
