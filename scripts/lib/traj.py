import re
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

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
