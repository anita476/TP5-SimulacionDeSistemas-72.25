#!/usr/bin/env python3
"""
Figuras del procesamiento de las trayectorias experimentales:
  recorte:  un evento crudo (cuadros de la prueba según el LEEME) contra el tramo que se simula
            (data/cruces_evento: tramo semihorizontal recortado al inicio común);
  espejado: un evento espejado, tramo original (data/cruces) contra el espejado (data/cruces_postprocess)
            y el eje y_eje = promedio de las y inicial y final de ambos peatones (como mirror_crossing.py).

Uso:
    python scripts/plot_preprocessing.py
    python scripts/plot_preprocessing.py --trim-event 13 --mirror-event 6
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from lib.plot_style import BLUE, FIGURE_SIZE, VERMILLION, apply_academic_style, save_figure, style_axes
from lib.traj import DEFAULT_DATA_PATH, DEFAULT_TRIALS_PATH, Experiment, read_experiment, read_trials

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
IMAGES = REPO / "docs" / "presentation" / "images"

DISCARDED = "0.72"
BEFORE_MIRROR = (0, (4, 2.5))
# mirror_crossing.py writes y with 6 significant figures, so the mirrored file only matches 2*y_eje - y to that precision.
MIRROR_TOLERANCE = 1e-4
MARGIN = 0.3  # m around the data


def ordered(track: dict[int, tuple[float, float]], first: int | None = None, last: int | None = None):
    frames = [f for f in sorted(track) if (first is None or f >= first) and (last is None or f <= last)]
    return [track[f][0] for f in frames], [track[f][1] for f in frames]


def trial_people(trials, event: int) -> tuple[str, str, int, int]:
    for number, left, right, start, final in trials:
        if number == event:
            return left, right, start, final
    sys.exit(f"event {event} is not in {DEFAULT_TRIALS_PATH}")


def require(experiment: Experiment, person: str, path: Path) -> dict[int, tuple[float, float]]:
    if person not in experiment.tracks:
        sys.exit(f"{path}: person {person} not found")
    return experiment.tracks[person]


def mirror_axis(original: Experiment, people: tuple[str, str]) -> float:
    """Same rule as mirror_crossing.py: mean of the first and last y of every pedestrian."""
    ends = []
    for person in people:
        _, ys = ordered(original.tracks[person])
        ends += [ys[0], ys[-1]]
    return sum(ends) / len(ends)


def draw_trim(ax, event: int, trials) -> None:
    left, right, start, final = trial_people(trials, event)
    raw = read_experiment(DEFAULT_DATA_PATH)
    used_path = DATA / "cruces_evento" / f"prueba{event}.txt"
    used = read_experiment(used_path)
    for person, color in ((left, BLUE), (right, VERMILLION)):
        rx, ry = ordered(require(raw, person, DEFAULT_DATA_PATH), start, final)
        ux, uy = ordered(require(used, person, used_path))
        ax.plot(rx, ry, color=DISCARDED, lw=4.0, solid_capstyle="round", zorder=1)
        ax.plot(ux, uy, color=color, lw=2.2, zorder=2)
        ax.plot(ux[0], uy[0], "o", mfc="white", mec=color, mew=2.0, ms=9, zorder=3)


def draw_mirror(ax, event: int, trials) -> None:
    left, right, _start, _final = trial_people(trials, event)
    original_path = DATA / "cruces" / f"prueba{event}.txt"
    mirrored_path = DATA / "cruces_postprocess" / f"prueba{event}.txt"
    original, mirrored = read_experiment(original_path), read_experiment(mirrored_path)
    y_axis = mirror_axis(original, (left, right))

    xs_all = []
    for person, color in ((left, BLUE), (right, VERMILLION)):
        before = require(original, person, original_path)
        after = require(mirrored, person, mirrored_path)
        if sorted(before) != sorted(after):
            sys.exit(f"event {event}, person {person}: {original_path} and {mirrored_path} have different frames")
        worst = max(abs(after[f][1] - (2 * y_axis - before[f][1])) for f in before)
        if worst > MIRROR_TOLERANCE:
            sys.exit(f"event {event}, person {person}: {mirrored_path} is not the mirror of {original_path} "
                     f"about y = {y_axis:.4f} m (max deviation {worst:.2e} m)")
        bx, by = ordered(before)
        mx, my = ordered(after)
        ax.plot(bx, by, color=color, lw=1.8, ls=BEFORE_MIRROR, alpha=0.75, zorder=2)
        ax.plot(mx, my, color=color, lw=2.2, zorder=3)
        xs_all += bx
    ax.plot([min(xs_all), max(xs_all)], [y_axis, y_axis], color="black", lw=1.6, ls=":", zorder=1)


def pedestrians() -> list[Line2D]:
    return [
        Line2D([], [], color=BLUE, lw=2.2, label="peatón izquierdo"),
        Line2D([], [], color=VERMILLION, lw=2.2, label="peatón derecho"),
    ]


TRIM_LEGEND = pedestrians() + [
    Line2D([], [], color=DISCARDED, lw=4.0, label="descartado"),
    Line2D([], [], ls="none", marker="o", mfc="white", mec="black", mew=2.0, ms=9, label="inicio ($t = 0$)"),
]
MIRROR_LEGEND = pedestrians() + [
    Line2D([], [], color="0.35", lw=1.8, ls=BEFORE_MIRROR, label="antes de espejar"),
    Line2D([], [], color="black", lw=1.6, ls=":", label="eje de espejado"),
]


def save_panel(draw, event: int, trials, handles: list[Line2D], figsize: tuple[float, float], out: Path) -> None:
    fig, ax = plt.subplots(figsize=figsize, layout="constrained")
    fig.get_layout_engine().set(h_pad=0.1)
    draw(ax, event, trials)
    box = ax.dataLim
    ax.set_xlim(box.x0 - MARGIN, box.x1 + MARGIN)
    ax.set_ylim(box.y0 - MARGIN, box.y1 + MARGIN)
    style_axes(ax, "posición $x$ (m)", "posición $y$ (m)")
    legend = fig.legend(handles=handles, loc="outside lower center", ncol=2, columnspacing=1.2, handletextpad=0.5)
    save_figure(fig, out, extra=(legend,))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trim-event", type=int, default=11, help="evento de la figura de recorte (default: 11)")
    parser.add_argument("--mirror-event", type=int, default=14, help="evento de la figura de espejado (default: 14)")
    parser.add_argument("--trim-out", type=Path, default=IMAGES / "procesamiento_recorte.png")
    parser.add_argument("--mirror-out", type=Path, default=IMAGES / "procesamiento_espejado.png")
    args = parser.parse_args()

    try:
        trials = read_trials(DEFAULT_TRIALS_PATH)
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    apply_academic_style()
    save_panel(draw_trim, args.trim_event, trials, TRIM_LEGEND, FIGURE_SIZE, args.trim_out)
    save_panel(draw_mirror, args.mirror_event, trials, MIRROR_LEGEND, FIGURE_SIZE, args.mirror_out)


if __name__ == "__main__":
    main()
