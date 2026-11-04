import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import matplotlib
from matplotlib.patches import Circle

from get_timestep import DEFAULT_DATA_PATH, DEFAULT_TRIALS_PATH, read_trials
from plot_style import BLUE, FONT_SIZE, SAVE_DPI, VERMILLION, apply_academic_style, style_axes
from traj import Experiment, Position, read_experiment

LEFT = BLUE
RIGHT = VERMILLION
UNTRACKED = "0.6"
UNTRACKED_ALPHA = 0.35
GIF_DPI = 100
MP4_DPI = 120


def find_trial(trials: list[tuple[int, str, str, int, int]], number: int) -> tuple[int, str, str, int, int]:
    for trial in trials:
        if trial[0] == number:
            return trial
    available = ", ".join(str(trial[0]) for trial in trials)
    raise ValueError(f"trial {number} not found; available: {available}")


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate the experimental trajectories of one 1-vs-1 elusion trial")
    parser.add_argument("--trial", type=int, required=True, help="trial number (prueba) from the trials file")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help=f"trajectories (default: {DEFAULT_DATA_PATH})")
    parser.add_argument(
        "--trials-file", type=Path, default=DEFAULT_TRIALS_PATH, help=f"trial frame ranges (default: {DEFAULT_TRIALS_PATH})"
    )
    parser.add_argument("--r", type=float, default=0.25, help="drawn pedestrian radius in m (default: SFM r = 0.25)")
    parser.add_argument("--out", help="output GIF")
    parser.add_argument("--mp4", help="output MP4 (requires ffmpeg)")
    parser.add_argument("--png", help="PNG of one frame")
    parser.add_argument("--frame", type=int, default=None, help="PNG frame index within the trial (default: middle; 0 = initial)")
    parser.add_argument("--show", action="store_true", help="open a window")
    parser.add_argument("--fps", type=int, default=None, help="video frames per second (default: experimental frame rate rounded, ~real time)")
    args = parser.parse_args()

    if args.r <= 0:
        sys.exit("--r must be > 0")
    if args.fps is not None and args.fps < 1:
        sys.exit("--fps must be >= 1")
    if not args.out and not args.mp4 and not args.png and not args.show:
        args.show = True
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

    try:
        experiment = read_experiment(args.data)
        trial, left, right, start, final = find_trial(read_trials(args.trials_file), args.trial)
        if final <= start:
            raise ValueError(f"trial {trial}: final frame {final} must be after start frame {start}")
        pedestrians = [
            (f"izquierda (id {left})", LEFT, trial_positions(experiment, trial, left, start, final)),
            (f"derecha (id {right})", RIGHT, trial_positions(experiment, trial, right, start, final)),
        ]
    except (OSError, ValueError) as error:
        sys.exit(str(error))
    fps = round(experiment.frame_rate) if args.fps is None else args.fps
    fig, draw = make_figure(trial, pedestrians, experiment.frame_rate, args.r)
    n_frames = final - start + 1

    if args.png:
        index = n_frames // 2 if args.frame is None else args.frame
        if not 0 <= index < n_frames:
            sys.exit(f"--frame must be in [0, {n_frames - 1}]")
        draw(index)
        png_path = Path(args.png)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=SAVE_DPI, facecolor="white")
        print(f"wrote {png_path} (frame {index} = cuadro {start + index})")

    if args.out:
        gif_path = Path(args.out)
        gif_path.parent.mkdir(parents=True, exist_ok=True)
        anim = FuncAnimation(fig, draw, frames=n_frames, blit=False, interval=1000 / fps)
        anim.save(gif_path, writer=PillowWriter(fps=fps), dpi=GIF_DPI, savefig_kwargs={"facecolor": "white"})
        print(f"wrote {gif_path} ({n_frames} frames at {fps} fps)")

    if args.mp4:
        mp4_path = Path(args.mp4)
        mp4_path.parent.mkdir(parents=True, exist_ok=True)
        anim = FuncAnimation(fig, draw, frames=n_frames, blit=False, interval=1000 / fps)
        anim.save(
            mp4_path,
            writer=FFMpegWriter(fps=fps, bitrate=3000),
            dpi=MP4_DPI,
            savefig_kwargs={"facecolor": "white"},
        )
        print(f"wrote {mp4_path} ({n_frames} frames at {fps} fps)")

    if args.show:
        anim = FuncAnimation(fig, draw, frames=n_frames, blit=False, interval=1000 / fps, repeat=True)
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
