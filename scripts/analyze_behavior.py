#!/usr/bin/env python3
"""Classify real 1-vs-1 crossings: which way each pedestrian evades, and by how much."""

import argparse
import math
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.plot_style import (
    BLUE,
    MARKERS,
    VERMILLION,
    new_figure,
    place_legend_below,
    save_figure,
    style_axes,
)
from lib.traj import DEFAULT_CROSSINGS_DIR, DEFAULT_TRIALS_PATH, Position, read_experiment, read_trials

NO_EVADE_M = 0.10
AMBIGUOUS_LO_M = 0.08
AMBIGUOUS_HI_M = 0.12

_SIDE_HEADER = re.compile(r"#\s*(izquierda|derecha):\s*id\s+([^,\s]+)", re.IGNORECASE)

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = _REPO_ROOT / "data" / "behavior"


@dataclass(frozen=True)
class Chord:
    x0: float
    y0: float
    ux: float
    uy: float
    rx: float
    ry: float


@dataclass(frozen=True)
class Walker:
    person: str
    side: str
    delta_peak: float
    lab_side: str
    evades: bool
    lado_propio: str
    delta_ca: float
    y_ca: float


@dataclass(frozen=True)
class Trial:
    number: int
    left: Walker
    right: Walker
    d_min: float
    higher_y: str
    yielding: str
    model: str
    tracks: dict[str, dict[int, Position]]


def _fail(path: Path, msg: str) -> None:
    raise ValueError(f"{path}: {msg}")


def parse_header_sides(path: Path) -> tuple[str, str]:
    left = right = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            match = _SIDE_HEADER.match(line.strip())
            if not match:
                continue
            side, person = match.group(1).lower(), match.group(2)
            if side == "izquierda":
                if left is not None:
                    _fail(path, "duplicate '# izquierda: id …' in the header")
                left = person
            else:
                if right is not None:
                    _fail(path, "duplicate '# derecha: id …' in the header")
                right = person
    if left is None or right is None:
        _fail(path, "missing '# izquierda: id …' or '# derecha: id …' in the header")
    if left == right:
        _fail(path, f"izquierda and derecha are both id {left}")
    return left, right


def geometric_left(tracks: dict[str, dict[int, Position]]) -> str:
    starts = []
    for person, track in tracks.items():
        if not track:
            raise ValueError(f"person {person} has no positions")
        first = min(track)
        starts.append((track[first][0], person))
    starts.sort()
    return starts[0][1]


def make_chord(track: dict[int, Position], person: str) -> Chord:
    frames = sorted(track)
    if len(frames) < 2:
        raise ValueError(f"person {person} needs at least two positions for a chord")
    x0, y0 = track[frames[0]]
    x1, y1 = track[frames[-1]]
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0.0:
        raise ValueError(f"person {person} has a zero-length chord")
    ux, uy = dx / length, dy / length
    return Chord(x0=x0, y0=y0, ux=ux, uy=uy, rx=uy, ry=-ux)


def lateral(chord: Chord, x: float, y: float) -> float:
    return (x - chord.x0) * chord.rx + (y - chord.y0) * chord.ry


def chord_y(chord: Chord, x: float, y: float) -> float:
    along = (x - chord.x0) * chord.ux + (y - chord.y0) * chord.uy
    return chord.y0 + along * chord.uy


def peak_sample(track: dict[int, Position], chord: Chord, person: str) -> tuple[float, float, float]:
    peak: tuple[float, float, float, float] | None = None
    for x, y in track.values():
        delta = lateral(chord, x, y)
        candidate = (abs(delta), delta, x, y)
        if peak is None or candidate > peak:
            peak = candidate
    if peak is None:
        raise ValueError(f"person {person} has no positions")
    _abs_delta, delta, x, y = peak
    return delta, x, y


def lab_side_of(chord: Chord, x: float, y: float) -> str:
    dy = y - chord_y(chord, x, y)
    if dy > 0.0:
        return "+y"
    if dy < 0.0:
        return "-y"
    return "0"


def nearest_frame(frames: list[int], target: int) -> int:
    return min(frames, key=lambda frame: (abs(frame - target), frame))


def closest_approach(
    left: dict[int, Position], right: dict[int, Position]
) -> tuple[float, int, int]:
    left_frames = sorted(left)
    right_frames = sorted(right)
    best: tuple[float, int, int] | None = None

    def consider(left_frame: int, right_frame: int) -> None:
        nonlocal best
        lx, ly = left[left_frame]
        rx, ry = right[right_frame]
        distance = math.hypot(lx - rx, ly - ry)
        candidate = (distance, left_frame, right_frame)
        if best is None or candidate < best:
            best = candidate

    for left_frame in left_frames:
        consider(left_frame, nearest_frame(right_frames, left_frame))
    for right_frame in right_frames:
        consider(nearest_frame(left_frames, right_frame), right_frame)
    if best is None:
        raise ValueError("closest approach needs positions on both sides")
    return best


def own_side(delta: float, evades: bool) -> str:
    if not evades:
        return "no_elude"
    if delta > 0.0:
        return "derecha"
    if delta < 0.0:
        return "izquierda"
    return "no_elude"


def classify_yielding(left_evades: bool, right_evades: bool) -> str:
    if left_evades and right_evades:
        return "ambos"
    if left_evades:
        return "solo_izquierda"
    if right_evades:
        return "solo_derecha"
    return "ninguno"


def classify_model(left: Walker, right: Walker) -> str:
    if left.evades and right.evades:
        if left.lado_propio == "derecha" and right.lado_propio == "derecha":
            return "ambos_derecha"
        if left.lado_propio == "izquierda" and right.lado_propio == "izquierda":
            return "ambos_izquierda"
        return "mixto"
    if left.evades or right.evades:
        return "uno_solo"
    return "ninguno"


def analyze_walker(
    person: str, side: str, track: dict[int, Position], chord: Chord, x_ca: float, y_ca: float
) -> Walker:
    delta_peak, x_peak, y_peak = peak_sample(track, chord, person)
    evades = abs(delta_peak) >= NO_EVADE_M
    return Walker(
        person=person,
        side=side,
        delta_peak=delta_peak,
        lab_side=lab_side_of(chord, x_peak, y_peak),
        evades=evades,
        lado_propio=own_side(delta_peak, evades),
        delta_ca=lateral(chord, x_ca, y_ca),
        y_ca=y_ca,
    )


def analyze_trial(path: Path, number: int, left_id: str, right_id: str) -> Trial:
    header_left, header_right = parse_header_sides(path)
    if (header_left, header_right) != (left_id, right_id):
        _fail(
            path,
            f"header ids izquierda={header_left} derecha={header_right} "
            f"do not match LEEME izquierda={left_id} derecha={right_id}",
        )

    try:
        experiment = read_experiment(path)
        tracks = experiment.tracks
        if set(tracks) != {left_id, right_id}:
            raise ValueError(f"expected ids {left_id} and {right_id}, found {sorted(tracks)}")

        geo_left = geometric_left(tracks)
        if geo_left != left_id:
            raise ValueError(f"smaller initial x is id {geo_left}, expected izquierda {left_id}")

        left_track, right_track = tracks[left_id], tracks[right_id]
        left_chord, right_chord = make_chord(left_track, left_id), make_chord(right_track, right_id)
        d_min, left_frame, right_frame = closest_approach(left_track, right_track)
        left_xy, right_xy = left_track[left_frame], right_track[right_frame]

        left = analyze_walker(left_id, "izquierda", left_track, left_chord, *left_xy)
        right = analyze_walker(right_id, "derecha", right_track, right_chord, *right_xy)
    except ValueError as error:
        message = str(error)
        if message.startswith(f"{path}:"):
            raise
        raise ValueError(f"{path}: {message}") from error

    if left.y_ca > right.y_ca:
        higher_y = "izquierda"
    elif right.y_ca > left.y_ca:
        higher_y = "derecha"
    else:
        higher_y = "empate"

    return Trial(
        number=number,
        left=left,
        right=right,
        d_min=d_min,
        higher_y=higher_y,
        yielding=classify_yielding(left.evades, right.evades),
        model=classify_model(left, right),
        tracks=tracks,
    )


def mean_std(values: list[float]) -> str:
    if not values:
        return "n=0"
    if len(values) == 1:
        return f"media={values[0]:.4f} m  std=n/a  n=1"
    return (
        f"media={statistics.fmean(values):.4f} m  "
        f"std={statistics.stdev(values):.4f} m  n={len(values)}"
    )


def count_own_side(walkers: list[Walker], label: str) -> int:
    return sum(1 for walker in walkers if own_side(walker.delta_peak, walker.evades) == label)


def write_table(path: Path, trials: list[Trial]) -> None:
    walkers = [walker for trial in trials for walker in (trial.left, trial.right)]
    abs_all = [abs(walker.delta_peak) for walker in walkers]
    abs_evaders = [abs(walker.delta_peak) for walker in walkers if walker.evades]
    abs_left = [abs(trial.left.delta_peak) for trial in trials]
    abs_right = [abs(trial.right.delta_peak) for trial in trials]
    ambiguous = [
        (trial.number, walker.person, abs(walker.delta_peak))
        for trial in trials
        for walker in (trial.left, trial.right)
        if AMBIGUOUS_LO_M <= abs(walker.delta_peak) <= AMBIGUOUS_HI_M
    ]

    lines = [
        f"# umbral |delta| < {NO_EVADE_M:.2f} m => no elude",
        "# delta > 0: desvio a su derecha (rx = uy, ry = -ux)",
        "# prueba id lado delta_pico_m lado_propio lado_lab elude delta_ca_m",
    ]
    for trial in trials:
        for walker in (trial.left, trial.right):
            lines.append(
                f"{trial.number} {walker.person} {walker.side} {walker.delta_peak:.6f} "
                f"{own_side(walker.delta_peak, walker.evades)} {walker.lab_side} "
                f"{int(walker.evades)} {walker.delta_ca:.6f}"
            )

    lines.append("")
    lines.append("# prueba d_min_m y_mayor cesion acuerdo_modelo delta_izq_m delta_der_m")
    for trial in trials:
        lines.append(
            f"{trial.number} {trial.d_min:.6f} {trial.higher_y} {trial.yielding} "
            f"{trial.model} {trial.left.delta_peak:.6f} {trial.right.delta_peak:.6f}"
        )

    yielding = [trial.yielding for trial in trials]
    model = [trial.model for trial in trials]
    lines.extend(
        [
            "",
            "# resumen",
            f"# umbral_no_elude_m {NO_EVADE_M:.2f}",
            f"# n_pruebas {len(trials)}",
            f"# n_peatones {len(walkers)}",
            f"# |delta_pico| todos {mean_std(abs_all)}",
            f"# |delta_pico| elusores {mean_std(abs_evaders)}",
            f"# |delta_pico| izquierda {mean_std(abs_left)}",
            f"# |delta_pico| derecha {mean_std(abs_right)}",
            f"# lado a_su_derecha {count_own_side(walkers, 'derecha')}",
            f"# lado a_su_izquierda {count_own_side(walkers, 'izquierda')}",
            f"# lado no_elude {count_own_side(walkers, 'no_elude')}",
            f"# cesion ambos {yielding.count('ambos')}",
            f"# cesion solo_izquierda {yielding.count('solo_izquierda')}",
            f"# cesion solo_derecha {yielding.count('solo_derecha')}",
            f"# cesion ninguno {yielding.count('ninguno')}",
            f"# acuerdo ambos_derecha {model.count('ambos_derecha')}",
            f"# acuerdo ambos_izquierda {model.count('ambos_izquierda')}",
            f"# acuerdo mixto {model.count('mixto')}",
            f"# acuerdo uno_solo {model.count('uno_solo')}",
            f"# acuerdo ninguno {model.count('ninguno')}",
            f"# y_mayor izquierda {sum(1 for trial in trials if trial.higher_y == 'izquierda')}",
            f"# y_mayor derecha {sum(1 for trial in trials if trial.higher_y == 'derecha')}",
            f"# y_mayor empate {sum(1 for trial in trials if trial.higher_y == 'empate')}",
        ]
    )
    if ambiguous:
        lines.append("# ambiguos |delta| en [0.08, 0.12] m: prueba id |delta_pico|")
        for number, person, value in ambiguous:
            lines.append(f"# {number} {person} {value:.6f}")
    else:
        lines.append("# ambiguos |delta| en [0.08, 0.12] m: ninguno")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(trials: list[Trial]) -> None:
    walkers = [walker for trial in trials for walker in (trial.left, trial.right)]
    print(f"umbral no elude: |delta| < {NO_EVADE_M:.2f} m")
    print(f"pruebas: {len(trials)}  peatones: {len(walkers)}")
    print(f"|delta_pico| todos:     {mean_std([abs(w.delta_peak) for w in walkers])}")
    print(f"|delta_pico| elusores:  {mean_std([abs(w.delta_peak) for w in walkers if w.evades])}")
    print(f"|delta_pico| izquierda: {mean_std([abs(t.left.delta_peak) for t in trials])}")
    print(f"|delta_pico| derecha:   {mean_std([abs(t.right.delta_peak) for t in trials])}")
    print(
        "lado: "
        f"a su derecha={count_own_side(walkers, 'derecha')}  "
        f"a su izquierda={count_own_side(walkers, 'izquierda')}  "
        f"no elude={count_own_side(walkers, 'no_elude')}"
    )
    yielding = [trial.yielding for trial in trials]
    model = [trial.model for trial in trials]
    print(
        "cesion: "
        f"ambos={yielding.count('ambos')}  "
        f"solo izquierda={yielding.count('solo_izquierda')}  "
        f"solo derecha={yielding.count('solo_derecha')}  "
        f"ninguno={yielding.count('ninguno')}"
    )
    print(
        "acuerdo con la heuristica: "
        f"ambos a su derecha={model.count('ambos_derecha')}  "
        f"ambos a su izquierda={model.count('ambos_izquierda')}  "
        f"mixto={model.count('mixto')}  "
        f"uno solo={model.count('uno_solo')}  "
        f"ninguno={model.count('ninguno')}"
    )


def _track_xy(track: dict[int, Position]) -> tuple[list[float], list[float]]:
    frames = sorted(track)
    return [track[frame][0] for frame in frames], [track[frame][1] for frame in frames]


def plot_deviations(trials: list[Trial], out_path: Path) -> None:
    numbers = [trial.number for trial in trials]
    fig, ax = new_figure()
    ax.plot(
        numbers,
        [trial.left.delta_peak for trial in trials],
        color=BLUE,
        marker=MARKERS[0],
        markeredgecolor="black",
        markeredgewidth=0.6,
        linestyle="-",
        zorder=3,
        label="izquierda",
    )
    ax.plot(
        numbers,
        [trial.right.delta_peak for trial in trials],
        color=VERMILLION,
        marker=MARKERS[1],
        markeredgecolor="black",
        markeredgewidth=0.6,
        linestyle="-",
        zorder=3,
        label="derecha",
    )
    ax.axhline(NO_EVADE_M, color="0.35", linestyle="--", zorder=2)
    ax.axhline(-NO_EVADE_M, color="0.35", linestyle="--", zorder=2, label=rf"umbral $\pm {NO_EVADE_M:.2f}$ m")
    ax.axhline(0.0, color="0.15", linewidth=0.9, zorder=1)
    style_axes(ax, "prueba", r"desvío a su derecha $\delta$ (m)")
    place_legend_below(ax, ncol=2)
    save_figure(fig, out_path)


def plot_trajectories(trials: list[Trial], out_path: Path) -> None:
    fig, ax = new_figure()
    for index, trial in enumerate(trials):
        left_x, left_y = _track_xy(trial.tracks[trial.left.person])
        right_x, right_y = _track_xy(trial.tracks[trial.right.person])
        ax.plot(
            left_x,
            left_y,
            color=BLUE,
            zorder=3,
            label="izquierda" if index == 0 else None,
        )
        ax.plot(
            right_x,
            right_y,
            color=VERMILLION,
            zorder=3,
            label="derecha" if index == 0 else None,
        )
    style_axes(ax, r"posición $x$ (m)", r"posición $y$ (m)")
    place_legend_below(ax, ncol=2)
    save_figure(fig, out_path)


def plot_summary(trials: list[Trial], out_path: Path) -> None:
    side_labels = ["a su derecha", "a su izquierda", "no elude"]
    side_keys = ["derecha", "izquierda", "no_elude"]
    counts = [
        sum(1 for trial in trials for walker in (trial.left, trial.right) if walker.lado_propio == key)
        for key in side_keys
    ]
    fig, ax = new_figure()
    ax.bar(side_labels, counts, color=BLUE, edgecolor="black", linewidth=0.6, zorder=3)
    ax.set_ylim(0, max(counts + [1]) * 1.08)
    style_axes(ax, "lado de elusión", "peatones")
    save_figure(fig, out_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify real 1-vs-1 crossings: evasion side and lateral displacement"
    )
    parser.add_argument(
        "--in-dir",
        type=Path,
        default=DEFAULT_CROSSINGS_DIR,
        help=f"crossing files (default: {DEFAULT_CROSSINGS_DIR})",
    )
    parser.add_argument(
        "--trials-file",
        type=Path,
        default=DEFAULT_TRIALS_PATH,
        help=f"trial left/right ids (default: {DEFAULT_TRIALS_PATH})",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"output directory (default: {DEFAULT_OUT_DIR})",
    )
    args = parser.parse_args()

    try:
        listings = read_trials(args.trials_file)
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    trials: list[Trial] = []
    try:
        for number, left, right, _start, _final in listings:
            path = args.in_dir / f"prueba{number}.txt"
            if not path.exists():
                print(f"prueba {number}: skipped, {path} does not exist", file=sys.stderr)
                continue
            trials.append(analyze_trial(path, number, left, right))
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    if not trials:
        sys.exit(f"{args.in_dir}: no crossing files were analyzed")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    table_path = args.out_dir / "elusion_behavior.txt"
    try:
        write_table(table_path, trials)
    except OSError as error:
        sys.exit(f"could not write {table_path}: {error}")
    print(f"wrote {table_path} ({len(trials)} crossings)")
    print_summary(trials)

    try:
        plot_deviations(trials, args.out_dir / "desvios_por_prueba.png")
        plot_trajectories(trials, args.out_dir / "trayectorias_reales.png")
        plot_summary(trials, args.out_dir / "resumen_lados.png")
    except OSError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
