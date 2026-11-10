import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import matplotlib

from anim import GIF_DPI, LEFT, RIGHT, make_figure
from plot_style import SAVE_DPI
from traj import read_sim

MP4_DPI = 120
TARGET_FPS = 15


def guess_trial(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate the simulated trajectories of one 1-vs-1 elusion trial")
    parser.add_argument("sim", type=Path, help="simulation output (particle_id time x y vx vy)")
    parser.add_argument("--trial", type=int, default=None, help="trial number for the title (default: parsed from the file name)")
    parser.add_argument("--r", type=float, default=0.25, help="drawn pedestrian radius in m (default: SFM r = 0.25)")
    parser.add_argument("--out", help="output GIF")
    parser.add_argument("--mp4", help="output MP4 (requires ffmpeg)")
    parser.add_argument("--png", help="PNG of one frame")
    parser.add_argument("--frame", type=int, default=None, help="PNG simulation row (default: last; 0 = initial); snaps to the nearest drawn row")
    parser.add_argument("--show", action="store_true", help="open a window")
    parser.add_argument("--fps", type=int, default=None, help="video frames per second (default: drawn frame rate rounded, ~real time)")
    parser.add_argument(
        "--stride",
        type=int,
        default=None,
        help="draw every N-th simulation row (default: auto, ~15 drawn frames per simulated second; 1 = every row)",
    )
    args = parser.parse_args()

    if args.r <= 0:
        sys.exit("--r must be > 0")
    if args.fps is not None and args.fps < 1:
        sys.exit("--fps must be >= 1")
    if args.stride is not None and args.stride < 1:
        sys.exit("--stride must be >= 1")
    if not args.out and not args.mp4 and not args.png and not args.show:
        args.show = True
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

    try:
        sim = read_sim(args.sim)
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    # left = the particle that starts with the smaller x
    left, right = sorted(sim, key=lambda particle: sim[particle][1][0][0])
    times = sim[left][0]
    n_frames = len(times)
    if n_frames < 2:
        sys.exit("need at least 2 time steps")
    dt = float(times[1] - times[0])
    frame_rate = 1.0 / dt  # full simulation rows per simulated second

    # Drawing the trail of ~1e6 points on every frame is what makes small-dt runs crawl (~1 s per frame),
    # so the figure is built from every `stride`-th row. --stride 1 draws every row.
    stride = args.stride if args.stride is not None else max(1, round(1.0 / (TARGET_FPS * dt)))
    drawn_rate = frame_rate / stride  # drawn frames per simulated second
    n_drawn = len(range(0, n_frames, stride))
    fps = max(1, round(drawn_rate)) if args.fps is None else args.fps

    trial = args.trial if args.trial is not None else guess_trial(args.sim)
    pedestrians = [
        (f"izquierda (id {left})", LEFT, sim[left][1][::stride]),
        (f"derecha (id {right})", RIGHT, sim[right][1][::stride]),
    ]
    fig, draw = make_figure(trial, pedestrians, drawn_rate, args.r)

    if args.png:
        row = n_frames - 1 if args.frame is None else args.frame
        if not 0 <= row < n_frames:
            sys.exit(f"--frame must be in [0, {n_frames - 1}]")
        index = min(round(row / stride), n_drawn - 1)  # nearest drawn frame
        draw(index)
        png_path = Path(args.png)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=SAVE_DPI, facecolor="white")
        print(f"wrote {png_path} (row {index * stride}, t = {times[index * stride]:.3f} s)")

    if args.out:
        gif_path = Path(args.out)
        gif_path.parent.mkdir(parents=True, exist_ok=True)
        anim = FuncAnimation(fig, draw, frames=n_drawn, blit=False, interval=1000 / fps)
        anim.save(gif_path, writer=PillowWriter(fps=fps), dpi=GIF_DPI, savefig_kwargs={"facecolor": "white"})
        print(f"wrote {gif_path} ({n_drawn} frames at {fps} fps, stride {stride})")

    if args.mp4:
        mp4_path = Path(args.mp4)
        mp4_path.parent.mkdir(parents=True, exist_ok=True)
        anim = FuncAnimation(fig, draw, frames=n_drawn, blit=False, interval=1000 / fps)
        anim.save(
            mp4_path,
            writer=FFMpegWriter(fps=fps, bitrate=3000),
            dpi=MP4_DPI,
            savefig_kwargs={"facecolor": "white"},
        )
        print(f"wrote {mp4_path} ({n_drawn} frames at {fps} fps, stride {stride})")

    if args.show:
        anim = FuncAnimation(fig, draw, frames=n_drawn, blit=False, interval=1000 / fps, repeat=True)
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()