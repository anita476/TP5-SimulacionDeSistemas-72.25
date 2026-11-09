import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import matplotlib
import numpy as np

from anim import GIF_DPI, LEFT, RIGHT, make_figure
from plot_style import SAVE_DPI

MP4_DPI = 120


def read_sim(path: Path) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Read 'particle_id time x y vx vy' rows. Returns {id: (times (n,), positions (n, 2))}."""
    rows: dict[int, list[tuple[float, float, float]]] = {}
    with open(path) as file:
        header = file.readline().split()
        if header[:4] != ["particle_id", "time", "x", "y"]:
            raise ValueError(f"{path}: unexpected header {header}")
        for number, line in enumerate(file, start=2):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 4:
                raise ValueError(f"{path}:{number}: expected at least 4 columns")
            particle = int(fields[0])
            time, x, y = (float(value) for value in fields[1:4])
            rows.setdefault(particle, []).append((time, x, y))
    if len(rows) != 2:
        raise ValueError(f"{path}: expected exactly 2 particles, found {len(rows)}")
    out = {}
    for particle, values in rows.items():
        data = np.array(values)
        out[particle] = (data[:, 0], data[:, 1:3])
    lengths = {len(times) for times, _ in out.values()}
    if len(lengths) != 1:
        raise ValueError(f"{path}: particles have different numbers of steps")
    return out


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
    parser.add_argument("--frame", type=int, default=None, help="PNG frame index (default: middle; 0 = initial)")
    parser.add_argument("--show", action="store_true", help="open a window")
    parser.add_argument("--fps", type=int, default=None, help="video frames per second (default: 1/dt rounded, ~real time)")
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
        sim = read_sim(args.sim)
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    # left = the particle that starts with the smaller x
    left, right = sorted(sim, key=lambda particle: sim[particle][1][0, 0])
    times = sim[left][0]
    n_frames = len(times)
    if n_frames < 2:
        sys.exit("need at least 2 time steps")
    dt = float(times[1] - times[0])
    frame_rate = 1.0 / dt

    trial = args.trial if args.trial is not None else guess_trial(args.sim)
    pedestrians = [
        (f"izquierda (id {left})", LEFT, sim[left][1]),
        (f"derecha (id {right})", RIGHT, sim[right][1]),
    ]
    fps = round(frame_rate) if args.fps is None else args.fps
    fig, draw = make_figure(trial, pedestrians, frame_rate, args.r)

    if args.png:
        index = n_frames // 2 if args.frame is None else args.frame
        if not 0 <= index < n_frames:
            sys.exit(f"--frame must be in [0, {n_frames - 1}]")
        draw(index)
        png_path = Path(args.png)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=SAVE_DPI, facecolor="white")
        print(f"wrote {png_path} (frame {index}, t = {times[index]:.3f} s)")

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