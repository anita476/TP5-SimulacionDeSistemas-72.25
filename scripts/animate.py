import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import matplotlib

from anim import GIF_DPI, LEFT, RIGHT, make_figure, trial_positions
from plot_style import SAVE_DPI
from traj import DEFAULT_DATA_PATH, DEFAULT_TRIALS_PATH, read_experiment, read_trials

MP4_DPI = 120


def find_trial(trials: list[tuple[int, str, str, int, int]], number: int) -> tuple[int, str, str, int, int]:
    for trial in trials:
        if trial[0] == number:
            return trial
    available = ", ".join(str(trial[0]) for trial in trials)
    raise ValueError(f"trial {number} not found; available: {available}")


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
