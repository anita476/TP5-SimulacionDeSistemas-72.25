import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import matplotlib

from anim import GIF_DPI, LEFT, RIGHT, SIM_LEFT, SIM_RIGHT, make_figure, trial_positions
from plot_style import SAVE_DPI
from traj import (
    DEFAULT_TRIALS_PATH,
    Position,
    read_experiment,
    read_sim,
    read_trials,
)

MP4_DPI = 120


def find_trial(trials: list[tuple[int, str, str, int, int]], number: int) -> tuple[int, str, str, int, int]:
    for trial in trials:
        if trial[0] == number:
            return trial
    available = ", ".join(str(trial[0]) for trial in trials)
    raise ValueError(f"trial {number} not found; available: {available}")


def trial_from_path(path: Path) -> int | None:
    match = re.search(r"prueba(\d+)", path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else None


def pad(positions: list[Position | None], n: int) -> list[Position | None]:
    if len(positions) >= n:
        return positions[:n]
    last = next((p for p in reversed(positions) if p is not None), None)
    return positions + [last] * (n - len(positions))


def positions_at_times(
    times: list[float],
    positions: list[Position | None],
    query: list[float],
) -> list[Position | None]:
    """Nearest sample at each query time; hold the last point after the series ends."""
    if not times:
        return [None] * len(query)
    t0, t1 = times[0], times[-1]
    j = 0
    n = len(times)
    sampled: list[Position | None] = []
    for t in query:
        if t < t0:
            sampled.append(None)
            continue
        while j + 1 < n and times[j + 1] <= t:
            j += 1
        if t > t1:
            sampled.append(positions[-1])
            continue
        nxt = j + 1
        if nxt < n and abs(times[nxt] - t) < abs(times[j] - t):
            sampled.append(positions[nxt])
        else:
            sampled.append(positions[j])
    return sampled


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Animate experimental and simulated trajectories together (any real case vs any sim dump)"
    )
    parser.add_argument("--data", type=Path, required=True, help="experimental trajectories (e.g. data/cruces/prueba1.txt)")
    parser.add_argument("--sim", type=Path, required=True, help="simulation output (particle_id time x y vx vy)")
    parser.add_argument(
        "--trial",
        type=int,
        default=None,
        help="trial number for left/right ids (default: parsed from --data if named pruebaN)",
    )
    parser.add_argument(
        "--trials-file", type=Path, default=DEFAULT_TRIALS_PATH, help=f"trial left/right ids (default: {DEFAULT_TRIALS_PATH})"
    )
    parser.add_argument("--out", help="output GIF")
    parser.add_argument("--mp4", help="output MP4 (requires ffmpeg)")
    parser.add_argument("--png", help="PNG of one frame")
    parser.add_argument("--frame", type=int, default=None, help="PNG frame index (default: last; 0 = initial)")
    parser.add_argument("--no-title", action="store_true", help="hide the 'prueba N  t = ...' line (slide figures carry no title)")
    parser.add_argument("--show", action="store_true", help="open a window")
    parser.add_argument("--fps", type=int, default=None, help="video frames per second (default: experimental frame rate rounded, ~real time)")
    args = parser.parse_args()

    if args.fps is not None and args.fps < 1:
        sys.exit("--fps must be >= 1")
    if not args.out and not args.mp4 and not args.png and not args.show:
        args.show = True
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

    if not args.data.is_file():
        sys.exit(f"{args.data}: file not found")
    if not args.sim.is_file():
        sys.exit(f"{args.sim}: file not found")
    real_n = trial_from_path(args.data)
    sim_n = trial_from_path(args.sim)
    if args.trial is not None:
        trial_number = args.trial
    elif real_n is not None:
        trial_number = real_n
    else:
        sys.exit("could not parse trial number from --data; pass --trial")
    if real_n is not None and sim_n is not None and real_n != sim_n:
        caption = rf"real prueba {real_n} / sim prueba {sim_n}"
    else:
        caption = rf"prueba {trial_number}"

    try:
        experiment = read_experiment(args.data)
        trial, left, right, _start, _final = find_trial(read_trials(args.trials_file), trial_number)
        frames = [frame for person in (left, right) for frame in experiment.tracks.get(person, ())]
        if not frames:
            raise ValueError(f"trial {trial}: no positions for ids {left} and {right} in {args.data}")
        start, final = min(frames), max(frames)
        real = [
            trial_positions(experiment, trial, left, start, final),
            trial_positions(experiment, trial, right, start, final),
        ]
        sim = read_sim(args.sim)
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    # left = the particle that starts with the smaller x
    sim_left, sim_right = sorted(sim, key=lambda particle: sim[particle][1][0][0])
    sim_times = sim[sim_left][0]
    if len(sim_times) < 2:
        sys.exit("need at least 2 simulation time steps")

    n_real = final - start + 1
    t0 = sim_times[0]
    sim_duration = sim_times[-1] - t0
    n_sim = round(sim_duration * experiment.frame_rate) + 1
    n_frames = max(n_real, n_sim)
    # t = 0 is the first experimental frame of the crossing and the first simulation dump.
    query = [k / experiment.frame_rate for k in range(n_frames)]
    sim_query = [t0 + t for t in query]

    pedestrians = [
        (f"izquierda real (id {left})", LEFT, pad(real[0], n_frames)),
        (f"derecha real (id {right})", RIGHT, pad(real[1], n_frames)),
        (f"izquierda sim (id {sim_left})", SIM_LEFT, positions_at_times(sim_times, sim[sim_left][1], sim_query)),
        (f"derecha sim (id {sim_right})", SIM_RIGHT, positions_at_times(sim_times, sim[sim_right][1], sim_query)),
    ]
    fps = round(experiment.frame_rate) if args.fps is None else args.fps
    fig, draw = make_figure(
        trial,
        pedestrians,
        experiment.frame_rate,
        dots=True,
        linestyles=["-", "-", "--", "--"],
        caption=caption,
        show_title=not args.no_title,
    )

    if args.png:
        index = n_frames - 1 if args.frame is None else args.frame
        if not 0 <= index < n_frames:
            sys.exit(f"--frame must be in [0, {n_frames - 1}]")
        draw(index)
        png_path = Path(args.png)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=SAVE_DPI, facecolor="white")
        print(f"wrote {png_path} (frame {index}, t = {query[index]:.2f} s)")

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
