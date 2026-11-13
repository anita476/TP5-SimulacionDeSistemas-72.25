#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SIM="${SIM:-./build/ElusionSIM}"
PYTHON="${PYTHON:-python3}"
TRAJ_DIR="${TRAJ_DIR:-data/cruces_evento}"   # cruces recortados al inicio común f0 (trim_to_common_start.py)
OUTPUT_DIR="${OUTPUT_DIR:-data/experiments}"
SPEEDS_PATH="${SPEEDS_PATH:-data/pruebas_speeds.txt}"
TIMES_PATH="${TIMES_PATH:-data/tiempos_totales.txt}"
INITIAL_SPEEDS_PATH="${INITIAL_SPEEDS_PATH:-data/velocidades_iniciales.txt}"
DT="${DT:-0.001}"
INITIAL_VELOCITY="${INITIAL_VELOCITY:-experimental}" # zero | experimental
NEAREST_POINT_SCRIPT="scripts/calculate_nearest_point.py"
EQUAL_TIME_SCRIPT="scripts/calculate_equal_time.py"
DIFF_PLOT_SCRIPT="scripts/plot_nearest_point_diff.py"
TRAJ_PLOT_SCRIPT="scripts/plot_traj.py"

usage() {
  cat <<'EOF'
Uso:
  scripts/experiment_runner.sh --r-mins VALORES --action-distances VALORES

Los valores se pasan como listas separadas por coma, por ejemplo:
  scripts/experiment_runner.sh --r-mins 0.3,0.4 --action-distances 5,6

Opciones:
  --r-mins VALORES          Valores de --r_min a simular (requerido)
  --action-distances VALORES Valores de --action_distance a simular (requerido)
  -h, --help                Mostrar esta ayuda

Variables de entorno opcionales:
  SIM, PYTHON, TRAJ_DIR, OUTPUT_DIR, SPEEDS_PATH, TIMES_PATH, INITIAL_SPEEDS_PATH
  DT=0.001
  INITIAL_VELOCITY=experimental
  SKIP_COMPARISONS=1  no escribe los txt de métrica por simulación (collect_errors.py las recalcula)
EOF
}

r_mins_csv=""
action_distances_csv=""

while (($# > 0)); do
  case "$1" in
    --r-mins)
      (($# >= 2)) || { echo "Falta el valor de --r-mins." >&2; exit 2; }
      r_mins_csv="$2"
      shift 2
      ;;
    --action-distances)
      (($# >= 2)) || { echo "Falta el valor de --action-distances." >&2; exit 2; }
      action_distances_csv="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opción desconocida: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$r_mins_csv" || -z "$action_distances_csv" ]]; then
  echo "Se requieren --r-mins y --action-distances." >&2
  usage >&2
  exit 2
fi

parse_values() {
  local csv="$1"
  local label="$2"
  local value

  IFS=',' read -r -a parsed_values <<< "$csv"
  if ((${#parsed_values[@]} == 0)); then
    echo "La lista de $label está vacía." >&2
    exit 2
  fi

  for value in "${parsed_values[@]}"; do
    if [[ ! "$value" =~ ^[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$ ]] ||
      ! awk -v number="$value" 'BEGIN { exit !(number > 0) }'; then
      echo "Valor inválido para $label: $value (se requiere un número positivo)." >&2
      exit 2
    fi
  done
}

declare -a r_mins action_distances trajs
declare -a parsed_values
parse_values "$r_mins_csv" "--r-mins"
r_mins=("${parsed_values[@]}")
parse_values "$action_distances_csv" "--action-distances"
action_distances=("${parsed_values[@]}")

if [[ ! -x "$SIM" ]]; then
  echo "No se encontró el ejecutable del motor: $SIM" >&2
  exit 1
fi

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "No se encontró Python: $PYTHON" >&2
  exit 1
fi

for script in "$NEAREST_POINT_SCRIPT" "$EQUAL_TIME_SCRIPT" "$DIFF_PLOT_SCRIPT" "$TRAJ_PLOT_SCRIPT"; do
  if [[ ! -f "$script" ]]; then
    echo "No se encontró el script de comparación requerido: $script" >&2
    exit 1
  fi
done

for input_file in "$SPEEDS_PATH" "$TIMES_PATH" "$INITIAL_SPEEDS_PATH"; do
  if [[ ! -f "$input_file" ]]; then
    echo "No se encontró un archivo de entrada requerido: $input_file" >&2
    exit 1
  fi
done

shopt -s nullglob
trajs=("$TRAJ_DIR"/prueba*.txt)
if ((${#trajs[@]} == 0)); then
  echo "No se encontraron pruebas en $TRAJ_DIR." >&2
  exit 1
fi

for traj in "${trajs[@]}"; do
  name="$(basename "$traj" .txt)"
  for action_distance in "${action_distances[@]}"; do
    combination_dir="$OUTPUT_DIR/$name/action_distance_${action_distance}"
    mkdir -p "$combination_dir"

    for r_min in "${r_mins[@]}"; do
      output_stem="${name}_action_distance_${action_distance}_radio_${r_min}"
      output="$combination_dir/${output_stem}.txt"
      comparison_dir="$combination_dir/comparisons_radio_${r_min}"
      metric="$comparison_dir/${output_stem}_nearest_point.txt"
      echo "Simulando $name (r_min=$r_min, action_distance=$action_distance)"

      "$SIM" \
        --traj_path "$traj" \
        --r_min "$r_min" \
        --action_distance "$action_distance" \
        --v_path "$SPEEDS_PATH" \
        --time_path "$TIMES_PATH" \
        --initial_speeds_path "$INITIAL_SPEEDS_PATH" \
        --dt "$DT" \
        --initial_velocity "$INITIAL_VELOCITY" \
        --out-path "$output"

      if [[ "${SKIP_COMPARISONS:-0}" != "1" ]]; then
        mkdir -p "$comparison_dir"
        echo "Comparando $name (r_min=$r_min, action_distance=$action_distance)"
        "$PYTHON" "$NEAREST_POINT_SCRIPT" \
          --traj "$traj" \
          --sim "$output" \
          --out "$metric"

        "$PYTHON" "$EQUAL_TIME_SCRIPT" \
          --traj "$traj" \
          --sim "$output" \
          --out "$comparison_dir/${output_stem}_equal_time.txt"
      fi


      ##"$PYTHON" "$DIFF_PLOT_SCRIPT" \
      ##  --diff "$metric" \
      ##  --traj "$traj" \
      ##  --outdir "$comparison_dir"

      ##"$PYTHON" "$TRAJ_PLOT_SCRIPT" \
      ##  --traj "$traj" \
      ##  --sim "$output" \
      ##  --outdir "$comparison_dir"
    done
  done
done

echo "Experimentos y comparaciones terminados: ${#trajs[@]} pruebas, ${#r_mins[@]} valores de r_min y ${#action_distances[@]} action_distances."
