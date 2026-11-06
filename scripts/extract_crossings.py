import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from traj import DEFAULT_CROSSINGS_DIR, DEFAULT_DATA_PATH, DEFAULT_TRIALS_PATH, Position, read_experiment, read_trials

# ~0.5 s at the 15 fps of the experiment: long enough to average out tracker jitter, short enough to locate the turn.
WINDOW_FRAMES = 8
MIN_ADVANCE = 0.2
# |dy| / dx below this (~27 degrees) counts as semi-horizontal; a looser bound accepts the diagonal step out of the queue.
MAX_SLOPE = 0.5


def crossing_start(track: dict[int, Position], frames: list[int], direction: int) -> int:
    """First frame from which the person walks mostly along x towards its destination, ending the approach to its departure point"""
    for frame in frames:
        later = track.get(frame + WINDOW_FRAMES)
        if later is None:
            continue
        advance = direction * (later[0] - track[frame][0])
        if advance >= MIN_ADVANCE and abs(later[1] - track[frame][1]) <= MAX_SLOPE * advance:
            return frame
    raise ValueError(f"never advances {MIN_ADVANCE} m along x within {WINDOW_FRAMES} frames")


def crossing_end(track: dict[int, Position], frames: list[int], start: int, direction: int, target_x: float) -> int | None:
    """First frame from start at which the person reaches target_x along direction; None if it never does"""
    for frame in frames:
        if frame >= start and direction * (track[frame][0] - target_x) >= 0:
            return frame
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write one file per trial with only the semi-horizontal crossing of each pedestrian"
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help=f"trajectories (default: {DEFAULT_DATA_PATH})")
    parser.add_argument(
        "--trials-file", type=Path, default=DEFAULT_TRIALS_PATH, help=f"trial frame ranges (default: {DEFAULT_TRIALS_PATH})"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_CROSSINGS_DIR, help=f"output directory (default: {DEFAULT_CROSSINGS_DIR})"
    )
    args = parser.parse_args()

    try:
        experiment = read_experiment(args.data)
        trials = read_trials(args.trials_file)
    except (OSError, ValueError) as error:
        sys.exit(str(error))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for trial, left, right, trial_start, _trial_final in trials:
        missing = [person for person in (left, right) if person not in experiment.tracks]
        if missing:
            print(f"prueba {trial}: skipped, person {', '.join(missing)} is not in the data", file=sys.stderr)
            continue

        # Before trial_start the right person is still walking back to its queue, which is not part of the crossing.
        walkers = []
        for side, person, direction in (("izquierda", left, 1), ("derecha", right, -1)):
            track = experiment.tracks[person]
            frames = sorted(frame for frame in track if frame >= trial_start)
            if not frames:
                sys.exit(f"prueba {trial}: person {person} has no frames from {trial_start} on")
            try:
                start = crossing_start(track, frames, direction)
            except ValueError as error:
                sys.exit(f"prueba {trial}: person {person} {error}")
            walkers.append((side, person, direction, track, frames, start))

        # Each person's destination is the other's departure point.
        departures_x = [track[start][0] for _side, _person, _direction, track, _frames, start in walkers]
        rows = []
        header = []
        for (side, person, direction, track, frames, start), target_x in zip(walkers, reversed(departures_x)):
            end = crossing_end(track, frames, start, direction, target_x)
            if end is None:
                end = frames[-1]
                print(
                    f"prueba {trial}: person {person} never reaches x = {target_x:.2f} m; "
                    f"kept up to its last frame {end} (x = {track[end][0]:.2f} m)",
                    file=sys.stderr,
                )
            header.append(f"# {side}: id {person}, cuadros {start}-{end}")
            # markerID equals id for every trial participant in the source data.
            rows.extend(
                f"{person} {frame} {track[frame][0]} {track[frame][1]} {person}"
                for frame in frames
                if start <= frame <= end
            )

        out_path = args.out_dir / f"prueba{trial}.txt"
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"# framerate: {experiment.frame_rate} fps\n")
            fh.write(f"# prueba {trial}: solo el tramo semihorizontal de cada persona\n")
            fh.writelines(line + "\n" for line in header)
            fh.write("# id frame x/m y/m markerID\n")
            fh.writelines(row + "\n" for row in rows)
        print(f"wrote {out_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
