#!/usr/bin/env python3
"""
Recolector E[m, i, j]: recorre data/experiments (salida de experiment_runner.sh), recalcula las dos métricas
de cada simulación con las mismas funciones de calculate_equal_time.py / calculate_nearest_point.py y escribe
una única tabla:

    metric prueba r_min action_distance E_left E_right E_event

m = métrica (1 iguales tiempos, 2 punto más cercano), i = evento (prueba), j = (r_min, action_distance).

Uso:
    python scripts/collect_errors.py                                   # data/experiments -> data/calibration/errors.txt
    python scripts/collect_errors.py --experiments-dir otra/carpeta --out otra/errors.txt
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # calculate_* scripts
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import calculate_equal_time  # noqa: E402
import calculate_nearest_point  # noqa: E402
from calib import ErrorRecord, parse_experiment_name, write_errors  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
_SIDE = re.compile(r"^#\s*(izquierda|derecha):\s*id\s+(\S+)")


def left_right_ids(traj_path: Path) -> tuple[int, int] | None:
    """Ids from the '# izquierda: id X' / '# derecha: id Y' header of a crossing file."""
    sides: dict[str, int] = {}
    with open(traj_path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            m = _SIDE.match(line)
            if m:
                try:
                    sides[m.group(1)] = int(m.group(2))
                except ValueError:
                    return None
    if "izquierda" in sides and "derecha" in sides:
        return sides["izquierda"], sides["derecha"]
    return None


def pedestrian_errors(traj: Path, sim: Path) -> tuple[dict[int, float], dict[int, float]]:
    """{id: E1_i}, {id: E2_i} for one simulation."""
    e1 = {pid: float(np.nanmean(d2)) for pid, (_, _, _, d2) in calculate_equal_time.procesar(str(traj), str(sim)).items()}
    e2 = {pid: float(np.mean(d2)) for pid, (_, _, _, d2) in calculate_nearest_point.procesar(str(traj), str(sim)).items()}
    return e1, e2


def order_left_right(traj: Path, errors: dict[int, float]) -> tuple[int, int]:
    ids = left_right_ids(traj)
    if ids is not None and set(ids) == set(errors):
        return ids
    # fallback: the left pedestrian is the one that starts with the smaller x
    real = calculate_nearest_point.leer_real(str(traj))
    return tuple(sorted(errors, key=lambda pid: real[pid][1][0, 0]))  # type: ignore[return-value]


def collect(experiments_dir: Path, traj_dir: Path) -> list[ErrorRecord]:
    records: list[ErrorRecord] = []
    sims = sorted(p for p in experiments_dir.rglob("prueba*_action_distance_*_radio_*.txt") if parse_experiment_name(p.stem))
    if not sims:
        raise SystemExit(f"no simulations found under {experiments_dir} (run scripts/experiment_runner.sh first)")
    for sim in sims:
        prueba, r_min, action_distance = parse_experiment_name(sim.stem)  # type: ignore[misc]
        traj = traj_dir / f"prueba{prueba}.txt"
        if not traj.is_file():
            print(f"[aviso] {sim}: no existe {traj}, se saltea", file=sys.stderr)
            continue
        e1, e2 = pedestrian_errors(traj, sim)
        if len(e1) != 2 or len(e2) != 2:
            print(f"[aviso] {sim}: se esperaban 2 peatones, hay {len(e1)}/{len(e2)}, se saltea", file=sys.stderr)
            continue
        left, right = order_left_right(traj, e1)
        records.append(ErrorRecord(1, prueba, r_min, action_distance, e1[left], e1[right]))
        records.append(ErrorRecord(2, prueba, r_min, action_distance, e2[left], e2[right]))
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--experiments-dir", type=Path, default=REPO / "data/experiments", help="salida de experiment_runner.sh")
    ap.add_argument("--traj-dir", type=Path, default=REPO / "data/cruces_evento", help="cruces experimentales (recortados a f0)")
    ap.add_argument("--out", type=Path, default=REPO / "data/calibration/errors.txt", help="tabla E[m, i, j]")
    args = ap.parse_args()

    records = collect(args.experiments_dir, args.traj_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_errors(args.out, records, source=f"{args.experiments_dir} vs {args.traj_dir}")
    events = sorted({r.prueba for r in records})
    grid = sorted({r.grid_point for r in records})
    print(f"wrote {args.out}: {len(records)} rows, {len(events)} events, {len(grid)} grid points")


if __name__ == "__main__":
    main()
