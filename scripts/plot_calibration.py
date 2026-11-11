#!/usr/bin/env python3
"""
Figuras de la calibración a partir de los archivos de calibrate.py. Por métrica m:

  E{m}_superficie.png               <E>(r_min, action_distance) como mapa de color, óptimo marcado           (b)
  E{m}_corte_rmin.png               <E> vs r_min con barras de error, a action_distance óptima                (b)
  E{m}_corte_action_distance.png    <E> vs action_distance con barras de error, a r_min óptimo                (b)
  E{m}_optimos_individuales.png     distribución de los óptimos individuales sobre la grilla + poblacional   (c)
  E{m}_error_por_evento.png         E_m de cada evento con parámetros poblacionales vs individuales           (c)
  E{m}_validacion_cruzada.png       error de validación y entrenamiento por partición vs <E> poblacional      (d)

Uso:
    python scripts/plot_calibration.py                       # lee data/calibration, escribe data/calibration/figures
    python scripts/plot_calibration.py --indir X --outdir Y
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from plot_style import BLUE, GREEN, RED, VERMILLION, apply_academic_style, style_axes  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
XLABEL = r"$r_{\min}$ [m]"
YLABEL = r"$d_a$ [m]"


def elabel(metric: int, mean: bool = True) -> str:
    return rf"$\langle E^{{({metric})}} \rangle$ [m$^2$]" if mean else rf"$E^{{({metric})}}_m$ [m$^2$]"


def read_table(path: Path):
    """Rows of numbers (first columns) + header comments. Returns (comments, rows as list of str lists)."""
    comments, rows = [], []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments.append(line[1:].strip())
        else:
            rows.append(line.split())
    return comments, rows


def header_value(comments: list[str], key: str) -> list[float]:
    for c in comments:
        parts = c.split()
        if parts and parts[0] == key:
            return [float(v) for v in parts[1:]]
    raise ValueError(f"missing '# {key} ...' header line")


def save(fig, path: Path) -> None:
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path}")


def plot_population(metric: int, indir: Path, outdir: Path) -> None:
    comments, rows = read_table(indir / f"population_m{metric}.txt")
    r_opt, a_opt, _, _ = header_value(comments, "optimum")
    data = np.array([[float(v) for v in r[:4]] for r in rows])  # r_min ad mean sem
    r_mins, ads = np.unique(data[:, 0]), np.unique(data[:, 1])
    Z = np.full((len(ads), len(r_mins)), np.nan)
    S = np.full_like(Z, np.nan)
    for r, a, m, s in data:
        Z[np.searchsorted(ads, a), np.searchsorted(r_mins, r)] = m
        S[np.searchsorted(ads, a), np.searchsorted(r_mins, r)] = s

    # surface; log colour scale when the grid spans more than a decade (a diverging run would flatten everything else)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    zmin, zmax = np.nanmin(Z), np.nanmax(Z)
    norm = LogNorm(vmin=zmin, vmax=zmax) if zmin > 0 and zmax / zmin > 20 else None
    mesh = ax.pcolormesh(r_mins, ads, Z, shading="nearest", cmap="viridis", norm=norm)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
    cbar.set_label(elabel(metric), labelpad=12)
    ax.plot(r_opt, a_opt, marker="*", markersize=22, color="white", markeredgecolor="black", markeredgewidth=1.2, linestyle="none")
    ax.set_xticks(r_mins)
    ax.set_yticks(ads)
    style_axes(ax, XLABEL, YLABEL)
    save(fig, outdir / f"E{metric}_superficie.png")

    # 1D cuts through the optimum
    ia, ir = np.searchsorted(ads, a_opt), np.searchsorted(r_mins, r_opt)
    for xs, ys, es, xlabel, fixed, name in (
        (r_mins, Z[ia], S[ia], XLABEL, rf"$d_a = {a_opt:g}$ m", "corte_rmin"),
        (ads, Z[:, ir], S[:, ir], YLABEL, rf"$r_{{\min}} = {r_opt:g}$ m", "corte_action_distance"),
    ):
        if len(xs) < 2:
            continue
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.errorbar(xs, ys, yerr=np.nan_to_num(es), fmt="o-", color=BLUE, ecolor=BLUE, label=fixed)
        k = int(np.nanargmin(ys))
        ax.plot(xs[k], ys[k], marker="*", markersize=20, color=VERMILLION, markeredgecolor="black", linestyle="none", label="óptimo")
        ax.set_xticks(xs)
        style_axes(ax, xlabel, elabel(metric))
        ax.legend()
        save(fig, outdir / f"E{metric}_{name}.png")


def plot_individual(metric: int, indir: Path, outdir: Path) -> None:
    pcom, prow = read_table(indir / f"population_m{metric}.txt")
    r_opt, a_opt, _, _ = header_value(pcom, "optimum")
    grid = np.array([[float(r[0]), float(r[1])] for r in prow])
    _, rows = read_table(indir / f"individual_m{metric}.txt")
    pruebas = [int(r[0]) for r in rows]
    opt = np.array([[float(r[1]), float(r[2])] for r in rows])
    E_ind = np.array([float(r[3]) for r in rows])
    E_pop = np.array([float(r[4]) for r in rows])

    # optima on the grid
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(grid[:, 0], grid[:, 1], linestyle="none", marker="o", color="0.8", markersize=5, label="grilla", zorder=1)
    pts, counts = np.unique(opt, axis=0, return_counts=True)
    ax.scatter(pts[:, 0], pts[:, 1], s=90 * counts, color=VERMILLION, alpha=0.75, edgecolor="black", zorder=2,
               label="óptimos individuales")
    for (x, y), c in zip(pts, counts):
        ax.annotate(str(c), (x, y), textcoords="offset points", xytext=(0, 14), ha="center", fontsize=14)
    ax.plot(r_opt, a_opt, marker="*", markersize=22, color=BLUE, markeredgecolor="black", linestyle="none",
            label="óptimo poblacional", zorder=3)
    ax.set_xticks(np.unique(grid[:, 0]))
    ax.set_yticks(np.unique(grid[:, 1]))
    pad_x = 0.5 * (np.ptp(grid[:, 0]) or 0.1) / max(len(np.unique(grid[:, 0])) - 1, 1)
    pad_y = 0.5 * (np.ptp(grid[:, 1]) or 1.0) / max(len(np.unique(grid[:, 1])) - 1, 1)
    ax.set_xlim(grid[:, 0].min() - pad_x, grid[:, 0].max() + pad_x)
    ax.set_ylim(grid[:, 1].min() - pad_y, grid[:, 1].max() + 1.2 * pad_y)
    style_axes(ax, XLABEL, YLABEL)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, fontsize=15, frameon=False)
    save(fig, outdir / f"E{metric}_optimos_individuales.png")

    # per-event errors, population vs individual parameters
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(pruebas))
    w = 0.4
    ax.bar(x - w / 2, E_pop, w, color=BLUE, label="parámetros poblacionales")
    ax.bar(x + w / 2, E_ind, w, color=VERMILLION, label="parámetros individuales")
    ax.axhline(E_pop.mean(), color=BLUE, linestyle="--", linewidth=1.5)
    ax.axhline(E_ind.mean(), color=VERMILLION, linestyle="--", linewidth=1.5)
    ax.set_xticks(x)
    ax.set_xticklabels([str(p) for p in pruebas], fontsize=15)
    style_axes(ax, "evento", elabel(metric, mean=False))
    ax.legend(fontsize=15)
    save(fig, outdir / f"E{metric}_error_por_evento.png")


def plot_crossval(metric: int, indir: Path, outdir: Path) -> None:
    pcom, _ = read_table(indir / f"population_m{metric}.txt")
    _, _, E_pop, sem_pop = header_value(pcom, "optimum")
    ccom, rows = read_table(indir / f"crossval_m{metric}.txt")
    val_mean, val_sd = header_value(ccom, "validation")
    k = np.array([int(r[0]) for r in rows])
    E_tr = np.array([float(r[3]) for r in rows])
    E_va = np.array([float(r[4]) for r in rows])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axhspan(val_mean - val_sd, val_mean + val_sd, color=VERMILLION, alpha=0.15, linewidth=0)
    ax.axhline(val_mean, color=VERMILLION, linestyle="--", linewidth=1.5, label=r"$\langle E \rangle$ validación")
    ax.axhline(E_pop, color="black", linestyle=":", linewidth=1.8, label=r"$\langle E \rangle$ poblacional (b)")
    ax.plot(k, E_va, linestyle="none", marker="o", color=VERMILLION, label="validación")
    ax.plot(k, E_tr, linestyle="none", marker="s", color=BLUE, markersize=6.5, label="entrenamiento")
    ax.set_xticks(k[:: max(1, len(k) // 10)])
    style_axes(ax, "partición", elabel(metric))
    ax.legend(fontsize=14, ncol=2)
    save(fig, outdir / f"E{metric}_validacion_cruzada.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--indir", type=Path, default=REPO / "data/calibration", help="salida de calibrate.py")
    ap.add_argument("--outdir", type=Path, default=None, help="carpeta de figuras (default: <indir>/figures)")
    args = ap.parse_args()
    outdir = args.outdir or args.indir / "figures"
    outdir.mkdir(parents=True, exist_ok=True)
    apply_academic_style()
    metrics = sorted(int(p.stem.split("_m")[1]) for p in args.indir.glob("population_m*.txt"))
    if not metrics:
        raise SystemExit(f"no population_m*.txt in {args.indir} (run scripts/calibrate.py first)")
    for metric in metrics:
        plot_population(metric, args.indir, outdir)
        plot_individual(metric, args.indir, outdir)
        plot_crossval(metric, args.indir, outdir)


if __name__ == "__main__":
    main()
