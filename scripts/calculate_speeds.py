import argparse
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from lib.traj import DEFAULT_CROSSINGS_DIR, DEFAULT_DATA_PATH, DEFAULT_TRIALS_PATH, read_experiment, read_trials


def median_speed(track: dict[int, tuple[float, float]], frame_rate: float) -> float:
    frames = sorted(track)
    if len(frames) < 2:
        raise ValueError("at least two positions are required to calculate speed")

    speeds = []
    for frame, next_frame in zip(frames, frames[1:]):
        elapsed_time = (next_frame - frame) / frame_rate
        x, y = track[frame]
        next_x, next_y = track[next_frame]
        speeds.append(math.hypot(next_x - x, next_y - y) / elapsed_time)
    return statistics.median(speeds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the median speed of each participant in every crossing")
    parser.add_argument(
        "--in-dir", type=Path, default=DEFAULT_CROSSINGS_DIR, help=f"crossing files (default: {DEFAULT_CROSSINGS_DIR})"
    )
    parser.add_argument(
        "--trials-file", type=Path, default=DEFAULT_TRIALS_PATH, help=f"trial left/right ids (default: {DEFAULT_TRIALS_PATH})"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_DATA_PATH.parent / "pruebas_speeds.txt",
        help="output file (default: data/pruebas_speeds.txt)",
    )
    args = parser.parse_args()

    try:
        trials = read_trials(args.trials_file)
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    rows = []
    for trial, left, right, _start, _final in trials:
        path = args.in_dir / f"prueba{trial}.txt"
        if not path.exists():
            print(f"prueba {trial}: skipped, {path} does not exist", file=sys.stderr)
            continue

        try:
            experiment = read_experiment(path)
            for person in (left, right):
                if person not in experiment.tracks:
                    raise ValueError(f"person {person} is not in the crossing data")
                speed = median_speed(experiment.tracks[person], experiment.frame_rate)
                rows.append(f"{trial} {person} {speed:.6f}")
        except (OSError, ValueError) as error:
            sys.exit(f"{path}: {error}")

    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(f"{row}\n" for row in rows), encoding="utf-8")
    except OSError as error:
        sys.exit(f"could not write {args.out}: {error}")

    print(f"wrote {args.out} ({len(rows)} particle speeds)")


if __name__ == "__main__":
    main()
