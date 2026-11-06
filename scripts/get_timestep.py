import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from traj import DEFAULT_DATA_PATH, DEFAULT_TRIALS_PATH, read_trials


def read_data(data_path: Path) -> tuple[float, list[int]]:
    frame_rate: float | None = None
    frames: set[int] = set()

    with data_path.open(encoding="utf-8") as data_file:
        for line_number, line in enumerate(data_file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            if stripped_line.startswith("#"):
                if frame_rate is None:
                    match = re.search(
                        r"\bframerate:\s*([0-9]+(?:\.[0-9]+)?)\s*fps\b",
                        stripped_line,
                        re.IGNORECASE,
                    )
                    if match:
                        frame_rate = float(match.group(1))
                continue

            fields = stripped_line.split()
            if len(fields) < 2:
                raise ValueError(
                    f"{data_path}:{line_number}: expected an id and frame number"
                )
            try:
                frames.add(int(fields[1]))
            except ValueError as error:
                raise ValueError(
                    f"{data_path}:{line_number}: invalid frame number {fields[1]!r}"
                ) from error

    if frame_rate is None or frame_rate <= 0:
        raise ValueError(f"{data_path}: missing a positive framerate in the header")
    if not frames:
        raise ValueError(f"{data_path}: no data frames found")

    return frame_rate, sorted(frames)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print per-pair durations and timesteps for the elusion dataset."
    )
    parser.add_argument(
        "data_file",
        nargs="?",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"input data file (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--trials-file",
        type=Path,
        default=DEFAULT_TRIALS_PATH,
        help=f"file containing trial frame ranges (default: {DEFAULT_TRIALS_PATH})",
    )
    args = parser.parse_args()
    data_path = args.data_file
    trials_path = args.trials_file

    frame_rate, frames = read_data(data_path)
    trials = read_trials(trials_path)
    timestep = 1 / frame_rate

    print(f"Data file: {data_path}")
    print(f"Frame rate: {frame_rate:.6f} fps")
    print(f"Trial data: {trials_path}")
    print("Per-pair total times and timesteps:")
    print("Trial | Pair (left-right) | Frames | dt (s/frame) | Total time (s)")

    total_times: list[float] = []
    for number, left_person, right_person, start_frame, final_frame in trials:
        if final_frame <= start_frame:
            raise ValueError(
                f"Trial {number}: final frame must be after start frame"
            )
        if start_frame not in frames or final_frame not in frames:
            raise ValueError(
                f"Trial {number}: frame range {start_frame}-{final_frame} "
                "is outside the data"
            )

        total_time = (final_frame - start_frame) / frame_rate
        total_times.append(total_time)
        print(
            f"{number:5} | {left_person} - {right_person} | "
            f"{start_frame}-{final_frame} | {timestep:.9f} | {total_time:.9f}"
        )

    average_total_time = sum(total_times) / len(total_times)
    print(f"Average total time: {average_total_time:.9f} s")
    print(f"Gathered timestep used: 1 / {frame_rate:.6f} = {timestep:.9f} s/frame")


if __name__ == "__main__":
    main()