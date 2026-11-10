import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from lib.traj import DEFAULT_CROSSINGS_DIR

_FRAME_RATE = re.compile(r"\bframerate:\s*([0-9]+(?:\.[0-9]+)?)\s*fps\b", re.IGNORECASE)
_CROSSING_FILE = re.compile(r"prueba(\d+)\.txt")


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
                    match = _FRAME_RATE.search(stripped_line)
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
    if len(frames) < 2:
        raise ValueError(f"{data_path}: expected at least two distinct data frames")

    return frame_rate, sorted(frames)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write each crossing's total time and print its timestep."
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
        default=DEFAULT_CROSSINGS_DIR / "tiempos_totales.txt",
        help="output file (default: data/cruces/tiempos_totales.txt)",
    )
    args = parser.parse_args()

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
            frame_rate, frames = read_data(path)
            timestep = 1 / frame_rate
            total_time = (frames[-1] - frames[0]) / frame_rate
            rows.append(f"{crossing} {total_time:.9f}")
            print(f"Cruce {crossing}: timestep = {timestep:.9f} s/frame")

        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(f"{row}\n" for row in rows), encoding="utf-8")
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    print(f"Escrito {args.out} ({len(rows)} cruces)")


if __name__ == "__main__":
    main()
