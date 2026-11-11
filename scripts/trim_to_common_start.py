#!/usr/bin/env python3
"""
Recorta cada cruce al instante inicial común del evento: f0 = max de los primeros cuadros de los
dos peatones (el primer cuadro en que ambos tienen dato). Se descartan las filas anteriores a f0.

Uso:
    python scripts/trim_to_common_start.py                       # in place en data/cruces_postprocess
    python scripts/trim_to_common_start.py --in-dir data/cruces --out-dir data/cruces_evento
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from traj import DEFAULT_CROSSINGS_DIR  # noqa: E402

_CROSSING_FILE = re.compile(r"prueba(\d+)\.txt")
_HEADER_RANGE = re.compile(r"^(# (?:izquierda|derecha): id (\S+), cuadros )(\d+)-(\d+)\s*$")
_COMMON_START = re.compile(r"^# inicio comun: cuadro (\d+)")


def trim_lines(lines: list[str]) -> tuple[list[str], int, int]:
    """Devuelve (líneas recortadas, f0, filas descartadas)."""
    data = [(i, l.split()) for i, l in enumerate(lines) if l.strip() and not l.lstrip().startswith("#")]
    first_frame: dict[str, int] = {}
    for _, c in data:
        pid, frame = c[0], int(c[1])
        first_frame[pid] = min(frame, first_frame.get(pid, frame))
    if len(first_frame) != 2:
        raise ValueError(f"se esperaban 2 ids, hay {sorted(first_frame)}")
    f0 = max(first_frame.values())

    drop = {i for i, c in data if int(c[1]) < f0}
    out = []
    for i, l in enumerate(lines):
        if i in drop:
            continue
        m = _HEADER_RANGE.match(l)
        if m:
            start = max(int(m.group(3)), f0)
            l = f"{m.group(1)}{start}-{m.group(4)}\n"
        if _COMMON_START.match(l):
            continue  # se reescribe abajo
        out.append(l)

    # la línea de inicio común va justo antes de la cabecera de columnas "# id frame ..."
    marker = f"# inicio comun: cuadro {f0} (max de los primeros cuadros de ambos peatones)\n"
    for j, l in enumerate(out):
        if l.startswith("# id frame"):
            out.insert(j, marker)
            break
    else:
        out.insert(0, marker)
    return out, f0, len(drop)


def main() -> None:
    ap = argparse.ArgumentParser(description="Recorta los cruces al inicio común f0 = max de los primeros cuadros")
    ap.add_argument("--in-dir", type=Path, default=DEFAULT_CROSSINGS_DIR, help=f"pruebaN.txt (default: {DEFAULT_CROSSINGS_DIR})")
    ap.add_argument("--out-dir", type=Path, default=None, help="directorio de salida (default: in place)")
    args = ap.parse_args()
    out_dir = args.out_dir or args.in_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted((int(m.group(1)), p) for p in args.in_dir.glob("prueba*.txt") if (m := _CROSSING_FILE.fullmatch(p.name)))
    if not files:
        sys.exit(f"{args.in_dir}: no hay archivos pruebaN.txt")
    for n, path in files:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        try:
            out, f0, dropped = trim_lines(lines)
        except ValueError as error:
            sys.exit(f"{path}: {error}")
        (out_dir / path.name).write_text("".join(out), encoding="utf-8")
        print(f"prueba {n:2d}: f0 = {f0}, {dropped} filas descartadas")


if __name__ == "__main__":
    main()
