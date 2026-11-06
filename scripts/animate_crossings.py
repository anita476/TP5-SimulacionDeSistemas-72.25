import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from anim import GIF_DPI, LEFT, RIGHT, make_figure, trial_positions
from traj import DEFAULT_CROSSINGS_DIR, DEFAULT_TRIALS_PATH, read_experiment, read_trials


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate the semi-horizontal crossing of every trial, one GIF per trial")
    parser.add_argument(
        "--in-dir", type=Path, default=DEFAULT_CROSSINGS_DIR, help=f"pruebaN.txt files (default: {DEFAULT_CROSSINGS_DIR})"
    )
    parser.add_argument(
        "--trials-file", type=Path, default=DEFAULT_TRIALS_PATH, help=f"trial left/right ids (default: {DEFAULT_TRIALS_PATH})"
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="output directory (default: <in-dir>/gif)")
    parser.add_argument("--r", type=float, default=0.10, help="drawn pedestrian radius in m (default: 0.10)")
    args = parser.parse_args()
    if args.r <= 0:
        sys.exit("--r must be > 0")
    out_dir = args.out_dir if args.out_dir is not None else args.in_dir / "gif"

    try:
        trials = read_trials(args.trials_file)
    except (OSError, ValueError) as error:
        sys.exit(str(error))
    out_dir.mkdir(parents=True, exist_ok=True)

    for trial, left, right, _start, _final in trials:
        path = args.in_dir / f"prueba{trial}.txt"
        if not path.exists():
            print(f"prueba {trial}: skipped, {path} does not exist", file=sys.stderr)
            continue
        try:
            experiment = read_experiment(path)
            frames = [frame for track in experiment.tracks.values() for frame in track]
            start, final = min(frames), max(frames)
            pedestrians = [
                (f"izquierda (id {left})", LEFT, trial_positions(experiment, trial, left, start, final)),
                (f"derecha (id {right})", RIGHT, trial_positions(experiment, trial, right, start, final)),
            ]
        except (OSError, ValueError) as error:
            sys.exit(str(error))

        fps = round(experiment.frame_rate)
        n_frames = final - start + 1
        fig, draw = make_figure(trial, pedestrians, experiment.frame_rate, args.r)
        gif_path = out_dir / f"prueba{trial}.gif"
        anim = FuncAnimation(fig, draw, frames=n_frames, blit=False, interval=1000 / fps)
        anim.save(gif_path, writer=PillowWriter(fps=fps), dpi=GIF_DPI, savefig_kwargs={"facecolor": "white"})
        plt.close(fig)
        print(f"wrote {gif_path} ({n_frames} frames at {fps} fps)")


if __name__ == "__main__":
    main()
