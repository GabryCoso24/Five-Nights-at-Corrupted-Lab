from __future__ import annotations

import shutil
import subprocess
import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENTRYPOINT = ROOT / "main.py"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_FILE = ROOT / "gioco_scuola.spec"


def main() -> int:
    if not ENTRYPOINT.exists():
        print(f"Impossibile trovare {ENTRYPOINT.name} nella cartella del progetto.")
        return 1

    if shutil.which("pyinstaller") is None:
        print("PyInstaller non e installato nel Python attivo.")
        print("Installa prima con: python -m pip install pyinstaller")
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "gioco_scuola",
        "--add-data",
        f"assets{os.pathsep}assets",
        str(ENTRYPOINT),
    ]

    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        return result.returncode

    exe_path = DIST_DIR / "gioco_scuola.exe"
    print()
    print(f"Eseguibile creato in: {exe_path}")
    print(f"Spec file: {SPEC_FILE}")
    print(f"Build folder: {BUILD_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())