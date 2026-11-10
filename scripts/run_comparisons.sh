#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON="${PYTHON:-python3}"
TRAJ_DIR="data/comparisons/traj"
DIFF_DIR="data/comparisons/diffs"
METRIC_DIR="data/comparisons/metrics"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "No se encontró Python: $PYTHON" >&2
  exit 1
fi

shopt -s nullglob
trajs=(data/cruces_postprocess/prueba*.txt)

if ((${#trajs[@]} == 0)); then
  echo "No se encontraron pruebas en data/cruces_postprocess/." >&2
  exit 1
fi

mkdir -p "$TRAJ_DIR" "$DIFF_DIR" "$METRIC_DIR"

for traj in "${trajs[@]}"; do
  name="$(basename "$traj" .txt)"
  sim="data/sim/${name}_sim.txt"

  if [[ ! -f "$sim" ]]; then
    echo "No se encontró la simulación correspondiente: $sim" >&2
    exit 1
  fi

  metric="$METRIC_DIR/${name}_nearest_point.txt"
  echo "Comparando $traj con $sim"

  "$PYTHON" scripts/calculate_nearest_point.py \
    --traj "$traj" \
    --sim "$sim" \
    --out "$metric"

  "$PYTHON" scripts/plot_nearest_point_diff.py \
    --diff "$metric" \
    --traj "$traj" \
    --outdir "$DIFF_DIR"

  "$PYTHON" scripts/plot_traj.py \
    --traj "$traj" \
    --sim "$sim" \
    --outdir "$TRAJ_DIR"
done