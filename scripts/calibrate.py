#!/usr/bin/env python3
"""
Calibración de la capa de elusión a partir de la tabla E[m, i, j] (collect_errors.py), por métrica:

  (b) poblacional:  <E>(d_lat, d_act) = promedio sobre eventos, con su error estándar; óptimo = mínimo de la grilla
  (c) individual:   óptimo de cada evento y su error con los parámetros poblacionales
  (d) validación cruzada: particiones aleatorias entrenamiento/validación; óptimo sobre entrenamiento, error sobre validación

Escribe en --outdir: population_m{1,2}.txt, individual_m{1,2}.txt, crossval_m{1,2}.txt, summary.txt y summary.tex.

Uso:
    python scripts/calibrate.py
    python scripts/calibrate.py --partitions 50 --train-fraction 0.7 --seed 1
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import calib  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
GAIN_NOTE = "ganancia = (E_pop - E_ind) / E_pop, promedios sobre eventos"


def write_population(path: Path, metric: int, table: calib.ErrorTable, pop: calib.PopulationResult) -> None:
    L = [
        f"# Métrica {metric}: calibración poblacional, <E> = promedio de E_m sobre {len(table.events)} eventos (m^2)",
        "# sem = desvío estándar (ddof=1) / sqrt(n); el óptimo se busca entre los puntos de grilla que tienen todos los eventos",
        f"# optimum {pop.optimum[0]:g} {pop.optimum[1]:g} {pop.optimum_mean:.8e} {pop.optimum_sem:.8e}",
        "# d_lat d_act mean sem n",
    ]
    for g, m, s, n in zip(pop.grid, pop.mean, pop.sem, pop.n):
        L.append(f"{g[0]:g} {g[1]:g} {m:.8e} {s:.8e} {int(n)}")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_individual(path: Path, metric: int, pop: calib.PopulationResult, ind: list[calib.IndividualResult]) -> None:
    L = [
        f"# Métrica {metric}: calibración individual (m^2). E_population = E_m con el óptimo poblacional "
        f"(d_lat={pop.optimum[0]:g}, d_act={pop.optimum[1]:g})",
        "# prueba d_lat_opt d_act_opt E_individual E_population",
    ]
    for r in ind:
        L.append(f"{r.prueba} {r.optimum[0]:g} {r.optimum[1]:g} {r.E_individual:.8e} {r.E_population:.8e}")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_crossval(path: Path, metric: int, folds: list[calib.Fold], summ: calib.CrossvalSummary, args) -> None:
    L = [
        f"# Métrica {metric}: validación cruzada, {summ.partitions} particiones aleatorias "
        f"(fracción de entrenamiento {args.train_fraction:g}, semilla {args.seed})",
        f"# validation {summ.E_validation_mean:.8e} {summ.E_validation_sd:.8e}",
        f"# train {summ.E_train_mean:.8e} {summ.E_train_sd:.8e}",
        "# optimos: " + ", ".join(f"({g[0]:g}, {g[1]:g}) x{c}" for g, c in sorted(summ.optimum_counts.items(), key=lambda kv: -kv[1])),
        "# partition d_lat_opt d_act_opt E_train E_validation n_train n_validation validation_pruebas",
    ]
    for f in folds:
        L.append(
            f"{f.partition} {f.optimum[0]:g} {f.optimum[1]:g} {f.E_train:.8e} {f.E_validation:.8e} "
            f"{len(f.train)} {len(f.validation)} {','.join(map(str, f.validation))}"
        )
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--errors", type=Path, default=REPO / "data/calibration/errors.txt", help="tabla de collect_errors.py")
    ap.add_argument("--outdir", type=Path, default=None, help="carpeta de salida (default: la de --errors)")
    ap.add_argument("--partitions", type=int, default=20, help="particiones de la validación cruzada (default 20)")
    ap.add_argument("--train-fraction", type=float, default=0.7, help="fracción de eventos de entrenamiento (default 0.7)")
    ap.add_argument("--seed", type=int, default=0, help="semilla de las particiones (default 0)")
    args = ap.parse_args()
    outdir = args.outdir or args.errors.parent
    outdir.mkdir(parents=True, exist_ok=True)

    records = calib.read_errors(args.errors)
    metrics = sorted({r.metric for r in records})
    summary_rows = []
    for metric in metrics:
        table = calib.ErrorTable.from_records(records, metric)
        missing = table.missing()
        if missing:
            print(f"[aviso] métrica {metric}: faltan {len(missing)} combinaciones evento x grilla, p.ej. {missing[:3]}", file=sys.stderr)
        pop = calib.population(table)
        ind = calib.individual(table, pop)
        folds = calib.crossval(table, args.partitions, args.train_fraction, args.seed)
        summ = calib.summarize_crossval(folds)

        write_population(outdir / f"population_m{metric}.txt", metric, table, pop)
        write_individual(outdir / f"individual_m{metric}.txt", metric, pop, ind)
        write_crossval(outdir / f"crossval_m{metric}.txt", metric, folds, summ, args)

        E_ind = sum(r.E_individual for r in ind) / len(ind)
        E_pop = sum(r.E_population for r in ind) / len(ind)
        gain = (E_pop - E_ind) / E_pop if E_pop > 0 else float("nan")
        summary_rows.append((metric, pop, len(table.events), len(table.grid), E_ind, gain, summ))

    L = [
        "# Resumen de la calibración (m^2). " + GAIN_NOTE,
        "# metric M grid d_lat_opt d_act_opt E_pop sem_pop E_ind gain cv_partitions cv_val_mean cv_val_sd cv_train_mean cv_train_sd",
    ]
    T = ["% generado por scripts/calibrate.py; unidades m^2", "\\begin{tabular}{lcccccc}", "\\hline",
         "Métrica & $(d_{\\mathrm{lat}}, d_{\\mathrm{act}})^*$ & $\\langle E\\rangle$ poblacional & $\\langle E_m\\rangle$ individual & Ganancia & "
         "$\\langle E\\rangle$ validación & $\\langle E\\rangle$ entrenamiento \\\\", "\\hline"]
    for metric, pop, M, J, E_ind, gain, summ in summary_rows:
        L.append(
            f"{metric} {M} {J} {pop.optimum[0]:g} {pop.optimum[1]:g} {pop.optimum_mean:.6e} {pop.optimum_sem:.6e} {E_ind:.6e} {gain:.4f} "
            f"{summ.partitions} {summ.E_validation_mean:.6e} {summ.E_validation_sd:.6e} {summ.E_train_mean:.6e} {summ.E_train_sd:.6e}"
        )
        T.append(
            f"$E^{{({metric})}}$ & $({pop.optimum[0]:g},\\ {pop.optimum[1]:g})$ & ${pop.optimum_mean:.3g} \\pm {pop.optimum_sem:.2g}$ & "
            f"${E_ind:.3g}$ & ${100 * gain:.0f}\\,\\%$ & ${summ.E_validation_mean:.3g} \\pm {summ.E_validation_sd:.2g}$ & "
            f"${summ.E_train_mean:.3g} \\pm {summ.E_train_sd:.2g}$ \\\\"
        )
    T += ["\\hline", "\\end{tabular}"]
    (outdir / "summary.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    (outdir / "summary.tex").write_text("\n".join(T) + "\n", encoding="utf-8")

    for metric, pop, M, J, E_ind, gain, summ in summary_rows:
        print(
            f"Métrica {metric} ({M} eventos, {J} puntos de grilla): óptimo d_lat={pop.optimum[0]:g}, d_act={pop.optimum[1]:g}, "
            f"<E>={pop.optimum_mean:.4g} ± {pop.optimum_sem:.2g} | individual <E_m>={E_ind:.4g} (ganancia {100 * gain:.1f} %) | "
            f"validación {summ.E_validation_mean:.4g} ± {summ.E_validation_sd:.2g} ({summ.partitions} particiones)"
        )
    print(f"escrito en {outdir}: population_m*.txt, individual_m*.txt, crossval_m*.txt, summary.txt, summary.tex")


if __name__ == "__main__":
    main()
