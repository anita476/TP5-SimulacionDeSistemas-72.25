#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SIM="./build/ElusionSIM"
ANIMATE="scripts/animate_sim.py"
PYTHON="${PYTHON:-python3}"

if [[ ! -x "$SIM" ]]; then
  echo "No se encontró el ejecutable $SIM. Compilá el proyecto primero." >&2
  exit 1
fi

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "No se encontró Python: $PYTHON" >&2
  exit 1
fi

mkdir -p data/sim
found=false

for traj in data/cruces_evento/prueba*.txt; do   # cruces recortados al inicio común f0 (trim_to_common_start.py)
  [[ -f "$traj" ]] || continue
  found=true

  name="$(basename "$traj" .txt)"
  sim="data/sim/${name}_sim.txt"

  echo "Procesando $traj"

  "$SIM" \
    --traj_path "$traj" \
    --r_min 0.4 \
    --action_distance 6.0 \
    --v_path data/pruebas_speeds.txt \
    --out-path "$sim"

  "$PYTHON" "$ANIMATE" "$sim" \
    --out "data/sim/animations/${name}_sim.gif" \
    --png "data/sim/animations/${name}_sim.png" \
    --r 0.01
done

if [[ "$found" == false ]]; then
  echo "No se encontraron pruebas en data/cruces_evento/ (correr scripts/trim_to_common_start.py)." >&2
  exit 1
fi