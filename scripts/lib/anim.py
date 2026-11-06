import math

from matplotlib.patches import Circle

from plot_style import BLUE, FONT_SIZE, VERMILLION, apply_academic_style, style_axes
from traj import Experiment, Position

LEFT = BLUE
RIGHT = VERMILLION
UNTRACKED = "0.6"
UNTRACKED_ALPHA = 0.35
GIF_DPI = 100


def trial_positions(
    experiment: Experiment, trial: int, person: str, start: int, final: int
) -> list[Position | None]:
    """Position at every frame of [start, final], None where the tracker lost the person"""
    track = experiment.tracks.get(person)
    if track is None:
        raise ValueError(f"trial {trial}: person {person!r} is not in the data")
    positions = [track.get(frame) for frame in range(start, final + 1)]
    if all(position is None for position in positions):
        raise ValueError(f"trial {trial}: person {person!r} has no positions in frames {start}-{final}")
    return positions


def _last_known(positions: list[Position | None]) -> list[Position | None]:
    held: list[Position | None] = []
    last = None
    for position in positions:
        last = position if position is not None else last
        held.append(last)
    return held


def _stats_line(trial: int, t: float) -> str:
    return rf"prueba {trial}    $t = {t:.2f}$ s"


def make_figure(
    trial: int,
    pedestrians: list[tuple[str, str, list[Position | None]]],
    frame_rate: float,
    r: float,
):
    """pedestrians: (label, color, positions) in drawing order"""
    apply_academic_style()
    import matplotlib.pyplot as plt

    known = [p for _label, _color, positions in pedestrians for p in positions if p is not None]
    margin = 2.0 * r
    x0, x1 = min(x for x, _ in known) - margin, max(x for x, _ in known) + margin
    y0, y1 = min(y for _, y in known) - margin, max(y for _, y in known) + margin

    # Figure height follows the data aspect so the equal-aspect axes fill the frame.
    width, left_in, right_in, top_in, bottom_in = 12.0, 1.3, 0.3, 0.8, 2.1
    ax_width = width - left_in - right_in
    ax_height = ax_width * (y1 - y0) / (x1 - x0)
    height = ax_height + top_in + bottom_in
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes((left_in / width, bottom_in / height, ax_width / width, ax_height / height))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    style_axes(ax, r"posición $x$ (m)", r"posición $y$ (m)")

    trails = []
    discs = []
    for label, color, _positions in pedestrians:
        (trail,) = ax.plot([], [], color=color, lw=1.6, alpha=0.8, zorder=3)
        disc = Circle((0.0, 0.0), r, fc=color, ec="black", lw=0.6, zorder=4)
        ax.add_patch(disc)
        ax.plot([], [], linestyle="none", marker="o", color=color, markeredgecolor="black", label=label)
        trails.append(trail)
        discs.append(disc)
    ax.plot(
        [],
        [],
        linestyle="none",
        marker="o",
        color=UNTRACKED,
        markeredgecolor="black",
        alpha=UNTRACKED_ALPHA,
        label="sin registro",
    )
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=True, fancybox=False)
    stats = fig.text(0.5, 1.0 - 0.15 / height, _stats_line(trial, 0.0), ha="center", va="top", fontsize=FONT_SIZE)

    # NaN breaks the trail where the tracker lost the person instead of bridging the gap.
    trail_xs = [[p[0] if p is not None else math.nan for p in positions] for _l, _c, positions in pedestrians]
    trail_ys = [[p[1] if p is not None else math.nan for p in positions] for _l, _c, positions in pedestrians]
    held = [_last_known(positions) for _l, _c, positions in pedestrians]

    def draw(index: int) -> None:
        for k, (_label, _color, positions) in enumerate(pedestrians):
            trails[k].set_data(trail_xs[k][: index + 1], trail_ys[k][: index + 1])
            shown = held[k][index]
            discs[k].set_visible(shown is not None)
            if shown is not None:
                discs[k].center = shown
                discs[k].set_alpha(1.0 if positions[index] is not None else UNTRACKED_ALPHA)
        stats.set_text(_stats_line(trial, index / frame_rate))

    draw(0)
    return fig, draw
