import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from lib.traj import DEFAULT_CROSSINGS_DIR, DEFAULT_TRIALS_PATH, read_experiment, read_trials

_CROSSING_FILE = re.compile(r"prueba(\d+)\.txt")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write the initial vx and vy of every particle in each crossing."
    )
    parser.add_argument(
        "--in-dir",
        type=Path,
        default=DEFAULT_CROSSINGS_DIR,
        help=f"directory containing pruebaN.txt files (default: {DEFAULT_CROSSINGS_DIR})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_CROSSINGS_DIR / "velocidades_iniciales.txt",
        help="output file (default: data/cruces/velocidades_iniciales.txt)",
    )
    parser.add_argument(
        "--trials-file",
        type=Path,
        default=DEFAULT_TRIALS_PATH,
        help=f"file containing left/right particle ids (default: {DEFAULT_TRIALS_PATH})",
    )
    args = parser.parse_args()

    try:
        trials = {
            number: (left, right)
            for number, left, right, _start, _final in read_trials(args.trials_file)
        }
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    crossing_files = []
    for path in args.in_dir.glob("prueba*.txt"):
        match = _CROSSING_FILE.fullmatch(path.name)
        if match:
            crossing_files.append((int(match.group(1)), path))
    crossing_files.sort()
    if not crossing_files:
        sys.exit(f"{args.in_dir}: no files matching pruebaN.txt")

    rows = []
    try:
        for crossing, path in crossing_files:
            experiment = read_experiment(path)
            if crossing not in trials:
                raise ValueError(
                    f"{path}: crossing {crossing} is not listed in {args.trials_file}"
                )
            left, right = trials[crossing]
            for particle in (left, right):
                if particle not in experiment.tracks:
                    raise ValueError(
                        f"{path}: particle {particle} is missing from the crossing data"
                    )
                track = experiment.tracks[particle]
                frames = sorted(track)
                if len(frames) < 2:
                    raise ValueError(f"particle {particle} has fewer than two positions")
                first_frame, next_frame = frames[:2]
                elapsed_time = (next_frame - first_frame) / experiment.frame_rate
                x, y = track[first_frame]
                next_x, next_y = track[next_frame]
                vx = (next_x - x) / elapsed_time
                vy = (next_y - y) / elapsed_time
                rows.append(f"{crossing} {particle} {vx:.6f} {vy:.6f}")

        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(f"{row}\n" for row in rows), encoding="utf-8")
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    print(f"wrote {args.out} ({len(rows)} initial particle velocities)")


if __name__ == "__main__":
    main()
