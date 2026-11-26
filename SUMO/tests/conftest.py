"""Test-suite configuration.

The campaigns calibrate on the video days (config/experiment.yaml data_split, decisions D17-D19 of
docs/DECISIONS_2026-11-26.md). The tests were written for the three LITERATURE_PROXY calibration days (R44: 36 runs =
12 specs x 3 days), so the suite runs against a copy of experiment.yaml whose data split keeps the PROXY days; every
other setting is the real file's. thesis_sumo.config.load_experiment reads THESIS_EXPERIMENT (subprocesses inherit it).
"""
import atexit
import os
import tempfile
from pathlib import Path

import yaml

_REAL = Path(__file__).resolve().parents[1] / "config" / "experiment.yaml"
_exp = yaml.safe_load(_REAL.read_text(encoding="utf-8"))
_exp["data_split"]["calibration_days"] = ["PROXY_D1", "PROXY_D2", "PROXY_D3"]
_exp["data_split"]["validation_days"] = ["PROXY_D4", "PROXY_D5"]
_fd, _path = tempfile.mkstemp(prefix="experiment.proxy.", suffix=".yaml")
with os.fdopen(_fd, "w", encoding="utf-8") as _f:
    yaml.safe_dump(_exp, _f, allow_unicode=True, sort_keys=False)
os.environ["THESIS_EXPERIMENT"] = _path
atexit.register(lambda: os.path.exists(_path) and os.remove(_path))
