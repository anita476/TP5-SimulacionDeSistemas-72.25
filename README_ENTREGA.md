# ElusionSIM

Motor de simulación (C++17) de un cruce peatonal 1 contra 1. Usa Social Force Model (Helbing et al., 2000) con una capa de elusión parametrizada por `d_lat` y `d_act`.

El target de cada peatón es la posición inicial del otro. La integración es Euler semi-implícito (primero velocidad, después posición). El volcado coincide con el framerate experimental (`15.0192 fps`).

## Compilación

Requiere CMake ≥ 3.16 y un compilador C++17. `argparse` se descarga en el configure.

```bash
cmake -S . -B build && cmake --build build
```

El ejecutable queda en `build/ElusionSIM` (`build/ElusionSIM.exe` en Windows).

## Ejecución

```bash
./build/ElusionSIM \
  --traj_path data/cruces_evento/prueba3.txt \
  --d_lat 0.4 --d_act 6.0 \
  --v_path data/pruebas_speeds.txt \
  --time_path data/tiempos_totales.txt \
  --initial_speeds_path data/velocidades_iniciales.txt \
  --initial_velocity experimental \
  --dt 0.001 \
  --out-path data/sim/prueba3.txt
```

`--traj_path` tiene que llamarse `pruebaN.txt`: el número `N` se usa para leer las rapideces, el tiempo final y las velocidades iniciales de esa prueba.

## Parámetros

Fijos (valores por defecto del motor):

| Parámetro | Valor |
| --- | --- |
| Radio `r` | 0.25 m |
| Masa | 80 kg |
| `τ` | 0.5 s |
| `k_n` | 1.2×10⁵ N/m |
| `k_t` | 2.4×10⁵ kg/(m s) |

A calibrar:

- `--d_lat`: margen lateral extra respecto del radio del otro peatón.
- `--d_act`: distancia entre centros a partir de la cual puede activarse la elusión.

Otros:

- `--dt`: paso de integración máximo, en segundos. Tiene que estar en `(0, dt₂]`, con `dt₂ = 1/15.0192 s`. El paso efectivo es `dt₂ / n`, `n = round(dt₂ / dt)`.
- `--initial_velocity`: `experimental` (default) usa `(vx, vy)` del primer cuadro; `zero` arranca en reposo.

## Entrada

**Trayectoria experimental** (`--traj_path`). Líneas `#` se ignoran.

```
id  frame  x/m  y/m  markerID
```

Las primeras filas de cada id dan la posición inicial. El evento se recorta al primer cuadro en el que ambos peatones tienen dato.

**Rapideces deseadas** (`--v_path`), dos filas por prueba (izquierda, derecha):

```
prueba  id  v0
```

**Tiempo final** (`--time_path`):

```
prueba  t_final
```

**Velocidades iniciales** (`--initial_speeds_path`):

```
prueba  id  vx  vy
```

## Salida

Una fila por peatón y por cuadro experimental (`t = k · dt₂`):

```
particle_id  time  x  y  vx  vy
```
