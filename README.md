# TP5-SimulacionDeSistemas-72.25
Simulación de dinámica peatonal



### Formato datos simulación
```
Personas: 38
Elusion 1 contra 1 de frente: en cada prueba una persona sale de la fila izquierda y otra de la fila derecha (abajo a la derecha) y se cruzan por y ~ 2 m. Pareja = la que pasa mas cerca (asignacion 1 a 1).
Pruebas/pasadas: 19
  prueba   1: sale izquierda   3, sale derecha  36, cuadros 20068-20261, distancia minima 0.91 m
  prueba   2: sale izquierda  V?, sale derecha  25, cuadros 20208-20391, distancia minima 0.88 m
  prueba   3: sale izquierda  43, sale derecha   1, cuadros 20370-20540, distancia minima 0.6 m
  prueba   4: sale izquierda  10, sale derecha   5, cuadros 20527-20734, distancia minima 0.54 m
  prueba   5: sale izquierda   4, sale derecha  12, cuadros 20632-20853, distancia minima 0.49 m
  prueba   6: sale izquierda   9, sale derecha   6, cuadros 20778-20971, distancia minima 0.8 m
  prueba   7: sale izquierda  20, sale derecha  44, cuadros 20910-21142, distancia minima 0.56 m
  prueba   8: sale izquierda  27, sale derecha  37, cuadros 21066-21298, distancia minima 0.83 m
  prueba   9: sale izquierda  16, sale derecha  39, cuadros 21228-21380, distancia minima 0.78 m
  prueba  10: sale izquierda  17, sale derecha  42, cuadros 21435-21635, distancia minima 0.63 m
  prueba  11: sale izquierda  23, sale derecha  24, cuadros 21536-21804, distancia minima 0.91 m
  prueba  12: sale izquierda  22, sale derecha  18, cuadros 21760-21960, distancia minima 0.64 m
  prueba  13: sale izquierda  15, sale derecha  35, cuadros 21877-22098, distancia minima 0.87 m
  prueba  14: sale izquierda  30, sale derecha  28, cuadros 22011-22206, distancia minima 0.92 m
  prueba  15: sale izquierda  46, sale derecha  34, cuadros 22278-22481, distancia minima 0.76 m
  prueba  16: sale izquierda  47, sale derecha  48, cuadros 22402-22639, distancia minima 0.68 m
  prueba  17: sale izquierda   2, sale derecha  45, cuadros 22561-22726, distancia minima 0.57 m
  prueba  18: sale izquierda  26, sale derecha  21, cuadros 22722-23000, distancia minima 0.57 m
  prueba  19: sale izquierda  29, sale derecha  38, cuadros 22902-23074, distancia minima 0.61 m

```


### Compilación 

Para compilar el motor de simulación:

```bash 
cmake -S . -B build && cmake --build build
```

y para los scripts crear el entorno virtual de python: 

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

### Esquema del sistema

Para generar el PNG con las dos partículas, sus trayectorias parabólicas, la
distancia de acción y `r_min`:

```bash
python scripts/plot_elusion.py
```

El archivo se guarda por defecto en
`docs/presentation/images/cuadro_inicial.png`. La ruta puede cambiarse con
`--out archivo.png`. El esquema es ilustrativo: no muestra valores numéricos en
los ejes ni en las cotas.

### Ejecución del motor 

Ejemplo de ejecución:

```bash 
./build/ElusionSIM \
  --traj_path data/cruces/prueba3.txt \
  --r_min 0.4 --action_distance 6.0 \
  --v_path data/pruebas_speeds.txt \
  --out-path data/sim/prueba3_NEW.txt
```

### Ejecución de experimentos

Para ejecutar todas las pruebas con cada combinación de `r_min` y
`action_distance`, pasando las listas separadas por coma:

```bash
scripts/experiment_runner.sh \
  --r-mins 0.3,0.4 \
  --action-distances 5,6 \
  --dt 0.001 \
  --initial-velocity experimental
```

El runner usa las pruebas de `data/cruces_evento/` (recortadas al inicio común, ver más abajo). Organiza los resultados
por prueba y luego por `action_distance`; dentro de cada carpeta guarda un TXT
por valor de `r_min` y ejecuta las comparaciones de trayectoria para cada
simulación. Las métricas se guardan en `comparisons_radio_<r_min>` junto con
sus gráficos. Por ejemplo:
`data/experiments/prueba1/action_distance_5/prueba1_action_distance_5_radio_0.3.txt`.
Los datos reales se toman de `data/cruces_evento/`. Se pueden cambiar los
directorios, el ejecutable, Python y los archivos de entrada mediante las
variables de entorno `TRAJ_DIR`, `OUTPUT_DIR`, `SIM`, `PYTHON`, `SPEEDS_PATH`,
`TIMES_PATH` y `INITIAL_SPEEDS_PATH`.

### Animación de trayectorias experimentales

```bash
python scripts/animate.py --trial 1 --show
python scripts/animate.py --trial 1 --out data/anim/prueba1.gif
python scripts/animate.py --trial 1 --mp4 data/anim/prueba1.mp4   # requiere ffmpeg
python scripts/animate.py --trial 1 --png data/anim/prueba1.png --frame 80
```

Experimental y simulada en la misma animación (`--data` el cruce real, `--sim` el
dump). Reales en línea continua, simuladas en punteado.

```bash
python scripts/animate_compare.py --data data/cruces/prueba1.txt --sim data/sim/prueba1.txt --show
python scripts/animate_compare.py --data data/cruces/prueba1.txt --sim data/sim/prueba1.txt --out data/anim/prueba1_compare.gif
python scripts/animate_compare.py --data data/cruces/prueba3.txt --sim data/sim/prueba6.txt --png data/anim/compare.png --frame 40
```

Tramo semihorizontal de cada prueba (sin la llegada a la posición inicial ni lo
posterior al destino), un `data/cruces/pruebaN.txt` por prueba con el mismo
formato que los datos, y su animación en `data/cruces/gif/pruebaN.gif`:

```bash
python scripts/extract_crossings.py
python scripts/animate_crossings.py
```

Duración total de cada cruce en segundos, calculada a partir de sus cuadros y
framerate. El script escribe `numero_cruce tiempo_total` en
`data/cruces_postprocess/tiempos_totales.txt` e imprime el timestep de cada archivo:

```bash
python scripts/get_timestep.py
```

Promedio de las rapideces entre cuadros consecutivos para cada
participante en cada prueba (en m/s), guardado como
`prueba id_particula rapidez_promedio` en `data/pruebas_speeds.txt`:

```bash
python scripts/calculate_speeds.py
```

Velocidades iniciales `vx` y `vy` de cada partícula en cada cruce, estimadas
con las dos primeras posiciones registradas y guardadas como
`cruce_num particula_id vx vy` en `data/cruces/velocidades_iniciales.txt`.
Para cada cruce, primero aparece la partícula de la izquierda y después la de
la derecha:

```bash
python scripts/get_initial_speeds.py
```

### Análisis de comportamiento

Lado y magnitud del desvío lateral en las pasadas reales. Para cada peatón, 
delta es la distancia con signo a la cuerda inicio-fin, positiva hacia su 
derecha (normal rx = uy, ry = -ux). Si |delta| < 0.10 m, cuenta como que 
no elude.

```bash
python scripts/analyze_behavior.py
```

Escribe en `data/behavior/` la tabla `elusion_behavior.txt` (una fila por
peatón, un bloque por prueba y el resumen) y las figuras
`desvios_por_prueba.png`, `desvios_histograma.png`, `trayectorias_reales.png`
y `resumen_lados.png`.

### Comparaciones de trayectorias 

Inicio común del evento. Los dos peatones entran al recorte en cuadros distintos; el evento empieza en `f0 = max` de los primeros cuadros (el primer cuadro en que ambos tienen dato), que es el "instante inicial" del enunciado. `trim_to_common_start.py` escribe en `data/cruces_evento/` una copia de cada `pruebaN.txt` de `cruces_postprocess/` sin las filas anteriores a `f0`, con la línea `# inicio comun: cuadro f0` en la cabecera (los originales no se tocan). El motor, los runners y los tres auxiliares usan esa carpeta:

```bash
python scripts/trim_to_common_start.py --in-dir data/cruces_postprocess --out-dir data/cruces_evento
python scripts/calculate_speeds.py --in-dir data/cruces_evento
python scripts/get_timestep.py --in-dir data/cruces_evento --out data/tiempos_totales.txt
python scripts/get_initial_speeds.py --in-dir data/cruces_evento --out data/velocidades_iniciales.txt
```

Con eso el motor escribe la fila `k` en `t = k·dt` (fila 0 = estado inicial, con la velocidad experimental) y la fila `k` es el cuadro `f0 + k`. Se integra con un paso igual a `dt` (un paso por cuadro).

Para obtener la comparación trayectoria - simulación de un cruce acorde a la métrica 2 del enunciado (punto más cercano, ecuación 2):

```
python scripts/calculate_nearest_point.py --traj data/cruces/prueba3.txt --sim data/sim/prueba3_sim.txt -o data/comparisons/prueba3_compare.txt 
``` 

Luego para graficar esa diferencia: 
```bash
python scripts/plot_nearest_point_diff.py --diff data/comparisons/prueba3_compare.txt --outdir data/comparisons
```

Métrica 1 del enunciado (iguales tiempos, ecuación 1): compara el cuadro `f` del experimento con la fila `k = f − f0` de la simulación. 

`run_comparisons.sh` y `experiment_runner.sh` calculan las dos.

```bash
python scripts/calculate_equal_time.py --traj data/cruces_evento/prueba3.txt --sim data/sim/prueba3_sim.txt -o data/comparisons/prueba3_equal_time.txt
python scripts/plot_nearest_point_diff.py --diff data/comparisons/prueba3_equal_time.txt --traj data/cruces_evento/prueba3.txt --outdir data/comparisons/equal_time
```
Y para graficar las trayectorias (png):

```bash
python scripts/plot_traj.py --traj data/cruces/prueba1.txt data/cruces/prueba1.txt --sim data/sim/prueba1_sim.txt data/sim/prueba1_sim.txt --outdir data/comparisons
```

### Calibración (puntos b, c y d)

A partir del barrido de `experiment_runner.sh` -> `scripts/run_calibration.sh`;

```bash
python scripts/collect_errors.py          # E[m, i, j] -> data/calibration/errors.txt (metric prueba r_min action_distance E_left E_right E_event)
python scripts/calibrate.py --partitions 20 --train-fraction 0.7 --seed 0
python scripts/plot_calibration.py        # figuras en data/calibration/figures/
```

`collect_errors.py` recalcula las dos métricas de cada simulación con las mismas funciones de `calculate_equal_time.py` y
`calculate_nearest_point.py`. 
`calibrate.py` escribe por métrica:

- `population_mK.txt`: `<E>` y su error estándar en cada punto de la grilla, con el óptimo el header (`# optimum r_min action_distance mean sem`). El óptimo se busca sólo entre los puntos que tienen todos los eventos.
- `individual_mK.txt`: óptimo de cada evento, su `E_m` con esos parámetros y con los poblacionales.
- `crossval_mK.txt`: una fila por partición aleatoria (óptimo sobre entrenamiento, error sobre entrenamiento y validación, eventos de validación); promedio y desvío en la cabecera.
- `summary.txt` y `summary.tex` (tabla lista para la presentación).

`plot_calibration.py` genera, por métrica: `EK_superficie.png`, `EK_corte_rmin.png`, `EK_corte_action_distance.png` (b),
`EK_optimos_individuales.png`, `EK_error_por_evento.png` (c) y `EK_validacion_cruzada.png` (d).

### Referencias

[CPP Reference](https://cppreference.com/)
