#!/usr/bin/env bash
# Recolecta E[m, i, j] desde el barrido de experiment_runner.sh, calibra (b, c, d) y genera las figuras y la tabla.
#   scripts/run_calibration.sh                       # data/experiments -> data/calibration/
#   EXPERIMENTS_DIR=otra OUT_DIR=otra/calib scripts/run_calibration.sh --partitions 50 --seed 1   # args extra van a calibrate.py
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
PYTHON="${PYTHON:-python3}"
EXPERIMENTS_DIR="${EXPERIMENTS_DIR:-data/experiments}"
TRAJ_DIR="${TRAJ_DIR:-data/cruces_evento}"
OUT_DIR="${OUT_DIR:-data/calibration}"

"$PYTHON" scripts/collect_errors.py --experiments-dir "$EXPERIMENTS_DIR" --traj-dir "$TRAJ_DIR" --out "$OUT_DIR/errors.txt"
"$PYTHON" scripts/calibrate.py --errors "$OUT_DIR/errors.txt" --outdir "$OUT_DIR" "$@"
"$PYTHON" scripts/plot_calibration.py --indir "$OUT_DIR" --outdir "$OUT_DIR/figures"
