#!/usr/bin/env python3
"""
Figuras de la calibración a partir de los archivos de calibrate.py. Por métrica m:

  E{m}_superficie.png               <E>(d_lat, d_act) como mapa de color, óptimo marcado           (b)
  E{m}_cortes.png                   <E> vs d_lat (a d_act óptima) y vs d_act (a d_lat óptimo), barras de error (b)

Y para todas las métricas juntas, un panel por métrica y una sola leyenda:

  optimos_individuales.png          distribución de los óptimos individuales sobre la grilla + poblacional   (c)
  error_por_evento.png              E_m de cada evento con parámetros poblacionales vs individuales           (c)
  validacion_cruzada.png            error de entrenamiento y validación entre particiones vs <E> poblacional  (d)

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
from matplotlib.ticker import ScalarFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from plot_style import (  # noqa: E402
    BLUE,
    D_ACT_COLOR,
    D_LAT_COLOR,
    VERMILLION,
    apply_academic_style,
    save_figure,
    style_axes,
)
from matplotlib.lines import Line2D  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
# words first (guía 1.8), and the symbol the slides use for the parameter, so the boxes beside the figures match
XLABEL = r"Margen lateral $d_{\mathrm{lat}}$ (m)"
YLABEL = r"Distancia de activación $d_{\mathrm{act}}$ (m)"
OPT_MARKER = dict(marker="o", markersize=14, markeredgecolor="black", markeredgewidth=1.5, linestyle="none")


def power_of_ten(value: float) -> int:
    """Exponent written in the axis label instead of matplotlib's floating offset (guía 1.9); 0 = plain values."""
    order = int(np.floor(np.log10(value)))
    return order if order < -1 else 0


def elabel(order: int = 0, mean: bool = True) -> str:
    """Rótulo de eje en palabras, con la unidad (y la potencia de 10, si hace falta) entre paréntesis (guía 1.8, 1.9)."""
    unit = f"10$^{{{order}}}$ m$^2$" if order else "m$^2$"
    return f"Error poblacional ({unit})" if mean else f"Error del evento ({unit})"


def thin_ticks(values: np.ndarray) -> np.ndarray:
    """Every other grid value, so 20 pt tick labels do not overlap on a half-slide figure."""
    return values[::2] if len(values) > 6 else values


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
    data = np.array([[float(v) for v in r[:4]] for r in rows])  # d_lat ad mean sd
    d_lats, ads = np.unique(data[:, 0]), np.unique(data[:, 1])
    Z = np.full((len(ads), len(d_lats)), np.nan)
    S = np.full_like(Z, np.nan)
    for r, a, m, s in data:
        Z[np.searchsorted(ads, a), np.searchsorted(d_lats, r)] = m
        S[np.searchsorted(ads, a), np.searchsorted(d_lats, r)] = s

    # surface; log colour scale, so the contrast is not spent on the bad corners and the valley around the optimum shows
    # sized for a 0.62 column of the slide, so the 20 pt text lands at ~10 pt there (guía 1.8)
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    zmin, zmax = np.nanmin(Z), np.nanmax(Z)
    norm = LogNorm(vmin=zmin, vmax=zmax) if zmin > 0 else None
    mesh = ax.pcolormesh(d_lats, ads, Z, shading="nearest", cmap="viridis", norm=norm)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
    if norm is None:
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((-2, 4))
        cbar.formatter = formatter
        cbar.update_ticks()
    cbar.set_label(elabel(), labelpad=12)
    ax.plot(r_opt, a_opt, color="white", **OPT_MARKER)
    ax.set_xticks(thin_ticks(d_lats))
    ax.set_yticks(thin_ticks(ads))
    style_axes(ax, XLABEL, YLABEL)
    save(fig, outdir / f"E{metric}_superficie.png")

    # 1D cuts through the optimum
    ia, ir = np.searchsorted(ads, a_opt), np.searchsorted(d_lats, r_opt)
    order = power_of_ten(Z[ia, ir])  # same power of ten on both cuts, taken from the optimum
    scale = 10.0**order
    # both cuts in one figure, a panel each: same quantity and scale, so they share the y axis, its label and one
    # legend below, and the panels come out the same height. Curve in the colour of the parameter being varied;
    # the fixed one is named beside the figure on the slide, not in the legend (guía 1.7)
    cuts = [(xs, ys, es, xlabel, color) for xs, ys, es, xlabel, color in (
        (d_lats, Z[ia], S[ia], XLABEL, D_LAT_COLOR),
        (ads, Z[:, ir], S[:, ir], YLABEL, D_ACT_COLOR),
    ) if len(xs) >= 2]
    fig, axes = plt.subplots(1, len(cuts), sharey=True, figsize=(9.4, 4.8), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.15)  # room between the x labels and the legend below
    axes = np.atleast_1d(axes)
    for ax, (xs, ys, es, xlabel, color) in zip(axes, cuts):
        ax.errorbar(xs, ys / scale, yerr=np.nan_to_num(es) / scale, fmt="o-", color=color, ecolor=color)
        k = int(np.nanargmin(ys))
        ax.plot(xs[k], ys[k] / scale, color=VERMILLION, label="óptimo", zorder=4, **OPT_MARKER)
        ax.set_xticks(thin_ticks(xs))
        style_axes(ax, xlabel, elabel(order) if ax is axes[0] else "")
        ax.ticklabel_format(axis="y", style="plain")
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="outside lower center", ncol=len(labels))
    save_figure(fig, outdir / f"E{metric}_cortes.png", extra=(legend,))


def read_individual(metric: int, indir: Path) -> dict:
    pcom, prow = read_table(indir / f"population_m{metric}.txt")
    r_opt, a_opt, _, _ = header_value(pcom, "optimum")
    _, rows = read_table(indir / f"individual_m{metric}.txt")
    return {
        "metric": metric,
        "r_opt": r_opt,
        "a_opt": a_opt,
        "grid": np.array([[float(r[0]), float(r[1])] for r in prow]),
        "pruebas": [int(r[0]) for r in rows],
        "opt": np.array([[float(r[1]), float(r[2])] for r in rows]),
        "E_ind": np.array([float(r[3]) for r in rows]),
        "E_pop": np.array([float(r[4]) for r in rows]),
    }


def draw_optima(ax, d: dict) -> None:
    """Optima of each event on the grid (circle area = number of events) and the population optimum."""
    grid = d["grid"]
    ax.plot(grid[:, 0], grid[:, 1], linestyle="none", marker="o", color="0.8", markersize=5, zorder=1)
    pts, counts = np.unique(d["opt"], axis=0, return_counts=True)
    ax.scatter(pts[:, 0], pts[:, 1], s=90 * counts, color=VERMILLION, alpha=0.75, edgecolor="black", zorder=2)
    # cantidad de eventos a la derecha de cada círculo, solo donde coincide más de uno
    for (x, y), c in zip(pts, counts):
        if c > 1:
            radius_pt = np.sqrt(90 * c / np.pi)
            ax.annotate(str(c), (x, y), textcoords="offset points", xytext=(radius_pt + 5, 0), ha="left",
                        va="center", fontsize=20, zorder=4)
    ax.plot(d["r_opt"], d["a_opt"], color=BLUE, zorder=3, **OPT_MARKER)
    ax.set_xticks(thin_ticks(np.unique(grid[:, 0])))
    ax.set_yticks(thin_ticks(np.unique(grid[:, 1])))
    pad_x = 0.5 * (np.ptp(grid[:, 0]) or 0.1) / max(len(np.unique(grid[:, 0])) - 1, 1)
    pad_y = 0.5 * (np.ptp(grid[:, 1]) or 1.0) / max(len(np.unique(grid[:, 1])) - 1, 1)
    ax.set_xlim(grid[:, 0].min() - pad_x, grid[:, 0].max() + pad_x)
    ax.set_ylim(grid[:, 1].min() - pad_y, grid[:, 1].max() + 1.2 * pad_y)


def draw_errors(ax, d: dict) -> int:
    """E_m of each event with population and individual parameters; returns the power of ten of the axis."""
    E_pop, E_ind, pruebas = d["E_pop"], d["E_ind"], d["pruebas"]
    order = power_of_ten(E_pop.mean())
    scale = 10.0**order
    x = np.arange(len(pruebas))
    w = 0.4
    ax.bar(x - w / 2, E_pop / scale, w, color=BLUE, label="parámetros poblacionales")
    ax.bar(x + w / 2, E_ind / scale, w, color=VERMILLION, label="parámetros individuales")
    ax.axhline(E_pop.mean() / scale, color=BLUE, linestyle="--", linewidth=1.5, label="promedio poblacional")
    ax.axhline(E_ind.mean() / scale, color=VERMILLION, linestyle="--", linewidth=1.5, label="promedio individual")
    ax.set_xticks(x)
    # 18 two-digit labels do not fit side by side at 20 pt: alternate two rows
    ax.set_xticklabels([str(p) if k % 2 == 0 else f"\n{p}" for k, p in enumerate(pruebas)])
    ax.set_xlim(-0.7, len(pruebas) - 0.3)
    ax.ticklabel_format(axis="y", style="plain")
    return order


def plot_individual(metrics: list[int], indir: Path, outdir: Path) -> None:
    """(c) for all metrics in one figure each, a panel per metric: the panels get the same height and one legend
    centred below (as fv_paneles of TP4)."""
    data = [read_individual(m, indir) for m in metrics]

    # optima on the grid: same grid in every panel, so they share the y axis and its label
    fig, axes = plt.subplots(1, len(data), sharey=True, figsize=(11.0, 4.6), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.15)  # room between the x labels and the legend below
    axes = np.atleast_1d(axes)
    for ax, d in zip(axes, data):
        draw_optima(ax, d)
        style_axes(ax, XLABEL, YLABEL if ax is axes[0] else "")
        ax.set_title(f"Métrica {d['metric']}")
    legend = fig.legend(
        [Line2D([], [], linestyle="none", marker="o", markersize=13, color=VERMILLION, alpha=0.75,
                markeredgecolor="black"),
         Line2D([], [], color=BLUE, **OPT_MARKER)],
        ["óptimos individuales (número de eventos)", "óptimo poblacional"],
        loc="outside lower center", ncol=2,
    )
    save_figure(fig, outdir / "optimos_individuales.png", extra=(legend,))

    # per-event errors: each metric keeps its own scale and unit, so each panel has its own y label
    fig, axes = plt.subplots(1, len(data), figsize=(11.6, 5.4), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.15)
    axes = np.atleast_1d(axes)
    for ax, d in zip(axes, data):
        order = draw_errors(ax, d)
        style_axes(ax, "Evento", elabel(order, mean=False))
        ax.set_title(f"Métrica {d['metric']}")
    handles, labels = axes[0].get_legend_handles_labels()
    # four entries do not fit in one row at 20 pt: two columns, bars in one and their averages in the other
    bars_first = [2, 3, 0, 1]  # matplotlib lists the lines (axhline) before the bars
    legend = fig.legend([handles[i] for i in bars_first], [labels[i] for i in bars_first],
                        loc="outside lower center", ncol=2)
    save_figure(fig, outdir / "error_por_evento.png", extra=(legend,))


def draw_crossval(ax, metric: int, indir: Path) -> int:
    """Training and validation error (mean over the partitions, error bar = sample sd between partitions) against
    the population calibration; returns the power of ten of the axis."""
    pcom, _ = read_table(indir / f"population_m{metric}.txt")
    _, _, E_pop, _ = header_value(pcom, "optimum")
    _, rows = read_table(indir / f"crossval_m{metric}.txt")
    E_tr = np.array([float(r[3]) for r in rows])
    E_va = np.array([float(r[4]) for r in rows])

    # Points, not bars: a bar has to start at zero and then the spread, which is the result, takes a sliver of the axis
    # (the partition index carries no information, so it is not an axis)
    order = power_of_ten(E_pop)  # same power of ten on the axis and in the written values
    scale = 10.0**order
    for x, vals, color in ((0, E_tr, BLUE), (1, E_va, VERMILLION)):
        mean, sd = vals.mean(), vals.std(ddof=1)
        ax.errorbar(x, mean / scale, yerr=sd / scale, fmt="o", markersize=13, color=color, ecolor=color, capsize=9,
                    capthick=2.2, elinewidth=2.2, zorder=3)
    ax.axhline(E_pop / scale, color="black", linestyle=":", linewidth=1.8, label="calibración poblacional", zorder=1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Entrenamiento\n(13 eventos)", "Validación\n(5 eventos)"])
    ax.set_xlim(-0.6, 1.6)
    ax.margins(y=0.12)
    ax.ticklabel_format(axis="y", style="plain")
    return order


def plot_crossval(metrics: list[int], indir: Path, outdir: Path) -> None:
    """(d) a panel per metric, same height, one legend centred below (as the other figures with one panel per
    metric). Each metric keeps its own scale and unit, so each panel has its own y label."""
    fig, axes = plt.subplots(1, len(metrics), figsize=(10.0, 5.0), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.15)  # room between the x labels and the legend below
    axes = np.atleast_1d(axes)
    for ax, metric in zip(axes, metrics):
        order = draw_crossval(ax, metric, indir)
        unit = f"10$^{{{order}}}$ m$^2$" if order else "m$^2$"
        style_axes(ax, "Conjunto de eventos", f"Error medio ({unit})")  # words, not symbols (guía 1.8)
        ax.set_title(f"Métrica {metric}")
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="outside lower center", ncol=len(labels))
    save_figure(fig, outdir / "validacion_cruzada.png", extra=(legend,))


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
    plot_individual(metrics, args.indir, outdir)
    plot_crossval(metrics, args.indir, outdir)


if __name__ == "__main__":
    main()
