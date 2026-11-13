"""Calibration of the elusion layer: the error collector E[m, i, j] and points b, c, d.

Indices: m = metric (1 equal times, 2 nearest point), i = event (prueba), j = grid point (d_lat, d_act).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

GridPoint = tuple[float, float]  # (d_lat, d_act)

_EXPERIMENT_NAME = re.compile(
    r"^prueba(\d+)_action_distance_([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)_radio_([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)$"
)


def parse_experiment_name(stem: str) -> tuple[int, float, float] | None:
    """'prueba12_action_distance_5_radio_0.3' -> (12, d_lat=0.3, d_act=5.0); None if it is not a sim stem."""
    match = _EXPERIMENT_NAME.match(stem)
    if match is None:
        return None
    prueba, d_act, d_lat = match.groups()
    return int(prueba), float(d_lat), float(d_act)


@dataclass(frozen=True)
class ErrorRecord:
    metric: int
    prueba: int
    d_lat: float
    d_act: float
    E_left: float
    E_right: float

    @property
    def grid_point(self) -> GridPoint:
        return (self.d_lat, self.d_act)

    @property
    def E_event(self) -> float:
        """Event error: mean over its 2 pedestrians (enunciado, eq. 3 prelude)."""
        return 0.5 * (self.E_left + self.E_right)


ERRORS_COLUMNS = "metric prueba d_lat d_act E_left E_right E_event"


def write_errors(path: str | Path, records: list[ErrorRecord], source: str) -> None:
    lines = [
        "# E[m, i, j]: error de cada peaton y del evento, por metrica m, evento i y punto de grilla j = (d_lat, d_act)",
        f"# fuente: {source}",
        "# unidades: m^2. E_event = (E_left + E_right) / 2",
        f"# {ERRORS_COLUMNS}",
    ]
    for r in sorted(records, key=lambda r: (r.metric, r.prueba, r.d_lat, r.d_act)):
        lines.append(f"{r.metric} {r.prueba} {r.d_lat:g} {r.d_act:g} {r.E_left:.8e} {r.E_right:.8e} {r.E_event:.8e}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_errors(path: str | Path) -> list[ErrorRecord]:
    records: list[ErrorRecord] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                raise ValueError(f"{path}:{lineno}: expected '{ERRORS_COLUMNS}', got {line!r}")
            records.append(
                ErrorRecord(int(parts[0]), int(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]))
            )
    if not records:
        raise ValueError(f"{path}: no error rows")
    return records


@dataclass
class ErrorTable:
    """E[i, j] for one metric: rows = events (sorted), columns = grid points (sorted by d_lat then d_act)."""

    metric: int
    events: list[int]
    grid: list[GridPoint]
    E: np.ndarray  # shape (len(events), len(grid)), NaN where the combination is missing

    @classmethod
    def from_records(cls, records: list[ErrorRecord], metric: int) -> "ErrorTable":
        rows = [r for r in records if r.metric == metric]
        if not rows:
            raise ValueError(f"no records for metric {metric}")
        events = sorted({r.prueba for r in rows})
        grid = sorted({r.grid_point for r in rows})
        E = np.full((len(events), len(grid)), np.nan)
        ei = {p: k for k, p in enumerate(events)}
        gj = {g: k for k, g in enumerate(grid)}
        for r in rows:
            E[ei[r.prueba], gj[r.grid_point]] = r.E_event
        return cls(metric, events, grid, E)

    def missing(self) -> list[tuple[int, GridPoint]]:
        out = []
        for i, j in zip(*np.where(np.isnan(self.E))):
            out.append((self.events[i], self.grid[j]))
        return out

    def d_lats(self) -> list[float]:
        return sorted({g[0] for g in self.grid})

    def d_acts(self) -> list[float]:
        return sorted({g[1] for g in self.grid})


# --- (b) population calibration -----------------------------------------------------------------


@dataclass
class PopulationResult:
    grid: list[GridPoint]
    mean: np.ndarray  # <E>(j) over the events that have that grid point
    sem: np.ndarray  # standard error of that mean (std ddof=1 / sqrt(n)); NaN when n < 2
    n: np.ndarray  # number of events behind each mean
    optimum_index: int

    @property
    def optimum(self) -> GridPoint:
        return self.grid[self.optimum_index]

    @property
    def optimum_mean(self) -> float:
        return float(self.mean[self.optimum_index])

    @property
    def optimum_sem(self) -> float:
        return float(self.sem[self.optimum_index])


def _mean_sem(E: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = np.sum(~np.isnan(E), axis=0)
    with np.errstate(invalid="ignore"):
        mean = np.nanmean(E, axis=0)
        sd = np.nanstd(E, axis=0, ddof=1)
    sem = np.where(n > 1, sd / np.sqrt(np.maximum(n, 1)), np.nan)
    return mean, sem, n


def population(table: ErrorTable) -> PopulationResult:
    """Grid search of <E>(p1, p2) = mean over events (eq. 3). The optimum is the grid point with the lowest mean,
    considering only grid points that every event has (an incomplete column cannot be compared fairly)."""
    mean, sem, n = _mean_sem(table.E)
    complete = n == len(table.events)
    if not complete.any():
        raise ValueError("no grid point is simulated for every event; complete the sweep first")
    candidate = np.where(complete, mean, np.inf)
    return PopulationResult(table.grid, mean, sem, n, int(np.argmin(candidate)))


# --- (c) individual calibration -----------------------------------------------------------------


@dataclass(frozen=True)
class IndividualResult:
    prueba: int
    optimum: GridPoint
    E_individual: float  # E_m at its own optimum
    E_population: float  # E_m at the population optimum of (b)


def individual(table: ErrorTable, pop: PopulationResult) -> list[IndividualResult]:
    out = []
    for i, prueba in enumerate(table.events):
        row = table.E[i]
        if np.all(np.isnan(row)):
            continue
        j = int(np.nanargmin(row))
        out.append(IndividualResult(prueba, table.grid[j], float(row[j]), float(row[pop.optimum_index])))
    return out


# --- (d) cross-validation ------------------------------------------------------------------------


@dataclass(frozen=True)
class Fold:
    partition: int
    train: tuple[int, ...]
    validation: tuple[int, ...]
    optimum: GridPoint
    E_train: float
    E_validation: float


def crossval(table: ErrorTable, partitions: int, train_fraction: float, seed: int) -> list[Fold]:
    """Random train/validation splits; the population optimum is found on the training events only
    (complete grid points only, as in population()) and its error reported on the validation events."""
    M = len(table.events)
    n_train = int(round(train_fraction * M))
    if n_train < 1 or n_train >= M:
        raise ValueError(f"train_fraction={train_fraction} leaves {n_train} training events out of {M}")
    complete = np.sum(~np.isnan(table.E), axis=0) == M
    if not complete.any():
        raise ValueError("no grid point is simulated for every event; complete the sweep first")
    rng = np.random.default_rng(seed)
    folds = []
    for k in range(partitions):
        perm = rng.permutation(M)
        tr, va = np.sort(perm[:n_train]), np.sort(perm[n_train:])
        train_mean = np.where(complete, table.E[tr].mean(axis=0), np.inf)
        j = int(np.argmin(train_mean))
        folds.append(
            Fold(
                k,
                tuple(table.events[i] for i in tr),
                tuple(table.events[i] for i in va),
                table.grid[j],
                float(train_mean[j]),
                float(table.E[va, j].mean()),
            )
        )
    return folds


@dataclass
class CrossvalSummary:
    partitions: int
    E_validation_mean: float
    E_validation_sd: float
    E_train_mean: float
    E_train_sd: float
    optimum_counts: dict[GridPoint, int] = field(default_factory=dict)


def summarize_crossval(folds: list[Fold]) -> CrossvalSummary:
    val = np.array([f.E_validation for f in folds])
    tr = np.array([f.E_train for f in folds])
    counts: dict[GridPoint, int] = {}
    for f in folds:
        counts[f.optimum] = counts.get(f.optimum, 0) + 1
    sd = lambda a: float(a.std(ddof=1)) if len(a) > 1 else float("nan")  # noqa: E731
    return CrossvalSummary(len(folds), float(val.mean()), sd(val), float(tr.mean()), sd(tr), counts)
