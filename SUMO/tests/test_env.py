"""Environment checks: traci/sumolib must come from %SUMO_HOME%/tools and match the SUMO binary."""

import os
import re
import subprocess
from pathlib import Path

import pytest


def _sumo_home() -> Path:
    home = os.environ.get("SUMO_HOME")
    if not home:
        pytest.fail("SUMO_HOME is not set")
    return Path(home).resolve()


def test_traci_and_sumolib_come_from_sumo_home():
    import sumolib
    import traci

    tools = _sumo_home() / "tools"
    for mod in (traci, sumolib):
        assert Path(mod.__file__).resolve().is_relative_to(tools), mod.__file__


def test_sumo_and_netconvert_binaries_are_1_27():
    import sumolib

    for name in ("sumo", "netconvert"):
        out = subprocess.run([sumolib.checkBinary(name), "--version"],
                             capture_output=True, text=True, check=True).stdout
        assert re.search(r"\b1\.27\.\d+\b", out), out.splitlines()[0]
