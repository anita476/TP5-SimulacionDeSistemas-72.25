import re
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_DATA_PATH = _DATA_DIR / "elusion_1_contra_1.txt"
DEFAULT_TRIALS_PATH = _DATA_DIR / "LEEME_elusion1contra1.txt"
DEFAULT_CROSSINGS_DIR = _DATA_DIR / "cruces"

_FRAME_RATE = re.compile(r"\bframerate:\s*([0-9]+(?:\.[0-9]+)?)\s*fps\b", re.IGNORECASE)

Position = tuple[float, float]


@dataclass
class Experiment:
    frame_rate: float
    tracks: dict[str, dict[int, Position]]


def _fail(path: str, lineno: int, msg: str) -> NoReturn:
    raise ValueError(f"{path}:{lineno}: {msg}")


def read_experiment(path: str | Path) -> Experiment:
    """Read 'id frame x y markerID' rows; tracks[id][frame] = (x, y) in meters"""
    path_s = str(path)
    frame_rate: float | None = None
    tracks: dict[str, dict[int, Position]] = {}
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                match = _FRAME_RATE.search(line)
                if match and frame_rate is None:
                    frame_rate = float(match.group(1))
                continue
            parts = line.split()
            if len(parts) != 5:
                _fail(path_s, lineno, f"expected 'id frame x y markerID', got {line!r}")
            person, frame_s, x_s, y_s, _marker = parts
            try:
                frame, position = int(frame_s), (float(x_s), float(y_s))
            except ValueError:
                _fail(path_s, lineno, f"invalid frame or position in {line!r}")
            track = tracks.setdefault(person, {})
            if frame in track:
                _fail(path_s, lineno, f"person {person!r} has frame {frame} twice")
            track[frame] = position

    if frame_rate is None or frame_rate <= 0:
        raise ValueError(f"{path_s}: missing a positive framerate in the header")
    if not tracks:
        raise ValueError(f"{path_s}: no data rows")
    return Experiment(frame_rate=frame_rate, tracks=tracks)


def read_trials(trials_path: Path) -> list[tuple[int, str, str, int, int]]:
    trials: list[tuple[int, str, str, int, int]] = []
    trial_pattern = re.compile(
        r"prueba\s+(\d+):\s*sale izquierda\s+([^,]+),\s*sale derecha\s+([^,]+),"
        r"\s*cuadros\s+(\d+)-(\d+)",
        re.IGNORECASE,
    )

    with trials_path.open(encoding="utf-8") as trials_file:
        for line in trials_file:
            match = trial_pattern.search(line)
            if match:
                number, left_person, right_person, start_frame, final_frame = (
                    match.groups()
                )
                trials.append(
                    (
                        int(number),
                        left_person.strip(),
                        right_person.strip(),
                        int(start_frame),
                        int(final_frame),
                    )
                )

    if not trials:
        raise ValueError(f"{trials_path}: no trial frame ranges found")
    return trials


def read_sim(path: Path) -> dict[int, tuple[list[float], list[Position | None]]]:
    """Read 'particle_id time x y vx vy' rows. Returns {id: (times, positions)}."""
    rows: dict[int, tuple[list[float], list[Position | None]]] = {}
    with open(path, encoding="utf-8") as file:
        header = file.readline().split()
        if header[:4] != ["particle_id", "time", "x", "y"]:
            raise ValueError(f"{path}: unexpected header {header}")
        for number, line in enumerate(file, start=2):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 4:
                raise ValueError(f"{path}:{number}: expected at least 4 columns")
            try:
                particle = int(fields[0])
                time, x, y = (float(value) for value in fields[1:4])
            except ValueError:
                raise ValueError(f"{path}:{number}: invalid values in {line.strip()!r}") from None
            times, positions = rows.setdefault(particle, ([], []))
            times.append(time)
            positions.append((x, y))
    if len(rows) != 2:
        raise ValueError(f"{path}: expected exactly 2 particles, found {len(rows)}")
    if len({len(times) for times, _ in rows.values()}) != 1:
        raise ValueError(f"{path}: particles have different numbers of steps")
    return rows
