"""Create .venv with the project, SUMO 1.27 tools and libsumo, on Windows or Linux:

    py -3.12 scripts/setup_env.py        # Windows (uses the installed SUMO at %SUMO_HOME%)
    python3.12 scripts/setup_env.py      # Linux (no SUMO_HOME: installs the eclipse-sumo 1.27.0 wheel into .venv)

Run from SUMO/. Afterwards `.venv/Scripts/python -m pytest` (Windows) or `.venv/bin/python -m pytest` (Linux).
`sumo_tools.pth` puts `<SUMO_HOME>/tools` on sys.path (traci/sumolib matching the binary, never the PyPI copies)
and sets SUMO_HOME for every venv process when it is not set, so nothing has to be exported by hand.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

SUMO_VERSION = "1.27.0"
ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


UV = shutil.which("uv")  # used when present: Ubuntu's python3.12 has no ensurepip without the python3.12-venv package


def pip(*args: str) -> None:
    cmd = [UV, "pip", "install", "-q", "--python", str(PY)] if UV else [str(PY), "-m", "pip", "install", "-q"]
    subprocess.run([*cmd, *args], check=True, cwd=ROOT)


def venv_python(code: str) -> str:
    return subprocess.run([str(PY), "-c", code], check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    if not PY.exists():
        if UV:
            subprocess.run([UV, "venv", "-q", "--python", sys.executable, str(VENV)], check=True)
        else:
            venv.create(VENV, with_pip=True)
    pip("-e", ".[dev,llm,optuna]")
    home = os.environ.get("SUMO_HOME")
    if not home:  # Linux / no installed SUMO: the official wheel ships the same binaries and tools
        pip(f"eclipse-sumo=={SUMO_VERSION}")
        home = venv_python("import sumo, os; print(os.path.dirname(sumo.__file__))")
    # --no-deps: libsumo's declared deps pull traci/sumolib 1.28 from PyPI and shadow the SUMO_HOME copies
    pip("--no-deps", f"libsumo=={SUMO_VERSION}", f"sumo-data=={SUMO_VERSION}")
    site = Path(venv_python("import sysconfig; print(sysconfig.get_paths()['purelib'])"))
    tools = Path(home) / "tools"
    (site / "sumo_tools.pth").write_text(
        f"{tools}\nimport os; os.environ.setdefault('SUMO_HOME', {str(home)!r})\n", encoding="utf-8")
    sumo = Path(home) / "bin" / ("sumo.exe" if os.name == "nt" else "sumo")
    version = subprocess.run([str(sumo), "--version"], check=True, capture_output=True, text=True).stdout
    if f"sumo {SUMO_VERSION[:4]}" not in version:
        sys.exit(f"{sumo} is not SUMO {SUMO_VERSION[:4]}.x: {version.splitlines()[0]}")
    print(f"ok: {version.splitlines()[0]}, SUMO_HOME={home}, python={PY}")


if __name__ == "__main__":
    main()
