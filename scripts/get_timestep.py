import argparse
import re
from pathlib import Path


DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "elusion_1_contra_1.txt"
)


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
        description="Print frame times and the timestep for the elusion dataset."
    )
    parser.add_argument(
        "data_file",
        nargs="?",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"input data file (default: {DEFAULT_DATA_PATH})",
    )
    data_path = parser.parse_args().data_file

    frame_rate, frames = read_data(data_path)
    timestep = 1 / frame_rate

    print(f"Data file: {data_path}")
    print(f"Frame rate: {frame_rate:.6f} fps")
    print("Timesteps (frame, time from frame 0 [s], delta from previous [s]):")
    previous_frame: int | None = None
    for frame in frames:
        time = frame / frame_rate
        delta = (
            "n/a"
            if previous_frame is None
            else f"{(frame - previous_frame) / frame_rate:.9f}"
        )
        print(f"{frame}, {time:.9f}, {delta}")
        previous_frame = frame

    start_frame = frames[0]
    final_frame = frames[-1]
    start_time = start_frame / frame_rate
    final_time = final_frame / frame_rate
    total_time = final_time - start_time
    print(f"Start time: {start_time:.9f} s (frame {start_frame})")
    print(f"Final time: {final_time:.9f} s (frame {final_frame})")
    print(
        f"Total time: {final_time:.9f} - {start_time:.9f} "
        f"= {total_time:.9f} s"
    )
    print(
        f"Gathered timestep used: 1 / {frame_rate:.6f} = "
        f"{timestep:.9f} s/frame"
    )


if __name__ == "__main__":
    main()