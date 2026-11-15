"""Export the two YouTube MP4s (16:9, 1920×1080) with descriptive titles."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPARE = ROOT / "scripts" / "animate_compare.py"
DATA = ROOT / "data" / "cruces_evento"
SIM = ROOT / "data" / "sim"
OUT = ROOT / "docs" / "presentation" / "images"

JOBS = (
    {
        "trial": 15,
        "sim": "prueba15_dlat025_dact5.txt",
        "caption": r"Ejecución evento 15, menor $E^{(2)}_m$",
        "mp4": "Ejecucion_evento_15_menor_E2.mp4",
    },
    {
        "trial": 11,
        "sim": "prueba11_dlat025_dact5.txt",
        "caption": r"Ejecución evento 11, mayor $E^{(2)}_m$",
        "mp4": "Ejecucion_evento_11_mayor_E2.mp4",
    },
)


def main() -> None:
    python = sys.executable
    OUT.mkdir(parents=True, exist_ok=True)
    for job in JOBS:
        sim = SIM / job["sim"]
        if not sim.is_file():
            sys.exit(f"missing simulation dump: {sim}")
        dest = OUT / job["mp4"]
        cmd = [
            python,
            str(COMPARE),
            "--data",
            str(DATA / f"prueba{job['trial']}.txt"),
            "--sim",
            str(sim),
            "--mp4",
            str(dest),
            "--figsize",
            "16",
            "9",
            "--fps",
            "12",
            "--no-untracked",
            "--caption",
            job["caption"],
        ]
        print(" ".join(cmd))
        subprocess.run(cmd, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
